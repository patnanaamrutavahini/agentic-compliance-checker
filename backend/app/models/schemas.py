from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ComplianceStatus(str, Enum):
    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"
    REQUIRES_HUMAN_REVIEW = "Requires Human Review"

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Informational"

class DocumentType(str, Enum):
    REFERENCE_STANDARD = "Reference Standard / Specification"
    SUBMITTED_REPORT = "Submitted Report / Procedure"
    INTERNAL_POLICY = "Internal Policy / Checklist"
    VENDOR_SUBMISSION = "Vendor Submission"
    UNKNOWN = "Unknown Document"

class EvidenceLocation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = 1
    section_title: Optional[str] = "General"
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    line_number: Optional[int] = None
    snippet: str
    similarity_score: Optional[float] = 1.0

class RequirementItem(BaseModel):
    id: str
    text: str
    source_document: Optional[str] = None
    section: str = "General"
    category: str = "Standard Requirement"
    severity: SeverityLevel = SeverityLevel.HIGH
    mandatory: bool = True
    source_clause: Optional[str] = None
    expected_evidence_type: Optional[str] = "Textual Clause / Data"

class HumanOverride(BaseModel):
    is_overridden: bool = False
    original_status: Optional[ComplianceStatus] = None
    overridden_status: Optional[ComplianceStatus] = None
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class DiscrepancyItem(BaseModel):
    id: str
    requirement_id: str
    discrepancy_type: str  # "Missing Information", "Direct Contradiction", "Incomplete Scope", "Technical Deviation", "Ambiguity"
    severity: SeverityLevel
    description: str
    expected_statement: str
    found_statement: Optional[str] = None
    remediation_recommendation: str

class ComplianceVerdict(BaseModel):
    requirement_id: str
    requirement_text: str
    category: str
    severity: SeverityLevel
    mandatory: bool
    status: ComplianceStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence_snippet: Optional[str] = None
    evidence_location: Optional[EvidenceLocation] = None
    supporting_evidence: List[EvidenceLocation] = []  # top-k retrieved passages (RAG trace)
    rationale: str
    missing_elements: List[str] = []
    conflicting_elements: List[str] = []
    deviations: List[str] = []
    remarks: str
    discrepancy_details: Optional[DiscrepancyItem] = None
    human_override: HumanOverride = Field(default_factory=HumanOverride)

class AgentExecutionEvent(BaseModel):
    agent_id: str
    agent_name: str
    status: str  # "pending", "running", "completed", "failed"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None
    thought_process: List[str] = []
    output_summary: Optional[str] = None
    tokens_used: int = 0
    artifacts_generated: List[str] = []

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    doc_type: DocumentType
    domain: str = "General Compliance"
    structure_summary: str = ""
    total_pages: int = 1
    total_characters: int = 0
    total_sections: int = 0
    sections: List[Dict[str, Any]] = []
    tables_found: int = 0
    raw_text: str = ""
    upload_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentInput(BaseModel):
    """One document supplied inline (name + extracted text) or by stored id."""
    name: str = "document.txt"
    text: str = ""
    document_id: Optional[str] = None


class ComplianceJobRequest(BaseModel):
    # Multi-document inputs (preferred)
    reference_documents: List[DocumentInput] = []
    submitted_documents: List[DocumentInput] = []
    reference_document_ids: List[str] = []
    submitted_document_ids: List[str] = []
    # Single-document / legacy inputs
    reference_document_id: Optional[str] = None
    submitted_document_id: Optional[str] = None
    reference_text: Optional[str] = None
    submitted_text: Optional[str] = None
    reference_doc_name: Optional[str] = None
    submitted_doc_name: Optional[str] = None
    domain: Optional[str] = "Technical & Regulatory Compliance"
    llm_provider: Optional[str] = None  # "gemini", "openai", "anthropic", "mock"
    api_key: Optional[str] = None

class ComplianceReport(BaseModel):
    job_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reference_doc_name: str
    submitted_doc_name: str
    reference_doc_names: List[str] = []
    submitted_doc_names: List[str] = []
    domain: str
    overall_status: ComplianceStatus
    compliance_score: float  # 0.0 to 100.0%
    confidence_score: float  # 0.0 to 100.0%
    total_requirements: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    human_review_count: int
    critical_violations_count: int
    executive_summary: str
    requirements: List[RequirementItem] = []
    requirements_matrix: List[ComplianceVerdict]
    discrepancies: List[DiscrepancyItem]
    agent_audit_trail: List[AgentExecutionEvent]
    classification: Dict[str, Any] = {}
    pipeline_info: Dict[str, str] = {}  # workflow engine, retrieval mode, vector backend, ...
    export_formats: Dict[str, str] = {}

class OverrideRequest(BaseModel):
    requirement_id: str
    new_status: ComplianceStatus
    notes: str
    reviewer_name: str = "Compliance Lead"

class SampleScenario(BaseModel):
    id: str
    title: str
    domain: str
    description: str
    reference_filename: str
    submitted_filename: str
    reference_text: str
    submitted_text: str
    expected_outcome_summary: str
