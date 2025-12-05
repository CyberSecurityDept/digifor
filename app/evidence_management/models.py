from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.utils.timezone import get_indonesia_time

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    source = Column(String(100), nullable=True)
    evidence_type = Column(String(100), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    suspect_id = Column(Integer, ForeignKey("suspects.id"), nullable=True)
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
    created_at = Column(DateTime(timezone=True), default=get_indonesia_time, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_indonesia_time, onupdate=get_indonesia_time, nullable=False)

    case = relationship("Case", back_populates="evidence")
    custody_logs = relationship("CustodyLog", back_populates="evidence", cascade="all, delete-orphan")
    custody_reports = relationship("CustodyReport", back_populates="evidence", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Evidence(id={self.id}, evidence_number='{self.evidence_number}')>"

class CustodyLog(Base):
    __tablename__ = "custody_logs"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    custody_type = Column(String(50), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=get_indonesia_time, nullable=False)
    created_by = Column(String(100))
    evidence = relationship("Evidence", back_populates="custody_logs")
    
    def __repr__(self):
        return f"<CustodyLog(id={self.id}, evidence_id={self.evidence_id}, event_type='{self.event_type}')>"

class CustodyReport(Base):
    __tablename__ = "custody_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    created_by = Column(String(100), nullable=False)
    investigator = Column(String(100), nullable=True)
    custody_type = Column(String(50), nullable=False)  
    location = Column(Text, nullable=True)
    evidence_source = Column(String(100), nullable=True)
    evidence_type = Column(String(100), nullable=True)
    evidence_detail = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_indonesia_time, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_indonesia_time, onupdate=get_indonesia_time, nullable=False)
    evidence = relationship("Evidence", back_populates="custody_reports")
    
    def __repr__(self):
        return f"<CustodyReport(id={self.id}, custody_type='{self.custody_type}')>"