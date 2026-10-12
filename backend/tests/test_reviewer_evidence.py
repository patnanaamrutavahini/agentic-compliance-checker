import pytest
from app.agents.reviewer_agent import DecisionReviewerAgent
from app.agents.state import ComplianceAgentState
from app.models.schemas import ComplianceStatus, ComplianceVerdict, SeverityLevel


class SummaryLLM:
    async def generate_json(self, prompt, system_prompt):
        return {"executive_summary": "Review completed."}


def make_verdict(snippet):
    return ComplianceVerdict(
        requirement_id="REQ-1",
        requirement_text="The report must include a hydrostatic test result.",
        category="Testing",
        severity=SeverityLevel.HIGH,
        mandatory=True,
        status=ComplianceStatus.COMPLIANT,
        confidence_score=0.95,
        evidence_snippet=snippet,
        rationale="Evidence indicates the test was completed.",
        remarks="",
    )


@pytest.mark.asyncio
async def test_reviewer_flags_compliant_verdict_without_grounded_evidence():
    state = ComplianceAgentState(
        job_id="review-test-missing",
        submitted_raw_text="The report contains a material list.",
        compliance_verdicts=[make_verdict(None)],
    )
    await DecisionReviewerAgent(SummaryLLM()).run(state)
    assert state.compliance_verdicts[0].status == ComplianceStatus.REQUIRES_HUMAN_REVIEW
    assert state.compliance_verdicts[0].confidence_score <= 0.49


@pytest.mark.asyncio
async def test_reviewer_keeps_compliant_verdict_with_verifiable_evidence():
    evidence = "Hydrostatic test result: passed at 1.5x design pressure."
    state = ComplianceAgentState(
        job_id="review-test-grounded",
        submitted_raw_text=f"Section 2. Testing\n{evidence}",
        compliance_verdicts=[make_verdict(evidence)],
    )
    await DecisionReviewerAgent(SummaryLLM()).run(state)
    assert state.compliance_verdicts[0].status == ComplianceStatus.COMPLIANT
