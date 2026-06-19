"""Orchestrates transcription of one media file.

Flow (the write-amplification story — one media file fans out into three
artifacts on B2):

    media/{key}  --download-->  engine.transcribe  --align words-->
                 engine.diarize (speakers, if HF_TOKEN)  -->
                 engine.embed (one vector per segment)  -->
    write  transcripts/{key}.json, segments/{key}.json, embeddings/{key}.json

This module owns NO boto3 — it calls the repo for all B2 I/O and the engine
for all local ML compute. The engine's heavy imports stay lazy, so importing
this module is cheap.
"""

import logging
import os

from app.config import settings
from app.repo import get_object_bytes, object_exists, put_json
from app.service import jobs
from app.service.engine import (
    diarize_words,
    embed_segments,
    is_diarization_available,
    transcribe_bytes,
)
from app.types import Segment, SpeakerSegment, Transcript

logger = logging.getLogger(__name__)

ARTIFACT_PREFIXES = {
    "transcript": "transcripts/",
    "segment": "segments/",
    "embedding": "embeddings/",
}


def _relative_key(media_key: str) -> str:
    """Strip the media prefix so artifact keys mirror the source filename."""
    prefix = settings.archive_media_prefix
    return media_key[len(prefix):] if media_key.startswith(prefix) else media_key


def transcript_key(media_key: str) -> str:
    return f"{ARTIFACT_PREFIXES['transcript']}{_relative_key(media_key)}.json"


def segment_key(media_key: str) -> str:
    return f"{ARTIFACT_PREFIXES['segment']}{_relative_key(media_key)}.json"


def embedding_key(media_key: str) -> str:
    return f"{ARTIFACT_PREFIXES['embedding']}{_relative_key(media_key)}.json"


def is_transcribed(media_key: str) -> bool:
    """Authoritative check: does this file's transcript artifact exist in B2?"""
    return object_exists(transcript_key(media_key))


def _build_segments(raw_segments: list[dict]) -> list[Segment]:
    out: list[Segment] = []
    for s in raw_segments:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        out.append(
            Segment(
                start=float(s.get("start") or 0.0),
                end=float(s.get("end") or 0.0),
                text=text,
                speaker=s.get("speaker"),
            )
        )
    return out


def transcribe_media(media_key: str, job_id: str | None = None) -> Transcript:
    """Run the full pipeline for one media key and persist artifacts to B2.

    Updates the live job registry as it advances when a job_id is given.
    Raises on engine / B2 failure (caller records the error on the job).
    """

    def progress(status, pct, message=None, diarized=None):
        if job_id:
            jobs.update_job(
                job_id, status=status, progress=pct, message=message, diarized=diarized
            )

    suffix = os.path.splitext(media_key)[1]

    progress("transcribing", 0.1, "Downloading media from B2")
    media_bytes = get_object_bytes(media_key)

    progress("transcribing", 0.2, "Transcribing (WhisperX)")
    result = transcribe_bytes(media_bytes, suffix=suffix)
    segments_raw = result["segments"]
    language = result.get("language")

    diarized = False
    speakers: list[str] = []
    if is_diarization_available():
        progress("diarizing", 0.5, "Assigning speakers (pyannote)")
        segments_raw, speakers = diarize_words(media_bytes, segments_raw, suffix=suffix)
        diarized = bool(speakers)
    else:
        progress("diarizing", 0.5, "HF_TOKEN unset — transcribe-only (no speakers)")

    segments = _build_segments(segments_raw)
    duration = segments[-1].end if segments else None

    progress("embedding", 0.7, "Embedding segments (sentence-transformers)")
    vectors = embed_segments([s.text for s in segments])

    progress("writing", 0.9, "Writing artifacts to B2")
    transcript = Transcript(
        key=media_key,
        language=language,
        duration=duration,
        diarized=diarized,
        speakers=speakers,
        segments=segments,
    )
    put_json(transcript_key(media_key), transcript.model_dump())

    speaker_segments = [
        SpeakerSegment(
            index=i, speaker=s.speaker, start=s.start, end=s.end, text=s.text
        ).model_dump()
        for i, s in enumerate(segments)
    ]
    put_json(segment_key(media_key), {"key": media_key, "segments": speaker_segments})

    put_json(
        embedding_key(media_key),
        {
            "key": media_key,
            "model": settings.embedding_model,
            "dim": len(vectors[0]) if vectors else 0,
            "segments": [
                {
                    "index": i,
                    "speaker": s.speaker,
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                    "vector": vectors[i] if i < len(vectors) else [],
                }
                for i, s in enumerate(segments)
            ],
        },
    )

    progress("done", 1.0, f"Done — {len(segments)} segments, {len(speakers)} speakers", diarized)
    logger.info(
        "Transcribed key=%s segments=%d speakers=%d diarized=%s",
        media_key,
        len(segments),
        len(speakers),
        diarized,
    )
    return transcript


def run_job(job_id: str, media_key: str) -> None:
    """Background entrypoint: run the pipeline, recording errors on the job."""
    try:
        transcribe_media(media_key, job_id=job_id)
    except Exception as e:  # surface any failure on the job
        logger.exception("Transcription job failed: key=%s", media_key)
        jobs.update_job(job_id, status="error", error=str(e))
