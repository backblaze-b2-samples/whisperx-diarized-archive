"""Per-segment embeddings via sentence-transformers (lazy imports).

One dense vector per speaker segment, written to embeddings/{key}.json. The
search service loads these and ranks by cosine similarity for semantic
search across the whole archive.

The model is cached per-process via lru_cache so repeated batch jobs don't
reload weights. Heavy imports stay inside the functions.
"""

import functools
import logging
import sys

from app.config import settings
from app.service.engine.errors import MissingMLDependencies

logger = logging.getLogger(__name__)


def _ensure_torchcodec_optional() -> None:
    """Make torchcodec a no-op import if its native libs can't load.

    sentence-transformers >=5 eagerly imports torchcodec for optional audio/video
    embedding inputs. torchcodec's prebuilt dylibs are linked against ffmpeg 4-7
    (libavutil.56-59); on a host with ffmpeg 8 (libavutil.60) the load raises
    *RuntimeError*. sentence-transformers guards that import with
    ``except (ImportError, OSError)`` — which does NOT catch RuntimeError — so a
    pure-text model load crashes even though every torchcodec consumer there is
    behind an ``is not None`` check.

    We embed text only, never audio/video, so torchcodec is genuinely optional.
    Probe it once; if it can't load for any reason, mask the module so the
    library's own optional-import fallback (AudioDecoder/VideoDecoder = None) is
    taken. ``sys.modules[name] = None`` makes Python raise ImportError on any
    ``import torchcodec...`` — the exact path the library already handles.
    """
    if "torchcodec" in sys.modules:
        return
    try:
        import torchcodec.decoders  # noqa: F401
    except Exception:  # ImportError, OSError, RuntimeError (bad ffmpeg ABI), ...
        logger.warning(
            "torchcodec unavailable (likely an ffmpeg ABI mismatch); disabling "
            "its optional audio/video import so text embedding can proceed."
        )
        sys.modules["torchcodec"] = None  # type: ignore[assignment]


@functools.lru_cache(maxsize=2)
def _load_model(model_name: str):
    _ensure_torchcodec_optional()
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
