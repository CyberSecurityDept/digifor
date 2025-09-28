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


@router.post("/create-cases/", response_model=CaseCreateResponse)
def create_case(
    case_form: CaseCreateForm,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    try:
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
                    content={
                        "status": 400,
                        "message": "Case number is required when auto-generated ID is disabled"
                    }
                )
            case_number = case_form.case_number
        
        # Check if case number already exists
        existing_case = db.query(Case).filter(Case.case_number == case_number).first()
        if existing_case:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Case number already exists"
                }
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
        
        return CaseResponse(
            status=200,
            message="Case retrieved successfully",
            data=case
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to retrieve case",
                "error": str(e)
            }
        )


@router.get("/{case_id}/detail")
def get_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get comprehensive case details including persons, evidence, activities, and notes"""
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
        
        # Get persons of interest
        persons = db.query(CasePerson).filter(CasePerson.case_id == case_uuid).all()
        
        # Get evidence items
        from app.models.evidence import EvidenceItem
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_uuid).all()
        
        # Get recent activities (case log)
        activities = db.query(CaseActivity).filter(
            CaseActivity.case_id == case_uuid
        ).order_by(CaseActivity.timestamp.desc()).limit(20).all()
        
        # Get case notes (stored in case.notes field for now)
        case_notes = []
        if case.notes:
            # Parse notes if they're stored as JSON
            try:
                import json
                case_notes = json.loads(case.notes) if isinstance(case.notes, str) else case.notes
            except:
                # If not JSON, treat as single note
                case_notes = [{"content": case.notes, "timestamp": case.updated_at.isoformat() if case.updated_at else case.created_at.isoformat()}]
        
        # Get evidence-person associations
        from app.models.case import EvidencePersonAssociation
        associations = db.query(EvidencePersonAssociation).filter(
            EvidencePersonAssociation.evidence_id.in_([str(e.id) for e in evidence_items])
        ).all()
        
        # Create mapping of evidence to persons
        evidence_to_persons = {}
        for assoc in associations:
            if str(assoc.evidence_id) not in evidence_to_persons:
                evidence_to_persons[str(assoc.evidence_id)] = []
            evidence_to_persons[str(assoc.evidence_id)].append({
                "person_id": str(assoc.person_id),
                "association_type": assoc.association_type,
                "confidence_level": assoc.confidence_level,
                "notes": assoc.association_notes
            })
        
        # Format persons with their evidence
        persons_with_evidence = []
        for person in persons:
            # Get evidence associated with this person through associations
            person_evidence = []
            for evidence in evidence_items:
                evidence_id_str = str(evidence.id)
                if evidence_id_str in evidence_to_persons:
                    for assoc_info in evidence_to_persons[evidence_id_str]:
                        if assoc_info["person_id"] == str(person.id):
                            person_evidence.append({
                                "id": str(evidence.id),
                                "evidence_number": evidence.evidence_number,
                                "description": evidence.description,
                                "item_type": evidence.item_type,
                                "analysis_status": evidence.analysis_status,
                                "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
                                "association_type": assoc_info["association_type"],
                                "confidence_level": assoc_info["confidence_level"],
                                "association_notes": assoc_info["notes"]
                            })
                            break
                
                # Fallback: check if person name is in evidence description (for backward compatibility)
                if not person_evidence or not any(e["id"] == str(evidence.id) for e in person_evidence):
                    if person.full_name.lower() in evidence.description.lower():
                        person_evidence.append({
                            "id": str(evidence.id),
                            "evidence_number": evidence.evidence_number,
                            "description": evidence.description,
                            "item_type": evidence.item_type,
                            "analysis_status": evidence.analysis_status,
                            "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
                            "association_type": "legacy",
                            "confidence_level": "medium",
                            "association_notes": "Legacy association based on description"
                        })
            
            persons_with_evidence.append({
                "id": str(person.id),
                "full_name": person.full_name,
                "person_type": person.person_type,
                "alias": person.alias,
                "description": person.description,
                "evidence": person_evidence
            })
        
        # Format case log (activities)
        case_log = []
        for activity in activities:
            user = db.query(User).filter(User.id == activity.user_id).first()
            case_log.append({
                "id": str(activity.id),
                "activity_type": activity.activity_type,
                "description": activity.description,
                "timestamp": activity.timestamp.isoformat(),
                "user_name": user.full_name if user else "Unknown",
                "user_role": user.role if user else "Unknown",
                "old_value": activity.old_value,
                "new_value": activity.new_value
            })
        
        # Format case notes
        formatted_notes = []
        for note in case_notes:
            if isinstance(note, dict):
                formatted_notes.append({
                    "content": note.get("content", ""),
                    "timestamp": note.get("timestamp", ""),
                    "status": note.get("status", "active")
                })
            else:
                formatted_notes.append({
                    "content": str(note),
                    "timestamp": case.updated_at.isoformat() if case.updated_at else case.created_at.isoformat(),
                    "status": "active"
                })
        
        return {
            "status": 200,
            "message": "Case detail retrieved successfully",
            "data": {
                "case": {
                    "id": str(case.id),
                    "case_number": case.case_number,
                    "title": case.title,
                    "description": case.description,
                    "status": case.status,
                    "priority": case.priority,
                    "case_type": case.case_type,
                    "jurisdiction": case.jurisdiction,
                    "work_unit": case.work_unit,
                    "case_officer": case.case_officer,
                    "created_at": case.created_at.isoformat() if case.created_at else None,
                    "updated_at": case.updated_at.isoformat() if case.updated_at else None,
                    "closed_at": case.closed_at.isoformat() if case.closed_at else None,
                    "evidence_count": case.evidence_count,
                    "analysis_progress": case.analysis_progress
                },
                "persons_of_interest": persons_with_evidence,
                "case_log": case_log,
                "notes": formatted_notes,
                "total_persons": len(persons),
                "total_evidence": len(evidence_items)
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to retrieve case detail",
                "error": str(e)
            }
        )


@router.put("/update-case/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    request: Request,
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
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to update case",
                "error": str(e)
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
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
            content={
                "status": 404,
                "message": "Person not found"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    if case.status == "closed":
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Case is already closed"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    if case.status != "closed":
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Only closed cases can be reopened"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    # Validate status transition
    valid_statuses = ["open", "closed", "reopened"]
    if status_request.status not in valid_statuses:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }
        )
    
    if case.status == status_request.status:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Case is already in the requested status"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
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
            content={
                "status": 404,
                "message": "Case not found"
            }
        )
    
    history = CaseActivityService.get_case_status_history(
        db=db,
        case_id=case_id,
        limit=limit,
        offset=offset
    )
    
    return history


@router.post("/{case_id}/notes")
def add_case_note(
    case_id: str,
    note_content: str = Query(..., description="Note content to add"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Add a note to a case"""
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
        
        # Parse existing notes
        import json
        existing_notes = []
        if case.notes:
            try:
                existing_notes = json.loads(case.notes) if isinstance(case.notes, str) else case.notes
            except:
                # If not JSON, treat as single note
                existing_notes = [{"content": case.notes, "timestamp": case.updated_at.isoformat() if case.updated_at else case.created_at.isoformat(), "status": "active"}]
        
        # Add new note
        new_note = {
            "content": note_content,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "added_by": current_user.full_name or current_user.username
        }
        existing_notes.append(new_note)
        
        # Update case notes
        case.notes = json.dumps(existing_notes)
        case.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Create activity log
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="note_added",
            description=f"Note added to case '{case.case_number}'",
            new_value={"note_content": note_content}
        )
        
        return {
            "status": 200,
            "message": "Note added successfully",
            "data": {
                "note": new_note,
                "total_notes": len(existing_notes)
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to add note",
                "error": str(e)
            }
        )


@router.get("/{case_id}/notes")
def get_case_notes(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get all notes for a case"""
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
        
        # Parse notes
        import json
        case_notes = []
        if case.notes:
            try:
                case_notes = json.loads(case.notes) if isinstance(case.notes, str) else case.notes
            except:
                # If not JSON, treat as single note
                case_notes = [{"content": case.notes, "timestamp": case.updated_at.isoformat() if case.updated_at else case.created_at.isoformat(), "status": "active"}]
        
        return {
            "status": 200,
            "message": "Case notes retrieved successfully",
            "data": {
                "notes": case_notes,
                "total_notes": len(case_notes)
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to retrieve notes",
                "error": str(e)
            }
        )


@router.delete("/{case_id}/notes/{note_index}")
def delete_case_note(
    case_id: str,
    note_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Delete a specific note from a case"""
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
        
        # Parse existing notes
        import json
        existing_notes = []
        if case.notes:
            try:
                existing_notes = json.loads(case.notes) if isinstance(case.notes, str) else case.notes
            except:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 400,
                        "message": "Invalid notes format"
                    }
                )
        
        # Check if note index is valid
        if note_index < 0 or note_index >= len(existing_notes):
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Invalid note index"
                }
            )
        
        # Remove note
        deleted_note = existing_notes.pop(note_index)
        
        # Update case notes
        case.notes = json.dumps(existing_notes) if existing_notes else None
        case.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Create activity log
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="note_deleted",
            description=f"Note deleted from case '{case.case_number}'",
            old_value={"note_content": deleted_note.get("content", "")}
        )
        
        return {
            "status": 200,
            "message": "Note deleted successfully",
            "data": {
                "deleted_note": deleted_note,
                "total_notes": len(existing_notes)
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to delete note",
                "error": str(e)
            }
        )


@router.post("/{case_id}/persons/{person_id}/evidence/{evidence_id}")
def associate_evidence_with_person(
    case_id: str,
    person_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Associate evidence with a person of interest"""
    try:
        case_uuid = parse_case_id(case_id)
        person_uuid = parse_case_id(person_id)
        evidence_uuid = parse_case_id(evidence_id)
        
        # Verify case exists
        case = db.query(Case).filter(Case.id == case_uuid).first()
        if not case:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Case not found"
                }
            )
        
        # Verify person exists and belongs to case
        person = db.query(CasePerson).filter(
            CasePerson.id == person_uuid,
            CasePerson.case_id == case_uuid
        ).first()
        if not person:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Person not found in this case"
                }
            )
        
        # Verify evidence exists and belongs to case
        from app.models.evidence import EvidenceItem
        evidence = db.query(EvidenceItem).filter(
            EvidenceItem.id == evidence_uuid,
            EvidenceItem.case_id == case_uuid
        ).first()
        if not evidence:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Evidence not found in this case"
                }
            )
        
        # Check if association already exists
        from app.models.case import EvidencePersonAssociation
        existing_association = db.query(EvidencePersonAssociation).filter(
            EvidencePersonAssociation.evidence_id == evidence_uuid,
            EvidencePersonAssociation.person_id == person_uuid
        ).first()
        
        if existing_association:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Evidence is already associated with this person"
                }
            )
        
        # Create new association
        association = EvidencePersonAssociation(
            evidence_id=evidence_uuid,
            person_id=person_uuid,
            association_type="related",
            confidence_level="medium",
            created_by=current_user.id
        )
        
        db.add(association)
        db.commit()
        
        # Create activity log
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="evidence_associated",
            description=f"Evidence {evidence.evidence_number} associated with person {person.full_name}",
            new_value={
                "evidence_id": str(evidence.id),
                "person_id": str(person.id),
                "person_name": person.full_name,
                "association_type": "related"
            }
        )
        
        return {
            "status": 200,
            "message": "Evidence associated with person successfully",
            "data": {
                "evidence": {
                    "id": str(evidence.id),
                    "evidence_number": evidence.evidence_number,
                    "description": evidence.description
                },
                "person": {
                    "id": str(person.id),
                    "full_name": person.full_name,
                    "person_type": person.person_type
                }
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to associate evidence with person",
                "error": str(e)
            }
        )


@router.get("/{case_id}/export/pdf")
def export_case_pdf(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Export case details as PDF (placeholder for future implementation)"""
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
        
        # For now, return a JSON response indicating PDF export is not yet implemented
        # In a real implementation, you would generate a PDF using libraries like reportlab or weasyprint
        return {
            "status": 200,
            "message": "PDF export functionality is not yet implemented",
            "data": {
                "case_id": str(case.id),
                "case_number": case.case_number,
                "title": case.title,
                "note": "PDF generation will be implemented in a future version"
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid case ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to export case PDF",
                "error": str(e)
            }
        )
