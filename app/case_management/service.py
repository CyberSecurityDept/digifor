from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.case_management.models import Case, Agency, WorkUnit, Person, CaseLog, WIB
from app.case_management.schemas import CaseCreate, CaseUpdate, PersonCreate, PersonUpdate
from datetime import datetime
from fastapi import HTTPException

def get_wib_now():
    return datetime.now(WIB)

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

        case_dict.pop("agency_name", None)
        case_dict.pop("work_unit_name", None)
        case_dict.pop("summary", None)  # Remove summary from case_dict if present (summary is managed separately)

        manual_case_number = case_dict.get("case_number")
        if manual_case_number and manual_case_number.strip():
            
            existing_case = db.query(Case).filter(Case.case_number == manual_case_number.strip()).first()
            if existing_case:
                raise HTTPException(status_code=409, detail=f"Case number '{manual_case_number}' already exists")
            case_dict["case_number"] = manual_case_number.strip()
        else:
            title = case_dict["title"].strip().upper()
            words = title.split()
            first_three = words[:3]
            initials = "".join([w[0] for w in first_three])
            date_part = get_wib_now().strftime("%d%m%y")
            today_str = get_wib_now().strftime("%Y-%m-%d")
            today_count = db.query(Case).filter(
                cast(Case.created_at, String).like(f"%{today_str}%")
            ).count() + 1

            case_number = f"{initials}-{date_part}-{str(today_count).zfill(4)}"
            case_dict["case_number"] = case_number
        
        try:
            # Remove any fields that don't exist in Case model to avoid errors
            # Note: summary is managed separately via save-summary endpoint, not during case creation
            valid_case_fields = {
                'case_number', 'title', 'description', 'status', 'main_investigator',
                'agency_id', 'work_unit_id', 'created_at', 'updated_at'
            }
            filtered_case_dict = {k: v for k, v in case_dict.items() if k in valid_case_fields}
            
            case = Case(**filtered_case_dict)
            db.add(case)
            db.commit()
            db.refresh(case)
        except Exception as e:
            db.rollback()
            import traceback
            error_details = traceback.format_exc()
            print("ERROR CREATE CASE:", str(e))
            print("ERROR DETAILS:", error_details)
            if "duplicate key value" in str(e) and "case_number" in str(e):
                raise HTTPException(status_code=409, detail=f"Case number '{case_dict.get('case_number')}' already exists")
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                raise HTTPException(
                    status_code=500, 
                    detail=f"Database schema error: {str(e)}. Please run database migration to add the 'summary' column."
                )
            # Log full error for debugging
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Error creating case: {str(e)}")
            logger.error(f"Error details: {error_details}")
            raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")
        
        try:
            initial_log = CaseLog(
                case_id=case.id,
                action="Open",
                changed_by="",
                change_detail="",
                notes="",
                status="Open"
            )
            db.add(initial_log)
            db.commit()
        except Exception as e:
            print(f"Warning: Could not create initial case log: {str(e)}")
            
        created_at_value = getattr(case, 'created_at', None)
        updated_at_value = getattr(case, 'updated_at', None)
        
        if created_at_value:
            if isinstance(created_at_value, datetime):
                date_created = created_at_value.strftime("%d/%m/%Y")
            else:
                date_created = str(created_at_value)
        else:
            date_created = get_wib_now().strftime("%d/%m/%Y")
        
        if updated_at_value:
            if isinstance(updated_at_value, datetime):
                date_updated = updated_at_value.strftime("%d/%m/%Y")
            else:
                date_updated = str(updated_at_value)
        else:
            date_updated = get_wib_now().strftime("%d/%m/%Y")
        
        case_response = {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "main_investigator": case.main_investigator,
            "agency_name": agency_name,
            "work_unit_name": work_unit_name,
            "created_at": date_created,
            "updated_at": date_updated,
        }
        
        assert isinstance(case_response["created_at"], str), f"created_at must be string, got {type(case_response['created_at'])}"
        assert isinstance(case_response["updated_at"], str), f"updated_at must be string, got {type(case_response['updated_at'])}"
        
        return case_response
    
    def get_cases(self, db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = None) -> dict:
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
            'Reopened': 'Re-open',
            'reopen': 'Re-open',
            'REOPEN': 'Re-open',
            'Reopen': 'Re-open'
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

        total_count = query.count()
        
        if sort_by == "created_at":
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(Case.created_at.asc())
            else:
                query = query.order_by(Case.created_at.desc())
        else:

            query = query.order_by(Case.id.desc())
        
        cases = query.offset(skip).limit(limit).all()
        
        result = []
        for case in cases:
            agency_name = None
            work_unit_name = None
            
            if case.agency_id is not None:
                agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
                if agency:
                    agency_name = agency.name
            
            if case.work_unit_id is not None:
                work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
                if work_unit:
                    work_unit_name = work_unit.name
            
            date_created = case.created_at.strftime("%d/%m/%Y")
            date_updated = case.updated_at.strftime("%d/%m/%Y")
            
            case_dict = {
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "main_investigator": case.main_investigator,
                "agency_name": agency_name,
                "work_unit_name": work_unit_name,
                "created_at": date_created,
                "updated_at": date_updated
            }
            result.append(case_dict)
        
        return {
            "cases": result,
            "total": total_count
        }
    
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
                date_part = get_wib_now().strftime("%d%m%y")
                case_id_str = str(case.id).zfill(4)
                update_data['case_number'] = f"{initials}-{date_part}-{case_id_str}"
        
        old_status = case.status
        old_title = case.title
        
        for field, value in update_data.items():
            setattr(case, field, value)
        
        db.commit()
        db.refresh(case)

        agency_name = None
        work_unit_name = None
        
        if case.agency_id is not None:
            agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
            if agency:
                agency_name = agency.name
        
        if case.work_unit_id is not None:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
            if work_unit:
                work_unit_name = work_unit.name

        date_created = case.created_at.strftime("%d/%m/%Y")
        date_updated = case.updated_at.strftime("%d/%m/%Y")
        
        case_dict = {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "main_investigator": case.main_investigator,
            "agency_name": agency_name,
            "work_unit_name": work_unit_name,
            "created_at": date_created,
            "updated_at": date_updated
        }
        
        return case_dict
    
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
    
    def save_case_notes(self, db: Session, case_id: int, notes: str) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        if not notes or not notes.strip():
            raise ValueError("Notes cannot be empty")
        
        setattr(case, 'notes', notes.strip())
        db.commit()
        db.refresh(case)
        
        updated_at_value = getattr(case, 'updated_at', None)
        updated_at_str = updated_at_value.isoformat() if updated_at_value is not None else None
        
        return {
            "case_id": case.id,
            "case_number": case.case_number,
            "case_title": case.title,
            "notes": getattr(case, 'notes', None),
            "updated_at": updated_at_str
        }
    
    def edit_case_notes(self, db: Session, case_id: int, notes: str) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        if not notes or not notes.strip():
            raise ValueError("Notes cannot be empty")
        
        setattr(case, 'notes', notes.strip())
        db.commit()
        db.refresh(case)
        
        updated_at_value = getattr(case, 'updated_at', None)
        updated_at_str = updated_at_value.isoformat() if updated_at_value is not None else None
        
        return {
            "case_id": case.id,
            "case_number": case.case_number,
            "case_title": case.title,
            "notes": getattr(case, 'notes', None),
            "updated_at": updated_at_str
        }
    
    def get_case_detail_comprehensive(self, db: Session, case_id: int) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case with ID {case_id} not found")
        
        agency_name = None
        work_unit_name = None
        
        if case.agency_id is not None:
            agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
            if agency:
                agency_name = agency.name
        
        if case.work_unit_id is not None:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
            if work_unit:
                work_unit_name = work_unit.name
        
        created_date = case.created_at.strftime("%d/%m/%Y")
        
        persons = db.query(Person).filter(Person.case_id == case_id).all()
        persons_of_interest = []
        
        for person in persons:
            analysis_items = []
            if person.evidence_id is not None and person.evidence_summary is not None:
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
        current_case_status = case.status  # Get current case status
        
        for log in logs:
            # Format created_at to "8 November 2025, 19:23"
            created_at_value = getattr(log, 'created_at', None)
            if created_at_value:
                if isinstance(created_at_value, datetime):
                    # Get day without leading zero
                    day = created_at_value.day
                    # Format: "8 November 2025, 19:23"
                    formatted_date = f"{day} {created_at_value.strftime('%B %Y, %H:%M')}"
                else:
                    formatted_date = str(created_at_value)
            else:
                formatted_date = None
            
            # Get log action and status
            log_action = getattr(log, 'action', '')
            log_status = getattr(log, 'status', '')
            
            # Only populate changed_by and change_detail if:
            # 1. action is "Edit" AND
            # 2. status matches current case status (status terakhir)
            if log_action == "Edit" and log_status == current_case_status:
                # Get changed_by and change_detail from log
                changed_by = getattr(log, 'changed_by', '') or ''
                change_detail = getattr(log, 'change_detail', '') or ''
            else:
                # Set to empty string if conditions not met
                changed_by = ''
                change_detail = ''
            
            # Create edit array with changed_by and change_detail
            edit_array = [{
                "changed_by": changed_by,
                "change_detail": change_detail
            }]
            
            # Get notes, default to empty string if None
            notes = getattr(log, 'notes', '') or ''
            
            log_data = {
                "id": log.id,
                "case_id": log.case_id,
                "action": log.action,
                "edit": edit_array,
                "notes": notes,
                "status": log.status,
                "created_at": formatted_date
            }
            case_log.append(log_data)
        
        case_notes_value = getattr(case, 'notes', None)
        
        case_data = {
            "case": {
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "description": case.description or "No description available",
                "status": case.status,
                "case_officer": case.main_investigator,
                "agency": agency_name or "N/A",
                "work_unit": work_unit_name,
                "created_date": created_date
            },
            "persons_of_interest": persons_of_interest,
            "case_log": case_log,
            "case_notes": case_notes_value
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
            "status": log.status,
            "created_at": log.created_at.strftime("%d %b %y, %H:%M")
        }
    
    def update_case_log(self, db: Session, case_id: int, log_data: dict) -> dict:
        """Update case status and create case log entry"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        new_status = log_data['status']
        old_status = case.status
        
        case.status = new_status
        db.commit()
        db.refresh(case)
        
        # Get notes from request body, default to empty string if not provided
        notes = log_data.get('notes', '') or ''
        
        log_entry = CaseLog(
            case_id=case_id,
            action=new_status,
            changed_by="",
            change_detail="",
            notes=notes,
            status=new_status
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        created_at_value = getattr(log_entry, 'created_at', None)
        if created_at_value:
            if isinstance(created_at_value, datetime):
                day = created_at_value.day
                formatted_date = f"{day} {created_at_value.strftime('%B %Y, %H:%M')}"
            else:
                formatted_date = str(created_at_value)
        else:
            formatted_date = None
        
        current_case_status = case.status
        
        log_action = getattr(log_entry, 'action', '')
        log_status = getattr(log_entry, 'status', '')
        
        if log_action == "Edit" and log_status == current_case_status:
            changed_by = getattr(log_entry, 'changed_by', '') or ''
            change_detail = getattr(log_entry, 'change_detail', '') or ''
        else:
            changed_by = ''
            change_detail = ''
        
        edit_array = [{
            "changed_by": changed_by,
            "change_detail": change_detail
        }]
        
        notes_value = getattr(log_entry, 'notes', '') or ''
        
        return {
            "id": log_entry.id,
            "case_id": log_entry.case_id,
            "action": log_entry.action,
            "edit": edit_array,
            "notes": notes_value,
            "status": log_entry.status,
            "created_at": formatted_date
        }
    
    def get_case_logs(self, db: Session, case_id: int, skip: int = 0, limit: int = 10) -> List[dict]:
        case = db.query(Case).filter(Case.id == case_id).first()
        current_case_status = case.status if case else None
        
        logs = db.query(CaseLog).filter(CaseLog.case_id == case_id)\
            .order_by(CaseLog.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for log in logs:
            created_at_value = getattr(log, 'created_at', None)
            if created_at_value:
                if isinstance(created_at_value, datetime):
                    day = created_at_value.day
                    formatted_date = f"{day} {created_at_value.strftime('%B %Y, %H:%M')}"
                else:
                    formatted_date = str(created_at_value)
            else:
                formatted_date = None
            
            log_action = getattr(log, 'action', '')
            log_status = getattr(log, 'status', '')
            
            if log_action == "Edit" and log_status == current_case_status:
                changed_by = getattr(log, 'changed_by', '') or ''
                change_detail = getattr(log, 'change_detail', '') or ''
            else:
                changed_by = ''
                change_detail = ''
            
            edit_array = [{
                "changed_by": changed_by,
                "change_detail": change_detail
            }]
            
            notes = getattr(log, 'notes', '') or ''
            
            log_dict = {
                "id": log.id,
                "case_id": log.case_id,
                "action": log.action,
                "edit": edit_array,
                "notes": notes,
                "status": log.status,
                "created_at": formatted_date
            }
            result.append(log_dict)
        
        return result
    
    def get_log_count(self, db: Session, case_id: int) -> int:
        return db.query(CaseLog).filter(CaseLog.case_id == case_id).count()

class PersonService:
    def create_person(self, db: Session, person_data: PersonCreate, changed_by: str = "") -> dict:
        person_dict = person_data.dict()
        
        try:
            person = Person(**person_dict)
            db.add(person)
            db.commit()
            db.refresh(person)
            try:
                case = db.query(Case).filter(Case.id == person.case_id).first()
                current_status = case.status if case else "Open"
                
                changed_by_value = changed_by if changed_by else ""
                
                case_log = CaseLog(
                    case_id=person.case_id,
                    action="Edit",
                    changed_by=changed_by_value,
                    change_detail=f"Adding Person: {person.name}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create case log for person: {str(e)}")
                
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
person_service = PersonService()
