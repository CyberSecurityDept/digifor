from re import search
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.case_management.models import Case, CasePerson, Agency, WorkUnit
from app.case_management.schemas import CaseCreate, CaseUpdate, CasePersonCreate, CasePersonUpdate


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
    
    def create_case(self, db: Session, case_data: CaseCreate) -> Case:
        case_dict = case_data.dict()
        
        agency = None
        if case_dict.get('agency_id'):
            agency = db.query(Agency).filter(Agency.id == case_dict['agency_id']).first()
            if not agency:
                raise Exception(f"Agency with ID {case_dict['agency_id']} not found")
        elif case_dict.get('agency_name'):
            agency = get_or_create_agency(db, case_dict['agency_name'])
            case_dict['agency_id'] = agency.id
        else:
            case_dict['agency_id'] = None
        
        if case_dict.get('work_unit_id'):
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case_dict['work_unit_id']).first()
            if not work_unit:
                raise Exception(f"Work unit with ID {case_dict['work_unit_id']} not found")
        elif case_dict.get('work_unit_name'):
            if not agency:
                raise Exception("Agency must be specified when creating work unit")
            work_unit = get_or_create_work_unit(db, case_dict['work_unit_name'], agency)
            case_dict['work_unit_id'] = work_unit.id
        else:
            case_dict['work_unit_id'] = None
        
        case_dict.pop('agency_name', None)
        case_dict.pop('work_unit_name', None)
        
        case = Case(**case_dict)
        db.add(case)
        db.commit()
        db.refresh(case)
        return case
    
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


    
    def update_case(self, db: Session, case_id: int, case_data: CaseUpdate) -> Case:
        case = self.get_case(db, case_id)
        update_data = case_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)
        db.commit()
        db.refresh(case)
        return case
    
    def delete_case(self, db: Session, case_id: int) -> bool:
        case = self.get_case(db, case_id)
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


class CasePersonService:
    
    def add_person_to_case(self, db: Session, case_id: int, person_data: CasePersonCreate) -> CasePerson:
        case_person = CasePerson(**person_data.dict(), case_id=case_id)
        db.add(case_person)
        db.commit()
        db.refresh(case_person)
        return case_person
    
    def get_case_persons(self, db: Session, case_id: int) -> List[CasePerson]:
        return db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
    
    def update_case_person(self, db: Session, case_person_id: int, person_data: CasePersonUpdate) -> CasePerson:
        case_person = db.query(CasePerson).filter(CasePerson.id == case_person_id).first()
        if not case_person:
            raise Exception(f"Case-Person association with ID {case_person_id} not found")
        update_data = person_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case_person, field, value)
        db.commit()
        db.refresh(case_person)
        return case_person
    
    def remove_person_from_case(self, db: Session, case_person_id: int) -> bool:
        case_person = db.query(CasePerson).filter(CasePerson.id == case_person_id).first()
        if not case_person:
            return False
        db.delete(case_person)
        db.commit()
        return True


case_service = CaseService()
case_person_service = CasePersonService()
