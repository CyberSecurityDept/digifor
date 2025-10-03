import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class EvidenceType(Base):
    
    __tablename__ = "evidence_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50))  # digital, physical, biological, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # evidence = relationship("Evidence", back_populates="evidence_type")  # Temporarily disabled
    
    def __repr__(self):
        return f"<EvidenceType(id={self.id}, name='{self.name}')>"


class Evidence(Base):
    
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evidence_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    evidence_type_id = Column(UUID(as_uuid=True), ForeignKey("evidence_types.id"))
    
    # Case association
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    
    # Physical properties
    weight = Column(Float)  # in grams
    dimensions = Column(String(100))  # e.g., "10x5x2 cm"
    color = Column(String(50))
    material = Column(String(100))
    
    # Digital properties
    file_path = Column(String(500))
    file_size = Column(Integer)  # in bytes
    file_hash = Column(String(64))  # SHA-256 hash
    file_type = Column(String(50))  # MIME type
    file_extension = Column(String(10))
    
    # Status and processing
    status = Column(String(20), default="collected")  # collected, analyzed, archived, destroyed
    analysis_status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    analysis_progress = Column(Integer, default=0)  # 0-100%
    
    # Chain of custody
    collected_by = Column(String(100))
    collected_date = Column(DateTime(timezone=True))
    collected_location = Column(String(200))
    collection_method = Column(String(100))
    
    # Storage
    storage_location = Column(String(200))
    storage_conditions = Column(String(100))  # temperature, humidity, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True))
    
    # Additional data
    tags = Column(JSON)
    notes = Column(Text)
    is_confidential = Column(Boolean, default=False)
    
    # Relationships
    # case = relationship("Case", back_populates="evidence")  # Temporarily disabled
    # evidence_type = relationship("EvidenceType", back_populates="evidence")  # Temporarily disabled
    # custody_logs = relationship("CustodyLog", back_populates="evidence")  # Temporarily disabled
    # custody_reports = relationship("CustodyReport", back_populates="evidence")  # Temporarily disabled
    
    def __repr__(self):
        return f"<Evidence(id={self.id}, evidence_number='{self.evidence_number}', status='{self.status}')>"


class CustodyLog(Base):
    
    __tablename__ = "custody_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    
    # Custody event details
    event_type = Column(String(50), nullable=False)  # acquisition, preparation, extraction, analysis, transfer, storage
    event_date = Column(DateTime(timezone=True), nullable=False)
    person_name = Column(String(100), nullable=False)  # Person handling the evidence
    person_title = Column(String(100))  # Job title/role
    person_id = Column(String(50))  # Employee ID or badge number
    location = Column(String(200), nullable=False)  # Where the event occurred
    location_type = Column(String(50))  # lab, field, storage, court, etc.
    
    # Event details
    action_description = Column(Text)  # What was done
    tools_used = Column(JSON)  # List of tools/equipment used
    conditions = Column(String(200))  # Environmental conditions
    duration = Column(Integer)  # Duration in minutes
    
    # Transfer details (if applicable)
    transferred_to = Column(String(100))  # Person receiving evidence
    transferred_from = Column(String(100))  # Person giving evidence
    transfer_reason = Column(String(200))  # Reason for transfer
    
    # Verification
    witness_name = Column(String(100))  # Witness to the event
    witness_signature = Column(String(500))  # Digital signature or signature hash
    verification_method = Column(String(50))  # signature, biometric, digital_cert
    
    # Immutable properties
    is_immutable = Column(Boolean, default=True)  # Cannot be modified after creation
    is_verified = Column(Boolean, default=False)  # Has been verified
    verification_date = Column(DateTime(timezone=True))
    verified_by = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))  # User who created the log
    notes = Column(Text)  # Additional notes
    
    # Hash for integrity verification
    log_hash = Column(String(64))  # SHA-256 hash of the log entry
    
    # Relationships
    # evidence = relationship("Evidence", back_populates="custody_logs")  # Temporarily disabled
    
    def __repr__(self):
        return f"<CustodyLog(id={self.id}, evidence_id={self.evidence_id}, event_type='{self.event_type}')>"


class CustodyReport(Base):
    
    __tablename__ = "custody_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    report_type = Column(String(50), default="standard")  # standard, iso_27037, nist
    
    # Report details
    report_title = Column(String(200), nullable=False)
    report_description = Column(Text)
    generated_by = Column(String(100), nullable=False)
    generated_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Report content
    report_data = Column(JSON)  # Structured report data
    report_file_path = Column(String(500))  # Path to generated report file
    report_file_hash = Column(String(64))  # Hash of the report file
    
    # Compliance
    compliance_standard = Column(String(50))  # iso_27037, nist, custom
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verification_date = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    # evidence = relationship("Evidence", back_populates="custody_reports")  # Temporarily disabled
    
    def __repr__(self):
        return f"<CustodyReport(id={self.id}, evidence_id={self.evidence_id}, report_type='{self.report_type}')>"
