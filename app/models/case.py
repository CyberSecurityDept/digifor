import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class Case(Base):
    
    __tablename__ = "cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    case_type = Column(String(50))  # criminal, civil, corporate, etc.
    status = Column(String(20), default="open")  # open, closed, reopened
    priority = Column(String(10), default="medium")  # low, medium, high, critical
    
    # Case details
    incident_date = Column(DateTime(timezone=True))
    reported_date = Column(DateTime(timezone=True))
    jurisdiction = Column(String(100))
    case_officer = Column(String(100))
    work_unit = Column(String(100))  # Work unit field
    
    # Digital evidence info
    evidence_count = Column(Integer, default=0)
    analysis_progress = Column(Integer, default=0)  # 0-100%
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
    
    # Additional data
    tags = Column(JSON)  # For categorization
    notes = Column(Text)
    is_confidential = Column(Boolean, default=False)
    
    # Status tracking
    reopened_count = Column(Integer, default=0)
    last_status_change = Column(DateTime(timezone=True))
    status_change_reason = Column(Text)
    status_history = Column(JSON)  # Track status changes with reasons
    
    # Relationships
    # creator = relationship("User", foreign_keys=[created_by])
    # assignee = relationship("User", foreign_keys=[assigned_to])
    # evidence_items = relationship("EvidenceItem", back_populates="case", cascade="all, delete-orphan")
    # analyses = relationship("Analysis", back_populates="case", cascade="all, delete-orphan")
    # activities = relationship("CaseActivity", back_populates="case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Case(id={self.id}, case_number='{self.case_number}', status='{self.status}')>"


class CasePerson(Base):
    
    __tablename__ = "case_persons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    person_type = Column(String(20), nullable=False)  # suspect, victim, witness, other
    
    # Personal information
    full_name = Column(String(100), nullable=False)
    alias = Column(String(100))
    date_of_birth = Column(DateTime(timezone=True))
    nationality = Column(String(50))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    
    # Digital identifiers
    social_media_accounts = Column(JSON)  # List of social media accounts
    device_identifiers = Column(JSON)  # IMEI, MAC addresses, etc.
    
    # Additional info
    description = Column(Text)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # case = relationship("Case")
    
    def __repr__(self):
        return f"<CasePerson(id={self.id}, name='{self.full_name}', type='{self.person_type}')>"
