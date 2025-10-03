from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID


class CaseStatusEnum(PyEnum):
    OPEN = "Open"
    CLOSED = "Closed"
    REOPENED = "Reopened"


class AgencyBase(BaseModel):
    name: str = Field(..., description="Agency name")


class AgencyCreate(AgencyBase):
    pass


class Agency(AgencyBase):
    id: UUID
    
    class Config:
        from_attributes = True


class WorkUnitBase(BaseModel):
    name: str = Field(..., description="Work unit name")
    agency_id: UUID = Field(..., description="Agency ID")


class WorkUnitCreate(WorkUnitBase):
    pass


class WorkUnit(WorkUnitBase):
    id: UUID
    
    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field("Open", description="Case status")
    main_investigator: str = Field(..., description="Main investigator name")
    
    agency_id: Optional[UUID] = Field(None, description="Agency ID")
    work_unit_id: Optional[UUID] = Field(None, description="Work unit ID")

    agency_name: Optional[str] = Field(None, description="Agency name (manual input)")
    work_unit_name: Optional[str] = Field(None, description="Work unit name (manual input)")


class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    case_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    main_investigator: Optional[str] = None
    agency_id: Optional[UUID] = None
    work_unit_id: Optional[UUID] = None
    agency_name: Optional[str] = None
    work_unit_name: Optional[str] = None


class Case(CaseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CasePersonBase(BaseModel):
    person_id: UUID = Field(..., description="Person ID")
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
    id: UUID
    case_id: UUID
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
