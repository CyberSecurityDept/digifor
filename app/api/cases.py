"""
Case Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.case import Case, CasePerson
from app.schemas.case import (
    CaseCreate, CaseUpdate, Case as CaseSchema, 
    CaseSummary, CasePersonCreate, CasePersonUpdate, CasePerson as CasePersonSchema
)
from app.api.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=CaseSchema)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new forensic case"""
    # Check if case number already exists
    existing_case = db.query(Case).filter(Case.case_number == case.case_number).first()
    if existing_case:
        raise HTTPException(
            status_code=400,
            detail="Case number already exists"
        )
    
    # Create new case
    db_case = Case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        case_type=case.case_type,
        status=case.status,
        priority=case.priority,
        incident_date=case.incident_date,
        reported_date=case.reported_date,
        jurisdiction=case.jurisdiction,
        case_officer=case.case_officer,
        tags=case.tags,
        notes=case.notes,
        is_confidential=case.is_confidential,
        created_by=current_user.id
    )
    
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    return db_case


@router.get("/", response_model=List[CaseSummary])
def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of cases with filtering and pagination"""
    query = db.query(Case)
    
    # Apply filters
    if status:
        query = query.filter(Case.status == status)
    if priority:
        query = query.filter(Case.priority == priority)
    if case_type:
        query = query.filter(Case.case_type == case_type)
    if search:
        query = query.filter(
            (Case.title.contains(search)) |
            (Case.case_number.contains(search)) |
            (Case.description.contains(search))
        )
    
    # Apply pagination
    cases = query.offset(skip).limit(limit).all()
    return cases


@router.get("/{case_id}", response_model=CaseSchema)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific case by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    return case


@router.put("/{case_id}", response_model=CaseSchema)
def update_case(
    case_id: int,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Update fields
    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(case)
    
    return case


@router.delete("/{case_id}")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a case (soft delete by changing status)"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Soft delete by changing status to archived
    case.status = "archived"
    case.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Case archived successfully"}


@router.post("/{case_id}/persons", response_model=CasePersonSchema)
def add_case_person(
    case_id: int,
    person: CasePersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a person to a case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
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


@router.get("/{case_id}/persons", response_model=List[CasePersonSchema])
def get_case_persons(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all persons in a case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    persons = db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
    return persons


@router.put("/{case_id}/persons/{person_id}", response_model=CasePersonSchema)
def update_case_person(
    case_id: int,
    person_id: int,
    person_update: CasePersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a case person"""
    person = db.query(CasePerson).filter(
        CasePerson.id == person_id,
        CasePerson.case_id == case_id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )
    
    # Update fields
    update_data = person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)
    
    person.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(person)
    
    return person


@router.delete("/{case_id}/persons/{person_id}")
def delete_case_person(
    case_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a case person"""
    person = db.query(CasePerson).filter(
        CasePerson.id == person_id,
        CasePerson.case_id == case_id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )
    
    db.delete(person)
    db.commit()
    
    return {"message": "Person deleted successfully"}


@router.get("/{case_id}/stats")
def get_case_stats(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get case statistics"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Get evidence count
    evidence_count = db.query(Case).filter(Case.id == case_id).first().evidence_count
    
    # Get analysis count
    from app.models.analysis import Analysis
    analysis_count = db.query(Analysis).filter(Analysis.case_id == case_id).count()
    
    # Get completed analysis count
    completed_analysis = db.query(Analysis).filter(
        Analysis.case_id == case_id,
        Analysis.status == "completed"
    ).count()
    
    return {
        "case_id": case_id,
        "evidence_count": evidence_count,
        "analysis_count": analysis_count,
        "completed_analysis": completed_analysis,
        "analysis_progress": case.analysis_progress,
        "status": case.status,
        "priority": case.priority
    }
