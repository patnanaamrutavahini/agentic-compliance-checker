import pytest

from app.agents.orchestrator import MultiAgentComplianceOrchestrator
from app.models.schemas import ComplianceStatus

REFERENCE = (
    "The submitted report must contain design calculations, material specifications, "
    "inspection requirements, and testing procedures."
)
DESIGN_DOC = (
    "SECTION 1: DESIGN CALCULATIONS\nDesign calculations: Available. Finite element stress analysis "
    "gives a safety margin of 2.74x.\n\nSECTION 2: MATERIAL SPECIFICATION\nMaterial specification: Available. "
    "Inconel 718 per AMS 5662."
)
TEST_DOC = (
    "SECTION 3: TESTING PROCEDURE\nTesting procedure: Available. Hydrostatic proof pressure test at 270 bar.\n\n"
    "SECTION 4: INSPECTION\nInspection requirements: Missing"
)


@pytest.mark.asyncio
async def test_multiple_submitted_documents_keep_evidence_traceable_to_their_own_file():
    report = await MultiAgentComplianceOrchestrator().execute_compliance_workflow(
        job_id="job_multidoc",
        reference_documents=[{"filename": "spec.txt", "text": REFERENCE}],
        submitted_documents=[
            {"filename": "design_report.txt", "text": DESIGN_DOC},
            {"filename": "test_report.txt", "text": TEST_DOC},
        ],
    )

    assert report.submitted_doc_names == ["design_report.txt", "test_report.txt"]
    assert report.pipeline_info["submitted_documents"] == "2"
    assert report.requirements, "requirements must be exposed on the report"

    inspection = [v for v in report.requirements_matrix if "inspection" in v.requirement_text.lower()]
    assert inspection, "an inspection requirement must be extracted"
    for verdict in inspection:
        assert verdict.status == ComplianceStatus.NON_COMPLIANT
        assert verdict.evidence_location.document_name == "test_report.txt"
        assert "Missing" in verdict.evidence_snippet
        text = TEST_DOC
        loc = verdict.evidence_location
        assert text[loc.start_char:loc.end_char] == verdict.evidence_snippet

    assert report.overall_status != ComplianceStatus.COMPLIANT
