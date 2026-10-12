from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, PlainTextResponse
from app.services.compliance_service import compliance_service
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/{job_id}/csv")
async def export_report_csv(job_id: str):
    report = await compliance_service.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    csv_content = ExportService.generate_csv(report)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=compliance_audit_{job_id}.csv"}
    )

@router.get("/{job_id}/json")
async def export_report_json(job_id: str):
    report = await compliance_service.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    json_content = ExportService.generate_json_str(report)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=compliance_audit_{job_id}.json"}
    )

@router.get("/{job_id}/markdown")
async def export_report_markdown(job_id: str):
    report = await compliance_service.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    md_content = ExportService.generate_markdown(report)
    return PlainTextResponse(
        content=md_content,
        headers={"Content-Disposition": f"attachment; filename=compliance_audit_{job_id}.md"}
    )


@router.get("/{job_id}/pdf")
async def export_report_pdf(job_id: str):
    report = await compliance_service.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return Response(
        content=ExportService.generate_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compliance_audit_{job_id}.pdf"}
    )
