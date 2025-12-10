from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.api.deps import get_database, get_current_user
from app.auth.models import User
from app.case_management.service import case_service
from app.case_management.schemas import (
    Case, CaseCreate, CaseUpdate, CaseResponse, CaseListResponse,
    Agency, AgencyCreate, WorkUnit, WorkUnitCreate, CaseDetailResponse,
    CaseNotesRequest
)
from fastapi.responses import JSONResponse, FileResponse
import os
import logging

logger = logging.getLogger(__name__)
from app.core.config import settings
from app.utils.security import sanitize_input, validate_sql_injection_patterns

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.post("/create-case", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        case_dict_data = case_data.dict()
        
        if case_dict_data.get("case_number"):
            if not validate_sql_injection_patterns(case_dict_data["case_number"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in case_number. Please remove any SQL injection attempts or malicious code."
                )
            case_number_cleaned = sanitize_input(case_dict_data["case_number"], max_length=50)
            if case_number_cleaned and len(case_number_cleaned) > 50:
                raise HTTPException(
                    status_code=400,
                    detail="Case number must not exceed 50 characters"
                )
            case_dict_data["case_number"] = case_number_cleaned
        
        if case_dict_data.get("title"):
            if not validate_sql_injection_patterns(case_dict_data["title"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in title. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["title"] = sanitize_input(case_dict_data["title"], max_length=500)
        
        if case_dict_data.get("description"):
            if not validate_sql_injection_patterns(case_dict_data["description"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in description. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["description"] = sanitize_input(case_dict_data["description"])
        
        if case_dict_data.get("main_investigator"):
            if not validate_sql_injection_patterns(case_dict_data["main_investigator"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in main_investigator. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["main_investigator"] = sanitize_input(case_dict_data["main_investigator"], max_length=255)
        
        if case_dict_data.get("agency_name"):
            if not validate_sql_injection_patterns(case_dict_data["agency_name"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in agency_name. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["agency_name"] = sanitize_input(case_dict_data["agency_name"], max_length=255)
        
        if case_dict_data.get("work_unit_name"):
            if not validate_sql_injection_patterns(case_dict_data["work_unit_name"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in work_unit_name. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["work_unit_name"] = sanitize_input(case_dict_data["work_unit_name"], max_length=255)

        for key, value in case_dict_data.items():
            if hasattr(case_data, key):
                setattr(case_data, key, value)
        
        case_dict = case_service.create_case(db, case_data, current_user)
        if isinstance(case_dict.get("created_at"), datetime):
            case_dict["created_at"] = case_dict["created_at"].strftime("%d/%m/%Y")
        if isinstance(case_dict.get("updated_at"), datetime):
            case_dict["updated_at"] = case_dict["updated_at"].strftime("%d/%m/%Y")
        
        return CaseResponse(
            status=201,
            message="Case created successfully",
            data=case_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_case: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating case. Please try again later."
        )

@router.get("/get-case-detail-comprehensive/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail_comprehensive(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        case_data = case_service.get_case_detail_comprehensive(db, case_id, current_user)
        return CaseDetailResponse(
            status=200,
            message="Case detail retrieved successfully",
            data=case_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_case_detail_comprehensive: {str(e)}", exc_info=True)
        error_message = str(e).lower()
        if "not found" in error_message:
            raise HTTPException(
                status_code=404, 
                detail=f"Case with ID {case_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="An unexpected error occurred while retrieving case details. Please try again later."
            )

@router.get("/get-all-cases", response_model=CaseListResponse)
async def get_cases(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by. Valid values: 'created_at', 'id'"),
    sort_order: Optional[str] = Query(None, description="Sort order. Valid values: 'asc' (oldest first), 'desc' (newest first)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        # Validate all query parameters to prevent SQL injection via unknown parameters
        allowed_params = {'skip', 'limit', 'search', 'status', 'sort_by', 'sort_order'}
        for param_name, param_value in request.query_params.items():
            if param_name not in allowed_params:
                if param_value and not validate_sql_injection_patterns(param_value):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid request. Please check your parameters and try again."
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Parameter '{param_name}' is not supported. Please use only 'skip', 'limit', 'search', 'status', 'sort_by', or 'sort_order' parameters."
                )
        
        if search:
            if not validate_sql_injection_patterns(search):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in search parameter. Please use valid characters only."
                )
            search = sanitize_input(search, max_length=255)
        
        if status:
            if not validate_sql_injection_patterns(status):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in status parameter. Please use valid characters only."
                )
            status = sanitize_input(status, max_length=50)
        
        if sort_by:
            if not validate_sql_injection_patterns(sort_by):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in sort_by parameter. Please use valid characters only."
                )
            sort_by = sanitize_input(sort_by, max_length=50)
            if sort_by not in ['created_at', 'id']:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid sort_by value. Valid values are: 'created_at', 'id'"
                )
        
        if sort_order:
            if not validate_sql_injection_patterns(sort_order):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in sort_order parameter. Please use valid characters only."
                )
            sort_order = sanitize_input(sort_order, max_length=10)
            if sort_order.lower() not in ['asc', 'desc']:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid sort_order value. Valid values are: 'asc', 'desc'"
                )
        
        result = case_service.get_cases(db, skip, limit, search, status, sort_by, sort_order, current_user)
        return CaseListResponse(
            status=200,
            message="Cases retrieved successfully",
            data=result["cases"],
            total=result["total"],
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.put("/update-case/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        case_dict_data = case_data.dict(exclude_unset=True)
        
        if case_dict_data.get("case_number"):
            if not validate_sql_injection_patterns(case_dict_data["case_number"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in case_number. Please remove any SQL injection attempts or malicious code."
                )
            case_number_cleaned = sanitize_input(case_dict_data["case_number"], max_length=50)
            if case_number_cleaned and len(case_number_cleaned) > 50:
                raise HTTPException(
                    status_code=400,
                    detail="Case number must not exceed 50 characters"
                )
            case_dict_data["case_number"] = case_number_cleaned
        
        if case_dict_data.get("title"):
            if not validate_sql_injection_patterns(case_dict_data["title"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in title. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["title"] = sanitize_input(case_dict_data["title"], max_length=500)
        
        if case_dict_data.get("description"):
            if not validate_sql_injection_patterns(case_dict_data["description"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in description. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["description"] = sanitize_input(case_dict_data["description"])
        
        if case_dict_data.get("main_investigator"):
            if not validate_sql_injection_patterns(case_dict_data["main_investigator"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in main_investigator. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["main_investigator"] = sanitize_input(case_dict_data["main_investigator"], max_length=255)
        
        if case_dict_data.get("agency_name"):
            if not validate_sql_injection_patterns(case_dict_data["agency_name"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in agency_name. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["agency_name"] = sanitize_input(case_dict_data["agency_name"], max_length=255)
        
        if case_dict_data.get("work_unit_name"):
            if not validate_sql_injection_patterns(case_dict_data["work_unit_name"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in work_unit_name. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["work_unit_name"] = sanitize_input(case_dict_data["work_unit_name"], max_length=255)
        
        if case_dict_data.get("notes"):
            if not validate_sql_injection_patterns(case_dict_data["notes"]):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code."
                )
            case_dict_data["notes"] = sanitize_input(case_dict_data["notes"])
        
        for key, value in case_dict_data.items():
            if hasattr(case_data, key):
                setattr(case_data, key, value)
        
        case = case_service.update_case(db, case_id, case_data, current_user)
        return CaseResponse(
            status=200,
            message="Case updated successfully",
            data=case
            )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404, 
                detail=f"Case with ID {case_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Unexpected server error, please try again later"
            )

@router.get("/statistics/summary")
async def get_case_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        stats = case_service.get_case_statistics(db, current_user)
        return {
            "status": 200,
            "message": "Statistics retrieved successfully",
            "data": {
                "open_cases": stats["open_cases"],
                "closed_cases": stats["closed_cases"],
                "reopened_cases": stats["reopened_cases"]
            },
            "total_cases": stats["total_cases"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.post("/save-notes")
async def save_case_notes(
    request: CaseNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        if request.notes:
            if not validate_sql_injection_patterns(request.notes):
                return JSONResponse(
                    content={
                        "status": 400,
                        "message": "Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            request.notes = sanitize_input(request.notes)
        
        result = case_service.save_case_notes(db, request.case_id, request.notes, current_user)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Case notes saved successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        logger.error(f"Validation error in edit_case_notes: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "status": 400,
                "message": "Invalid input data. Please check your request and try again.",
                "data": None
            },
            status_code=400
        )
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Case with ID {request.case_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": "Failed to edit case notes. Please try again later.",
                    "data": None
                },
                status_code=500
            )

@router.put("/edit-notes")
async def edit_case_notes(
    request: CaseNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        if request.notes:
            if not validate_sql_injection_patterns(request.notes):
                return JSONResponse(
                    content={
                        "status": 400,
                        "message": "Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            request.notes = sanitize_input(request.notes)
        
        result = case_service.edit_case_notes(db, request.case_id, request.notes, current_user)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Case notes updated successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        logger.error(f"Validation error in edit_case_notes: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "status": 400,
                "message": "Invalid input data. Please check your request and try again.",
                "data": None
            },
            status_code=400
        )
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Case with ID {request.case_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": "Failed to edit case notes. Please try again later.",
                    "data": None
                },
                status_code=500
            )

@router.get("/export-case-details-pdf/{case_id}")
async def export_case_details_pdf(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        pdf_path = case_service.export_case_detail_pdf(db, case_id, settings.REPORTS_DIR, current_user)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PDF file"
            )

        filename = os.path.basename(pdf_path)
        
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting case detail PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export case detail PDF. Please try again later."
        )
