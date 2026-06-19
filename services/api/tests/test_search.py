"""Tests for keyword + semantic search and artifact key derivation.

Mocks the repo (B2 reads) and the engine (query embedding) so it runs
without the ML stack.
"""

from app.service import search as search_service
from app.service import transcription


def test_artifact_keys_mirror_media_filename():
    assert transcription.transcript_key("media/ep1.mp3") == "transcripts/ep1.mp3.json"
    assert transcription.segment_key("media/ep1.mp3") == "segments/ep1.mp3.json"
    assert transcription.embedding_key("media/ep1.mp3") == "embeddings/ep1.mp3.json"


def test_keyword_search_substring_match(monkeypatch):
    segments_artifact = {
        "key": "media/ep1.mp3",
        "segments": [
            {"index": 0, "speaker": "SPEAKER_00", "start": 0, "end": 2, "text": "Hello world"},
            {"index": 1, "speaker": "SPEAKER_01", "start": 2, "end": 4, "text": "Goodbye now"},
        ],
    }
    monkeypatch.setattr(search_service, "list_keys", lambda prefix: ["segments/ep1.mp3.json"])
    monkeypatch.setattr(search_service, "get_json", lambda key: segments_artifact)

    hits = search_service.search("world", mode="keyword")
    assert len(hits) == 1
    assert hits[0].text == "Hello world"
    assert hits[0].key == "media/ep1.mp3"


def test_semantic_search_ranks_by_cosine(monkeypatch):
    emb_artifact = {
        "key": "media/ep1.mp3",
        "segments": [
            {"index": 0, "speaker": None, "start": 0, "end": 1, "text": "cats", "vector": [1.0, 0.0]},
            {"index": 1, "speaker": None, "start": 1, "end": 2, "text": "dogs", "vector": [0.0, 1.0]},
        ],
    }
    monkeypatch.setattr(search_service, "list_keys", lambda prefix: ["embeddings/ep1.mp3.json"])
    monkeypatch.setattr(search_service, "get_json", lambda key: emb_artifact)
    # Query vector closest to the first segment.
    monkeypatch.setattr(search_service, "embed_query", lambda text: [1.0, 0.0])

    hits = search_service.search("feline", mode="semantic")
    assert hits[0].text == "cats"
    assert hits[0].score > hits[1].score
