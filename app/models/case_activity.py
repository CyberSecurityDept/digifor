import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class CaseActivity(Base):
    
    __tablename__ = "case_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # created, updated, closed, reopened, assigned, etc.
    description = Column(Text, nullable=False)
    
    # Change tracking
    old_value = Column(JSON)  # Previous value before change
    new_value = Column(JSON)  # New value after change
    changed_fields = Column(JSON)  # List of fields that changed
    
    # Status change specific
    status_change_reason = Column(Text)  # Reason for status change
    previous_status = Column(String(20))  # Previous status
    new_status = Column(String(20))  # New status
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # IP address of the user
    user_agent = Column(Text)  # User agent string
    
    # Relationships
    # case = relationship("Case", back_populates="activities")
    # user = relationship("User", back_populates="case_activities")
    
    def __repr__(self):
        return f"<CaseActivity(id={self.id}, case_id={self.case_id}, type='{self.activity_type}')>"


class CaseStatusHistory(Base):
    
    __tablename__ = "case_status_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Status change details
    previous_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    reason = Column(Text)  # Reason for status change
    notes = Column(Text)  # Additional notes
    
    # Metadata
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    
    # Relationships
    # case = relationship("Case", back_populates="status_history")
    # user = relationship("User", back_populates="case_status_history")
    
    def __repr__(self):
        return f"<CaseStatusHistory(id={self.id}, case_id={self.case_id}, {self.previous_status}->{self.new_status})>"
