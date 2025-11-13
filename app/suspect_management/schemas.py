from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class SuspectBase(BaseModel):
    name: str = Field(..., description="Full name")
    case_name: Optional[str] = Field(None, description="Associated case name")
    investigator: Optional[str] = Field(None, description="Investigator name")
    status: Optional[str] = Field(None, description="Suspect status: Witness, Reported, Suspected, Suspect, Defendant (must be selected from UI, no default)")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    nationality: Optional[str] = Field(None, description="Nationality")
    phone_number: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Address")
    height: Optional[int] = Field(None, description="Height in cm")
    weight: Optional[int] = Field(None, description="Weight in kg")
    eye_color: Optional[str] = Field(None, description="Eye color")
    hair_color: Optional[str] = Field(None, description="Hair color")
    distinguishing_marks: Optional[str] = Field(None, description="Distinguishing marks")
    has_criminal_record: bool = Field(False, description="Has criminal record")
    criminal_record_details: Optional[str] = Field(None, description="Criminal record details")
    risk_level: str = Field("medium", description="Risk level")
    risk_assessment_notes: Optional[str] = Field(None, description="Risk assessment notes")
    is_confidential: bool = Field(False, description="Is confidential")
    notes: Optional[str] = Field(None, description="Additional notes")

class SuspectCreate(SuspectBase):
    pass

class SuspectUpdate(BaseModel):
    name: Optional[str] = None
    case_name: Optional[str] = None
    investigator: Optional[str] = None
    status: Optional[str] = None
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    distinguishing_marks: Optional[str] = None
    has_criminal_record: Optional[bool] = None
    criminal_record_details: Optional[str] = None
    risk_level: Optional[str] = None
    risk_assessment_notes: Optional[str] = None
    is_confidential: Optional[bool] = None
    notes: Optional[str] = None

class Suspect(SuspectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class SuspectResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: Suspect

class SuspectListItem(BaseModel):
    id: int
    case_id: Optional[int]
    person_name: str = Field(..., description="Person name (alias for name)")
    case_name: Optional[str] = Field(None, description="Associated case name")
    investigator: Optional[str] = Field(None, description="Investigator name")
    agency: Optional[str] = Field(None, description="Agency name from case")
    status: Optional[str] = Field(None, description="Suspect status")
    created_at: Optional[str] = Field(None, description="Created at timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Updated at timestamp (ISO format)")

    class Config:
        from_attributes = True

class SuspectListResponse(BaseModel):
    status: int = Field(200, description="Response status")
    message: str = Field("Success", description="Response message")
    data: List[SuspectListItem]
    total: int = Field(..., description="Total number of suspects")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")

class SuspectNotesRequest(BaseModel):
    suspect_id: int = Field(..., description="Suspect ID")
    notes: str = Field(..., description="Suspect notes text")
