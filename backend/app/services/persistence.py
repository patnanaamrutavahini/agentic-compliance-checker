"""PostgreSQL / SQLite persistence for documents, compliance jobs and audit trails."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.db_models import AuditTrailRecord, ComplianceJobRecord, DocumentRecord
from app.models.schemas import ComplianceReport

logger = logging.getLogger(__name__)


async def save_document(
    doc_id: str, filename: str, file_type: str, role: str, domain: str,
    total_pages: int, raw_text: str, structure: Dict[str, Any],
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(DocumentRecord(
            id=doc_id, filename=filename, file_type=file_type, doc_role=role, domain=domain,
            total_pages=total_pages, raw_text=raw_text, structure_metadata=structure,
        ))
        await session.commit()


async def get_documents(doc_ids: List[str]) -> List[DocumentRecord]:
    """Return stored documents in the order requested; unknown ids are skipped."""
    if not doc_ids:
        return []
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(DocumentRecord).where(DocumentRecord.id.in_(doc_ids)))).scalars().all()
    by_id = {r.id: r for r in rows}
    return [by_id[i] for i in doc_ids if i in by_id]


async def save_report(
    report: ComplianceReport, reference_ids: Optional[List[str]] = None, submitted_ids: Optional[List[str]] = None
) -> None:
    """Upsert the report (JSON) and replace its audit-trail rows."""
    data = report.model_dump(mode="json")
    async with AsyncSessionLocal() as session:
        record = await session.get(ComplianceJobRecord, report.job_id)
        if record is None:
            record = ComplianceJobRecord(id=report.job_id)
            session.add(record)
        if reference_ids is not None:
            record.reference_doc_ids = reference_ids
        if submitted_ids is not None:
            record.submitted_doc_ids = submitted_ids
        record.domain = report.domain
        record.status = "completed"
        record.overall_verdict = report.overall_status.value
        record.compliance_score = report.compliance_score
        record.confidence_score = report.confidence_score
        record.report_data = data
        record.completed_at = datetime.now(timezone.utc)

        await session.execute(delete(AuditTrailRecord).where(AuditTrailRecord.job_id == report.job_id))
        for event in report.agent_audit_trail:
            session.add(AuditTrailRecord(
                job_id=report.job_id, agent_name=event.agent_name,
                action=event.output_summary or event.status,
                details=event.model_dump(mode="json"),
            ))
        await session.commit()


async def load_report(job_id: str) -> Optional[ComplianceReport]:
    async with AsyncSessionLocal() as session:
        record = await session.get(ComplianceJobRecord, job_id)
    if record is None or not record.report_data:
        return None
    return ComplianceReport(**record.report_data)


async def list_reports(limit: int = 25) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(ComplianceJobRecord).order_by(ComplianceJobRecord.created_at.desc()).limit(limit)
        )).scalars().all()
    return [
        {"job_id": r.id, "overall_status": r.overall_verdict, "compliance_score": r.compliance_score,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
