from app.agents.evidence_rules import (
    detect_numeric_deviation,
    find_explicit_omission,
    find_omission_in_documents,
    locate_chunk,
)
from app.core.db_url import normalize_database_url


def test_numeric_deviation_flags_value_below_minimum():
    req = "The report must contain burst pressure safety margin verifications exceeding 2.5x nominal load."
    assert detect_numeric_deviation(req, "Safety margin factor is 2.1x, below the 2.5x threshold.")


def test_numeric_deviation_ignores_compliant_values_and_restatements():
    req = "The report must contain burst pressure safety margin verifications exceeding 2.5x nominal load."
    assert detect_numeric_deviation(req, "The safety margin factor is 2.74x, exceeding the mandatory 2.5x threshold.") == []
    assert detect_numeric_deviation(req, "Safety margin was verified.") == []  # no comparable number: never guessed


def test_numeric_deviation_maximum_with_business_days():
    req = "CAPA root-cause closure within a maximum of 30 business days."
    assert detect_numeric_deviation(req, "Closure takes 45 days on average.")
    assert detect_numeric_deviation(req, "Closure takes 12 days.") == []


def test_omission_found_in_the_right_document():
    docs = [("design.txt", "Design calculations are complete."),
            ("addendum.txt", "Inspection records are pending subcontractor sign-off.")]
    topic, sentence, name = find_omission_in_documents("must include inspection records", docs)
    assert (topic, name) == ("inspection", "addendum.txt")
    assert sentence == "Inspection records are pending subcontractor sign-off."


def test_unrelated_text_is_not_an_omission():
    assert find_explicit_omission("must include inspection records", "Design verified at 412 MPa.") == (None, None)


def test_locate_chunk_prefers_tightest_span_in_same_document():
    chunks = [
        {"document_name": "b", "start_char": 0, "end_char": 100, "page_number": 1},
        {"document_name": "b", "start_char": 10, "end_char": 30, "page_number": 2},
        {"document_name": "a", "start_char": 12, "end_char": 18, "page_number": 9},
    ]
    assert locate_chunk(chunks, "b", 15)["page_number"] == 2
    assert locate_chunk(chunks, "c", 15) is None


def test_database_url_normalisation_for_render_and_sqlite():
    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"
    assert normalize_database_url("postgresql://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"
    assert normalize_database_url("sqlite:///x.db") == "sqlite+aiosqlite:///x.db"
    assert normalize_database_url("sqlite+aiosqlite:///x.db") == "sqlite+aiosqlite:///x.db"
