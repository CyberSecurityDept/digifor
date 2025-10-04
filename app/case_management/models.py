from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from app.db.base import Base


class CaseStatus(PyEnum):
    OPEN = "Open"
    CLOSED = "Closed"
    REOPENED = "Re-open"


class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    
    work_units = relationship("WorkUnit", back_populates="agency")
    
    def __repr__(self):
        return f"<Agency(id={self.id}, name='{self.name}')>"


class WorkUnit(Base):
    __tablename__ = "work_units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.id"))
    
    agency = relationship("Agency", back_populates="work_units")
    
    def __repr__(self):
        return f"<WorkUnit(id={self.id}, name='{self.name}', agency_id={self.agency_id})>"


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum("Open", "Closed", "Re-open", name="casestatus"), default="Open")
    main_investigator = Column(String(255), nullable=False)
    
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=True)
    work_unit_id = Column(Integer, ForeignKey("work_units.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    logs = relationship("CaseLog", back_populates="case")
    notes = relationship("CaseNote", back_populates="case")
    
    def generate_case_number(self):

        if not self.case_number:
            today = datetime.today()
            self.case_number = f"CASE {today.year}-{today.month:02d}-01"
    
    def __repr__(self):
        return f"<Case(id={self.id}, case_number='{self.case_number}', status='{self.status}')>"


class CasePerson(Base):
    
    __tablename__ = "case_persons"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    person_id = Column(Integer, nullable=False)
    person_type = Column(String(20), nullable=False)
    notes = Column(Text)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    
    def __repr__(self):
        return f"<CasePerson(id={self.id}, person_id={self.person_id}, type='{self.person_type}')>"


class CaseLog(Base):
    __tablename__ = "case_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    action = Column(String(50), nullable=False)  # "Open", "Closed", "Re-open", "Edit", etc.
    description = Column(Text)  # Detailed description of the action
    changed_by = Column(String(255), nullable=False)  # User who made the change
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to Case
    case = relationship("Case", back_populates="logs")
    
    def __repr__(self):
        return f"<CaseLog(id={self.id}, case_id={self.case_id}, action='{self.action}')>"


class CaseNote(Base):
    __tablename__ = "case_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    note = Column(Text, nullable=False)
    status = Column(String(20), nullable=True)  # Optional status for the note
    created_by = Column(String(255), nullable=False)  # User who created the note
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to Case
    case = relationship("Case", back_populates="notes")
    
    def __repr__(self):
        return f"<CaseNote(id={self.id}, case_id={self.case_id}, status='{self.status}')>"
