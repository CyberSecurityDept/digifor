from typing import List, Optional
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
            "date_of_birth": suspect.date_of_birth,
            "place_of_birth": suspect.place_of_birth,
            "nationality": suspect.nationality,
            "phone_number": suspect.phone_number,
            "email": suspect.email,
            "address": suspect.address,
            "height": suspect.height,
            "weight": suspect.weight,
            "eye_color": suspect.eye_color,
            "hair_color": suspect.hair_color,
            "distinguishing_marks": suspect.distinguishing_marks,
            "has_criminal_record": suspect.has_criminal_record,
            "criminal_record_details": suspect.criminal_record_details,
            "risk_level": suspect.risk_level,
            "risk_assessment_notes": suspect.risk_assessment_notes,
            "is_confidential": suspect.is_confidential,
            "notes": suspect.notes,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at,
            "last_seen": suspect.last_seen
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
            "date_of_birth": suspect.date_of_birth,
            "place_of_birth": suspect.place_of_birth,
            "nationality": suspect.nationality,
            "phone_number": suspect.phone_number,
            "email": suspect.email,
            "address": suspect.address,
            "height": suspect.height,
            "weight": suspect.weight,
            "eye_color": suspect.eye_color,
            "hair_color": suspect.hair_color,
            "distinguishing_marks": suspect.distinguishing_marks,
            "has_criminal_record": suspect.has_criminal_record,
            "criminal_record_details": suspect.criminal_record_details,
            "risk_level": suspect.risk_level,
            "risk_assessment_notes": suspect.risk_assessment_notes,
            "is_confidential": suspect.is_confidential,
            "notes": suspect.notes,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at,
            "last_seen": suspect.last_seen
        }
    
    def get_suspects(self, db: Session, skip: int = 0, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
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
        
        suspects = query.offset(skip).limit(limit).all()
        
        result = []
        for suspect in suspects:
            suspect_dict = {
                "id": suspect.id,
                "name": suspect.name,
                "case_name": suspect.case_name,
                "investigator": suspect.investigator,
                "status": suspect.status,
                "date_of_birth": suspect.date_of_birth,
                "place_of_birth": suspect.place_of_birth,
                "nationality": suspect.nationality,
                "phone_number": suspect.phone_number,
                "email": suspect.email,
                "address": suspect.address,
                "height": suspect.height,
                "weight": suspect.weight,
                "eye_color": suspect.eye_color,
                "hair_color": suspect.hair_color,
                "distinguishing_marks": suspect.distinguishing_marks,
                "has_criminal_record": suspect.has_criminal_record,
                "criminal_record_details": suspect.criminal_record_details,
                "risk_level": suspect.risk_level,
                "risk_assessment_notes": suspect.risk_assessment_notes,
                "is_confidential": suspect.is_confidential,
                "notes": suspect.notes,
                "created_at": suspect.created_at,
                "updated_at": suspect.updated_at,
                "last_seen": suspect.last_seen
            }
            result.append(suspect_dict)
        
        return result
    
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
            "date_of_birth": suspect.date_of_birth,
            "place_of_birth": suspect.place_of_birth,
            "nationality": suspect.nationality,
            "phone_number": suspect.phone_number,
            "email": suspect.email,
            "address": suspect.address,
            "height": suspect.height,
            "weight": suspect.weight,
            "eye_color": suspect.eye_color,
            "hair_color": suspect.hair_color,
            "distinguishing_marks": suspect.distinguishing_marks,
            "has_criminal_record": suspect.has_criminal_record,
            "criminal_record_details": suspect.criminal_record_details,
            "risk_level": suspect.risk_level,
            "risk_assessment_notes": suspect.risk_assessment_notes,
            "is_confidential": suspect.is_confidential,
            "notes": suspect.notes,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at,
            "last_seen": suspect.last_seen
        }
    
    def delete_suspect(self, db: Session, suspect_id: int) -> bool:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return False
        
        db.delete(suspect)
        db.commit()
        return True

suspect_service = SuspectService()
