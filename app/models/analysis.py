"""
Analysis model for forensic analysis results
"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Analysis(Base):
    """Forensic analysis model"""
    
    __tablename__ = "analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence_items.id"))
    
    # Analysis details
    analysis_type = Column(String(50), nullable=False)  # contacts, social_media, apk, hash, etc.
    analysis_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Status and progress
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100%
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Results
    results = Column(JSON)  # Analysis results in JSON format
    findings = Column(Text)  # Human-readable findings
    confidence_score = Column(Float)  # 0.0-1.0 confidence in results
    
    # Configuration
    analysis_config = Column(JSON)  # Analysis parameters and settings
    algorithm_version = Column(String(20))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_automated = Column(Boolean, default=True)
    
    # Relationships
    case = relationship("Case", back_populates="analyses")
    evidence_item = relationship("EvidenceItem", back_populates="analyses")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, type='{self.analysis_type}', status='{self.status}')>"


class AnalysisResult(Base):
    """Detailed analysis results"""
    
    __tablename__ = "analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    
    # Result details
    result_type = Column(String(50), nullable=False)  # contact, correlation, pattern, etc.
    result_data = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    
    # Classification
    category = Column(String(50))  # suspicious, normal, critical, etc.
    severity = Column(String(20))  # low, medium, high, critical
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # Relationships
    analysis = relationship("Analysis")
    verifier = relationship("User")
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, type='{self.result_type}', confidence={self.confidence})>"


class Correlation(Base):
    """Data correlation results"""
    
    __tablename__ = "correlations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    
    # Correlation details
    correlation_type = Column(String(50), nullable=False)  # contacts, social_media, timeline, etc.
    source_data = Column(JSON, nullable=False)
    target_data = Column(JSON, nullable=False)
    
    # Match details
    match_score = Column(Float, nullable=False)  # 0.0-1.0
    match_type = Column(String(50))  # exact, partial, fuzzy, etc.
    match_confidence = Column(Float, default=1.0)
    
    # Context
    context = Column(Text)
    significance = Column(String(20))  # low, medium, high, critical
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    case = relationship("Case")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<Correlation(id={self.id}, type='{self.correlation_type}', score={self.match_score})>"
