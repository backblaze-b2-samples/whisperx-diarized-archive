"""Archive router: transcription jobs, library, transcripts, search, stats.

Thin HTTP layer — validation + status mapping only. All work flows through
the service layer (transcription / archive / search / jobs); no boto3, no ML
imports here.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.service import jobs
from app.service.archive import (
    TranscriptNotFound,
    get_archive_items,
    get_archive_stats,
    get_transcript,
)
from app.service.files import FileKeyError, validate_key
from app.service.search import search as run_search
from app.service.transcription import is_transcribed, run_job
from app.types import (
    ArchiveItem,
    ArchiveStats,
    SearchHit,
    Transcript,
    TranscriptionJob,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/archive/transcribe", response_model=TranscriptionJob)
async def transcribe_endpoint(payload: dict, background_tasks: BackgroundTasks):
    key = (payload or {}).get("key", "")
    try:
        validate_key(key)
    except FileKeyError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None

    # Don't double-enqueue a file that's already being processed.
    existing = jobs.active_job_for(key)
    if existing is not None:
        return existing

    job = jobs.create_job(key)
    background_tasks.add_task(run_job, job.id, key)
    logger.info("Enqueued transcription job=%s key=%s", job.id, key)
    return job


@router.get("/archive/jobs", response_model=list[TranscriptionJob])
async def list_jobs_endpoint():
    return jobs.list_jobs()


@router.get("/archive/jobs/{job_id}", response_model=TranscriptionJob)
async def get_job_endpoint(job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/archive/items", response_model=list[ArchiveItem])
async def list_items_endpoint():
    return get_archive_items()


@router.get("/archive/stats", response_model=ArchiveStats)
async def stats_endpoint():
    return get_archive_stats()


@router.get("/archive/search", response_model=list[SearchHit])
async def search_endpoint(
    q: str = Query(..., min_length=1),
    mode: str = Query("keyword"),
    k: int = Query(20, ge=1, le=100),
):
    if mode not in ("keyword", "semantic"):
        raise HTTPException(status_code=400, detail="mode must be keyword|semantic")
    return run_search(q, mode=mode, k=k)


@router.get("/archive/transcripts/{key:path}", response_model=Transcript)
async def transcript_endpoint(key: str):
    try:
        return get_transcript(key)
    except FileKeyError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except TranscriptNotFound:
        # Distinguish "not transcribed yet" from a bad key for the UI.
        detail = (
            "Not transcribed yet" if not _safe_is_transcribed(key) else "Transcript missing"
        )
        raise HTTPException(status_code=404, detail=detail) from None


def _safe_is_transcribed(key: str) -> bool:
    try:
        return is_transcribed(key)
    except Exception:  # best-effort detail only
        return False
