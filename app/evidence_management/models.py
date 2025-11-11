from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class EvidenceType(Base):
    
    __tablename__ = "evidence_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    evidence = relationship("Evidence", back_populates="evidence_type")
    
    def __repr__(self):
        return f"<EvidenceType(id={self.id}, name='{self.name}')>"


class Evidence(Base):
    
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    evidence_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    evidence_type_id = Column(Integer, ForeignKey("evidence_types.id"))
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_hash = Column(String(64))
    file_type = Column(String(50))
    file_extension = Column(String(10))
    analysis_status = Column(String(20), default="pending")
    analysis_progress = Column(Integer, default=0)
    investigator = Column(String(100))
    collected_date = Column(DateTime(timezone=True))
    notes = Column(JSON, nullable=True)
    is_confidential = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("Case", back_populates="evidence")
    evidence_type = relationship("EvidenceType", back_populates="evidence")
    custody_logs = relationship("CustodyLog", back_populates="evidence", cascade="all, delete-orphan")
    custody_reports = relationship("CustodyReport", back_populates="evidence", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Evidence(id={self.id}, evidence_number='{self.evidence_number}')>"


class CustodyLog(Base):
    
    __tablename__ = "custody_logs"
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    person_name = Column(String(100), nullable=False)
    person_title = Column(String(100))
    person_id = Column(String(50))
    location = Column(String(200), nullable=False)
    location_type = Column(String(50))
    action_description = Column(Text)
    tools_used = Column(JSON)
    conditions = Column(String(200))
    duration = Column(Integer)
    transferred_to = Column(String(100)) 
    transferred_from = Column(String(100))
    transfer_reason = Column(String(200))
    witness_name = Column(String(100))
    witness_signature = Column(String(500))
    verification_method = Column(String(50))
    is_immutable = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True))
    verified_by = Column(String(100))
    notes = Column(Text)
    log_hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))

    evidence = relationship("Evidence", back_populates="custody_logs")
    
    def __repr__(self):
        return f"<CustodyLog(id={self.id}, evidence_id={self.evidence_id}, event_type='{self.event_type}')>"


class CustodyReport(Base):
    
    __tablename__ = "custody_reports"
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    report_type = Column(String(50), default="standard")
    report_title = Column(String(200), nullable=False)
    report_description = Column(Text)
    generated_by = Column(String(100), nullable=False)
    generated_date = Column(DateTime(timezone=True), server_default=func.now())
    report_data = Column(JSON)
    report_file_path = Column(String(500))
    report_file_hash = Column(String(64))
    compliance_standard = Column(String(50))
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verification_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    evidence = relationship("Evidence", back_populates="custody_reports")
    
    def __repr__(self):
        return f"<CustodyReport(id={self.id}, evidence_id={self.evidence_id}, report_type='{self.report_type}')>"
