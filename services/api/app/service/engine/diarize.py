"""Speaker diarization via pyannote (local compute, lazy imports).

Uses WhisperX's DiarizationPipeline (a thin wrapper over pyannote's
`speaker-diarization-3.1`) to label which speaker is talking when, then
assigns those labels onto the word-aligned transcript segments.

Graceful degradation is a hard requirement: if `HF_TOKEN` is unset we do NOT
attempt to download pyannote's gated weights. `is_diarization_available()`
returns False and the caller proceeds transcribe-only with a clear warning,
so the app still runs end-to-end with B2 credentials alone.
"""

import contextlib
import logging
import os
import tempfile

from app.config import settings
from app.service.engine.errors import MissingMLDependencies

logger = logging.getLogger(__name__)


def is_diarization_available() -> bool:
    """True only if a HuggingFace token is configured for gated weights."""
    return bool(settings.hf_token.strip())


def _write_temp(media_bytes: bytes, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix or ".bin", prefix="wxda_diar_")
    with os.fdopen(fd, "wb") as f:
        f.write(media_bytes)
    return path


def diarize_words(media_bytes: bytes, segments: list[dict], suffix: str = "") -> tuple[list[dict], list[str]]:
    """Assign speaker labels to the given word-aligned segments.

    Returns (segments_with_speakers, sorted_unique_speakers).

    Raises MissingMLDependencies if pyannote / whisperx are absent. Callers
    should first check `is_diarization_available()` to honor graceful
    transcribe-only degradation when HF_TOKEN is unset.
    """
    if not is_diarization_available():
        logger.warning(
            "HF_TOKEN not set — skipping diarization (transcribe-only). "
            "Add a free HuggingFace token to enable speaker labels."
        )
        return segments, []

    try:
        import whisperx  # type: ignore
        from whisperx.diarize import DiarizationPipeline  # type: ignore
    except ImportError as e:
        raise MissingMLDependencies("Diarization") from e

    path = _write_temp(media_bytes, suffix)
    try:
        pipeline = DiarizationPipeline(
            model_name=settings.diarization_model,
            use_auth_token=settings.hf_token,
            device=settings.whisperx_device,
        )
        audio = whisperx.load_audio(path)
        diarize_df = pipeline(audio)
        result = whisperx.assign_word_speakers(diarize_df, {"segments": segments})
        labeled = result.get("segments", segments)
        speakers = sorted(
            {s["speaker"] for s in labeled if s.get("speaker")}
        )
        return labeled, speakers
    finally:
        with contextlib.suppress(OSError):
            os.unlink(path)
