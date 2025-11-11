from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.suspect_management.models import Suspect
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate


class SuspectService:
    def create_suspect(self, db: Session, suspect_data: SuspectCreate) -> dict:
        suspect = Suspect(**suspect_data.dict())
        db.add(suspect)
        db.commit()
        db.refresh(suspect)
        
        return {
            "id": suspect.id,
            "name": suspect.name,
            "case_name": suspect.case_name,
            "investigator": suspect.investigator,
            "status": suspect.status,
            "is_unknown": suspect.is_unknown,
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def get_suspect(self, db: Session, suspect_id: int) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise Exception(f"Suspect with ID {suspect_id} not found")
        
        return {
            "id": suspect.id,
            "name": suspect.name,
            "case_name": suspect.case_name,
            "investigator": suspect.investigator,
            "status": suspect.status,
            "is_unknown": suspect.is_unknown,
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def get_suspects(self, db: Session, skip: int = 0, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = None) -> Tuple[List[dict], int]:
        query = db.query(Suspect)
        if search:
            search_filter = or_(
                Suspect.name.ilike(f"%{search}%"),
                Suspect.case_name.ilike(f"%{search}%"),
                Suspect.investigator.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        if status:
            query = query.filter(Suspect.status == status)
        if sort_by == "created_at":
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(Suspect.created_at.asc())
            else:
                query = query.order_by(Suspect.created_at.desc())
        else:
            query = query.order_by(Suspect.id.desc())
        total = query.count()
        suspects = query.offset(skip).limit(limit).all()
        result = []
        for suspect in suspects:
            suspect_dict = {
                "id": suspect.id,
                "name": suspect.name,
                "case_name": suspect.case_name,
                "investigator": suspect.investigator,
                "status": suspect.status,
                "is_unknown": suspect.is_unknown,
                "evidence_id": suspect.evidence_id,
                "evidence_source": suspect.evidence_source,
                "evidence_summary": suspect.evidence_summary,
                "created_by": suspect.created_by,
                "case_id": suspect.case_id,
                "created_at": suspect.created_at,
                "updated_at": suspect.updated_at
            }
            result.append(suspect_dict)
        return result, total
    
    def update_suspect(self, db: Session, suspect_id: int, suspect_data: SuspectUpdate) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise Exception(f"Suspect with ID {suspect_id} not found")
        update_data = suspect_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(suspect, field, value)
        db.commit()
        db.refresh(suspect)
        return {
            "id": suspect.id,
            "name": suspect.name,
            "case_name": suspect.case_name,
            "investigator": suspect.investigator,
            "status": suspect.status,
            "is_unknown": suspect.is_unknown,
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }

    def delete_suspect(self, db: Session, suspect_id: int) -> bool:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return False
        
        db.delete(suspect)
        db.commit()
        return True
    

suspect_service = SuspectService()
