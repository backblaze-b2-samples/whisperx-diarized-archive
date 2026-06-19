"""Library + dashboard aggregations derived from B2 listings and artifacts.

The library is the media/ prefix; transcription status is derived from the
existence (and contents) of the matching transcripts/{key}.json artifact —
there is no application DB. Dashboard stats roll up the same artifacts.

No boto3 — everything goes through the repo. ML lives in the engine, not here.
"""

import logging

from app.config import settings
from app.repo import get_json, list_files
from app.service.files import validate_key
from app.service.transcription import transcript_key
from app.types import ArchiveItem, ArchiveStats, Transcript
from app.types.formatting import humanize_bytes

logger = logging.getLogger(__name__)


class TranscriptNotFound(Exception):
    """Raised when a media key has no transcript artifact yet."""


def _media_files():
    return list_files(prefix=settings.archive_media_prefix, max_keys=1000)


def get_archive_items() -> list[ArchiveItem]:
    """List media files plus their derived transcription status."""
    items: list[ArchiveItem] = []
    for f in _media_files():
        # Skip the bare "folder marker" object some tools create.
        if f.key.endswith("/"):
            continue
        transcript = get_json(transcript_key(f.key))
        transcribed = transcript is not None
        diarized = bool(transcript.get("diarized")) if transcript else False
        duration = transcript.get("duration") if transcript else None
        speakers = len(transcript.get("speakers", [])) if transcript else None
        items.append(
            ArchiveItem(
                key=f.key,
                filename=f.filename,
                size_bytes=f.size_bytes,
                size_human=f.size_human,
                content_type=f.content_type,
                uploaded_at=f.uploaded_at.isoformat(),
                url=f.url,
                transcribed=transcribed,
                diarized=diarized,
                duration=duration,
                speakers=speakers,
            )
        )
    items.sort(key=lambda i: i.uploaded_at, reverse=True)
    return items


def get_transcript(media_key: str) -> Transcript:
    """Fetch a stored transcript. Raises TranscriptNotFound if absent."""
    validate_key(media_key)
    obj = get_json(transcript_key(media_key))
    if obj is None:
        raise TranscriptNotFound(media_key)
    return Transcript(**obj)


def get_archive_stats() -> ArchiveStats:
    """Roll up archive metrics for the dashboard."""
    media = [f for f in _media_files() if not f.key.endswith("/")]
    media_files = len(media)
    storage_bytes = sum(f.size_bytes for f in media)

    transcribed_files = 0
    speakers: set[str] = set()
    segments_indexed = 0
    seconds_processed = 0.0

    for f in media:
        transcript = get_json(transcript_key(f.key))
        if not transcript:
            continue
        transcribed_files += 1
        for sp in transcript.get("speakers", []):
            # Namespace speakers by file — "SPEAKER_00" repeats across files.
            speakers.add(f"{f.key}::{sp}")
        segs = transcript.get("segments", [])
        segments_indexed += len(segs)
        if transcript.get("duration"):
            seconds_processed += float(transcript["duration"])

    return ArchiveStats(
        media_files=media_files,
        transcribed_files=transcribed_files,
        speakers_detected=len(speakers),
        segments_indexed=segments_indexed,
        hours_processed=round(seconds_processed / 3600.0, 2),
        storage_bytes=storage_bytes,
        storage_human=humanize_bytes(storage_bytes),
    )
