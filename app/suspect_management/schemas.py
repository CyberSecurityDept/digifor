from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


class PersonBase(BaseModel):
    full_name: str = Field(..., description="Full name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    alias: Optional[str] = Field(None, description="Alias or nickname")
    gender: Optional[str] = Field(None, description="Gender")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    nationality: Optional[str] = Field(None, description="Nationality")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    phone_number: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    id_number: Optional[str] = Field(None, description="ID number")
    id_type: Optional[str] = Field(None, description="ID type")
    passport_number: Optional[str] = Field(None, description="Passport number")
    driver_license: Optional[str] = Field(None, description="Driver license")
    height: Optional[int] = Field(None, description="Height in cm")
    weight: Optional[int] = Field(None, description="Weight in kg")
    eye_color: Optional[str] = Field(None, description="Eye color")
    hair_color: Optional[str] = Field(None, description="Hair color")
    distinguishing_marks: Optional[str] = Field(None, description="Distinguishing marks")
    has_criminal_record: bool = Field(False, description="Has criminal record")
    criminal_record_details: Optional[str] = Field(None, description="Criminal record details")
    risk_level: str = Field("medium", description="Risk level")
    risk_assessment_notes: Optional[str] = Field(None, description="Risk assessment notes")
    status: str = Field("Active", description="Person status")
    is_primary_suspect: bool = Field(False, description="Is primary suspect")
    is_person_of_interest: bool = Field(False, description="Is person of interest")
    is_confidential: bool = Field(False, description="Is confidential")
    notes: Optional[str] = Field(None, description="Additional notes")


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    alias: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    ethnicity: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    passport_number: Optional[str] = None
    driver_license: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    distinguishing_marks: Optional[str] = None
    has_criminal_record: Optional[bool] = None
    criminal_record_details: Optional[str] = None
    risk_level: Optional[str] = None
    risk_assessment_notes: Optional[str] = None
    status: Optional[str] = None
    is_primary_suspect: Optional[bool] = None
    is_person_of_interest: Optional[bool] = None
    is_confidential: Optional[bool] = None
    notes: Optional[str] = None


class Person(PersonBase):
    id: UUID
    risk_assessment_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    last_seen: Optional[datetime]

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
