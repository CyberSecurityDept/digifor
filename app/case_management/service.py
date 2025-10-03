from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

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
        
        # Handle agency logic
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
    
    def get_case(self, db: Session, case_id: UUID) -> Case:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        return case
    
    def get_cases(self, db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None) -> List[Case]:
        query = db.query(Case)
        if search:
            query = query.filter(Case.title.ilike(f"%{search}%"))
        if status:
            query = query.filter(Case.status == status)
        return query.offset(skip).limit(limit).all()
    
    def update_case(self, db: Session, case_id: UUID, case_data: CaseUpdate) -> Case:
        case = self.get_case(db, case_id)
        update_data = case_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)
        db.commit()
        db.refresh(case)
        return case
    
    def delete_case(self, db: Session, case_id: UUID) -> bool:
        case = self.get_case(db, case_id)
        db.delete(case)
        db.commit()
        return True
    
    def get_case_statistics(self, db: Session) -> dict:
        from app.case_management.models import CaseStatus
        
        total_cases = db.query(Case).count()
        open_cases = db.query(Case).filter(Case.status == CaseStatus.OPEN).count()
        closed_cases = db.query(Case).filter(Case.status == CaseStatus.CLOSED).count()
        reopened_cases = db.query(Case).filter(Case.status == CaseStatus.REOPENED).count()
        
        return {
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "reopened_cases": reopened_cases,
            "total_cases": total_cases
        }


class CasePersonService:
    
    def add_person_to_case(self, db: Session, case_id: UUID, person_data: CasePersonCreate) -> CasePerson:
        case_person = CasePerson(**person_data.dict(), case_id=case_id)
        db.add(case_person)
        db.commit()
        db.refresh(case_person)
        return case_person
    
    def get_case_persons(self, db: Session, case_id: UUID) -> List[CasePerson]:
        return db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
    
    def update_case_person(self, db: Session, case_person_id: UUID, person_data: CasePersonUpdate) -> CasePerson:
        case_person = db.query(CasePerson).filter(CasePerson.id == case_person_id).first()
        if not case_person:
            raise Exception(f"Case-Person association with ID {case_person_id} not found")
        update_data = person_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case_person, field, value)
        db.commit()
        db.refresh(case_person)
        return case_person
    
    def remove_person_from_case(self, db: Session, case_person_id: UUID) -> bool:
        case_person = db.query(CasePerson).filter(CasePerson.id == case_person_id).first()
        if not case_person:
            return False
        db.delete(case_person)
        db.commit()
        return True


# Create service instances
case_service = CaseService()
case_person_service = CasePersonService()
