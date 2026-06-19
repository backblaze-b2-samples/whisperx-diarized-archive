"""Pydantic models for the transcript archive.

Pure data — no logic, no imports from other app layers (types is the
bottom layer). These are the contract shared with the frontend via
packages/shared/src/types.ts.
"""

from typing import Literal

from pydantic import BaseModel

JobStatus = Literal[
    "queued",
    "transcribing",
    "diarizing",
    "embedding",
    "writing",
    "done",
    "error",
]

SearchMode = Literal["keyword", "semantic"]


class Segment(BaseModel):
    """One contiguous chunk of transcript with optional speaker label."""

    start: float
    end: float
    text: str
    speaker: str | None = None


class Word(BaseModel):
    """A single word with alignment timing and optional speaker."""

    word: str
    start: float | None = None
    end: float | None = None
    score: float | None = None
    speaker: str | None = None


class Transcript(BaseModel):
    """Word-aligned transcript + speaker-attributed segments for one media key."""

    key: str
    language: str | None = None
    duration: float | None = None
    diarized: bool = False
    speakers: list[str] = []
    segments: list[Segment] = []


class SpeakerSegment(BaseModel):
    """A speaker segment persisted to segments/{key}.json."""

    index: int
    speaker: str | None = None
    start: float
    end: float
    text: str


class SearchHit(BaseModel):
    """A single search result, scored and traceable back to its source."""

    key: str
    segment_index: int
    speaker: str | None = None
    start: float
    end: float
    text: str
    score: float


class TranscriptionJob(BaseModel):
    """Live, process-local job progress. Ephemeral — see service/jobs.py."""

    id: str
    key: str
    status: JobStatus
    progress: float = 0.0
    message: str | None = None
    error: str | None = None
    diarized: bool = False
    created_at: str
    updated_at: str


class ArchiveItem(BaseModel):
    """A media file in the library plus its derived transcription status."""

    key: str
    filename: str
    size_bytes: int
    size_human: str
    content_type: str
    uploaded_at: str
    url: str | None = None
    transcribed: bool = False
    diarized: bool = False
    duration: float | None = None
    speakers: int | None = None


class ArchiveStats(BaseModel):
    """Dashboard metrics derived from B2 listings + artifacts."""

    media_files: int
    transcribed_files: int
    speakers_detected: int
    segments_indexed: int
    hours_processed: float
    storage_bytes: int
    storage_human: str
