"""Hybrid RAG retrieval: dense (Sentence-Transformers + Chroma/FAISS) + BM25 + token overlap.

One store instance is created per audit job (collection name == job id) so concurrent
audits never share or clear each other's index.
"""
import logging
import math
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.ingestion.chunker import DocumentChunk
from app.ingestion.dense_index import build_dense_index
from app.ingestion.embeddings import SentenceTransformerEmbedder, get_embedder

logger = logging.getLogger(__name__)


class HybridVectorStore:
    def __init__(
        self,
        name: str = "compliance",
        embedder: Optional[SentenceTransformerEmbedder] = None,
        backend: Optional[str] = None,
    ):
        self.name = name
        self.backend = backend
        self.embedder = embedder if embedder is not None else get_embedder()
        self.chunks: List[DocumentChunk] = []
        self.doc_freq: Dict[str, int] = {}
        self.total_docs: int = 0
        self.avg_doc_len: float = 1.0
        self._dense = None  # created on first successful embedding
        self._dense_rows: int = 0

    # ------------------------------------------------------------------ info
    @property
    def retrieval_mode(self) -> str:
        if self._dense is not None and self._dense_rows == len(self.chunks) and self.chunks:
            return f"hybrid: sentence-transformers + {self._dense.name} + BM25"
        return "lexical: BM25 + token overlap"

    # -------------------------------------------------------------- embeddings
    def _embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        return self.embedder.encode(texts)

    # ---------------------------------------------------------------- indexing
    def add_chunks(self, chunks: List[DocumentChunk]):
        if not chunks:
            return
        previously_aligned = self._dense is None or self._dense_rows == len(self.chunks)
        self.chunks.extend(chunks)
        self.total_docs = len(self.chunks)

        total_len = 0
        self.doc_freq.clear()
        for chk in self.chunks:
            tokens = set(self._tokenize(chk.text))
            total_len += len(tokens)
            for token in tokens:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1
        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 1.0

        vectors = self._embed_texts([c.text for c in chunks])
        if vectors is None or len(vectors) != len(chunks) or not previously_aligned:
            return  # keep lexical-only; dense rows would be misaligned otherwise
        if self._dense is None:
            self._dense = build_dense_index(vectors.shape[1], self.name, self.backend)
        metadatas = [
            {
                "document_name": c.document_name,
                "section": c.section_title,
                "page": int(c.page_number or 1),
                "chunk_id": c.chunk_id,
            }
            for c in chunks
        ]
        self._dense.add([c.text for c in chunks], vectors, metadatas)
        self._dense_rows += len(chunks)

    # --------------------------------------------------------------- scoring
    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w{2,}\b", text.lower())

    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> float:
        score = 0.0
        doc_len = len(doc_tokens)
        counts: Dict[str, int] = {}
        for token in doc_tokens:
            counts[token] = counts.get(token, 0) + 1
        for token in query_tokens:
            if token in self.doc_freq:
                n_q = self.doc_freq[token]
                idf = math.log((self.total_docs - n_q + 0.5) / (n_q + 0.5) + 1.0)
                freq = counts.get(token, 0)
                numerator = freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * (doc_len / (self.avg_doc_len or 1.0)))
                score += idf * (numerator / (denominator or 1.0))
        return score

    @staticmethod
    def _token_overlap_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
        q_set, d_set = set(query_tokens), set(doc_tokens)
        if not q_set or not d_set:
            return 0.0
        return len(q_set.intersection(d_set)) / math.sqrt(len(q_set) * len(d_set))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        if not self.chunks or top_k <= 0:
            return []
        query_tokens = self._tokenize(query)

        dense_scores: Dict[int, float] = {}
        if self._dense is not None and self._dense_rows == len(self.chunks):
            q_vec = self._embed_texts([query])
            if q_vec is not None:
                for row, sim in self._dense.query(q_vec[0], len(self.chunks)):
                    dense_scores[row] = max(0.0, min(1.0, sim))

        raw = []
        max_bm25 = 0.0
        for index, chunk in enumerate(self.chunks):
            doc_tokens = self._tokenize(chunk.text)
            bm25 = self._bm25_score(query_tokens, doc_tokens)
            overlap = self._token_overlap_score(query_tokens, doc_tokens)
            raw.append((chunk, bm25, overlap, dense_scores.get(index)))
            max_bm25 = max(max_bm25, bm25)

        scored = []
        for chunk, bm25, overlap, dense in raw:
            norm_bm25 = bm25 / max_bm25 if max_bm25 > 0 else 0.0
            if dense is None:
                score = 0.7 * norm_bm25 + 0.3 * overlap
            else:
                score = 0.55 * dense + 0.30 * norm_bm25 + 0.15 * overlap
            scored.append((chunk, round(score, 4)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    # ---------------------------------------------------------------- cleanup
    def clear(self):
        self.chunks.clear()
        self.doc_freq.clear()
        self.total_docs = 0
        self.avg_doc_len = 1.0
        if self._dense is not None:
            self._dense.close()
        self._dense = None
        self._dense_rows = 0

    close = clear
