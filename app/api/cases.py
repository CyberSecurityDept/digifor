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
    CaseCreateForm, CaseResponse as CaseResponseSchema
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
        return JSONResponse(
            status_code=400,
            content="Invalid case ID format"
        )


@router.post("/create-cases/", response_model=CaseCreateResponse)
def create_case(
    case_form: CaseCreateForm,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    try:
        from datetime import datetime
        
        # Generate case number if auto-generated is enabled
        if case_form.use_auto_generated_id:
            # Generate case number with format: CASE-YYYY-NNNN
            current_year = datetime.now().year
            # Get the last case number for this year
            last_case = db.query(Case).filter(
                Case.case_number.like(f"CASE-{current_year}-%")
            ).order_by(Case.created_at.desc()).first()
            
            if last_case:
                # Extract number from last case and increment
                try:
                    last_number = int(last_case.case_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            case_number = f"CASE-{current_year}-{new_number:04d}"
        else:
            # Use manual case number
            if not case_form.case_number:
                return JSONResponse(
                    status_code=400,
                    content="Case number is required when auto-generated ID is disabled"
                )
            case_number = case_form.case_number
        
        # Check if case number already exists
        existing_case = db.query(Case).filter(Case.case_number == case_number).first()
        if existing_case:
            return JSONResponse(
                status_code=400,
                content="Case number already exists"
            )
        
        # Create new case
        db_case = Case(
            case_number=case_number,
            title=case_form.title,
            description=case_form.description,
            case_type=case_form.case_type,
            status=case_form.status,
            priority=case_form.priority,
            incident_date=None,  # Not in UI form
            reported_date=None,   # Not in UI form
            jurisdiction=case_form.jurisdiction,
            case_officer=case_form.case_officer,
            work_unit=case_form.work_unit,
            tags=None,           # Not in UI form
            notes=None,          # Not in UI form
            is_confidential=case_form.is_confidential,
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
        
        return CaseCreateResponse(
            status=201,
            message="Case created successfully",
            data=db_case
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Case creation failed: {str(e)}"}
        )


@router.get("/get-all-cases/", response_model=CaseListResponse)
def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    try:
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
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        cases = query.offset(skip).limit(limit).all()
        
        # Calculate pagination info
        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit  # Ceiling division
        
        return CaseListResponse(
            status=200,
            message="Cases retrieved successfully",
            data=cases,
            pagination=PaginationInfo(
                total=total,
                page=page,
                per_page=limit,
                pages=pages
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Failed to retrieve cases: {str(e)}"}
        )


@router.get("/search")
def search_cases(
    q: str = Query(..., description="Search query"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    query = db.query(Case)
    
    # Apply search filter
    if q:
        query = query.filter(
            (Case.title.contains(q)) |
            (Case.case_number.contains(q)) |
            (Case.description.contains(q)) |
            (Case.case_officer.contains(q)) |
            (Case.jurisdiction.contains(q))
        )
    
    # Apply additional filters
    if status:
        query = query.filter(Case.status == status)
    if priority:
        query = query.filter(Case.priority == priority)
    if case_type:
        query = query.filter(Case.case_type == case_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    
    # Format cases for dashboard display
    case_list = []
    for case in cases:
        # Get investigator name
        investigator_name = case.case_officer or "Unassigned"
        if case.assigned_to:
            assigned_user = db.query(User).filter(User.id == case.assigned_to).first()
            if assigned_user:
                investigator_name = assigned_user.full_name or assigned_user.username
        
        # Format date for display
        created_date = case.created_at.strftime("%m/%d/%y") if case.created_at else "N/A"
        
        case_list.append({
            "id": str(case.id),
            "case_name": case.title,
            "case_number": case.case_number,
            "investigator": investigator_name,
            "agency": case.jurisdiction or "N/A",
            "date_created": created_date,
            "status": case.status.title(),
            "priority": case.priority,
            "case_type": case.case_type,
            "evidence_count": case.evidence_count,
            "analysis_progress": case.analysis_progress,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None
        })
    
    # Calculate pagination info
    page = (skip // limit) + 1
    pages = (total + limit - 1) // limit
    
    return {
        "status": 200,
        "message": "Case search completed successfully",
        "data": {
            "cases": case_list,
            "total": total,
            "pagination": {
                "page": page,
                "per_page": limit,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            },
            "filters_applied": {
                "search_query": q,
                "status": status,
                "priority": priority,
                "case_type": case_type
            }
        }
    }


@router.get("/filter-options")
def get_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get available filter options for case management dashboard"""
    
    # Get unique statuses
    statuses = db.query(Case.status).distinct().all()
    status_list = [status[0] for status in statuses if status[0]]
    
    # Get unique priorities
    priorities = db.query(Case.priority).distinct().all()
    priority_list = [priority[0] for priority in priorities if priority[0]]
    
    # Get unique case types
    case_types = db.query(Case.case_type).distinct().all()
    case_type_list = [case_type[0] for case_type in case_types if case_type[0]]
    
    # Get unique jurisdictions
    jurisdictions = db.query(Case.jurisdiction).distinct().all()
    jurisdiction_list = [jurisdiction[0] for jurisdiction in jurisdictions if jurisdiction[0]]
    
    # Get unique case officers
    case_officers = db.query(Case.case_officer).distinct().all()
    officer_list = [officer[0] for officer in case_officers if officer[0]]
    
    return {
        "status": 200,
        "message": "Filter options retrieved successfully",
        "data": {
            "statuses": status_list,
            "priorities": priority_list,
            "case_types": case_type_list,
            "jurisdictions": jurisdiction_list,
            "case_officers": officer_list
        }
    }


@router.get("/form-options")
def get_form_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get available options for case creation form"""
    
    # Get available investigators (users with investigator role or all users)
    investigators = db.query(User).filter(
        (User.role == "investigator") | (User.role == "admin")
    ).all()
    
    investigator_list = []
    for user in investigators:
        investigator_list.append({
            "id": str(user.id),
            "name": user.full_name or user.username,
            "username": user.username,
            "role": user.role
        })
    
    # Get unique agencies from existing cases
    agencies = db.query(Case.jurisdiction).distinct().all()
    agency_list = [agency[0] for agency in agencies if agency[0]]
    
    # Get unique work units from existing cases
    work_units = db.query(Case.work_unit).distinct().all()
    work_unit_list = [unit[0] for unit in work_units if unit[0]]
    
    # Get case types for dropdown
    case_types = ["criminal", "civil", "corporate", "cybercrime", "fraud", "other"]
    
    # Get priorities for dropdown
    priorities = ["low", "medium", "high", "critical"]
    
    return {
        "status": 200,
        "message": "Form options retrieved successfully",
        "data": {
            "investigators": investigator_list,
            "agencies": agency_list,
            "work_units": work_unit_list,
            "case_types": case_types,
            "priorities": priorities
        }
    }


@router.get("/overview")
def get_case_management_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    
    # Get case statistics for dashboard cards
    open_cases = db.query(Case).filter(Case.status == "open").count()
    closed_cases = db.query(Case).filter(Case.status == "closed").count()
    reopened_cases = db.query(Case).filter(Case.status == "reopened").count()
    
    return {
        "status": 200,
        "message": "Case management overview retrieved successfully",
        "data": {
            "dashboard_cards": {
                "case_open": open_cases,
                "case_closed": closed_cases,
                "case_reopen": reopened_cases
            }
        }
    }


@router.get("/case-by-id", response_model=CaseResponse)
def get_case(
    case_id: str = Query(..., description="Case ID to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    case = db.query(Case).filter(Case.id == case_uuid).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    return CaseResponse(
        status=200,
        message="Case retrieved successfully",
        data=case
    )


@router.put("/update-case/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    case = db.query(Case).filter(Case.id == case_uuid).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
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
        
        # Convert datetime and UUID objects to strings for JSON serialization
        def serialize_for_json(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif obj is None:
                return None
            else:
                return obj
        
        # Serialize old_values and new_values
        serialized_old_values = {k: serialize_for_json(v) for k, v in old_values.items()}
        serialized_new_values = {k: serialize_for_json(v) for k, v in new_values.items()}
        
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="updated",
            description=f"Case '{case.case_number}' updated - Fields: {', '.join(changed_fields)}",
            old_value=serialized_old_values,
            new_value=serialized_new_values,
            changed_fields=changed_fields,
            ip_address=client_ip,
            user_agent=user_agent
        )
    
    return CaseResponse(
        status=200,
        message="Case updated successfully",
        data=case
    )


@router.delete("/delete-case/")
def delete_case_by_query(
    case_id: str = Query(..., description="Case ID to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    try:
        case_uuid = parse_case_id(case_id)
        case = db.query(Case).filter(Case.id == case_uuid).first()
        if not case:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Case not found"
                }
            )
        
        # Soft delete by changing status to archived
        case.status = "archived"
        case.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Case archived successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Case deletion failed: {str(e)}"}
        )


@router.post("/{case_id}/persons", response_model=CasePersonSchema)
def add_case_person(
    case_id: int,
    person: CasePersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
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
    current_user: User = Depends(get_current_active_user_safe)
):
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    persons = db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
    return persons


@router.put("/{case_id}/persons/{person_id}", response_model=CasePersonSchema)
def update_case_person(
    case_id: int,
    person_id: int,
    person_update: CasePersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    person = db.query(CasePerson).filter(
        CasePerson.id == person_id,
        CasePerson.case_id == case_id
    ).first()
    
    if not person:
        return JSONResponse(
            status_code=404,
            content="Person not found"
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
    case_id: str,
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    person_uuid = parse_case_id(person_id)
    
    person = db.query(CasePerson).filter(
        CasePerson.id == person_uuid,
        CasePerson.case_id == case_uuid
    ).first()
    
    if not person:
        return JSONResponse(
            status_code=404,
            content="Person not found"
        )
    
    db.delete(person)
    db.commit()
    
    return {"message": "Person deleted successfully"}


@router.get("/{case_id}/stats")
def get_case_stats(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
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


@router.post("/{case_id}/close", response_model=CaseResponse)
def close_case(
    case_id: str,
    close_request: CaseCloseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    case = db.query(Case).filter(Case.id == case_uuid).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    if case.status == "closed":
        return JSONResponse(
            status_code=400,
            content="Case is already closed"
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
    
    return CaseResponse(
        status=200,
        message="Case closed successfully",
        data=updated_case
    )


@router.post("/{case_id}/reopen", response_model=CaseResponse)
def reopen_case(
    case_id: str,
    reopen_request: CaseReopenRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    case = db.query(Case).filter(Case.id == case_uuid).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    if case.status != "closed":
        return JSONResponse(
            status_code=400,
            content="Only closed cases can be reopened"
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
    
    return CaseResponse(
        status=200,
        message="Case reopened successfully",
        data=updated_case
    )


@router.post("/{case_id}/change-status", response_model=CaseResponse)
def change_case_status(
    case_id: str,
    status_request: CaseStatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    case_uuid = parse_case_id(case_id)
    case = db.query(Case).filter(Case.id == case_uuid).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    # Validate status transition
    valid_statuses = ["open", "closed", "reopened"]
    if status_request.status not in valid_statuses:
        return JSONResponse(
            status_code=400,
            content=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    if case.status == status_request.status:
        return JSONResponse(
            status_code=400,
            content="Case is already in the requested status"
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
    
    return CaseResponse(
        status=200,
        message="Case status changed successfully",
        data=updated_case
    )


@router.get("/{case_id}/activities", response_model=List[CaseActivity])
def get_case_activities(
    case_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
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
    current_user: User = Depends(get_current_active_user_safe)
):
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
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
    current_user: User = Depends(get_current_active_user_safe)
):
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content="Case not found"
        )
    
    history = CaseActivityService.get_case_status_history(
        db=db,
        case_id=case_id,
        limit=limit,
        offset=offset
    )
    
    return history
