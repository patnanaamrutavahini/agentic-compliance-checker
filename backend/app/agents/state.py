from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.schemas import (
    DocumentMetadata,
    RequirementItem,
    ComplianceVerdict,
    DiscrepancyItem,
    AgentExecutionEvent,
    ComplianceStatus
)
from app.ingestion.chunker import DocumentChunk

class ComplianceAgentState(BaseModel):
    """
    Shared blackboard / graph state passed across all 6 specialized agents.
    """
    job_id: str
    reference_raw_text: str = ""
    submitted_raw_text: str = ""
    reference_filename: str = "reference_doc.txt"
    submitted_filename: str = "submitted_doc.txt"

    # Multi-document inputs: [{"document_id", "filename", "text"}, ...]
    reference_documents: List[Dict[str, Any]] = Field(default_factory=list)
    submitted_documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Ingested and parsed document models
    reference_doc: Optional[DocumentMetadata] = None
    submitted_doc: Optional[DocumentMetadata] = None
    
    # Chunks and vector representation
    submitted_chunks: List[Dict[str, Any]] = []
    
    # Agent 1: Document Classification results
    classification_result: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent 2: Information Extraction results
    extracted_information: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent 3: Structured Requirements extracted from Reference Document
    requirements: List[RequirementItem] = Field(default_factory=list)
    
    # Agent 4: Requirement-level compliance comparison verdicts
    compliance_verdicts: List[ComplianceVerdict] = Field(default_factory=list)
    
    # Agent 5: Discrepancies, missing items, contradictions, deviations
    discrepancies: List[DiscrepancyItem] = Field(default_factory=list)
    
    # Agent 6: Final Reviewer Evaluation, overall compliance verdict & score
    overall_status: ComplianceStatus = ComplianceStatus.REQUIRES_HUMAN_REVIEW
    compliance_score: float = 0.0
    confidence_score: float = 0.0
    executive_summary: str = ""
    
    # Audit Trail of execution
    agent_logs: List[AgentExecutionEvent] = Field(default_factory=list)
    current_agent: str = "Idle"
    is_completed: bool = False
    error: Optional[str] = None
