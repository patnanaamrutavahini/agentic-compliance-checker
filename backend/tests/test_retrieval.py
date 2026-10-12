import numpy as np

from app.ingestion.chunker import DocumentChunk
from app.ingestion.vector_store import HybridVectorStore


def make_chunk(chunk_id: str, text: str, section: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id, document_name="sample.txt", text=text, page_number=1,
        section_title=section, start_char=0, end_char=len(text), line_number=1,
    )


def test_retrieval_ranks_matching_requirement_first():
    store = HybridVectorStore()
    relevant = make_chunk(
        "relevant",
        "Hydrostatic testing must be performed at 1.5 times the design pressure.",
        "Testing",
    )
    unrelated = make_chunk(
        "unrelated",
        "The document lists employee onboarding steps and office attendance rules.",
        "Human Resources",
    )
    store.add_chunks([unrelated, relevant])

    results = store.search("hydrostatic testing design pressure", top_k=2)

    assert results[0][0].chunk_id == "relevant"
    assert results[0][1] > results[1][1]


def test_empty_store_returns_no_results():
    assert HybridVectorStore(embedder=NoEmbedder()).search("required test", top_k=3) == []


class FakeEmbedder:
    """Deterministic bag-of-words embedder (unit-norm) so dense retrieval is testable offline."""
    VOCAB = ["pressure", "hydrostatic", "test", "inspection", "xray", "design", "onboarding", "office"]

    def encode(self, texts):
        rows = []
        for text in texts:
            low = text.lower()
            vec = np.array([low.count(w) for w in self.VOCAB], dtype="float32") + 1e-3
            rows.append(vec / np.linalg.norm(vec))
        return np.array(rows, dtype="float32")


class NoEmbedder:
    def encode(self, texts):
        return None


def test_dense_hybrid_retrieval_uses_vector_index_and_ranks_correctly():
    store = HybridVectorStore(name="job_test", embedder=FakeEmbedder(), backend="memory")
    store.add_chunks([
        make_chunk("hr", "Employee onboarding and office attendance rules.", "HR"),
        make_chunk("test", "Hydrostatic test at design pressure.", "Testing"),
    ])
    store.add_chunks([make_chunk("insp", "X-ray inspection records are attached.", "Inspection")])

    assert store.retrieval_mode.startswith("hybrid")
    results = store.search("hydrostatic pressure test", top_k=3)
    assert results[0][0].chunk_id == "test"
    assert len(results) == 3
    store.close()
    assert store.search("anything", top_k=3) == []


def test_numpy_dense_index_returns_nearest_first():
    from app.ingestion.dense_index import NumpyIndex
    index = NumpyIndex(2, "t")
    index.add(["a", "b"], np.array([[1, 0], [0, 1]], dtype="float32"), [{}, {}])
    assert index.query(np.array([0.9, 0.1], dtype="float32"), 2)[0][0] == 0


def test_retrieval_falls_back_to_lexical_without_embeddings():
    store = HybridVectorStore(embedder=NoEmbedder())
    relevant = make_chunk("relevant", "Hydrostatic testing must use design pressure.", "Testing")
    unrelated = make_chunk("unrelated", "Employee onboarding and office attendance rules.", "HR")
    store.add_chunks([unrelated, relevant])

    assert store.retrieval_mode.startswith("lexical")
    results = store.search("hydrostatic testing design pressure", top_k=2)
    assert results[0][0].chunk_id == "relevant"


def test_vector_stores_are_isolated_per_job():
    first = HybridVectorStore(name="job_a", embedder=NoEmbedder())
    second = HybridVectorStore(name="job_b", embedder=NoEmbedder())
    first.add_chunks([make_chunk("only_a", "alpha text", "A")])
    assert second.search("alpha", top_k=1) == []
