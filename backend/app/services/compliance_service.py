import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.agents.orchestrator import MultiAgentComplianceOrchestrator
from app.core.llm_provider import LLMProvider
from app.core.memory import memory_store
from app.models.schemas import (
    ComplianceJobRequest,
    ComplianceReport,
    ComplianceStatus,
    HumanOverride,
    OverrideRequest,
    SeverityLevel,
)
from app.services import persistence

logger = logging.getLogger(__name__)

DEFAULT_REFERENCE = (
    "The submitted report must contain design calculations, material specifications, "
    "inspection requirements, and testing procedures."
)

_SEVERITY_WEIGHTS = {
    SeverityLevel.CRITICAL: 3.0, SeverityLevel.HIGH: 2.0, SeverityLevel.MEDIUM: 1.0,
    SeverityLevel.LOW: 0.5, SeverityLevel.INFO: 0.25,
}


class ComplianceService:
    def __init__(self):
        self._active_reports: Dict[str, ComplianceReport] = {}

    # ---------------------------------------------------------- input resolve
    async def _resolve_documents(
        self, inline: List[Any], ids: List[str], legacy_id: Optional[str],
        legacy_text: Optional[str], legacy_name: Optional[str], default_name: str,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Merge inline documents, stored document ids, and the single-text legacy fields."""
        docs: List[Dict[str, Any]] = []
        stored_ids: List[str] = []

        wanted_ids = list(ids) + ([legacy_id] if legacy_id else [])
        wanted_ids += [d.document_id for d in inline if d.document_id and not d.text.strip()]
        for rec in await persistence.get_documents(list(dict.fromkeys(wanted_ids))):
            docs.append({"document_id": rec.id, "filename": rec.filename, "text": rec.raw_text})
            stored_ids.append(rec.id)

        for d in inline:
            if d.text.strip():
                docs.append({"document_id": d.document_id, "filename": d.name, "text": d.text})
                if d.document_id:
                    stored_ids.append(d.document_id)

        if not docs and legacy_text and legacy_text.strip():
            docs.append({"filename": legacy_name or default_name, "text": legacy_text})
        return docs, list(dict.fromkeys(stored_ids))

    async def run_compliance_check(self, req: ComplianceJobRequest) -> ComplianceReport:
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        ref_docs, ref_ids = await self._resolve_documents(
            req.reference_documents, req.reference_document_ids, req.reference_document_id,
            req.reference_text, req.reference_doc_name, "Reference_Standard.txt",
        )
        sub_docs, sub_ids = await self._resolve_documents(
            req.submitted_documents, req.submitted_document_ids, req.submitted_document_id,
            req.submitted_text, req.submitted_doc_name, "Submitted_Document.txt",
        )
        if not ref_docs:
            # The problem-statement example is used only when no reference was supplied at all.
            ref_docs = [{"filename": "Reference_Standard.txt", "text": DEFAULT_REFERENCE}]
        if not sub_docs:
            raise ValueError("No submitted document text was provided.")

        llm = LLMProvider(provider=req.llm_provider, api_key=req.api_key)
        orchestrator = MultiAgentComplianceOrchestrator(llm_provider=llm)
        report = await orchestrator.execute_compliance_workflow(
            job_id=job_id,
            reference_documents=ref_docs,
            submitted_documents=sub_docs,
            domain=req.domain or "General Compliance",
        )

        self._active_reports[job_id] = report
        try:
            await persistence.save_report(report, ref_ids, sub_ids)
        except Exception:
            logger.exception("Could not persist report %s to the database", job_id)
        return report

    # -------------------------------------------------------------- retrieval
    async def get_report(self, job_id: str) -> Optional[ComplianceReport]:
        if job_id in self._active_reports:
            return self._active_reports[job_id]
        try:
            report = await persistence.load_report(job_id)
            if report:
                return report
        except Exception:
            logger.exception("Database lookup failed for %s", job_id)
        state = await memory_store.get_state(f"report_{job_id}")
        return ComplianceReport(**state) if state else None

    # --------------------------------------------------------------- override
    @staticmethod
    def _recompute(report: ComplianceReport) -> None:
        matrix = report.requirements_matrix
        counts = {s: sum(1 for v in matrix if v.status == s) for s in ComplianceStatus}
        report.compliant_count = counts[ComplianceStatus.COMPLIANT]
        report.partial_count = counts[ComplianceStatus.PARTIALLY_COMPLIANT]
        report.non_compliant_count = counts[ComplianceStatus.NON_COMPLIANT]
        report.human_review_count = counts[ComplianceStatus.REQUIRES_HUMAN_REVIEW]
        report.critical_violations_count = sum(
            1 for v in matrix if v.severity == SeverityLevel.CRITICAL and v.status == ComplianceStatus.NON_COMPLIANT
        )

        total = earned = 0.0
        for v in matrix:
            w = _SEVERITY_WEIGHTS.get(v.severity, 1.0)
            total += w
            earned += w * {ComplianceStatus.COMPLIANT: 1.0, ComplianceStatus.PARTIALLY_COMPLIANT: 0.5,
                           ComplianceStatus.REQUIRES_HUMAN_REVIEW: 0.3}.get(v.status, 0.0)
        report.compliance_score = round((earned / total) * 100.0, 1) if total else 0.0

        # Same decision rule as the Decision/Reviewer agent.
        if report.critical_violations_count > 0 or report.compliance_score < 50.0:
            report.overall_status = ComplianceStatus.NON_COMPLIANT
        elif report.non_compliant_count > 0 or report.partial_count > 0 or report.compliance_score < 85.0:
            report.overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif report.human_review_count > 0:
            report.overall_status = ComplianceStatus.REQUIRES_HUMAN_REVIEW
        else:
            report.overall_status = ComplianceStatus.COMPLIANT

    async def apply_human_override(self, job_id: str, override: OverrideRequest) -> Optional[ComplianceReport]:
        report = await self.get_report(job_id)
        if not report:
            return None

        for verdict in report.requirements_matrix:
            if verdict.requirement_id == override.requirement_id:
                # Keep the first automated status if the same item is overridden twice.
                original = verdict.human_override.original_status if verdict.human_override.is_overridden else verdict.status
                verdict.human_override = HumanOverride(
                    is_overridden=True,
                    original_status=original,
                    overridden_status=override.new_status,
                    reviewer_notes=override.notes,
                    reviewed_by=override.reviewer_name,
                    reviewed_at=datetime.now(timezone.utc),
                )
                verdict.status = override.new_status
                verdict.remarks = (verdict.remarks + " " if verdict.remarks else "") + (
                    f"[Human Override by {override.reviewer_name}: {override.notes}]"
                )
                break
        else:
            return None

        self._recompute(report)
        self._active_reports[job_id] = report
        await memory_store.save_state(f"report_{job_id}", report.model_dump(mode="json"))
        await memory_store.append_event(job_id, {
            "agent_id": "human_reviewer", "agent_name": "Human Reviewer", "status": "completed",
            "output_summary": f"{override.requirement_id} set to {override.new_status.value} by {override.reviewer_name}",
        })
        try:
            await persistence.save_report(report)  # keeps the stored document ids
        except Exception:
            logger.exception("Could not persist override for %s", job_id)
        return report


compliance_service = ComplianceService()
