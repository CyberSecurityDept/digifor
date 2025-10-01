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


@router.get("/overview", tags=["Case List Management"])
def get_case_management_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get dashboard statistics for case management cards"""
    
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


@router.get("/get-all-cases/", response_model=CaseListResponse, tags=["Case List Management"])
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
    """Retrieve paginated list of cases with filtering options"""
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


@router.get("/search", tags=["Case List Management"])
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
    """Search cases with advanced filtering"""
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


@router.get("/filter-options", tags=["Case List Management"])
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


@router.get("/form-options", tags=["Case List Management"])
def get_form_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Get dropdown options for case creation form"""
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
