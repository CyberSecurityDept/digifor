from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_database
from app.case_management.service import case_note_service
from app.case_management.schemas import (
    CaseNoteCreate, CaseNoteResponse, CaseNoteListResponse
)

router = APIRouter(prefix="/case-notes", tags=["Case Note Management"])


@router.post("/create-note", response_model=CaseNoteResponse)
async def create_note(
    note_data: CaseNoteCreate,
    db: Session = Depends(get_database)
):
    try:
        note = case_note_service.create_note(db, note_data.dict())
        return CaseNoteResponse(
            status=201,
            message="Case note created successfully",
            data=note
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )


@router.get("/case/{case_id}/notes", response_model=CaseNoteListResponse)
async def get_case_notes(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database)
):
    try:
        notes = case_note_service.get_case_notes(db, case_id, skip, limit)
        total = case_note_service.get_note_count(db, case_id)
        
        return CaseNoteListResponse(
            status=200,
            message="Case notes retrieved successfully",
            data=notes,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )


@router.put("/update-note/{note_id}", response_model=CaseNoteResponse)
async def update_note(
    note_id: int,
    note_data: dict,
    db: Session = Depends(get_database)
):
    try:
        note = case_note_service.update_note(db, note_id, note_data)
        return CaseNoteResponse(
            status=200,
            message="Case note updated successfully",
            data=note
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Note with ID {note_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )


@router.delete("/delete-note/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_database)
):
    try:
        success = case_note_service.delete_note(db, note_id)
        if success:
            return {"status": 200, "message": "Case note deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Note with ID {note_id} not found"
            )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Note with ID {note_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )
