from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_database
from app.suspect_management.service import suspect_service
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate, SuspectResponse, SuspectListResponse

router = APIRouter(prefix="/suspects", tags=["Suspect Management"])

@router.get("/", response_model=SuspectListResponse)
async def get_suspects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        suspects = suspect_service.get_suspects(db, skip, limit, search, status)
        total = len(suspects)
        
        return SuspectListResponse(
            status=200,
            message="Suspects retrieved successfully",
            data=suspects,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )

@router.post("/create-suspect", response_model=SuspectResponse)
async def create_suspect(
    suspect_data: SuspectCreate,
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.create_suspect(db, suspect_data)
        return SuspectResponse(
            status=201,
            message="Suspect created successfully",
            data=suspect
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )

@router.get("/get-suspect-by-id/{suspect_id}", response_model=SuspectResponse)
async def get_suspect(
    suspect_id: int,
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.get_suspect(db, suspect_id)
        return SuspectResponse(
            status=200,
            message="Suspect retrieved successfully",
            data=suspect
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )

@router.put("/update-suspect/{suspect_id}", response_model=SuspectResponse)
async def update_suspect(
    suspect_id: int,
    suspect_data: SuspectUpdate,
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.update_suspect(db, suspect_id, suspect_data)
        return SuspectResponse(
            status=200,
            message="Suspect updated successfully",
            data=suspect
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )

@router.delete("/delete-suspect/{suspect_id}")
async def delete_suspect(
    suspect_id: int,
    db: Session = Depends(get_database)
):
    try:
        success = suspect_service.delete_suspect(db, suspect_id)
        if success:
            return {"status": 200, "message": "Suspect deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )