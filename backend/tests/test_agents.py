import pytest
import asyncio
from app.agents.orchestrator import MultiAgentComplianceOrchestrator
from app.models.schemas import ComplianceStatus, SeverityLevel

@pytest.mark.asyncio
async def test_multi_agent_workflow_missing_inspection():
    """
    Test the exact problem statement case:
    Reference requires: design calculations, material specifications, inspection requirements, and testing procedures.
    Submitted has: calculations, materials, testing. Inspection is missing.
    Expected: Inspection requirement classified as Non-Compliant / Missing, Overall: Partially Compliant / Non-Compliant.
    """
    reference = """The submitted report must contain design calculations, material specifications, inspection requirements, and testing procedures."""
    
    submitted = """Design calculations: Available and compliant with ASME.
Material specification: Inconel 718 available.
Inspection requirements: Missing from current submittal.
Testing procedure: Hydrostatic proof testing available."""

    orchestrator = MultiAgentComplianceOrchestrator()
    report = await orchestrator.execute_compliance_workflow(
        job_id="test_job_001",
        reference_text=reference,
        submitted_text=submitted
    )

    # the compound sentence must become exactly four atomic requirements
    assert report.total_requirements == 4
    assert len(report.requirements_matrix) == 4

    # Check for inspection requirement verdict
    inspection_verdict = next((v for v in report.requirements_matrix if "inspection" in v.requirement_text.lower()), None)
    assert inspection_verdict is not None
    assert inspection_verdict.status == ComplianceStatus.NON_COMPLIANT
    assert "missing" in (inspection_verdict.evidence_snippet or "").lower()

    # the other three are present in the submission and must not be marked non-compliant
    for topic in ("design", "material", "testing"):
        v = next(v for v in report.requirements_matrix if topic in v.requirement_text.lower())
        assert v.status != ComplianceStatus.NON_COMPLIANT

    # one missing mandatory item: the overall result must never be "Compliant"
    assert report.overall_status != ComplianceStatus.COMPLIANT
    
    # Verify audit logs generated for all 6 agents
    agent_ids = [log.agent_id for log in report.agent_audit_trail]
    assert "agent_01_classifier" in agent_ids
    assert "agent_02_extractor" in agent_ids
    assert "agent_03_req_extractor" in agent_ids
    assert "agent_04_compliance" in agent_ids
    assert "agent_05_discrepancy" in agent_ids
    assert "agent_06_reviewer" in agent_ids
