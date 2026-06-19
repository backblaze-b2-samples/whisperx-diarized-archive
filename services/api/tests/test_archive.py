"""Tests for the archive library, transcripts, stats, and jobs endpoints.

These mock the repo + engine so they run WITHOUT the ML stack installed —
the whole point of the lazy-import design.
"""

from datetime import UTC, datetime

import pytest

from app.service import archive as archive_service
from app.types import FileMetadata


def _media(key: str) -> FileMetadata:
    return FileMetadata(
        key=key,
        filename=key.split("/")[-1],
        folder="media/",
        size_bytes=1000,
        size_human="1.0 KB",
        content_type="audio/mpeg",
        uploaded_at=datetime(2026, 6, 1, tzinfo=UTC),
        url=None,
    )


@pytest.mark.asyncio
async def test_items_reflect_transcription_status(client, monkeypatch):
    monkeypatch.setattr(
        archive_service,
        "list_files",
        lambda prefix, max_keys: [_media("media/a.mp3"), _media("media/b.mp3")],
    )

    transcripts = {
        "transcripts/a.mp3.json": {
            "key": "media/a.mp3",
            "diarized": True,
            "duration": 120.0,
            "speakers": ["SPEAKER_00", "SPEAKER_01"],
            "segments": [{"start": 0, "end": 1, "text": "hi"}],
        }
    }
    monkeypatch.setattr(
        archive_service, "get_json", lambda key: transcripts.get(key)
    )

    response = await client.get("/archive/items")
    assert response.status_code == 200
    items = {i["key"]: i for i in response.json()}
    assert items["media/a.mp3"]["transcribed"] is True
    assert items["media/a.mp3"]["diarized"] is True
    assert items["media/a.mp3"]["speakers"] == 2
    assert items["media/b.mp3"]["transcribed"] is False


@pytest.mark.asyncio
async def test_stats_rollup(client, monkeypatch):
    monkeypatch.setattr(
        archive_service,
        "list_files",
        lambda prefix, max_keys: [_media("media/a.mp3"), _media("media/b.mp3")],
    )
    transcripts = {
        "transcripts/a.mp3.json": {
            "key": "media/a.mp3",
            "duration": 3600.0,
            "speakers": ["SPEAKER_00"],
            "segments": [{"start": 0, "end": 1, "text": "x"}] * 5,
        }
    }
    monkeypatch.setattr(
        archive_service, "get_json", lambda key: transcripts.get(key)
    )

    response = await client.get("/archive/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["media_files"] == 2
    assert body["transcribed_files"] == 1
    assert body["segments_indexed"] == 5
    assert body["hours_processed"] == 1.0
    assert body["speakers_detected"] == 1


@pytest.mark.asyncio
async def test_transcript_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(archive_service, "get_json", lambda key: None)
    response = await client.get("/archive/transcripts/media/missing.mp3")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_transcribe_enqueues_job(client, monkeypatch):
    # Don't actually run the pipeline — capture the background task target.
    from app.runtime import archive as archive_router

    called = {}

    def fake_run_job(job_id, key):
        called["job_id"] = job_id
        called["key"] = key

    monkeypatch.setattr(archive_router, "run_job", fake_run_job)

    response = await client.post("/archive/transcribe", json={"key": "media/a.mp3"})
    assert response.status_code == 200
    body = response.json()
    assert body["key"] == "media/a.mp3"
    assert body["status"] == "queued"


@pytest.mark.asyncio
async def test_transcribe_rejects_bad_key(client):
    response = await client.post("/archive/transcribe", json={"key": "../etc/passwd"})
    assert response.status_code == 400
