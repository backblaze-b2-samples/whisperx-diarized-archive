"""WhisperX word-aligned transcription (local compute, lazy imports).

WhisperX loads a faster-whisper model, transcribes, then runs a forced
alignment pass so every word carries start/end timestamps. Those word-level
times are what diarization needs to attribute speakers precisely.

All heavy imports live inside `transcribe_bytes` so importing this module is
free and the API boots without requirements-ml.txt.
"""

import contextlib
import logging
import os
import tempfile

from app.config import settings
from app.service.engine._torch_safe import allowlist_pyannote_globals
from app.service.engine.errors import MissingMLDependencies

logger = logging.getLogger(__name__)


def _write_temp(media_bytes: bytes, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix or ".bin", prefix="wxda_")
    with os.fdopen(fd, "wb") as f:
        f.write(media_bytes)
    return path


def transcribe_bytes(media_bytes: bytes, suffix: str = "") -> dict:
    """Transcribe raw media bytes into a word-aligned result.

    Returns a dict:
        {
          "language": str,
          "segments": [ {start, end, text, words: [ {word, start, end, score} ] } ],
          "word_segments": [ {word, start, end, score}, ... ],
        }

    Raises MissingMLDependencies if whisperx / its backends are absent.
    """
    try:
        import whisperx  # type: ignore
    except ImportError as e:
        raise MissingMLDependencies("Transcription") from e

    path = _write_temp(media_bytes, suffix)
    try:
        device = settings.whisperx_device
        compute_type = settings.whisperx_compute_type
        logger.info(
            "Loading WhisperX model=%s device=%s compute=%s",
            settings.whisperx_model,
            device,
            compute_type,
        )
        # whisperx.load_model eagerly loads a pyannote VAD checkpoint via
        # torch.load; under torch 2.6+ that needs the safe-globals allowlist.
        # Applied here (transcription always runs first) so it also covers the
        # later DiarizationPipeline load — add_safe_globals is process-global.
        allowlist_pyannote_globals()
        model = whisperx.load_model(
            settings.whisperx_model,
            device,
            compute_type=compute_type,
        )
        audio = whisperx.load_audio(path)
        result = model.transcribe(audio, batch_size=settings.whisperx_batch_size)
        language = result.get("language", "en")

        # Forced alignment -> word-level timestamps.
        try:
            align_model, metadata = whisperx.load_align_model(
                language_code=language, device=device
            )
            aligned = whisperx.align(
                result["segments"],
                align_model,
                metadata,
                audio,
                device,
                return_char_alignments=False,
            )
            segments = aligned.get("segments", result["segments"])
            word_segments = aligned.get("word_segments", [])
        except Exception:
            logger.warning("Alignment failed; using segment-level times only", exc_info=True)
            segments = result["segments"]
            word_segments = []

        return {
            "language": language,
            "segments": segments,
            "word_segments": word_segments,
        }
    finally:
        with contextlib.suppress(OSError):
            os.unlink(path)
