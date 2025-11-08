from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
from enum import Enum as PyEnum
from app.db.base import Base

WIB = timezone(timedelta(hours=7))


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
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    logs = relationship("CaseLog", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")
    persons = relationship("Person", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    suspects = relationship("Suspect", back_populates="case", cascade="all, delete-orphan")
    
    def generate_case_number(self):
        if self.case_number is None or (isinstance(self.case_number, str) and self.case_number.strip() == ""):
            title_words = self.title.split()[:3]
            title_prefix = ''.join([word[0].upper() for word in title_words])
            today = datetime.today()
            date_str = today.strftime("%d%m%y")
            
            case_num_value = f"{title_prefix}-{date_str}-{self.id:04d}"
            setattr(self, 'case_number', case_num_value)
    
    def __repr__(self):
        return f"<Case(id={self.id}, case_number='{self.case_number}', status='{self.status}')>"

class CaseLog(Base):
    __tablename__ = "case_logs"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)
    changed_by = Column(String(255), nullable=True, default="")
    change_detail = Column(Text, nullable=True, default="")
    notes = Column(Text, nullable=True, default="")
    status = Column(Enum("Open", "Closed", "Re-open", name="casestatus"), default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case = relationship("Case", back_populates="logs")

    def __repr__(self):
        return (
            f"<CaseLog(id={self.id}, case_id={self.case_id}, "
            f"action='{self.action}', changed_by='{self.changed_by}')>"
        )

class CaseNote(Base):
    __tablename__ = "case_notes"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    note = Column(Text, nullable=False)
    status = Column(String(20), nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case = relationship("Case", back_populates="notes")
    
    def __repr__(self):
        return f"<CaseNote(id={self.id}, case_id={self.case_id}, status='{self.status}')>"

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_unknown = Column(Boolean, default=False)
    custody_stage = Column(String(100))
    evidence_id = Column(String(100))
    evidence_source = Column(String(100))
    evidence_summary = Column(Text)
    investigator = Column(String(255))

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=False)

    case = relationship("Case", back_populates="persons")
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}', case_id={self.case_id})>"
