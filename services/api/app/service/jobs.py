"""Process-local transcription job registry.

EPHEMERAL by design: this tracks *live* progress (queued -> transcribing ->
diarizing -> embedding -> writing -> done/error) for the UI. It resets on
restart and is not shared across workers. The authoritative answer to "is
this file transcribed?" is the existence of its transcripts/{key}.json
artifact in B2 (see service/transcription.py and service/stats.py), never
this registry.

Thread-safe so a FastAPI BackgroundTask thread can update progress while the
request thread reads it.
"""

import uuid
from datetime import UTC, datetime
from threading import Lock

from app.types import JobStatus, TranscriptionJob

_jobs: dict[str, TranscriptionJob] = {}
_lock = Lock()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def create_job(key: str) -> TranscriptionJob:
    """Register a new queued job for a media key and return it."""
    job_id = uuid.uuid4().hex
    now = _now()
    job = TranscriptionJob(
        id=job_id,
        key=key,
        status="queued",
        progress=0.0,
        created_at=now,
        updated_at=now,
    )
    with _lock:
        _jobs[job_id] = job
    return job


def update_job(
    job_id: str,
    *,
    status: JobStatus | None = None,
    progress: float | None = None,
    message: str | None = None,
    error: str | None = None,
    diarized: bool | None = None,
) -> None:
    """Patch a job's live fields. No-op if the job id is unknown."""
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        data = job.model_dump()
        if status is not None:
            data["status"] = status
        if progress is not None:
            data["progress"] = progress
        if message is not None:
            data["message"] = message
        if error is not None:
            data["error"] = error
        if diarized is not None:
            data["diarized"] = diarized
        data["updated_at"] = _now()
        _jobs[job_id] = TranscriptionJob(**data)


def get_job(job_id: str) -> TranscriptionJob | None:
    with _lock:
        return _jobs.get(job_id)


def list_jobs() -> list[TranscriptionJob]:
    with _lock:
        return sorted(
            _jobs.values(), key=lambda j: j.created_at, reverse=True
        )


def active_job_for(key: str) -> TranscriptionJob | None:
    """Return a non-terminal job for this key, if any (avoid double-enqueue)."""
    terminal = {"done", "error"}
    with _lock:
        for job in _jobs.values():
            if job.key == key and job.status not in terminal:
                return job
    return None
