from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_database
from app.case_management.service import case_service
from app.case_management.schemas import (
    Case, CaseCreate, CaseUpdate, CaseResponse, CaseListResponse,
    Agency, AgencyCreate, WorkUnit, WorkUnitCreate, CaseDetailResponse,
    CaseSummaryRequest
)
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.post("/create-case", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_database)
):
    try:
        case = case_service.create_case(db, case_data)
        return CaseResponse(
            status=201,
            message="Case created successfully",
            data=case
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.get("/get-case-detail-comprehensive/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail_comprehensive(
    case_id: int,
    db: Session = Depends(get_database)
):
    try:
        case_data = case_service.get_case_detail_comprehensive(db, case_id)
        return CaseDetailResponse(
            status=200,
            message="Case detail retrieved successfully",
            data=case_data
        )
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            raise HTTPException(
                status_code=404, 
                detail=f"Case with ID {case_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Unexpected server error, please try again later"
            )

@router.get("/get-all-cases", response_model=CaseListResponse)
async def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by. Valid values: 'created_at', 'id'"),
    sort_order: Optional[str] = Query(None, description="Sort order. Valid values: 'asc' (oldest first), 'desc' (newest first)"),
    db: Session = Depends(get_database)
):
    try:
        result = case_service.get_cases(db, skip, limit, search, status, sort_by, sort_order)
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
    db: Session = Depends(get_database)
):
    try:
        case = case_service.update_case(db, case_id, case_data)
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
    db: Session = Depends(get_database)
):
    try:
        stats = case_service.get_case_statistics(db)
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

@router.post("/save-summary")
async def save_case_summary(
    request: CaseSummaryRequest,
    db: Session = Depends(get_database)
):
    try:
        result = case_service.save_case_summary(db, request.case_id, request.summary)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Case summary saved successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": 400,
                "message": str(e),
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
                    "message": f"Failed to save case summary: {str(e)}",
                    "data": None
                },
                status_code=500
            )

@router.put("/edit-summary")
async def edit_case_summary(
    request: CaseSummaryRequest,
    db: Session = Depends(get_database)
):
    try:
        result = case_service.edit_case_summary(db, request.case_id, request.summary)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Case summary updated successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": 400,
                "message": str(e),
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
                    "message": f"Failed to edit case summary: {str(e)}",
                    "data": None
                },
                status_code=500
            )
