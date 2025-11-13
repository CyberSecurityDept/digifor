from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EvidenceBase(BaseModel):
    evidence_number: str = Field(..., description="Evidence number")
    title: str = Field(..., description="Evidence title")
    description: Optional[str] = Field(None, description="Evidence description")
    evidence_type_id: Optional[int] = Field(None, description="Evidence type ID")
    case_id: int = Field(..., description="Case ID")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_hash: Optional[str] = Field(None, description="File hash")
    file_type: Optional[str] = Field(None, description="File type")
    file_extension: Optional[str] = Field(None, description="File extension")
    analysis_status: str = Field("pending", description="Analysis status")
    investigator: Optional[str] = Field(None, description="Investigator name")
    collected_date: Optional[datetime] = Field(None, description="Collection date")
    is_confidential: bool = Field(False, description="Is confidential")
    notes: Optional[str] = Field(None, description="Evidence notes")


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    evidence_type_id: Optional[int] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    file_type: Optional[str] = None
    file_extension: Optional[str] = None
    analysis_status: Optional[str] = None
    investigator: Optional[str] = None
    collected_date: Optional[datetime] = None
    is_confidential: Optional[bool] = None
    notes: Optional[str] = None


class Evidence(EvidenceBase):
    id: int
    analysis_progress: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvidenceResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: Evidence


class EvidenceListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[Evidence]
    total: int = Field(..., description="Total number of evidence")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")

class CustodyLogBase(BaseModel):
    evidence_id: int = Field(..., description="Evidence ID")
    event_type: str = Field(..., description="Event type (acquisition, preparation, extraction, analysis, transfer, storage)")
    event_date: datetime = Field(..., description="Event date and time")
    person_name: str = Field(..., description="Person handling the evidence")
    person_title: Optional[str] = Field(None, description="Job title/role")
    person_id: Optional[str] = Field(None, description="Employee ID or badge number")
    location: str = Field(..., description="Where the event occurred")
    location_type: Optional[str] = Field(None, description="Location type (lab, field, storage, court, etc.)")
    action_description: Optional[str] = Field(None, description="What was done")
    tools_used: Optional[List[str]] = Field(None, description="List of tools/equipment used")
    conditions: Optional[str] = Field(None, description="Environmental conditions")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    transferred_to: Optional[str] = Field(None, description="Person receiving evidence")
    transferred_from: Optional[str] = Field(None, description="Person giving evidence")
    transfer_reason: Optional[str] = Field(None, description="Reason for transfer")
    witness_name: Optional[str] = Field(None, description="Witness to the event")
    witness_signature: Optional[str] = Field(None, description="Digital signature or signature hash")
    verification_method: Optional[str] = Field(None, description="Verification method (signature, biometric, digital_cert)")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustodyLogCreate(CustodyLogBase):
    created_by: str = Field(..., description="User who created the log")


class CustodyLogUpdate(BaseModel):
    action_description: Optional[str] = None
    tools_used: Optional[List[str]] = None
    conditions: Optional[str] = None
    duration: Optional[int] = None
    notes: Optional[str] = None


class CustodyLog(CustodyLogBase):
    id: int
    is_immutable: bool
    is_verified: bool
    verification_date: Optional[datetime]
    verified_by: Optional[str]
    created_at: datetime
    created_by: str
    log_hash: Optional[str]

    class Config:
        from_attributes = True


class CustodyLogResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: CustodyLog


class CustodyLogListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[CustodyLog]
    total: int = Field(..., description="Total number of custody logs")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


class CustodyChainResponse(BaseModel):
    evidence_id: int
    evidence_number: str
    evidence_title: str
    custody_chain: List[CustodyLog]
    chain_integrity: bool = Field(..., description="Whether the chain is intact")
    total_events: int
    first_event: Optional[CustodyLog]
    last_event: Optional[CustodyLog]



class CustodyReportBase(BaseModel):
    evidence_id: int = Field(..., description="Evidence ID")
    report_type: str = Field("standard", description="Report type (standard, iso_27037, nist)")
    report_title: str = Field(..., description="Report title")
    report_description: Optional[str] = Field(None, description="Report description")
    compliance_standard: Optional[str] = Field(None, description="Compliance standard (iso_27037, nist, custom)")


class CustodyReportCreate(CustodyReportBase):
    generated_by: str = Field(..., description="User who generated the report")


class CustodyReport(CustodyReportBase):
    id: int
    generated_by: str
    generated_date: datetime
    report_data: Optional[dict] = None
    report_file_path: Optional[str] = None
    report_file_hash: Optional[str] = None
    is_verified: bool
    verified_by: Optional[str] = None
    verification_date: Optional[datetime] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class CustodyReportResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: CustodyReport


class CustodyReportListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[CustodyReport]
    total: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


class EvidenceNotesRequest(BaseModel):
    evidence_id: int = Field(..., description="Evidence ID")
    notes: Dict[str, Any] = Field(..., description="Evidence notes as JSON object with id, thumbnail, and text")
