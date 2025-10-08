from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_database
from app.case_management.service import person_service
from app.case_management.schemas import (
    Person, PersonCreate, PersonUpdate, PersonResponse, PersonListResponse
)

router = APIRouter(prefix="/persons", tags=["Person Management"])


@router.post("/create-person", response_model=PersonResponse)
async def create_person(
    person_data: PersonCreate,
    db: Session = Depends(get_database)
):
    try:
        person = person_service.create_person(db, person_data)
        return PersonResponse(
            status=201,
            message="Person created successfully",
            data=person
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )


@router.get("/get-person/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    db: Session = Depends(get_database)
):
    try:
        person = person_service.get_person(db, person_id)
        return PersonResponse(
            status=200,
            message="Person retrieved successfully",
            data=person
        )
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Person with ID {person_id} not found"
        )


@router.get("/get-persons-by-case/{case_id}", response_model=PersonListResponse)
async def get_persons_by_case(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database)
):
    try:
        persons = person_service.get_persons_by_case(db, case_id, skip, limit)
        total = person_service.get_person_count_by_case(db, case_id)
        return PersonListResponse(
            status=200,
            message="Persons retrieved successfully",
            data=persons,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )


@router.put("/update-person/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    person_data: PersonUpdate,
    db: Session = Depends(get_database)
):
    try:
        person = person_service.update_person(db, person_id, person_data)
        return PersonResponse(
            status=200,
            message="Person updated successfully",
            data=person
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404, 
                detail=f"Person with ID {person_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Unexpected server error, please try again later"
            )


@router.delete("/delete-person/{person_id}")
async def delete_person(
    person_id: int,
    db: Session = Depends(get_database)
):
    try:
        success = person_service.delete_person(db, person_id)
        if success:
            return {"status": 200, "message": "Person deleted successfully"}
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Person with ID {person_id} not found"
            )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404, 
                detail=f"Person with ID {person_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Unexpected server error, please try again later"
            )
