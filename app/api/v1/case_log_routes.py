from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_database
from app.case_management.service import case_log_service
from app.case_management.schemas import (
    CaseLogUpdate, CaseLogResponse, CaseLogListResponse
)
import logging

router = APIRouter(prefix="/case-logs", tags=["Case Log Management"])

@router.put("/change-log/{case_id}")
async def update_case_log(
    case_id: int,
    log_data: CaseLogUpdate,
    db: Session = Depends(get_database)
):
    try:
        log = case_log_service.update_case_log(db, case_id, log_data.dict())
        cleaned_log = {k: v for k, v in log.items() if v is not None}
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Case log updated successfully",
                "data": cleaned_log
            }
        )
    except HTTPException:
        raise
    except Exception as e:

        logger = logging.getLogger(__name__)
        logger.error(f"Error updating case log: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.get("/case/logs/{case_id}")
async def get_case_logs(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database)
):
    try:
        logs = case_log_service.get_case_logs(db, case_id, skip, limit)
        total = case_log_service.get_log_count(db, case_id)
        
        cleaned_logs = []
        for log in logs:
            cleaned_log = {k: v for k, v in log.items() if v is not None}
            cleaned_logs.append(cleaned_log)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Case logs retrieved successfully",
                "data": cleaned_logs,
                "total": total,
                "page": skip // limit + 1,
                "size": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )

@router.get("/log/{log_id}", response_model=CaseLogResponse)
async def get_case_log_detail(
    log_id: int,
    db: Session = Depends(get_database)
):
    logger = logging.getLogger(__name__)
    logger.info(f"Getting case log detail for log_id: {log_id}")
    try:
        log = case_log_service.get_case_log_detail(db, log_id)
        logger.info(f"Successfully retrieved case log detail for log_id: {log_id}")
        
        cleaned_log = {k: v for k, v in log.items() if v is not None}
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Case log detail retrieved successfully",
                "data": cleaned_log
            }
        )
    except HTTPException as e:
        logger.warning(f"HTTPException for log_id {log_id}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error getting case log detail for log_id {log_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )
