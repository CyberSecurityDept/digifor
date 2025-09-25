import uuid
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CasePersonBase(BaseModel):
    """Base case person schema"""
    person_type: str  # suspect, victim, witness, other
    full_name: str
    alias: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_media_accounts: Optional[Dict[str, Any]] = None
    device_identifiers: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_primary: bool = False


class CasePersonCreate(CasePersonBase):
    """Schema for creating a case person"""
    pass


class CasePersonUpdate(BaseModel):
    """Schema for updating a case person"""
    person_type: Optional[str] = None
    full_name: Optional[str] = None
    alias: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_media_accounts: Optional[Dict[str, Any]] = None
    device_identifiers: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None


class CasePerson(CasePersonBase):
    """Schema for case person response"""
    id: uuid.UUID
    case_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    """Base case schema"""
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    incident_date: Optional[datetime] = None
    reported_date: Optional[datetime] = None
    jurisdiction: Optional[str] = None
    case_officer: Optional[str] = None
    work_unit: Optional[str] = None  # Work unit field
    tags: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_confidential: bool = False


class CaseCreate(CaseBase):
    """Schema for creating a case"""
    pass


class CaseCreateForm(BaseModel):
    """Schema for case creation form with auto-generated case ID option"""
    # Required fields for UI
    title: str  # Case name
    description: Optional[str] = None  # Case Description
    
    # Case ID options (UI radio buttons)
    use_auto_generated_id: bool = True  # "Generating" vs "Manual input"
    case_number: Optional[str] = None  # Only used when use_auto_generated_id is False
    
    # Investigator and Agency fields (UI dropdowns/inputs)
    case_officer: Optional[str] = None  # Main Investigator
    jurisdiction: Optional[str] = None   # Agency
    work_unit: Optional[str] = None     # Work Unit
    
    # System fields with defaults (not visible in UI but needed for backend)
    status: str = "open"  # Default status for new cases
    priority: str = "medium"  # Default priority
    case_type: Optional[str] = None  # Default case type
    is_confidential: bool = False  # Default confidentiality


class CaseUpdate(BaseModel):
    """Schema for updating a case"""
    case_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    incident_date: Optional[datetime] = None
    reported_date: Optional[datetime] = None
    jurisdiction: Optional[str] = None
    case_officer: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    tags: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_confidential: Optional[bool] = None


class Case(CaseBase):
    """Schema for case response"""
    id: uuid.UUID
    evidence_count: int
    analysis_progress: int
    created_by: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reopened_count: int = 0
    last_status_change: Optional[datetime] = None
    status_change_reason: Optional[str] = None
    persons: List[CasePerson] = []

    class Config:
        from_attributes = True


class CaseResponseData(BaseModel):
    """Schema for case response with custom field order"""
    id: uuid.UUID
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    incident_date: Optional[datetime] = None
    reported_date: Optional[datetime] = None
    jurisdiction: Optional[str] = None
    case_officer: Optional[str] = None
    work_unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_confidential: bool = False
    evidence_count: int
    analysis_progress: int
    created_by: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reopened_count: int = 0
    last_status_change: Optional[datetime] = None
    status_change_reason: Optional[str] = None
    persons: List[CasePerson] = []

    class Config:
        from_attributes = True


class CaseSummary(BaseModel):
    """Schema for case summary in lists"""
    id: uuid.UUID
    case_number: str
    title: str
    status: str
    priority: str
    evidence_count: int
    analysis_progress: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Schema for pagination information"""
    total: int
    page: int
    per_page: int
    pages: int


class CaseListResponse(BaseModel):
    """Schema for case list response with pagination"""
    status: int
    message: str
    data: List[CaseSummary]
    pagination: PaginationInfo


class CaseResponse(BaseModel):
    """Schema for single case response"""
    status: int
    message: str
    data: CaseResponseData


class CaseCreateResponse(BaseModel):
    """Schema for case creation response"""
    status: int
    message: str
    data: CaseResponseData
