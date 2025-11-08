from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_database
from app.case_management.service import case_log_service
from app.case_management.schemas import (
    CaseLogUpdate, CaseLogResponse, CaseLogListResponse
)

router = APIRouter(prefix="/case-logs", tags=["Case Log Management"])

@router.put("/change-log/{case_id}", response_model=CaseLogResponse)
async def update_case_log(
    case_id: int,
    log_data: CaseLogUpdate,
    db: Session = Depends(get_database)
):
    try:
        log = case_log_service.update_case_log(db, case_id, log_data.dict())
        return CaseLogResponse(
            status=200,
            message="Case log updated successfully",
            data=log
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )

@router.get("/case/logs/{case_id}", response_model=CaseLogListResponse)
async def get_case_logs(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database)
):
    try:
        logs = case_log_service.get_case_logs(db, case_id, skip, limit)
        total = case_log_service.get_log_count(db, case_id)
        
        return CaseLogListResponse(
            status=200,
            message="Case logs retrieved successfully",
            data=logs,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )
