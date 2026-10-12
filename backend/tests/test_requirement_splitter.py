import pytest

from app.agents.requirement_splitter import split_compound_requirement
from app.core.llm_provider import LLMProvider

HEADLINE = (
    "The submitted report must contain design calculations, material specifications, "
    "inspection requirements, and testing procedures."
)


def test_headline_sentence_splits_into_four_atomic_requirements():
    parts = split_compound_requirement(HEADLINE)
    assert parts == [
        "The submitted report must contain design calculations.",
        "The submitted report must contain material specifications.",
        "The submitted report must contain inspection requirements.",
        "The submitted report must contain testing procedures.",
    ]


def test_splitter_is_idempotent_and_conservative():
    assert split_compound_requirement("The submitted report must contain complete design calculations.") == [
        "The submitted report must contain complete design calculations."
    ]
    # not a plain list -> unchanged
    sentence = "The system shall encrypt data at rest, in transit, and in backups."
    assert split_compound_requirement(sentence) == [sentence]
    for atom in split_compound_requirement(HEADLINE):
        assert split_compound_requirement(atom) == [atom]


def test_pairs_and_idioms():
    assert split_compound_requirement(
        "The submitted report must contain design calculations and material specifications."
    ) == [
        "The submitted report must contain design calculations.",
        "The submitted report must contain material specifications.",
    ]
    idiom = "The contract must include terms and conditions."
    assert split_compound_requirement(idiom) == [idiom]


def test_elaboration_is_not_split_into_a_requirement():
    sentence = (
        "The submission must contain comprehensive NDE inspection requirements, including 100% X-ray "
        "radiography and fluorescent penetrant inspection (FPI) acceptance standards."
    )
    assert split_compound_requirement(sentence) == [sentence]


@pytest.mark.asyncio
async def test_offline_extractor_ignores_prompt_boilerplate():
    prompt = (
        f"Reference Standard Document:\n{HEADLINE}\n\n"
        "Extract all requirements in JSON with format:\n{\n"
        '  "requirements": [\n    {\n      "id": "REQ-001",\n'
        '      "text": "The submitted report must contain complete design calculations.",\n'
        '      "source_clause": "The submitted report must contain..."\n    }\n  ]\n}'
    )
    result = await LLMProvider("mock").generate_json(prompt, "You are an expert Requirement Extraction Agent.")
    texts = [r["text"] for r in result["requirements"]]
    assert len(texts) == 4
    assert all(t.startswith("The submitted report must contain ") for t in texts)


@pytest.mark.asyncio
async def test_offline_extractor_skips_titles_and_section_headings():
    reference = (
        "SPECIFICATION: AERO-STD-4402 (REVISION D)\n"
        "TITLE: High-Pressure Fuel Manifold Subsystem Qualification Requirements\n\n"
        "1.0 SCOPE & APPLICABILITY\n"
        "This standard establishes mandatory technical criteria for fabricated cryogenic fuel manifolds.\n\n"
        "2.0 MANDATORY DELIVERABLES\n"
        "2.1 Design Calculations: The submitted report must contain complete design calculations, "
        "finite element stress analysis (FEA), and burst pressure safety margin verifications "
        "exceeding 2.5x nominal load.\n"
    )
    prompt = f"Reference Standard Document:\n{reference}\n\nExtract all requirements in JSON with format:\n{{"
    result = await LLMProvider("mock").generate_json(prompt, "You are an expert Requirement Extraction Agent.")
    texts = [r["text"] for r in result["requirements"]]
    assert len(texts) == 3
    assert all("must contain" in t for t in texts)
    assert not any("SCOPE" in t or "TITLE" in t or "DELIVERABLES" in t for t in texts)
    assert "exceeding 2.5x nominal load" in texts[2]  # numeric limit stays with its own requirement
