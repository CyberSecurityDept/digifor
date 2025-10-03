from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_database
from app.case_management.service import case_service, case_person_service
from app.case_management.schemas import (
    Case, CaseCreate, CaseUpdate, CaseResponse, CaseListResponse,
    CasePerson, CasePersonCreate, CasePersonUpdate,
    Agency, AgencyCreate, WorkUnit, WorkUnitCreate
)

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
        # Re-raise HTTPException as-is (already has correct status code)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )


@router.get("/get-case-by-id/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_database)
):
    try:
        case = case_service.get_case(db, case_id)
        return CaseResponse(
            status=200,
            message="Case retrieved successfully",
            data=case
        )
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Case with ID {case_id} not found"
        )


@router.get("/get-all-cases", response_model=CaseListResponse)
async def get_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        cases = case_service.get_cases(db, skip, limit, search, status)
        return CaseListResponse(
            status=200,
            message="Cases retrieved successfully",
            data=cases,
            total=len(cases),
            page=skip // limit + 1,
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


@router.delete("/delete-case/{case_id}")
async def delete_case(
    case_id: int,
    db: Session = Depends(get_database)
):
    try:
        success = case_service.delete_case(db, case_id)
        if success:
            return {"status": 200, "message": "Case deleted successfully"}
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Case with ID {case_id} not found"
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
