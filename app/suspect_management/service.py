from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.suspect_management.models import Suspect
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate
from app.case_management.models import Case, Agency

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
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def get_suspects(self, db: Session, skip: int = 0, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[dict], int]:
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
        
        query = query.order_by(Suspect.id.desc())
        total = query.count()
        suspects = query.offset(skip).limit(limit).all()
        result = []
        for suspect in suspects:
            created_at_str = None
            updated_at_str = None
            try:
                created_at_value = getattr(suspect, 'created_at', None)
                if created_at_value is not None:
                    created_at_str = created_at_value.isoformat() if hasattr(created_at_value, 'isoformat') else str(created_at_value)
            except (AttributeError, TypeError):
                pass
            try:
                updated_at_value = getattr(suspect, 'updated_at', None)
                if updated_at_value is not None:
                    updated_at_str = updated_at_value.isoformat() if hasattr(updated_at_value, 'isoformat') else str(updated_at_value)
            except (AttributeError, TypeError):
                pass
            
            agency_name = None
            case_id_value = getattr(suspect, 'case_id', None)
            if case_id_value is not None:
                case = db.query(Case).filter(Case.id == case_id_value).first()
                if case:
                    agency_id_value = getattr(case, 'agency_id', None)
                    if agency_id_value is not None:
                        agency = db.query(Agency).filter(Agency.id == agency_id_value).first()
                        if agency:
                            agency_name = getattr(agency, 'name', None)
            
            suspect_dict = {
                "id": suspect.id,
                "case_id": suspect.case_id,
                "person_name": suspect.name,
                "case_name": suspect.case_name,
                "investigator": suspect.investigator,
                "agency": agency_name,
                "status": suspect.status,
                "created_at": created_at_str,
                "updated_at": updated_at_str
            }
            result.append(suspect_dict)
        return result, total
    
    def update_suspect(self, db: Session, suspect_id: int, suspect_data: SuspectUpdate) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise Exception(f"Suspect with ID {suspect_id} not found")
        
        current_is_unknown = getattr(suspect, 'is_unknown', False)
        update_data = suspect_data.dict(exclude_unset=True)
        
        if not current_is_unknown:
            if 'name' in update_data:
                if not update_data['name'] or not str(update_data['name']).strip():
                    raise Exception("name is required when is_unknown is false")
            if 'status' in update_data:
                if not update_data['status'] or not str(update_data['status']).strip():
                    raise Exception("status is required when is_unknown is false")
        
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
