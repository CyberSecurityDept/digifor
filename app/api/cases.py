"""
Case Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
from app.schemas.case_activity import (
    CaseActivity, CaseStatusHistory, CaseCloseRequest, 
    CaseReopenRequest, CaseStatusChangeRequest, CaseActivitySummary
)
from app.services.case_activity_service import CaseActivityService
from app.api.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=CaseSchema)
def create_case(
    case: CaseCreate,
    request: Request,
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
    
    # Create activity log for case creation
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    CaseActivityService.create_activity(
        db=db,
        case_id=db_case.id,
        user_id=current_user.id,
        activity_type="created",
        description=f"Case '{db_case.case_number}' created",
        new_value={"case_number": db_case.case_number, "title": db_case.title, "status": db_case.status},
        ip_address=client_ip,
        user_agent=user_agent
    )
    
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
    request: Request,
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
    
    # Track changes for activity log
    old_values = {}
    changed_fields = []
    update_data = case_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        old_value = getattr(case, field)
        old_values[field] = old_value
        setattr(case, field, value)
        changed_fields.append(field)
    
    case.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(case)
    
    # Create activity log for case update
    if changed_fields:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        new_values = {field: getattr(case, field) for field in changed_fields}
        
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="updated",
            description=f"Case '{case.case_number}' updated - Fields: {', '.join(changed_fields)}",
            old_value=old_values,
            new_value=new_values,
            changed_fields=changed_fields,
            ip_address=client_ip,
            user_agent=user_agent
        )
    
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


@router.post("/{case_id}/close", response_model=CaseSchema)
def close_case(
    case_id: int,
    close_request: CaseCloseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Close a case with reason and activity tracking"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    if case.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="Case is already closed"
        )
    
    # Get client IP and user agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Update case status to closed
    updated_case = CaseActivityService.update_case_status(
        db=db,
        case=case,
        new_status="closed",
        user_id=current_user.id,
        reason=close_request.reason,
        notes=close_request.notes,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return updated_case


@router.post("/{case_id}/reopen", response_model=CaseSchema)
def reopen_case(
    case_id: int,
    reopen_request: CaseReopenRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reopen a case with reason and activity tracking"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    if case.status != "closed":
        raise HTTPException(
            status_code=400,
            detail="Only closed cases can be reopened"
        )
    
    # Get client IP and user agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Update case status to reopened
    updated_case = CaseActivityService.update_case_status(
        db=db,
        case=case,
        new_status="reopened",
        user_id=current_user.id,
        reason=reopen_request.reason,
        notes=reopen_request.notes,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return updated_case


@router.post("/{case_id}/change-status", response_model=CaseSchema)
def change_case_status(
    case_id: int,
    status_request: CaseStatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Change case status with reason and activity tracking"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Validate status transition
    valid_statuses = ["open", "in_progress", "closed", "reopened", "archived"]
    if status_request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    if case.status == status_request.status:
        raise HTTPException(
            status_code=400,
            detail="Case is already in the requested status"
        )
    
    # Get client IP and user agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Update case status
    updated_case = CaseActivityService.update_case_status(
        db=db,
        case=case,
        new_status=status_request.status,
        user_id=current_user.id,
        reason=status_request.reason,
        notes=status_request.notes,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return updated_case


@router.get("/{case_id}/activities", response_model=List[CaseActivity])
def get_case_activities(
    case_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get case activities with pagination"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    activities = CaseActivityService.get_case_activities(
        db=db,
        case_id=case_id,
        limit=limit,
        offset=offset
    )
    
    return activities


@router.get("/{case_id}/activities/recent", response_model=List[CaseActivitySummary])
def get_recent_case_activities(
    case_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent case activities with user information"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    activities = CaseActivityService.get_recent_activities(
        db=db,
        case_id=case_id,
        limit=limit
    )
    
    # Convert to summary format with user info
    activity_summaries = []
    for activity in activities:
        user = db.query(User).filter(User.id == activity.user_id).first()
        summary = CaseActivitySummary(
            id=activity.id,
            activity_type=activity.activity_type,
            description=activity.description,
            timestamp=activity.timestamp,
            user_name=user.full_name if user else "Unknown",
            user_role=user.role if user else "Unknown"
        )
        activity_summaries.append(summary)
    
    return activity_summaries


@router.get("/{case_id}/status-history", response_model=List[CaseStatusHistory])
def get_case_status_history(
    case_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get case status history with pagination"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    history = CaseActivityService.get_case_status_history(
        db=db,
        case_id=case_id,
        limit=limit,
        offset=offset
    )
    
    return history
