import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Date, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Person(Base):    
    __tablename__ = "persons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(200), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    alias = Column(String(200))  # Nickname or alias
    gender = Column(String(10))  # male, female, other
    date_of_birth = Column(Date)
    place_of_birth = Column(String(100))
    nationality = Column(String(50))
    ethnicity = Column(String(50))
    
    # Contact information
    phone_number = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(50))
    postal_code = Column(String(20))
    
    # Identification
    id_number = Column(String(50))  # National ID, passport, etc.
    id_type = Column(String(20))  # passport, national_id, driver_license, etc.
    passport_number = Column(String(50))
    driver_license = Column(String(50))
    
    # Physical description
    height = Column(Integer)  # in cm
    weight = Column(Integer)  # in kg
    eye_color = Column(String(20))
    hair_color = Column(String(20))
    distinguishing_marks = Column(Text)  # Tattoos, scars, etc.
    
    # Criminal record
    has_criminal_record = Column(Boolean, default=False)
    criminal_record_details = Column(Text)
    previous_convictions = Column(JSON)  # List of previous convictions
    
    # Risk assessment
    risk_level = Column(String(10), default="medium")  # low, medium, high, critical
    risk_assessment_date = Column(DateTime(timezone=True))
    risk_assessment_notes = Column(Text)
    
    # Status
    status = Column(Enum("Active", "Inactive", "Deceased", name="person_status"), nullable=False, default="Active")
    is_primary_suspect = Column(Boolean, default=False)
    is_person_of_interest = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))
    
    # Additional data
    tags = Column(JSON)
    notes = Column(Text)
    is_confidential = Column(Boolean, default=False)
    
    # Relationships
    # case_persons = relationship("CasePerson", back_populates="person")  # Will be added later
    
    def __repr__(self):
        return f"<Person(id={self.id}, full_name='{self.full_name}', status='{self.status}')>"
