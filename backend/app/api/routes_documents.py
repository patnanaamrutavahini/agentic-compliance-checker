import os
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.ingestion.parser import DocumentParser
from app.models.schemas import DocumentMetadata, DocumentType
from app.services import persistence

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...),
    doc_role: str = Form("submitted"),  # "reference" or "submitted"
    domain: str = Form("General Compliance"),
):
    """Upload and parse a PDF, DOCX or TXT document; the extracted text is stored and returned.

    Call repeatedly to ingest several reference and/or submitted documents.
    """
    filename = file.filename or "document.txt"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Use PDF, DOCX or TXT.")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.")
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    file_id = f"doc_{uuid.uuid4().hex[:8]}"
    saved_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    with open(saved_path, "wb") as f:
        f.write(contents)

    try:
        parsed = DocumentParser.parse_file(saved_path, filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse {filename}: {exc}")
    if not (parsed.get("raw_text") or "").strip():
        raise HTTPException(
            status_code=422,
            detail=f"No extractable text found in {filename}. Scanned/image-only PDFs need OCR first.",
        )

    doc_type = DocumentType.REFERENCE_STANDARD if doc_role == "reference" else DocumentType.SUBMITTED_REPORT
    try:
        await persistence.save_document(
            file_id, filename, ext.lstrip("."), doc_role, domain,
            parsed.get("total_pages", 1), parsed["raw_text"],
            {"sections": parsed.get("sections", []), "tables_found": parsed.get("tables_found", 0)},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not store document: {exc}")

    return DocumentMetadata(
        id=file_id,
        filename=filename,
        doc_type=doc_type,
        domain=domain,
        structure_summary=f"Parsed {parsed.get('total_sections', 0)} sections and {parsed.get('tables_found', 0)} tables.",
        total_pages=parsed.get("total_pages", 1),
        total_characters=parsed.get("total_characters", 0),
        total_sections=parsed.get("total_sections", 0),
        sections=parsed.get("sections", []),
        tables_found=parsed.get("tables_found", 0),
        raw_text=parsed["raw_text"],
    )
