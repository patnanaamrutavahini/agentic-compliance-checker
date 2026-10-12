from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.models.schemas import (
    ComplianceJobRequest,
    ComplianceReport,
    OverrideRequest,
    AgentExecutionEvent
)
from app.services.compliance_service import compliance_service
from app.core.memory import memory_store

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

@router.post("/analyze", response_model=ComplianceReport)
async def start_compliance_analysis(request: ComplianceJobRequest):
    """
    Executes the multi-agent document intelligence and compliance workflow.
    """
    try:
        report = await compliance_service.run_compliance_check(request)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@router.get("/report/{job_id}", response_model=ComplianceReport)
async def get_compliance_report(job_id: str):
    """
    Retrieves the complete compliance audit report.
    """
    report = await compliance_service.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Compliance report for job {job_id} not found.")
    return report

@router.get("/events/{job_id}", response_model=List[Dict[str, Any]])
async def get_agent_audit_events(job_id: str):
    """
    Fetches real-time execution events and thought streams of all agents.
    """
    events = await memory_store.get_events(job_id)
    return events

@router.post("/override/{job_id}", response_model=ComplianceReport)
async def human_review_override(job_id: str, override: OverrideRequest):
    """
    Allows a human reviewer to override an automated agent verdict with notes.
    """
    updated_report = await compliance_service.apply_human_override(job_id, override)
    if not updated_report:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found to apply override.")
    return updated_report


@router.get("/reports", response_model=List[Dict[str, Any]])
async def list_saved_reports(limit: int = 25):
    """Most recent audits stored in the database."""
    from app.services import persistence
    return await persistence.list_reports(limit)
