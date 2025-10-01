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


@router.post("/create-cases/", response_model=CaseCreateResponse, tags=["Case Detail Management"])
def create_case(
    case_form: CaseCreateForm,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Create a new case with auto-generated or manual case number"""
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
        
        # Convert case object to dictionary for JSON serialization
        case_dict = {
            "id": str(db_case.id),
            "case_number": db_case.case_number,
            "title": db_case.title,
            "description": db_case.description,
            "case_type": db_case.case_type,
            "status": db_case.status,
            "priority": db_case.priority,
            "jurisdiction": db_case.jurisdiction,
            "work_unit": db_case.work_unit,
            "case_officer": db_case.case_officer,
            "is_confidential": db_case.is_confidential,
            "created_at": db_case.created_at.isoformat() if db_case.created_at else None,
            "updated_at": db_case.updated_at.isoformat() if db_case.updated_at else None
        }
        
        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Case created successfully",
                "data": case_dict
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Case creation failed: {str(e)}"}
        )


@router.get("/case-by-id", response_model=CaseResponse, tags=["Case Detail Management"])
def get_case(
    case_id: str = Query(..., description="Case ID to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get basic case information by case ID"""
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


@router.get("/{case_id}/detail", tags=["Case Detail Management"])
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


@router.put("/update-case/{case_id}", response_model=CaseResponse, tags=["Case Detail Management"])
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Update case information"""
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


@router.delete("/delete-case/", tags=["Case Detail Management"])
def delete_case_by_query(
    case_id: str = Query(..., description="Case ID to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Soft delete (archive) a case"""
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


@router.get("/{case_id}/stats", tags=["Case Detail Management"])
def get_case_stats(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get case statistics"""
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


@router.get("/{case_id}/export/pdf", tags=["Case Detail Management"])
def export_case_pdf(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Export case details as PDF (placeholder implementation)"""
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
