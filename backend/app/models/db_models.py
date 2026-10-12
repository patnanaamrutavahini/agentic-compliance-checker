from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class DocumentRecord(Base):
    __tablename__ = "documents"
    
    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # pdf, docx, txt
    doc_role = Column(String(32), nullable=False)  # reference, submitted
    domain = Column(String(128), default="General Compliance")
    total_pages = Column(Integer, default=1)
    raw_text = Column(Text, nullable=False)
    structure_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ComplianceJobRecord(Base):
    __tablename__ = "compliance_jobs"
    
    id = Column(String(64), primary_key=True, index=True)
    reference_doc_ids = Column(JSON, default=list)
    submitted_doc_ids = Column(JSON, default=list)
    domain = Column(String(128), default="General Compliance")
    status = Column(String(32), default="pending")  # pending, processing, completed, failed
    overall_verdict = Column(String(64), default="Requires Human Review")
    compliance_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

class AuditTrailRecord(Base):
    __tablename__ = "audit_trails"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), index=True)
    agent_name = Column(String(128))
    action = Column(String(255))
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
