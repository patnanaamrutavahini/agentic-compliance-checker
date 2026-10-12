"""Dense vector index backends: ChromaDB, FAISS, and a NumPy fallback.

All backends expose the same tiny interface so the retrieval store does not care
which one is active:

    add(texts, vectors, metadatas)   -> appends rows (row id == insertion order)
    query(vector, k)                 -> [(row_id, cosine_similarity), ...] best first
    close()                          -> release / delete the underlying collection

Vectors are expected to be L2-normalised, so inner product == cosine similarity.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class NumpyIndex:
    name = "memory"

    def __init__(self, dim: int, collection: str):
        self.dim = dim
        self._matrix = np.zeros((0, dim), dtype="float32")

    def add(self, texts: List[str], vectors: np.ndarray, metadatas: List[Dict[str, Any]]):
        self._matrix = np.vstack([self._matrix, vectors.astype("float32")])

    def query(self, vector: np.ndarray, k: int) -> List[Tuple[int, float]]:
        if self._matrix.shape[0] == 0:
            return []
        sims = self._matrix @ vector.astype("float32")
        order = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in order]

    def close(self):
        self._matrix = np.zeros((0, self.dim), dtype="float32")


class FaissIndex:
    name = "faiss"

    def __init__(self, dim: int, collection: str):
        import faiss  # type: ignore

        self._faiss = faiss
        self.dim = dim
        self._index = faiss.IndexFlatIP(dim)

    def add(self, texts: List[str], vectors: np.ndarray, metadatas: List[Dict[str, Any]]):
        self._index.add(np.ascontiguousarray(vectors, dtype="float32"))

    def query(self, vector: np.ndarray, k: int) -> List[Tuple[int, float]]:
        if self._index.ntotal == 0:
            return []
        k = min(k, self._index.ntotal)
        sims, ids = self._index.search(np.ascontiguousarray(vector.reshape(1, -1), dtype="float32"), k)
        return [(int(i), float(s)) for i, s in zip(ids[0], sims[0]) if i >= 0]

    def close(self):
        self._index.reset()


_chroma_client = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb  # type: ignore

        if settings.CHROMA_PERSIST_DIR:
            _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        else:
            _chroma_client = chromadb.EphemeralClient()
    return _chroma_client


class ChromaIndex:
    name = "chroma"

    def __init__(self, dim: int, collection: str):
        self.dim = dim
        self._client = _get_chroma_client()
        # Chroma collection names: 3-63 chars, alphanumerics/underscore/hyphen.
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in collection)[:48]
        self._name = f"{safe}_{uuid.uuid4().hex[:8]}"
        self._collection = self._client.create_collection(
            name=self._name, metadata={"hnsw:space": "cosine"}
        )
        self._count = 0

    def add(self, texts: List[str], vectors: np.ndarray, metadatas: List[Dict[str, Any]]):
        ids = [str(self._count + i) for i in range(len(texts))]
        clean_meta = [
            {k: v for k, v in (m or {}).items() if isinstance(v, (str, int, float, bool))} or {"_": "_"}
            for m in metadatas
        ]
        self._collection.add(
            ids=ids,
            embeddings=[v.tolist() for v in vectors],
            documents=texts,
            metadatas=clean_meta,
        )
        self._count += len(texts)

    def query(self, vector: np.ndarray, k: int) -> List[Tuple[int, float]]:
        if self._count == 0:
            return []
        res = self._collection.query(
            query_embeddings=[vector.tolist()], n_results=min(k, self._count)
        )
        ids = res["ids"][0]
        distances = res["distances"][0]
        # cosine distance = 1 - cosine similarity
        return [(int(i), 1.0 - float(d)) for i, d in zip(ids, distances)]

    def close(self):
        try:
            self._client.delete_collection(self._name)
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.debug("Could not delete Chroma collection %s: %s", self._name, exc)


def build_dense_index(dim: int, collection: str, backend: Optional[str] = None):
    """Create the configured dense index, falling back to NumPy if unavailable."""
    requested = (backend or settings.VECTOR_BACKEND or "chroma").lower()
    order = {
        "chroma": [ChromaIndex, FaissIndex, NumpyIndex],
        "faiss": [FaissIndex, ChromaIndex, NumpyIndex],
        "memory": [NumpyIndex],
    }.get(requested, [ChromaIndex, FaissIndex, NumpyIndex])
    for cls in order:
        try:
            index = cls(dim, collection)
            if cls.name != requested:
                logger.warning("Vector backend '%s' unavailable; using '%s'.", requested, cls.name)
            return index
        except Exception as exc:
            logger.warning("Could not initialise %s index: %s", cls.__name__, exc)
    return NumpyIndex(dim, collection)
