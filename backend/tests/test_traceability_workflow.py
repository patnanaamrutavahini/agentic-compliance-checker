from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import DocumentChunker
from app.ingestion.vector_store import HybridVectorStore


def test_chunk_offsets_point_to_original_extracted_text():
    text = "SPECIFICATION AERO-101\n\nSection 1.0 Scope\nThe report must include a hydrostatic test record.\n\nSection 2.0 Training\nEmployees must complete annual safety training."
    parsed = DocumentParser.parse_raw_text(text, "spec.txt")
    chunks = DocumentChunker(chunk_size=90, chunk_overlap=20).chunk_document(parsed)

    assert chunks
    for chunk in chunks:
        assert 0 <= chunk.start_char < chunk.end_char <= len(text)
        # Citation offsets should point at the relevant source text, not an estimated position.
        source_slice = text[chunk.start_char:chunk.end_char]
        assert any(token in source_slice for token in chunk.text.split()[:3])
        assert chunk.line_number == text.count("\n", 0, chunk.start_char) + 1
        assert chunk.metadata["source_offset_basis"] == "extracted_text"


def test_end_to_end_retrieval_keeps_source_location():
    text = "Section 1.0 Testing\nHydrostatic testing shall be performed at 1.5 times design pressure.\n\nSection 2.0 Personnel\nStaff must attend annual safety training."
    parsed = DocumentParser.parse_raw_text(text, "submission.txt")
    chunks = DocumentChunker(chunk_size=120, chunk_overlap=20).chunk_document(parsed)
    store = HybridVectorStore()
    store.add_chunks(chunks)

    results = store.search("hydrostatic testing design pressure", top_k=2)
    assert results
    best_chunk = results[0][0]
    assert "Hydrostatic testing" in best_chunk.text
    assert text[best_chunk.start_char:best_chunk.end_char].strip()
    assert best_chunk.metadata["source_start_char"] == best_chunk.start_char
    assert best_chunk.metadata["source_end_char"] == best_chunk.end_char


def test_explicitly_omitted_inspection_records_are_found_as_grounded_evidence():
    from app.agents.evidence_rules import find_explicit_omission as _find_explicit_omission

    requirement = "The report must include 100% X-ray radiography and FPI inspection records."
    submission = (
        "SECTION 1: DESIGN CALCULATIONS\nCalculations are complete.\n\n"
        "NOTE: Inspection protocols, X-ray radiography records, and FPI reports are currently "
        "pending secondary metallurgical subcontractor sign-off and were omitted from this revision."
    )
    topic, quote = _find_explicit_omission(requirement, submission)
    assert topic == "inspection"
    assert quote == (
        "NOTE: Inspection protocols, X-ray radiography records, and FPI reports are currently "
        "pending secondary metallurgical subcontractor sign-off and were omitted from this revision."
    )


def test_design_evidence_is_not_mistaken_for_missing_inspection_evidence():
    from app.agents.evidence_rules import find_explicit_omission as _find_explicit_omission

    requirement = "The report must include inspection protocols and X-ray radiography records."
    submission = "Design calculations verified a maximum von Mises stress of 412 MPa."
    topic, quote = _find_explicit_omission(requirement, submission)
    assert topic is None
    assert quote is None
