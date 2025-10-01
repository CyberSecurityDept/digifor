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


def parse_case_id(case_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(case_id)
    except ValueError:
        raise ValueError("Invalid case ID format")


@router.post("/{case_id}/persons/{person_id}/evidence/{evidence_id}", tags=["Case Evidence Management"])
def associate_evidence_with_person(
    case_id: str,
    person_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_safe)
):
    """Associate evidence with a person of interest"""
    try:
        case_uuid = parse_case_id(case_id)
        person_uuid = parse_case_id(person_id)
        evidence_uuid = parse_case_id(evidence_id)
        
        # Verify case exists
        case = db.query(Case).filter(Case.id == case_uuid).first()
        if not case:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Case not found"
                }
            )
        
        # Verify person exists and belongs to case
        person = db.query(CasePerson).filter(
            CasePerson.id == person_uuid,
            CasePerson.case_id == case_uuid
        ).first()
        if not person:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Person not found in this case"
                }
            )
        
        # Verify evidence exists and belongs to case
        from app.models.evidence import EvidenceItem
        evidence = db.query(EvidenceItem).filter(
            EvidenceItem.id == evidence_uuid,
            EvidenceItem.case_id == case_uuid
        ).first()
        if not evidence:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": "Evidence not found in this case"
                }
            )
        
        # Check if association already exists
        from app.models.case import EvidencePersonAssociation
        existing_association = db.query(EvidencePersonAssociation).filter(
            EvidencePersonAssociation.evidence_id == evidence_uuid,
            EvidencePersonAssociation.person_id == person_uuid
        ).first()
        
        if existing_association:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Evidence is already associated with this person"
                }
            )
        
        # Create new association
        association = EvidencePersonAssociation(
            evidence_id=evidence_uuid,
            person_id=person_uuid,
            association_type="related",
            confidence_level="medium",
            created_by=current_user.id
        )
        
        db.add(association)
        db.commit()
        
        # Create activity log
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=current_user.id,
            activity_type="evidence_associated",
            description=f"Evidence {evidence.evidence_number} associated with person {person.full_name}",
            new_value={
                "evidence_id": str(evidence.id),
                "person_id": str(person.id),
                "person_name": person.full_name,
                "association_type": "related"
            }
        )
        
        return {
            "status": 200,
            "message": "Evidence associated with person successfully",
            "data": {
                "evidence": {
                    "id": str(evidence.id),
                    "evidence_number": evidence.evidence_number,
                    "description": evidence.description
                },
                "person": {
                    "id": str(person.id),
                    "full_name": person.full_name,
                    "person_type": person.person_type
                }
            }
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": "Invalid ID format",
                "error": str(e)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "Failed to associate evidence with person",
                "error": str(e)
            }
        )
