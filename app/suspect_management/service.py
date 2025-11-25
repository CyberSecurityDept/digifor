from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.suspect_management.models import Suspect
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate
from app.case_management.models import Case, Agency
import logging

logger = logging.getLogger(__name__)

class SuspectService:
    def _format_datetime(self, dt_value):
        if dt_value is None:
            return None
        try:
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            else:
                return str(dt_value)
        except (AttributeError, TypeError):
            return None
    
    def create_suspect(self, db: Session, suspect_data: SuspectCreate) -> dict:
        suspect_data_dict = suspect_data.dict()
        valid_fields = {
            'name', 'case_name', 'investigator', 'status', 'case_id', 
            'is_unknown', 'evidence_number', 'evidence_source', 'created_by'
        }
        filtered_dict = {k: v for k, v in suspect_data_dict.items() if k in valid_fields}
        suspect = Suspect(**filtered_dict)
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
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": self._format_datetime(suspect.created_at),
            "updated_at": self._format_datetime(suspect.updated_at)
        }
    
    def get_suspect(self, db: Session, suspect_id: int, current_user=None) -> dict:
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
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": self._format_datetime(suspect.created_at),
            "updated_at": self._format_datetime(suspect.updated_at)
        }
    
    def get_suspects(
        self, db: Session, skip: int = 0, limit: int = 10,
        search: Optional[str] = None, status: Optional[List[str]] = None,
        current_user=None
    ) -> Tuple[List[dict], int]:
        logger.info(f"get_suspects called with skip={skip}, limit={limit}, search={search}, status={status}")

        query = db.query(Suspect)
        
        total_before = query.count()
        logger.info(f"Total suspects before filtering: {total_before}")

        if status:
            if isinstance(status, list):
                if len(status) == 1 and isinstance(status[0], str) and "," in status[0]:
                    status = status[0].split(",")
            elif isinstance(status, str):
                status = status.split(",")

            status = [s.strip() for s in status if s and s.strip()]

            if len(status) > 0:
                query = query.filter(Suspect.status.in_(status))

        if search and search.strip():
            search_filter = or_(
                Suspect.name.ilike(f"%{search.strip()}%"),
                Suspect.case_name.ilike(f"%{search.strip()}%"),
                Suspect.investigator.ilike(f"%{search.strip()}%")
            )
            query = query.filter(search_filter)


        query = query.order_by(Suspect.id.desc())

        total = query.count()
        logger.info(f"Total suspects after filtering: {total}")

        suspects = query.offset(skip).limit(limit).all()
        logger.debug(f"Retrieved {len(suspects)} suspects (skip={skip}, limit={limit})")

        result = []
        for suspect in suspects:
            created_at_str = suspect.created_at.isoformat() if getattr(suspect, 'created_at', None) else None
            updated_at_str = suspect.updated_at.isoformat() if getattr(suspect, 'updated_at', None) else None

            agency_name = None
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case:
                agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
                if agency:
                    agency_name = agency.name

            result.append({
                "id": suspect.id,
                "case_id": suspect.case_id,
                "person_name": suspect.name,
                "case_name": suspect.case_name,
                "investigator": suspect.investigator,
                "agency": agency_name,
                "status": suspect.status,
                "created_at": created_at_str,
                "updated_at": updated_at_str
            })

        return result, total


    
    def update_suspect(self, db: Session, suspect_id: int, suspect_data: SuspectUpdate, current_user=None) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise Exception(f"Suspect with ID {suspect_id} not found")
        
        if current_user is not None:
            user_role = getattr(current_user, 'role', None)
            if user_role != "admin":
                case = db.query(Case).filter(Case.id == suspect.case_id).first()
                if case:
                    user_fullname = getattr(current_user, 'fullname', '') or ''
                    user_email = getattr(current_user, 'email', '') or ''
                    main_investigator = case.main_investigator or ''
                    if not (user_fullname.lower() in main_investigator.lower() or user_email.lower() in main_investigator.lower()):
                        raise Exception("You do not have permission to update this suspect")
        
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
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "created_by": suspect.created_by,
            "case_id": suspect.case_id,
            "created_at": self._format_datetime(suspect.created_at),
            "updated_at": self._format_datetime(suspect.updated_at)
        }

    def delete_suspect(self, db: Session, suspect_id: int, current_user=None) -> bool:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return False
        
        if current_user is not None:
            user_role = getattr(current_user, 'role', None)
            if user_role != "admin":
                case = db.query(Case).filter(Case.id == suspect.case_id).first()
                if case:
                    user_fullname = getattr(current_user, 'fullname', '') or ''
                    user_email = getattr(current_user, 'email', '') or ''
                    main_investigator = case.main_investigator or ''
                    if not (user_fullname.lower() in main_investigator.lower() or user_email.lower() in main_investigator.lower()):
                        raise Exception("You do not have permission to delete this suspect")
        
        db.delete(suspect)
        db.commit()
        return True
    

suspect_service = SuspectService()
