from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.utils.timezone import get_indonesia_time


class Suspect(Base):    
    __tablename__ = "suspects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    case_name = Column(String(500))
    investigator = Column(String(100))
    status = Column(Enum("Witness", "Reported", "Suspected", "Suspect", "Defendant", name="suspect_status"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    is_unknown = Column(Boolean, default=False)
    evidence_number = Column(String(100))
    evidence_source = Column(String(100))
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_indonesia_time, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_indonesia_time, onupdate=get_indonesia_time, nullable=False)
    
    case = relationship("Case", back_populates="suspects")
    
    def __repr__(self):
        return f"<Suspect(id={self.id}, name='{self.name}', status='{self.status}')>"
