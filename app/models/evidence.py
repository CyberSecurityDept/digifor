"""
Evidence model for digital evidence management
"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class EvidenceItem(Base):
    """Digital evidence item model"""
    
    __tablename__ = "evidence_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    evidence_number = Column(String(50), nullable=False)  # E001, E002, etc.
    
    # Evidence details
    item_type = Column(String(50), nullable=False)  # phone, computer, usb, apk, image, etc.
    description = Column(Text, nullable=False)
    source = Column(String(200))  # Where evidence was found
    
    # File information
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    file_type = Column(String(50))  # MIME type
    file_extension = Column(String(10))
    
    # Hash values for integrity
    md5_hash = Column(String(32))
    sha1_hash = Column(String(40))
    sha256_hash = Column(String(64))
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status and processing
    status = Column(String(20), default="uploaded")  # uploaded, processing, analyzed, archived
    is_encrypted = Column(Boolean, default=False)
    encryption_method = Column(String(50))
    
    # Chain of custody
    custody_chain = Column(JSON)  # List of custody transfers
    current_custodian = Column(String(100))
    
    # Analysis results
    analysis_status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    analysis_notes = Column(Text)
    
    # Additional metadata
    tags = Column(JSON)
    is_sensitive = Column(Boolean, default=False)
    
    # Relationships
    case = relationship("Case", back_populates="evidence_items")
    creator = relationship("User")
    analyses = relationship("Analysis", back_populates="evidence_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EvidenceItem(id={self.id}, evidence_number='{self.evidence_number}', type='{self.item_type}')>"


class CustodyTransfer(Base):
    """Chain of custody transfer record"""
    
    __tablename__ = "custody_transfers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence_items.id"), nullable=False)
    
    # Transfer details
    from_custodian = Column(String(100), nullable=False)
    to_custodian = Column(String(100), nullable=False)
    transfer_date = Column(DateTime(timezone=True), server_default=func.now())
    transfer_reason = Column(Text)
    transfer_method = Column(String(50))  # handover, courier, digital, etc.
    
    # Verification
    from_signature = Column(String(500))  # Digital signature
    to_signature = Column(String(500))
    witness = Column(String(100))
    witness_signature = Column(String(500))
    
    # Location and condition
    transfer_location = Column(String(200))
    evidence_condition = Column(Text)
    notes = Column(Text)
    
    # Relationships
    evidence_item = relationship("EvidenceItem")
    
    def __repr__(self):
        return f"<CustodyTransfer(id={self.id}, evidence_id={self.evidence_id}, from='{self.from_custodian}')>"
