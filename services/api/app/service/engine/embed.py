"""Per-segment embeddings via sentence-transformers (lazy imports).

One dense vector per speaker segment, written to embeddings/{key}.json. The
search service loads these and ranks by cosine similarity for semantic
search across the whole archive.

The model is cached per-process via lru_cache so repeated batch jobs don't
reload weights. Heavy imports stay inside the functions.
"""

import functools
import logging

from app.config import settings
from app.service.engine.errors import MissingMLDependencies

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as e:
        raise MissingMLDependencies("Embedding") from e
    logger.info("Loading embedding model=%s", model_name)
    return SentenceTransformer(model_name)


def embed_segments(texts: list[str]) -> list[list[float]]:
    """Embed a list of segment texts into normalized float vectors.

    Returns a list of vectors (each a plain list[float]) aligned 1:1 with the
    input texts. Empty input returns an empty list. Raises
    MissingMLDependencies if sentence-transformers is absent.
    """
    if not texts:
        return []
    model = _load_model(settings.embedding_model)
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    """Embed a single query string (normalized) for semantic search."""
    vectors = embed_segments([text])
    return vectors[0] if vectors else []
