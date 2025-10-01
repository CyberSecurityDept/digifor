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


@router.get("/{case_id}/activities", response_model=List[CaseActivity], tags=["Case Log & Notes Management"])
def get_case_activities(
    case_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get case activity log (case log)"""
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


@router.get("/{case_id}/activities/recent", response_model=List[CaseActivitySummary], tags=["Case Log & Notes Management"])
def get_recent_case_activities(
    case_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get recent case activities with user information"""
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


@router.get("/{case_id}/status-history", response_model=List[CaseStatusHistory], tags=["Case Log & Notes Management"])
def get_case_status_history(
    case_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get case status change history"""
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


@router.post("/{case_id}/notes", tags=["Case Log & Notes Management"])
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


@router.get("/{case_id}/notes", tags=["Case Log & Notes Management"])
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


@router.delete("/{case_id}/notes/{note_index}", tags=["Case Log & Notes Management"])
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


@router.post("/{case_id}/close", response_model=CaseResponse, tags=["Case Log & Notes Management"])
def close_case(
    case_id: str,
    close_request: CaseCloseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Close a case with reason and notes"""
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


@router.post("/{case_id}/reopen", response_model=CaseResponse, tags=["Case Log & Notes Management"])
def reopen_case(
    case_id: str,
    reopen_request: CaseReopenRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Reopen a closed case"""
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


@router.post("/{case_id}/change-status", response_model=CaseResponse, tags=["Case Log & Notes Management"])
def change_case_status(
    case_id: str,
    status_request: CaseStatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Change case status with reason and notes"""
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
