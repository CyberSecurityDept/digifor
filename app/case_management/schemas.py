from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum as PyEnum


class CaseStatusEnum(PyEnum):
    OPEN = "Open"
    CLOSED = "Closed"
    REOPENED = "Re-open"


class AgencyBase(BaseModel):
    name: str = Field(..., description="Agency name")


class AgencyCreate(AgencyBase):
    pass


class Agency(AgencyBase):
    id: int
    
    class Config:
        from_attributes = True


class WorkUnitBase(BaseModel):
    name: str = Field(..., description="Work unit name")
    agency_id: int = Field(..., description="Agency ID")


class WorkUnitCreate(WorkUnitBase):
    pass


class WorkUnit(WorkUnitBase):
    id: int
    
    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field("Open", description="Case status")
    main_investigator: str = Field(..., description="Main investigator name")
    
    agency_id: Optional[Union[int, str]] = Field(None, description="Agency ID")
    work_unit_id: Optional[Union[int, str]] = Field(None, description="Work unit ID")
    agency_name: Optional[str] = Field(None, description="Agency name (manual input)")
    work_unit_name: Optional[str] = Field(None, description="Work unit name (manual input)")
    
    @validator('agency_id', pre=True)
    def validate_agency_id(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('work_unit_id', pre=True)
    def validate_work_unit_id(cls, v):
        if v == "" or v is None:
            return None
        return v


class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    case_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    main_investigator: Optional[str] = None
    agency_id: Optional[int] = None
    work_unit_id: Optional[int] = None
    agency_name: Optional[str] = None
    work_unit_name: Optional[str] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields not defined in schema


class Case(BaseModel):
    id: int
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field("Open", description="Case status")
    main_investigator: str = Field(..., description="Main investigator name")
    agency_name: Optional[str] = Field(None, description="Agency name")
    work_unit_name: Optional[str] = Field(None, description="Work unit name")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CasePersonBase(BaseModel):
    person_id: int = Field(..., description="Person ID")
    person_type: str = Field(..., description="Person type")
    notes: Optional[str] = Field(None, description="Notes")
    is_primary: bool = Field(False, description="Is primary person")


class CasePersonCreate(CasePersonBase):
    pass


class CasePersonUpdate(BaseModel):
    person_type: Optional[str] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None


class CasePerson(CasePersonBase):
    id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: Case


class CaseListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[Case]
    total: int = Field(..., description="Total number of cases")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


# Case Log Schemas
class CaseLogBase(BaseModel):
    action: str = Field(..., description="Action performed")
    description: Optional[str] = Field(None, description="Detailed description of the action")
    changed_by: str = Field(..., description="User who made the change")


class CaseLogCreate(CaseLogBase):
    case_id: int = Field(..., description="Case ID")


class CaseLog(CaseLogBase):
    id: int
    case_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CaseLogResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: CaseLog


class CaseLogListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[CaseLog]
    total: int = Field(..., description="Total number of logs")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


# Case Notes Schemas
class CaseNoteBase(BaseModel):
    note: str = Field(..., description="Note content")
    status: Optional[str] = Field(None, description="Optional status for the note")
    created_by: str = Field(..., description="User who created the note")


class CaseNoteCreate(CaseNoteBase):
    case_id: int = Field(..., description="Case ID")


class CaseNote(CaseNoteBase):
    id: int
    case_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CaseNoteResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: CaseNote


class CaseNoteListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[CaseNote]
    total: int = Field(..., description="Total number of notes")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
