from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.case_management.models import Case, Agency, WorkUnit, Person, CaseLog, CaseNote
from app.case_management.schemas import CaseCreate, CaseUpdate, PersonCreate, PersonUpdate
from datetime import datetime
from fastapi import HTTPException


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
        
        if not case_dict.get("status"):
            case_dict["status"] = "Open"
        
        agency = None
        agency_name = None
        agency_id = case_dict.get("agency_id")

        if agency_id and agency_id > 0:
            agency = db.query(Agency).filter(Agency.id == agency_id).first()
            if not agency:
                raise Exception(f"Agency with ID {agency_id} not found")
            agency_name = agency.name
        elif case_dict.get("agency_name"):
            agency = get_or_create_agency(db, case_dict["agency_name"])
            case_dict["agency_id"] = agency.id
            agency_name = agency.name
        else:
            case_dict["agency_id"] = None
        
        # 🔹 Handle work unit
        work_unit = None
        work_unit_name = None
        work_unit_id = case_dict.get("work_unit_id")

        if work_unit_id and work_unit_id > 0:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == work_unit_id).first()
            if not work_unit:
                raise Exception(f"Work unit with ID {work_unit_id} not found")
            work_unit_name = work_unit.name
        elif case_dict.get("work_unit_name"):
            if not agency:
                raise Exception("Agency must be specified when creating work unit")
            work_unit = get_or_create_work_unit(db, case_dict["work_unit_name"], agency)
            case_dict["work_unit_id"] = work_unit.id
            work_unit_name = work_unit.name
        else:
            case_dict["work_unit_id"] = None

        # Hapus field tambahan
        case_dict.pop("agency_name", None)
        case_dict.pop("work_unit_name", None)

        manual_case_number = case_dict.get("case_number")
        if manual_case_number and manual_case_number.strip():
            # Cek duplikat
            existing_case = db.query(Case).filter(Case.case_number == manual_case_number.strip()).first()
            if existing_case:
                raise HTTPException(status_code=409, detail=f"Case number '{manual_case_number}' already exists")
            case_dict["case_number"] = manual_case_number.strip()
        else:
            # 🔥 Auto-generate sebelum insert
            title = case_dict["title"].strip().upper()
            words = title.split()
            first_three = words[:3]
            initials = "".join([w[0] for w in first_three])
            date_part = datetime.now().strftime("%d%m%y")

            # Hitung total case di hari yang sama (buat urutan 0001, 0002, dst)
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_count = db.query(Case).filter(
                cast(Case.created_at, String).like(f"%{today_str}%")
            ).count() + 1

            case_number = f"{initials}-{date_part}-{str(today_count).zfill(4)}"
            case_dict["case_number"] = case_number
        
        try:
            case = Case(**case_dict)
            db.add(case)
            db.commit()
            db.refresh(case)

        except Exception as e:
            db.rollback()
            print("🔥 ERROR CREATE CASE:", str(e))
            if "duplicate key value" in str(e) and "case_number" in str(e):
                raise HTTPException(status_code=409, detail=f"Case number '{case_dict.get('case_number')}' already exists")
            raise HTTPException(status_code=500, detail="Unexpected server error, please try again later")
        
        # Create initial case log entry for "Open" status
        try:
            initial_log = CaseLog(
                case_id=case.id,
                action="Open",
                changed_by=case.main_investigator,
                change_detail="Case created and opened",
                notes="Initial case creation",
                status="Open"
            )
            db.add(initial_log)
            db.commit()
        except Exception as e:
            print(f"Warning: Could not create initial case log: {str(e)}")
            # Don't fail the case creation if log creation fails

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
            "updated_at": case.updated_at,
        }
        
        return case_response
    
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
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        update_data = case_data.dict(exclude_unset=True)
        
        if 'case_number' in update_data:
            manual_case_number = update_data['case_number']
            if manual_case_number and manual_case_number.strip():

                existing_case = db.query(Case).filter(
                    Case.case_number == manual_case_number.strip(),
                    Case.id != case_id
                ).first()
                if existing_case:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=409, 
                        detail=f"Case number '{manual_case_number}' already exists"
                    )
                update_data['case_number'] = manual_case_number.strip()
            else:
                title = update_data.get('title', case.title).strip().upper()
                words = title.split()
                first_three_words = words[:3]
                initials = ''.join([w[0] for w in first_three_words])
                date_part = datetime.now().strftime("%d%m%y")
                case_id_str = str(case.id).zfill(4)
                update_data['case_number'] = f"{initials}-{date_part}-{case_id_str}"
        
        old_status = case.status
        old_title = case.title
        
        for field, value in update_data.items():
            setattr(case, field, value)
        
        db.commit()
        db.refresh(case)
        
        try:
            changes = []
            if 'title' in update_data and update_data['title'] != old_title:
                changes.append(f"Title changed from '{old_title}' to '{update_data['title']}'")
            if 'status' in update_data and update_data['status'] != old_status:
                changes.append(f"Status changed from '{old_status}' to '{update_data['status']}'")
            if 'description' in update_data:
                changes.append("Description updated")
            if 'main_investigator' in update_data:
                changes.append("Main investigator updated")
            if 'case_number' in update_data:
                changes.append("Case number updated")
            
            if changes:
                change_detail = "; ".join(changes)
                update_log = CaseLog(
                    case_id=case.id,
                    action="Edit",
                    changed_by=case.main_investigator,
                    change_detail=change_detail,
                    notes="Case updated",
                    status=case.status
                )
                db.add(update_log)
                db.commit()
        except Exception as e:
            print(f"Warning: Could not create update case log: {str(e)}")

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
        
        return case_dict
    
    def delete_case(self, db: Session, case_id: int) -> bool:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        try:
            db.query(CaseLog).filter(CaseLog.case_id == case_id).delete()
            
            db.query(CaseNote).filter(CaseNote.case_id == case_id).delete()
            
            db.query(Person).filter(Person.case_id == case_id).delete()
            
            db.delete(case)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to delete case: {str(e)}")
    
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
    
    def get_case_detail_comprehensive(self, db: Session, case_id: int) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
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
        
        created_date = case.created_at.strftime("%d/%m/%Y")
        
        persons = db.query(Person).filter(Person.case_id == case_id).all()
        persons_of_interest = []
        
        for person in persons:
            analysis_items = []
            if person.evidence_id and person.evidence_summary:
                summaries = person.evidence_summary.split('\n') if '\n' in person.evidence_summary else [person.evidence_summary]
                for summary in summaries:
                    if summary.strip():
                        analysis_item = {
                            "evidence_id": person.evidence_id,
                            "summary": summary.strip(),
                            "status": "Analysis"
                        }
                        analysis_items.append(analysis_item)
            
            person_data = {
                "id": person.id,
                "name": person.name,
                "person_type": "Suspect",
                "analysis": analysis_items
            }
            persons_of_interest.append(person_data)
        
        logs = db.query(CaseLog).filter(CaseLog.case_id == case_id)\
            .order_by(CaseLog.created_at.desc()).all()
        
        case_log = []
        for log in logs:
            timestamp = log.created_at.strftime("%d %b %Y, %H:%M")
            
            log_data = {
                "status": log.action,
                "timestamp": timestamp,
                "description": log.change_detail if log.change_detail else log.action,
                "notes": log.notes,
                "case_status": case.status
            }
            case_log.append(log_data)
        
        notes = db.query(CaseNote).filter(CaseNote.case_id == case_id)\
            .order_by(CaseNote.created_at.desc()).all()
        
        case_notes = []
        for note in notes:
            timestamp = note.created_at.strftime("%d %b %Y, %H:%M")
            
            note_data = {
                "timestamp": timestamp,
                "status": note.status or "Active",
                "content": note.note
            }
            case_notes.append(note_data)
        
        evidence_count = len([p for p in persons if p.evidence_id])
        
        case_data = {
            "case": {
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "status": case.status,
                "case_officer": case.main_investigator,
                "created_date": created_date,
                "agency": agency_name or "Unknown",
                "work_unit": work_unit_name,
                "description": case.description or "No description available"
            },
            "persons_of_interest": persons_of_interest,
            "case_log": case_log,
            "notes": case_notes,
            "summary": {
                "total_persons": len(persons),
                "total_evidence": evidence_count
            }
        }
        
        return case_data


class CaseLogService:
    def create_log(self, db: Session, log_data: dict) -> dict:
        case = db.query(Case).filter(Case.id == log_data['case_id']).first()
        case_status = case.status if case else None
        
        log = CaseLog(**log_data)
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return {
            "id": log.id,
            "case_id": log.case_id,
            "action": log.action,
            "changed_by": log.changed_by,
            "change_detail": log.change_detail,
            "notes": log.notes,
            "status": log.status,  # Use log.status instead of case_status
            "created_at": log.created_at
        }
    
    def get_case_logs(self, db: Session, case_id: int, skip: int = 0, limit: int = 10) -> List[dict]:
        case = db.query(Case).filter(Case.id == case_id).first()
        case_status = case.status if case else None
        
        logs = db.query(CaseLog).filter(CaseLog.case_id == case_id)\
            .order_by(CaseLog.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "case_id": log.case_id,
                "action": log.action,
                "changed_by": log.changed_by,
                "change_detail": log.change_detail,
                "notes": log.notes,
                "status": log.status,  # Use log.status instead of case_status
                "created_at": log.created_at
            }
            result.append(log_dict)
        
        return result
    
    def get_log_count(self, db: Session, case_id: int) -> int:
        return db.query(CaseLog).filter(CaseLog.case_id == case_id).count()


class CaseNoteService:
    def create_note(self, db: Session, note_data: dict) -> dict:
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
        return db.query(CaseNote).filter(CaseNote.case_id == case_id).count()
    
    def update_note(self, db: Session, note_id: int, note_data: dict) -> dict:
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
