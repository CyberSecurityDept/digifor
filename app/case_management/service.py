from re import search
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.case_management.models import Case, Agency, WorkUnit, Person
from app.case_management.schemas import CaseCreate, CaseUpdate, PersonCreate, PersonUpdate


def get_or_create_agency(db: Session, name: str):
    agency = db.query(Agency).filter(Agency.name == name).first()
    if not agency:
        agency = Agency(name=name)
        db.add(agency)
        db.commit()
        db.refresh(agency)
    return agency


def get_or_create_work_unit(db: Session, name: str, agency: Agency):
    work_unit = db.query(WorkUnit).filter(WorkUnit.name == name, WorkUnit.agency_id == agency.id).first()
    if not work_unit:
        work_unit = WorkUnit(name=name, agency_id=agency.id)
        db.add(work_unit)
        db.commit()
        db.refresh(work_unit)
    return work_unit


class CaseService:
    
    def create_case(self, db: Session, case_data: CaseCreate) -> dict:
        case_dict = case_data.dict()
        
        agency = None
        agency_name = None
        if case_dict.get('agency_id'):
            agency = db.query(Agency).filter(Agency.id == case_dict['agency_id']).first()
            if not agency:
                raise Exception(f"Agency with ID {case_dict['agency_id']} not found")
            agency_name = agency.name
        elif case_dict.get('agency_name'):
            agency = get_or_create_agency(db, case_dict['agency_name'])
            case_dict['agency_id'] = agency.id
            agency_name = agency.name
        else:
            case_dict['agency_id'] = None
        
        work_unit = None
        work_unit_name = None
        if case_dict.get('work_unit_id'):
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case_dict['work_unit_id']).first()
            if not work_unit:
                raise Exception(f"Work unit with ID {case_dict['work_unit_id']} not found")
            work_unit_name = work_unit.name
        elif case_dict.get('work_unit_name'):
            if not agency:
                raise Exception("Agency must be specified when creating work unit")
            work_unit = get_or_create_work_unit(db, case_dict['work_unit_name'], agency)
            case_dict['work_unit_id'] = work_unit.id
            work_unit_name = work_unit.name
        else:
            case_dict['work_unit_id'] = None
        
        case_dict.pop('agency_name', None)
        case_dict.pop('work_unit_name', None)
        
        try:
            case = Case(**case_dict)
            db.add(case)
            db.commit()
            db.refresh(case)
        except Exception as e:
            db.rollback()
            if "duplicate key value violates unique constraint" in str(e) and "case_number" in str(e):
                # Create custom exception for duplicate case number with 409 status
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=409,
                    detail=f"Case number '{case_dict.get('case_number')}' already exists"
                )
            else:
                # Re-raise other exceptions as 500 server errors
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected server error, please try again later"
                )
        
        # Return case as dict with agency and work unit names
        case_response = {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "main_investigator": case.main_investigator,
            "agency_name": agency_name,
            "work_unit_name": work_unit_name,
            "created_at": case.created_at,
            "updated_at": case.updated_at
        }
        
        return case_response
    
    def get_case(self, db: Session, case_id: int) -> Case:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        # Get agency and work unit names
        agency_name = None
        work_unit_name = None
        
        if case.agency_id:
            agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
            if agency:
                agency_name = agency.name
        
        if case.work_unit_id:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
            if work_unit:
                work_unit_name = work_unit.name
        
        # Create case dict with additional fields
        case_dict = {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "main_investigator": case.main_investigator,
            "agency_name": agency_name,
            "work_unit_name": work_unit_name,
            "created_at": case.created_at,
            "updated_at": case.updated_at
        }
        
        return case_dict
    
    def get_cases(self, db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None) -> List[Case]:
        query = db.query(Case).join(Agency, Case.agency_id == Agency.id, isouter=True).join(WorkUnit, Case.work_unit_id == WorkUnit.id, isouter=True)

        status_mapping = {
            'open': 'Open',
            'OPEN': 'Open',
            'Open': 'Open',
            'closed': 'Closed', 
            'CLOSED': 'Closed',
            'Closed': 'Closed',
            're-open': 'Re-open',
            'RE-OPEN': 'Re-open',
            'Re-open': 'Re-open',
            'Re-Open': 'Re-open',
            'reopened': 'Re-open',
            'REOPENED': 'Re-open',
            'Reopened': 'Re-open'
        }

        if search:
            search_pattern = f"%{search}%"

            normalized_status = status_mapping.get(search, search)

            search_conditions = [
                    Case.title.ilike(search_pattern),
                    Case.main_investigator.ilike(search_pattern),
                    cast(Case.agency_id, String).ilike(search_pattern),
                Agency.name.ilike(search_pattern),
                    cast(Case.created_at, String).ilike(search_pattern),
                    cast(Case.updated_at, String).ilike(search_pattern),
                cast(Case.status, String).ilike(search_pattern)
            ]
            
            if normalized_status in ['Open', 'Closed', 'Re-open']:
                search_conditions.append(Case.status == normalized_status)

            query = query.filter(or_(*search_conditions))

        if status:
            normalized_status = status_mapping.get(status, status)
            query = query.filter(Case.status == normalized_status)

        cases = query.order_by(Case.id.desc()).offset(skip).limit(limit).all()
        
        # Convert cases to dict with agency and work unit names
        result = []
        for case in cases:
            agency_name = None
            work_unit_name = None
            
            if case.agency_id:
                agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
                if agency:
                    agency_name = agency.name
            
            if case.work_unit_id:
                work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
                if work_unit:
                    work_unit_name = work_unit.name
            
            case_dict = {
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "main_investigator": case.main_investigator,
                "agency_name": agency_name,
                "work_unit_name": work_unit_name,
                "created_at": case.created_at,
                "updated_at": case.updated_at
            }
            result.append(case_dict)
        
        return result


    
    def update_case(self, db: Session, case_id: int, case_data: CaseUpdate) -> dict:
        # Get the actual Case object from database
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        update_data = case_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)
        
        db.commit()
        db.refresh(case)
        
        # Get agency and work unit names for response
        agency_name = None
        work_unit_name = None
        
        if case.agency_id:
            agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
            if agency:
                agency_name = agency.name
        
        if case.work_unit_id:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
            if work_unit:
                work_unit_name = work_unit.name
        
        # Return updated case as dict with names
        case_dict = {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "main_investigator": case.main_investigator,
            "agency_name": agency_name,
            "work_unit_name": work_unit_name,
            "created_at": case.created_at,
            "updated_at": case.updated_at
        }
        
        return case_dict
    
    def delete_case(self, db: Session, case_id: int) -> bool:
        # Get the actual Case object from database
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        db.delete(case)
        db.commit()
        return True
    
    def get_case_statistics(self, db: Session) -> dict:
        total_cases = db.query(Case).count()
        open_cases = db.query(Case).filter(Case.status == "Open").count()
        closed_cases = db.query(Case).filter(Case.status == "Closed").count()
        reopened_cases = db.query(Case).filter(Case.status == "Re-open").count()
        
        return {
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "reopened_cases": reopened_cases,
            "total_cases": total_cases
        }


class CaseLogService:
    def create_log(self, db: Session, log_data: dict) -> dict:
        from app.case_management.models import CaseLog
        
        log = CaseLog(**log_data)
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return {
            "id": log.id,
            "case_id": log.case_id,
            "action": log.action,
            "description": log.description,
            "changed_by": log.changed_by,
            "created_at": log.created_at
        }
    
    def get_case_logs(self, db: Session, case_id: int, skip: int = 0, limit: int = 10) -> List[dict]:
        from app.case_management.models import CaseLog
        
        logs = db.query(CaseLog).filter(CaseLog.case_id == case_id)\
            .order_by(CaseLog.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "case_id": log.case_id,
                "action": log.action,
                "description": log.description,
                "changed_by": log.changed_by,
                "created_at": log.created_at
            }
            result.append(log_dict)
        
        return result
    
    def get_log_count(self, db: Session, case_id: int) -> int:
        from app.case_management.models import CaseLog
        return db.query(CaseLog).filter(CaseLog.case_id == case_id).count()


class CaseNoteService:
    def create_note(self, db: Session, note_data: dict) -> dict:
        from app.case_management.models import CaseNote
        
        note = CaseNote(**note_data)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        return {
            "id": note.id,
            "case_id": note.case_id,
            "note": note.note,
            "status": note.status,
            "created_by": note.created_by,
            "created_at": note.created_at
        }
    
    def get_case_notes(self, db: Session, case_id: int, skip: int = 0, limit: int = 10) -> List[dict]:
        from app.case_management.models import CaseNote
        
        notes = db.query(CaseNote).filter(CaseNote.case_id == case_id)\
            .order_by(CaseNote.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for note in notes:
            note_dict = {
                "id": note.id,
                "case_id": note.case_id,
                "note": note.note,
                "status": note.status,
                "created_by": note.created_by,
                "created_at": note.created_at
            }
            result.append(note_dict)
        
        return result
    
    def get_note_count(self, db: Session, case_id: int) -> int:
        from app.case_management.models import CaseNote
        return db.query(CaseNote).filter(CaseNote.case_id == case_id).count()
    
    def update_note(self, db: Session, note_id: int, note_data: dict) -> dict:
        from app.case_management.models import CaseNote
        
        note = db.query(CaseNote).filter(CaseNote.id == note_id).first()
        if not note:
            raise Exception(f"Note with ID {note_id} not found")
        
        update_data = {k: v for k, v in note_data.items() if v is not None}
        for field, value in update_data.items():
            setattr(note, field, value)
        
        db.commit()
        db.refresh(note)
        
        return {
            "id": note.id,
            "case_id": note.case_id,
            "note": note.note,
            "status": note.status,
            "created_by": note.created_by,
            "created_at": note.created_at
        }
    
    def delete_note(self, db: Session, note_id: int) -> bool:
        from app.case_management.models import CaseNote
        
        note = db.query(CaseNote).filter(CaseNote.id == note_id).first()
        if not note:
            return False
        
        db.delete(note)
        db.commit()
        return True


class PersonService:
    def create_person(self, db: Session, person_data: PersonCreate) -> dict:
        person_dict = person_data.dict()
        
        try:
            person = Person(**person_dict)
            db.add(person)
            db.commit()
            db.refresh(person)
        except Exception as e:
            db.rollback()
            from fastapi import HTTPException
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )
        
        return {
            "id": person.id,
            "name": person.name,
            "is_unknown": person.is_unknown,
            "custody_stage": person.custody_stage,
            "evidence_id": person.evidence_id,
            "evidence_source": person.evidence_source,
            "evidence_summary": person.evidence_summary,
            "investigator": person.investigator,
            "case_id": person.case_id,
            "created_by": person.created_by,
            "created_at": person.created_at,
            "updated_at": person.updated_at
        }
    
    def get_person(self, db: Session, person_id: int) -> dict:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise Exception(f"Person with ID {person_id} not found")
        
        return {
            "id": person.id,
            "name": person.name,
            "is_unknown": person.is_unknown,
            "custody_stage": person.custody_stage,
            "evidence_id": person.evidence_id,
            "evidence_source": person.evidence_source,
            "evidence_summary": person.evidence_summary,
            "investigator": person.investigator,
            "case_id": person.case_id,
            "created_by": person.created_by,
            "created_at": person.created_at,
            "updated_at": person.updated_at
        }
    
    def get_persons_by_case(self, db: Session, case_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        persons = db.query(Person).filter(Person.case_id == case_id)\
            .order_by(Person.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for person in persons:
            person_dict = {
                "id": person.id,
                "name": person.name,
                "is_unknown": person.is_unknown,
                "custody_stage": person.custody_stage,
                "evidence_id": person.evidence_id,
                "evidence_source": person.evidence_source,
                "evidence_summary": person.evidence_summary,
                "investigator": person.investigator,
                "case_id": person.case_id,
                "created_by": person.created_by,
                "created_at": person.created_at,
                "updated_at": person.updated_at
            }
            result.append(person_dict)
        
        return result
    
    def get_person_count_by_case(self, db: Session, case_id: int) -> int:
        return db.query(Person).filter(Person.case_id == case_id).count()
    
    def update_person(self, db: Session, person_id: int, person_data: PersonUpdate) -> dict:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise Exception(f"Person with ID {person_id} not found")
        
        update_data = person_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        db.commit()
        db.refresh(person)
        
        return {
            "id": person.id,
            "name": person.name,
            "is_unknown": person.is_unknown,
            "custody_stage": person.custody_stage,
            "evidence_id": person.evidence_id,
            "evidence_source": person.evidence_source,
            "evidence_summary": person.evidence_summary,
            "investigator": person.investigator,
            "case_id": person.case_id,
            "created_by": person.created_by,
            "created_at": person.created_at,
            "updated_at": person.updated_at
        }
    
    def delete_person(self, db: Session, person_id: int) -> bool:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            return False
        
        db.delete(person)
        db.commit()
        return True


case_service = CaseService()
case_log_service = CaseLogService()
case_note_service = CaseNoteService()
person_service = PersonService()
