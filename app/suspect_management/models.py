from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Suspect(Base):    
    __tablename__ = "suspects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    case_name = Column(String(200))
    investigator = Column(String(100))
    status = Column(Enum("Witness", "Reported", "Suspected", "Suspect", "Defendant", name="suspect_status"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    is_unknown = Column(Boolean, default=False)
    evidence_number = Column(String(100))
    evidence_source = Column(String(100))
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    case = relationship("Case", back_populates="suspects")
    
    def __repr__(self):
        return f"<Suspect(id={self.id}, name='{self.name}', status='{self.status}')>"
