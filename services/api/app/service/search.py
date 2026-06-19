"""Keyword and semantic search across the whole transcript archive.

- keyword:  case-insensitive substring match over segment text.
- semantic: cosine similarity between the query embedding and each stored
            segment embedding.

Both iterate the artifacts written by service/transcription.py. The
small-archive caveat is documented: embeddings are loaded from B2 and ranked
in-process, which is fine for a demo archive; a vector DB is the scale path.

No boto3 here — all B2 reads go through the repo. The query embedding is
local ML compute via the engine (lazy-imported).
"""

import logging

from app.repo import get_json, list_keys
from app.service.engine import embed_query
from app.types import SearchHit

logger = logging.getLogger(__name__)

_EMBEDDINGS_PREFIX = "embeddings/"
_SEGMENTS_PREFIX = "segments/"


def _iter_embedding_artifacts() -> list[dict]:
    artifacts: list[dict] = []
    for key in list_keys(_EMBEDDINGS_PREFIX):
        if not key.endswith(".json"):
            continue
        obj = get_json(key)
        if obj:
            artifacts.append(obj)
    return artifacts


def _iter_segment_artifacts() -> list[dict]:
    artifacts: list[dict] = []
    for key in list_keys(_SEGMENTS_PREFIX):
        if not key.endswith(".json"):
            continue
        obj = get_json(key)
        if obj:
            artifacts.append(obj)
    return artifacts


def _cosine(a: list[float], b: list[float]) -> float:
    # Vectors are stored already L2-normalized, so dot product == cosine.
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=False))


def keyword_search(query: str, k: int = 20) -> list[SearchHit]:
    q = query.strip().lower()
    if not q:
        return []
    hits: list[SearchHit] = []
    for artifact in _iter_segment_artifacts():
        key = artifact.get("key", "")
        for seg in artifact.get("segments", []):
            text = seg.get("text", "")
            if q in text.lower():
                hits.append(
                    SearchHit(
                        key=key,
                        segment_index=seg.get("index", 0),
                        speaker=seg.get("speaker"),
                        start=float(seg.get("start") or 0.0),
                        end=float(seg.get("end") or 0.0),
                        text=text,
                        score=1.0,
                    )
                )
    # Keyword has no graded score; keep earliest-first within a stable order.
    return hits[:k]


def semantic_search(query: str, k: int = 20) -> list[SearchHit]:
    q = query.strip()
    if not q:
        return []
    qvec = embed_query(q)
    if not qvec:
        return []
    scored: list[SearchHit] = []
    for artifact in _iter_embedding_artifacts():
        key = artifact.get("key", "")
        for seg in artifact.get("segments", []):
            score = _cosine(qvec, seg.get("vector", []))
            scored.append(
                SearchHit(
                    key=key,
                    segment_index=seg.get("index", 0),
                    speaker=seg.get("speaker"),
                    start=float(seg.get("start") or 0.0),
                    end=float(seg.get("end") or 0.0),
                    text=seg.get("text", ""),
                    score=round(score, 6),
                )
            )
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:k]


def search(query: str, mode: str = "keyword", k: int = 20) -> list[SearchHit]:
    if mode == "semantic":
        return semantic_search(query, k=k)
    return keyword_search(query, k=k)
