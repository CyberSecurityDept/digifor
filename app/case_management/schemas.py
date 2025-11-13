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

class CaseCreate(BaseModel):
    case_number: Optional[str] = Field(None, description="Case number (optional - will auto-generate if not provided)")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
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
    
    @validator('case_number', pre=True)
    def validate_case_number(cls, v):
        if v == "" or v is None:
            return None
        
        if v and len(v.strip()) < 3:
            raise ValueError("Case number must be at least 3 characters long")
        return v.strip() if v else None

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
        extra = "ignore"

class Case(BaseModel):
    id: int
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field("Open", description="Case status")
    main_investigator: str = Field(..., description="Main investigator name")
    agency_name: Optional[str] = Field(None, description="Agency name")
    work_unit_name: Optional[str] = Field(None, description="Work unit name")
    created_at: str = Field(..., description="Date created in DD/MM/YYYY format")
    updated_at: str = Field(..., description="Date updated in DD/MM/YYYY format")

    class Config:
        from_attributes = True

class CaseListItem(BaseModel):
    id: int
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field("Open", description="Case status")
    main_investigator: str = Field(..., description="Main investigator name")
    agency_name: Optional[str] = Field(None, description="Agency name")
    work_unit_name: Optional[str] = Field(None, description="Work unit name")
    created_at: str = Field(..., description="Date created in DD/MM/YYYY format")
    updated_at: Optional[str] = Field(None, description="Date updated in DD/MM/YYYY format")

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

class PersonBase(BaseModel):
    name: str = Field(..., description="Person name")
    is_unknown: bool = Field(False, description="Is unknown person")
    suspect_status: Optional[str] = Field(None, description="Suspect status: Witness, Reported, Suspected, Suspect, Defendant (must be selected from UI)")
    custody_stage: Optional[str] = Field(None, description="Custody stage")
    evidence_id: Optional[str] = Field(None, description="Evidence ID")
    evidence_source: Optional[str] = Field(None, description="Evidence source: Handphone, SSD, Harddisk, PC, Laptop, DVR")
    evidence_summary: Optional[str] = Field(None, description="Evidence summary")
    investigator: Optional[str] = Field(None, description="Investigator name")
    created_by: str = Field(..., description="User who created the person record")

class PersonCreate(PersonBase):
    case_id: int = Field(..., description="Case ID")

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    is_unknown: Optional[bool] = None
    custody_stage: Optional[str] = None
    evidence_id: Optional[str] = None
    evidence_source: Optional[str] = None
    evidence_summary: Optional[str] = None
    investigator: Optional[str] = None

    class Config:
        extra = "ignore"

class Person(PersonBase):
    id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: Person

class PersonListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[Person]
    total: int = Field(..., description="Total number of persons")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")

class CaseResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: Case

class CaseListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[CaseListItem]
    total: int = Field(..., description="Total number of cases")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")

class CaseLogBase(BaseModel):
    action: str = Field(..., description="Action performed")
    changed_by: str = Field(..., description="User who made the change")
    change_detail: Optional[str] = Field(None, description="Detail perubahan (misal 'Adding Evidence: 32342223; Description change')")
    notes: Optional[str] = Field(None, description="Catatan tambahan (bisa kosong saat create case, tapi wajib diisi saat update status)")

class CaseLogCreate(CaseLogBase):
    case_id: int = Field(..., description="Case ID")

class CaseLogUpdate(BaseModel):
    status: str = Field(..., description="Case status (Open, Closed, Re-open)")
    notes: str = Field(..., description="Notes/alasan wajib untuk perubahan status case log entry")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['Open', 'Closed', 'Re-open']
        status_mapping = {
            'open': 'Open',
            'closed': 'Closed', 
            're-open': 'Re-open',
            'reopen': 'Re-open'
        }

        if v in valid_statuses:
            return v
        elif v.lower() in status_mapping:
            return status_mapping[v.lower()]
        else:
            raise ValueError(f"Invalid status '{v}'. Valid values are: {valid_statuses} (case-sensitive)")
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if not v or not v.strip():
            raise ValueError("Notes/alasan wajib diisi ketika mengubah status case")
        return v.strip()

class CaseLogEditItem(BaseModel):
    changed_by: str = Field(..., description="User who made the change")
    change_detail: str = Field(..., description="Detail perubahan (misal 'Adding Evidence: 32342223; Description change')")

class CaseLog(BaseModel):
    id: int
    case_id: int
    action: str = Field(..., description="Action performed")
    edit: Optional[List[CaseLogEditItem]] = Field(None, description="Array of edit details (only included if changed_by or change_detail has value)")
    notes: Optional[str] = Field(None, description="Catatan tambahan (bisa kosong saat create case, tapi wajib diisi saat update status via change-log endpoint)")
    status: Optional[str] = Field(None, description="Case status at the time of log creation")
    created_at: str
    
    class Config:
        exclude_unset = True
        exclude_none = False

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

class AnalysisItem(BaseModel):
    evidence_id: str = Field(..., description="Evidence ID")
    summary: str = Field(..., description="Analysis summary")
    status: str = Field(..., description="Analysis status")

    class Config:
        from_attributes = True

class PersonWithAnalysis(BaseModel):
    id: int
    name: str = Field(..., description="Person name")
    person_type: str = Field(..., description="Person type")
    analysis: List[AnalysisItem] = Field(default_factory=list, description="Analysis items")

    class Config:
        from_attributes = True

class CaseLogDetail(BaseModel):
    status: str = Field(..., description="Log status")
    timestamp: str = Field(..., description="Formatted timestamp")
    description: str = Field(..., description="Log description")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        from_attributes = True

class CaseSummary(BaseModel):
    total_persons: int = Field(..., description="Total number of persons")
    total_evidence: int = Field(..., description="Total number of evidence")

    class Config:
        from_attributes = True

class CaseNotesRequest(BaseModel):
    case_id: int = Field(..., description="Case ID")
    notes: str = Field(..., description="Case notes text")

class CaseDetailResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Case detail retrieved successfully", description="Response message")
    data: dict = Field(..., description="Case detail data")

    class Config:
        from_attributes = True
