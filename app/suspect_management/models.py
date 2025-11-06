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
    status = Column(Enum("Witness", "Suspected Person", "Reported Person", "Suspect", "Defendant / Accused", name="suspect_status"), nullable=False, default="Suspect")
    
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    
    date_of_birth = Column(Date)
    place_of_birth = Column(String(100))
    nationality = Column(String(50))
    
    phone_number = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    
    height = Column(Integer)
    weight = Column(Integer)
    eye_color = Column(String(20))
    hair_color = Column(String(20))
    distinguishing_marks = Column(Text)
    
    has_criminal_record = Column(Boolean, default=False)
    criminal_record_details = Column(Text)
    
    risk_level = Column(String(10), default="medium")
    risk_assessment_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))
    
    notes = Column(Text)
    is_confidential = Column(Boolean, default=False)
    
    case = relationship("Case", back_populates="suspects")
    
    def __repr__(self):
        return f"<Suspect(id={self.id}, name='{self.name}', status='{self.status}')>"
