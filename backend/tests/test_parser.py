import pytest
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import DocumentChunker
from app.ingestion.vector_store import HybridVectorStore

def test_document_parser_raw_text():
    sample_text = """SPECIFICATION AERO-101
Section 1.0 Scope
The submitted report must contain design calculations and material specifications.

Section 2.0 Testing
Hydrostatic testing must be executed at 1.5x design pressure."""
    
    parsed = DocumentParser.parse_raw_text(sample_text, "AERO-101.txt")
    assert parsed["filename"] == "AERO-101.txt"
    assert parsed["total_characters"] > 0
    assert len(parsed["sections"]) >= 2
    assert "Section 1.0" in parsed["sections"][0]["title"]

def test_chunker_and_vector_store():
    sample_text = """Design calculations were conducted per ASME Section VIII.
Maximum von Mises stress was 412 MPa.
Material specification confirms Inconel 718 alloy composition."""
    
    parsed = DocumentParser.parse_raw_text(sample_text, "submission.txt")
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk_document(parsed)
    
    assert len(chunks) >= 1
    assert chunks[0].page_number >= 1

    store = HybridVectorStore()
    store.add_chunks(chunks)
    
    results = store.search("Inconel material specification", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "Inconel" in top_chunk.text
    assert score > 0.1
