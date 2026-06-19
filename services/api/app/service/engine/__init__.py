"""Local ML inference engine for the transcription pipeline.

Everything here is LAZY: heavy dependencies (whisperx, faster-whisper,
pyannote.audio, torch, sentence-transformers) are imported *inside the
functions*, never at module top level. That keeps the API bootable and
`pnpm test:api` / `pnpm check:structure` green without requirements-ml.txt
installed.

This package performs local compute on bytes already pulled from B2 by the
repo layer. It deliberately does NOT touch boto3 — the boto3-only-in-repo
invariant stays intact (ML inference is compute, not storage).

A MissingMLDependencies error is raised with an actionable message when the
heavy stack is absent, so callers can surface a clear "install
requirements-ml.txt" hint instead of an opaque ImportError.
"""

from app.service.engine.diarize import diarize_words, is_diarization_available
from app.service.engine.embed import embed_query, embed_segments
from app.service.engine.errors import MissingMLDependencies
from app.service.engine.transcribe import transcribe_bytes

__all__ = [
    "MissingMLDependencies",
    "diarize_words",
    "embed_query",
    "embed_segments",
    "is_diarization_available",
    "transcribe_bytes",
]
