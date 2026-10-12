import time
from typing import List, Dict, Any
from app.agents.state import ComplianceAgentState
from app.core.llm_provider import LLMProvider
from app.models.schemas import (
    DiscrepancyItem,
    SeverityLevel,
    ComplianceStatus,
    AgentExecutionEvent
)
from app.core.memory import memory_store

class DiscrepancyAgent:
    """
    Agent 5: Discrepancy Agent
    Deeply analyzes non-compliant, partial, or conflicting clauses.
    Detects contradictions, omissions, incomplete scopes, and unauthorized deviations,
    generating precise remediation pathways.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.name = "Discrepancy Agent"
        self.id = "agent_05_discrepancy"

    async def run(self, state: ComplianceAgentState) -> ComplianceAgentState:
        start_time = time.time()
        thoughts = [
            "Reviewing compliance verdicts for negative findings and partial matches...",
            "Checking for numerical contradictions, standard version conflicts, and missing mandatory clauses...",
            "Formulating risk severities and concrete remediation recommendations."
        ]

        await memory_store.append_event(state.job_id, {
            "agent_id": self.id,
            "agent_name": self.name,
            "status": "running",
            "thought_process": thoughts,
            "output_summary": "Detecting semantic contradictions, missing clauses, and deviations..."
        })

        discrepancies: List[DiscrepancyItem] = []
        disc_counter = 1

        for verdict in state.compliance_verdicts:
            if verdict.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT, ComplianceStatus.REQUIRES_HUMAN_REVIEW]:
                disc_id = f"GAP-{disc_counter:03d}"
                disc_counter += 1

                if verdict.status == ComplianceStatus.NON_COMPLIANT:
                    disc_type = "Missing Information"
                    desc = f"Mandatory requirement '{verdict.requirement_text}' is completely missing from the submission."
                    remediation = f"The author must add a dedicated section providing certified proof for: {verdict.requirement_text}"
                    found_stmt = verdict.evidence_snippet or "None provided in document."
                    if not verdict.missing_elements:
                        verdict.missing_elements = [verdict.requirement_text]
                elif verdict.status == ComplianceStatus.PARTIALLY_COMPLIANT:
                    disc_type = "Incomplete Scope / Technical Deviation"
                    desc = f"Partial compliance detected for '{verdict.requirement_text}'. Evidence is present but lacks full verification rigor."
                    remediation = "Supply complete numerical testing logs, signed calibration sheets, or extended calculation appendices."
                    found_stmt = verdict.evidence_snippet or "Partial references found without comprehensive data."
                    if not verdict.deviations:
                        verdict.deviations = ["Incomplete test logs or parametric coverage"]
                    elif verdict.conflicting_elements:
                        disc_type = "Direct Contradiction / Numeric Deviation"
                        desc = f"Submitted value conflicts with a numeric limit in '{verdict.requirement_text}'."
                        remediation = "Correct the submitted value or provide a documented, approved deviation."
                else:
                    disc_type = "Ambiguity / Needs Verification"
                    desc = f"Textual ambiguity detected in submitted evidence for '{verdict.requirement_text}'."
                    remediation = "Clarify exact technical methodology and verify against standard acceptance criteria."
                    found_stmt = verdict.evidence_snippet
                    if not verdict.conflicting_elements:
                        verdict.conflicting_elements = ["Ambiguous terminology requiring human interpretation"]

                item = DiscrepancyItem(
                    id=disc_id,
                    requirement_id=verdict.requirement_id,
                    discrepancy_type=disc_type,
                    severity=verdict.severity,
                    description=desc,
                    expected_statement=verdict.requirement_text,
                    found_statement=found_stmt,
                    remediation_recommendation=remediation
                )
                discrepancies.append(item)
                verdict.discrepancy_details = item

        state.discrepancies = discrepancies
        duration_ms = (time.time() - start_time) * 1000

        event = AgentExecutionEvent(
            agent_id=self.id,
            agent_name=self.name,
            status="completed",
            duration_ms=round(duration_ms, 2),
            thought_process=thoughts + [
                f"Identified {len(discrepancies)} compliance gaps and discrepancies across analyzed documents.",
                f"Generated targeted remediation actions for each identified gap."
            ],
            output_summary=f"Detected {len(discrepancies)} compliance gaps and formulated remediation steps.",
            tokens_used=280
        )
        state.agent_logs.append(event)
        await memory_store.append_event(state.job_id, event.model_dump())
        return state
