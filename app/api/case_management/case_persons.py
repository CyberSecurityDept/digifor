from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.user import User
from app.models.case import Case, CasePerson
from app.schemas.case import (
    CaseCreate, CaseUpdate, Case as CaseSchema, 
    CaseSummary, CasePersonCreate, CasePersonUpdate, CasePerson as CasePersonSchema,
    CaseListResponse, PaginationInfo, CaseResponse, CaseCreateResponse,
    CaseCreateForm
)
from app.schemas.case_activity import (
    CaseActivity, CaseStatusHistory, CaseCloseRequest, 
    CaseReopenRequest, CaseStatusChangeRequest, CaseActivitySummary
)
from app.services.case_activity_service import CaseActivityService
from app.dependencies.auth import get_current_active_user_safe

router = APIRouter()


def parse_case_id(case_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(case_id)
    except ValueError:
        raise ValueError("Invalid case ID format")


@router.post("/{case_id}/persons", response_model=CasePersonSchema, tags=["Case Person of Interest Management"])
def add_case_person(
    case_id: int,
    person: CasePersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Add a new person of interest to a case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    # Create new case person
    db_person = CasePerson(
        case_id=case_id,
        person_type=person.person_type,
        full_name=person.full_name,
        alias=person.alias,
        date_of_birth=person.date_of_birth,
        nationality=person.nationality,
        address=person.address,
        phone=person.phone,
        email=person.email,
        social_media_accounts=person.social_media_accounts,
        device_identifiers=person.device_identifiers,
        description=person.description,
        is_primary=person.is_primary
    )
    
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    
    return db_person


@router.get("/{case_id}/persons", response_model=List[CasePersonSchema], tags=["Case Person of Interest Management"])
def get_case_persons(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get all persons of interest for a case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    persons = db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
    return persons


@router.put("/{case_id}/persons/{person_id}", response_model=CasePersonSchema, tags=["Case Person of Interest Management"])
def update_case_person(
    case_id: int,
    person_id: int,
    person_update: CasePersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Update person of interest information"""
    person = db.query(CasePerson).filter(
        CasePerson.id == person_id,
        CasePerson.case_id == case_id
    ).first()
    
    if not person:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "message": "Person not found"
            }
        )
    
    # Update fields
    update_data = person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)
    
    person.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(person)
    
    return person


@router.delete("/{case_id}/persons/{person_id}", tags=["Case Person of Interest Management"])
def delete_case_person(
    case_id: str,
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Delete a person of interest from a case"""
    case_uuid = parse_case_id(case_id)
    person_uuid = parse_case_id(person_id)
    
    person = db.query(CasePerson).filter(
        CasePerson.id == person_uuid,
        CasePerson.case_id == case_uuid
    ).first()
    
    if not person:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "message": "Person not found"
            }
        )
    
    db.delete(person)
    db.commit()
    
    return {"message": "Person deleted successfully"}
