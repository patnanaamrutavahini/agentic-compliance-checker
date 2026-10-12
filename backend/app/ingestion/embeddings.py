"""Sentence-Transformers embedding service (lazy, with graceful degradation)."""
import logging
import threading
from typing import List, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Wraps a sentence-transformers model. Returns L2-normalised float32 vectors.

    The model is loaded lazily on first use. If the package or model weights are
    unavailable the embedder marks itself unavailable and callers fall back to
    lexical (BM25 + token overlap) retrieval, so the pipeline never hard-fails.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._failed = settings.EMBEDDING_BACKEND.lower() in ("none", "off", "lexical")
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self._load() is not None

    def _load(self):
        if self._failed:
            return None
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info("Loaded embedding model %s", self.model_name)
            except Exception as exc:  # ImportError, network/weights problems, ...
                logger.warning(
                    "Sentence-Transformers unavailable (%s); using lexical retrieval only.", exc
                )
                self._failed = True
                self._model = None
        return self._model

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        if not texts:
            return None
        model = self._load()
        if model is None:
            return None
        try:
            vectors = model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype="float32")
        except Exception as exc:
            logger.warning("Embedding failed (%s); using lexical retrieval for this call.", exc)
            return None


_embedder: Optional[SentenceTransformerEmbedder] = None


def get_embedder() -> SentenceTransformerEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder()
    return _embedder
