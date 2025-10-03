from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api.deps import get_database
from app.suspect_management.models import Person
from app.case_management.models import Case, CasePerson
from app.evidence_management.models import Evidence
from app.suspect_management.schemas import PersonCreate, PersonUpdate, PersonResponse, PersonListResponse

router = APIRouter(prefix="/suspects", tags=["Suspect Management"])


@router.get("/")
async def get_suspects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    is_primary_suspect: Optional[bool] = Query(None),
    has_criminal_record: Optional[bool] = Query(None),
    person_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    
    query = db.query(Person)
    
    if search:
        search_filter = or_(
            Person.full_name.ilike(f"%{search}%"),
            Person.alias.ilike(f"%{search}%"),
            Person.phone_number.ilike(f"%{search}%"),
            Person.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if status:
        query = query.filter(Person.status == status)
    
    if risk_level:
        query = query.filter(Person.risk_level == risk_level)
    
    if is_primary_suspect is not None:
        query = query.filter(Person.is_primary_suspect == is_primary_suspect)
    
    if has_criminal_record is not None:
        query = query.filter(Person.has_criminal_record == has_criminal_record)
    
    total = query.count()

    suspects = query.offset(skip).limit(limit).all()
    
    result_data = []
    for suspect in suspects:
        case_person = db.query(CasePerson).filter(CasePerson.person_id == suspect.id).first()
        case_info = None
        if case_person:
            case = db.query(Case).filter(Case.id == case_person.case_id).first()
            if case:
                case_info = {
                    "case_id": str(case.id),
                    "case_name": case.title,
                    "case_number": case.case_number,
                    "investigator": case.case_officer,
                    "person_type": case_person.person_type,
                    "is_primary": case_person.is_primary
                }
        
        evidence_count = 0
        if case_person:
            evidence_count = db.query(Evidence).filter(Evidence.case_id == case_person.case_id).count()
        
        suspect_data = {
            "id": str(suspect.id),
            "full_name": suspect.full_name,
            "alias": suspect.alias,
            "status": suspect.status,
            "risk_level": suspect.risk_level,
            "is_primary_suspect": suspect.is_primary_suspect,
            "has_criminal_record": suspect.has_criminal_record,
            "phone_number": suspect.phone_number,
            "email": suspect.email,
            "created_at": suspect.created_at,
            "last_seen": suspect.last_seen,
            "case_info": case_info,
            "evidence_count": evidence_count
        }
        result_data.append(suspect_data)
    
    return {
        "status": 200,
        "message": "Suspects retrieved successfully",
        "data": result_data,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }


@router.post("/create-suspect")
async def create_suspect(
    suspect_data: PersonCreate,
    db: Session = Depends(get_database)
):
    try:
        person = Person(**suspect_data.dict())
        db.add(person)
        db.commit()
        db.refresh(person)
        
        return {
            "status": 201,
            "message": "Suspect created successfully",
            "data": {
                "id": str(person.id),
                "full_name": person.full_name,
                "status": person.status,
                "created_at": person.created_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create suspect: {str(e)}")


@router.get("/get-suspect-by-id/{person_id}")
async def get_suspect(
    person_id: UUID,
    db: Session = Depends(get_database)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Suspect not found")

    case_persons = db.query(CasePerson).filter(CasePerson.person_id == person_id).all()
    case_info = []
    for cp in case_persons:
        case = db.query(Case).filter(Case.id == cp.case_id).first()
        if case:
            case_info.append({
                "case_id": str(case.id),
                "case_name": case.title,
                "case_number": case.case_number,
                "investigator": case.case_officer,
                "person_type": cp.person_type,
                "is_primary": cp.is_primary,
                "case_status": case.status,
                "created_at": cp.created_at
            })

    evidence_info = []
    for cp in case_persons:
        evidence_items = db.query(Evidence).filter(Evidence.case_id == cp.case_id).all()
        for evidence in evidence_items:
            evidence_info.append({
                "id": str(evidence.id),
                "evidence_number": evidence.evidence_number,
                "description": evidence.description,
                "evidence_type": evidence.evidence_type,
                "status": evidence.status,
                "created_at": evidence.created_at
            })
    
    return {
        "status": 200,
        "message": "Suspect retrieved successfully",
        "data": {
            "id": str(person.id),
            "full_name": person.full_name,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "alias": person.alias,
            "gender": person.gender,
            "date_of_birth": person.date_of_birth,
            "phone_number": person.phone_number,
            "email": person.email,
            "address": person.address,
            "status": person.status,
            "risk_level": person.risk_level,
            "is_primary_suspect": person.is_primary_suspect,
            "has_criminal_record": person.has_criminal_record,
            "criminal_record_details": person.criminal_record_details,
            "risk_assessment_notes": person.risk_assessment_notes,
            "notes": person.notes,
            "created_at": person.created_at,
            "updated_at": person.updated_at,
            "last_seen": person.last_seen,
            "case_info": case_info,
            "evidence_info": evidence_info
        }
    }


@router.put("/update-suspect{person_id}")
async def update_suspect(
    person_id: UUID,
    suspect_data: PersonUpdate,
    db: Session = Depends(get_database)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    try:
        update_data = suspect_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        person.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(person)
        
        return {
            "status": 200,
            "message": "Suspect updated successfully",
            "data": {
                "id": str(person.id),
                "full_name": person.full_name,
                "status": person.status,
                "updated_at": person.updated_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update suspect: {str(e)}")


@router.put("/{person_id}/status")
async def update_suspect_status(
    person_id: UUID,
    status_data: dict,
    db: Session = Depends(get_database)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    try:
        person.status = status_data.get("status", person.status)
        person.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": 200,
            "message": "Suspect status updated successfully",
            "data": {
                "id": str(person.id),
                "status": person.status,
                "updated_at": person.updated_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update status: {str(e)}")


@router.get("/{person_id}/evidence")
async def get_suspect_evidence(
    person_id: UUID,
    db: Session = Depends(get_database)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    case_persons = db.query(CasePerson).filter(CasePerson.person_id == person_id).all()
    evidence_data = []
    
    for cp in case_persons:
        evidence_items = db.query(Evidence).filter(Evidence.case_id == cp.case_id).all()
        for evidence in evidence_items:
            evidence_data.append({
                "id": str(evidence.id),
                "evidence_number": evidence.evidence_number,
                "description": evidence.description,
                "evidence_type": evidence.evidence_type,
                "status": evidence.status,
                "analysis_status": evidence.analysis_status,
                "created_at": evidence.created_at,
                "file_path": evidence.file_path,
                "file_size": evidence.file_size,
                "hash_value": evidence.hash_value
            })
    
    return {
        "status": 200,
        "message": "Evidence retrieved successfully",
        "data": evidence_data,
        "total": len(evidence_data)
    }


@router.post("/{person_id}/export-pdf")
async def export_suspect_pdf(
    person_id: UUID,
    db: Session = Depends(get_database)
):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Suspect not found")

    return {
        "status": 200,
        "message": "PDF export initiated",
        "data": {
            "export_id": f"export_{person_id}",
            "status": "processing",
            "download_url": f"/api/v1/suspects/{person_id}/download-pdf"
        }
    }


@router.get("/stats/summary")
async def get_suspect_stats(
    db: Session = Depends(get_database)
):
    try:
        total_persons = db.query(Person).count()
        total_evidence = db.query(Evidence).count()

        status_counts = db.query(Person.status, func.count(Person.id)).group_by(Person.status).all()
        status_stats = {status: count for status, count in status_counts}

        risk_counts = db.query(Person.risk_level, func.count(Person.id)).group_by(Person.risk_level).all()
        risk_stats = {risk: count for risk, count in risk_counts}
        
        return {
            "status": 200,
            "message": "Statistics retrieved successfully",
            "data": {
                "total_persons": total_persons,
                "total_evidence": total_evidence,
                "status_breakdown": status_stats,
                "risk_breakdown": risk_stats
            }
        }
    except Exception as e:
        return {
            "status": 500,
            "message": f"Error retrieving statistics: {str(e)}",
            "data": {
                "total_persons": 0,
                "total_evidence": 0,
                "status_breakdown": {},
                "risk_breakdown": {}
            }
    }
