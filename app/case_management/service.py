from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.case_management.models import Case, Agency, WorkUnit, CaseLog, WIB
from app.suspect_management.models import Suspect
from app.case_management.schemas import CaseCreate, CaseUpdate, PersonCreate, PersonUpdate
from app.evidence_management.models import Evidence, CustodyLog
from datetime import datetime
from fastapi import HTTPException
import traceback, logging, os
from app.case_management.pdf_export import generate_case_detail_pdf
from app.core.config import settings

def get_wib_now():
    return datetime.now(WIB)

def check_case_access(case: Case, current_user) -> bool:
    return True

def format_date_indonesian(date_value: datetime) -> str:
    month_names = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    day = date_value.day
    month = month_names[date_value.month]
    year = date_value.year
    time = date_value.strftime("%H:%M")
    return f"{day} {month} {year}, {time}"

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
        case_dict.pop("summary", None)
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
    
    def get_cases(self, db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = None, current_user=None) -> dict:
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
    
    def update_case(self, db: Session, case_id: int, case_data: CaseUpdate, current_user=None) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        # Store old values for tracking changes
        old_values = {
            'case_number': case.case_number,
            'title': case.title,
            'description': getattr(case, 'description', None) or '',
            'main_investigator': case.main_investigator,
            'notes': getattr(case, 'notes', None) or '',
            'agency_id': getattr(case, 'agency_id', None),
            'work_unit_id': getattr(case, 'work_unit_id', None)
        }
        
        # Get old agency and work unit names
        old_agency_name = None
        if old_values['agency_id']:
            old_agency = db.query(Agency).filter(Agency.id == old_values['agency_id']).first()
            if old_agency:
                old_agency_name = old_agency.name
        
        old_work_unit_name = None
        if old_values['work_unit_id']:
            old_work_unit = db.query(WorkUnit).filter(WorkUnit.id == old_values['work_unit_id']).first()
            if old_work_unit:
                old_work_unit_name = old_work_unit.name
        
        update_data = case_data.dict(exclude_unset=True)
        
        agency = None
        agency_name = None
        agency_id_value = update_data.get('agency_id')
        if agency_id_value is not None:
            try:
                agency_id_int = int(agency_id_value) if agency_id_value else None
                if agency_id_int and agency_id_int > 0:
                    agency = db.query(Agency).filter(Agency.id == agency_id_int).first()
                    if not agency:
                        raise HTTPException(status_code=404, detail=f"Agency with ID {agency_id_int} not found")
                    agency_name = agency.name
                    update_data['agency_id'] = agency.id
            except (ValueError, TypeError):
                pass
        
        if agency_name is None and 'agency_name' in update_data and update_data['agency_name']:
            agency = get_or_create_agency(db, update_data['agency_name'])
            update_data['agency_id'] = agency.id
            agency_name = agency.name
            update_data.pop('agency_name', None)
        
        work_unit = None
        work_unit_name = None
        work_unit_id_value = update_data.get('work_unit_id')
        if work_unit_id_value is not None:
            try:
                work_unit_id_int = int(work_unit_id_value) if work_unit_id_value else None
                if work_unit_id_int and work_unit_id_int > 0:
                    work_unit = db.query(WorkUnit).filter(WorkUnit.id == work_unit_id_int).first()
                    if not work_unit:
                        raise HTTPException(status_code=404, detail=f"Work unit with ID {work_unit_id_int} not found")
                    work_unit_name = work_unit.name
                    update_data['work_unit_id'] = work_unit.id
            except (ValueError, TypeError):
                pass
        
        if work_unit_name is None and 'work_unit_name' in update_data and update_data['work_unit_name']:
            if not agency:
                case_agency_id = getattr(case, 'agency_id', None)
                if case_agency_id:
                    agency = db.query(Agency).filter(Agency.id == case_agency_id).first()
                if not agency:
                    raise HTTPException(status_code=400, detail="Agency must be specified when creating work unit")
            work_unit = get_or_create_work_unit(db, update_data['work_unit_name'], agency)
            update_data['work_unit_id'] = work_unit.id
            work_unit_name = work_unit.name
            update_data.pop('work_unit_name', None)
        
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
            if hasattr(case, field):
                setattr(case, field, value)
        
        db.commit()
        db.refresh(case)
        
        if agency_name is None and case.agency_id is not None:
            agency = db.query(Agency).filter(Agency.id == case.agency_id).first()
            if agency:
                agency_name = agency.name
        
        if work_unit_name is None and case.work_unit_id is not None:
            work_unit = db.query(WorkUnit).filter(WorkUnit.id == case.work_unit_id).first()
            if work_unit:
                work_unit_name = work_unit.name
        
        changed_fields = []
        changed_by = None
        if current_user:
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', '') or getattr(current_user, 'username', 'Unknown User')
            changed_by = f"By: {changed_by}"
        else:
            changed_by = "By: Unknown User"
        
        if 'case_number' in update_data:
            new_case_number = case.case_number
            if str(old_values['case_number']) != str(new_case_number):
                changed_fields.append(f"Case Number: {old_values['case_number']} | {new_case_number}")
        
        if 'title' in update_data:
            new_title = case.title
            if str(old_values['title']) != str(new_title):
                changed_fields.append(f"Case Name: {old_values['title']} | {new_title}")
        
        if 'description' in update_data:
            new_description = getattr(case, 'description', None) or ''
            old_desc_str = str(old_values['description'])
            new_desc_str = str(new_description)
            if old_desc_str != new_desc_str:
                if len(old_desc_str) > 50 or len(new_desc_str) > 50:
                    changed_fields.append(f"Description: {old_desc_str[:50]}... | {new_desc_str[:50]}...")
                else:
                    changed_fields.append(f"Description: {old_desc_str} | {new_desc_str}")

        if 'main_investigator' in update_data:
            new_main_investigator = getattr(case, 'main_investigator', None) or ''
            if str(old_values['main_investigator']) != str(new_main_investigator):
                changed_fields.append(f"Main Investigator: {old_values['main_investigator']} | {new_main_investigator}")
        
        if 'agency_id' in update_data or 'agency_name' in case_data.dict(exclude_unset=True):
            new_agency_id = getattr(case, 'agency_id', None)
            if new_agency_id != old_values['agency_id']:
                new_agency_name = agency_name or (old_agency_name if new_agency_id == old_values['agency_id'] else None)
                if new_agency_name is None and new_agency_id is not None:
                    new_agency_obj = db.query(Agency).filter(Agency.id == new_agency_id).first()
                    if new_agency_obj:
                        new_agency_name = new_agency_obj.name
                changed_fields.append(f"Agency: {old_agency_name or 'None'} | {new_agency_name or 'None'}")

        if 'work_unit_id' in update_data or 'work_unit_name' in case_data.dict(exclude_unset=True):
            new_work_unit_id = getattr(case, 'work_unit_id', None)
            if new_work_unit_id != old_values['work_unit_id']:
                new_work_unit_name = work_unit_name or (old_work_unit_name if new_work_unit_id == old_values['work_unit_id'] else None)
                if new_work_unit_name is None and new_work_unit_id is not None:
                    new_work_unit_obj = db.query(WorkUnit).filter(WorkUnit.id == new_work_unit_id).first()
                    if new_work_unit_obj:
                        new_work_unit_name = new_work_unit_obj.name
                changed_fields.append(f"Work Unit: {old_work_unit_name or 'None'} | {new_work_unit_name or 'None'}")

        if 'notes' in update_data:
            new_notes = getattr(case, 'notes', None) or ''
            old_notes_str = str(old_values['notes'])
            new_notes_str = str(new_notes)
            if old_notes_str != new_notes_str:
                if len(old_notes_str) > 50 or len(new_notes_str) > 50:
                    changed_fields.append(f"Summary: {old_notes_str[:50]}... | {new_notes_str[:50]}...")
                else:
                    changed_fields.append(f"Summary: {old_notes_str} | {new_notes_str}")

        if changed_fields:
            for change_detail_text in changed_fields:
                try:
                    case_log = CaseLog(
                        case_id=case_id,
                        action="Edit",
                        changed_by=changed_by,
                        change_detail=f"Change: {change_detail_text}",
                        notes="",
                        status=case.status
                    )
                    db.add(case_log)
                except Exception as e:
                    print(f"Warning: Could not create case log for field change: {str(e)}")
            
            try:
                db.commit()
            except Exception as e:
                print(f"Warning: Could not commit case logs: {str(e)}")
                db.rollback()

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
    
    def get_case_statistics(self, db: Session, current_user=None) -> dict:
        query = db.query(Case)
        
        total_cases = query.count()
        open_cases = query.filter(Case.status == "Open").count()
        closed_cases = query.filter(Case.status == "Closed").count()
        reopened_cases = query.filter(Case.status == "Re-open").count()
        
        return {
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "reopened_cases": reopened_cases,
            "total_cases": total_cases
        }
    
    def save_case_notes(self, db: Session, case_id: int, notes: str, current_user=None) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
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
    
    def edit_case_notes(self, db: Session, case_id: int, notes: str, current_user=None) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
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
    
    def _get_chain_of_custody(self, db: Session, evidence_id: int) -> dict:
        custody_logs = db.query(CustodyLog).filter(
            CustodyLog.evidence_id == evidence_id
        ).order_by(CustodyLog.event_date.asc()).all()
        
        chain_of_custody = {
            "acquisition": None,
            "preparation": None,
            "extraction": None,
            "analysis": None
        }
        
        for log in custody_logs:
            event_type_lower = getattr(log, 'event_type', '').lower()
            event_date = getattr(log, 'event_date', None)
            person_name = getattr(log, 'person_name', '')
            location = getattr(log, 'location', '')
            action_description = getattr(log, 'action_description', '')
            tools_used = getattr(log, 'tools_used', None)
            notes = getattr(log, 'notes', '')
            
            formatted_date = None
            if event_date:
                if isinstance(event_date, datetime):
                    formatted_date = format_date_indonesian(event_date)
                else:
                    formatted_date = str(event_date)
            
            custody_data = {
                "date": formatted_date,
                "investigator": person_name,
                "location": location,
                "description": action_description or notes,
                "tools_used": tools_used if isinstance(tools_used, list) else ([tools_used] if tools_used else [])
            }
            
            if event_type_lower == "acquisition":
                chain_of_custody["acquisition"] = custody_data
            elif event_type_lower == "preparation":
                chain_of_custody["preparation"] = custody_data
            elif event_type_lower == "extraction":
                chain_of_custody["extraction"] = custody_data
            elif event_type_lower == "analysis":
                chain_of_custody["analysis"] = custody_data
        
        return chain_of_custody
    
    def get_case_detail_comprehensive(self, db: Session, case_id: int, current_user=None) -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
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
        suspects = db.query(Suspect).filter(Suspect.case_id == case_id).order_by(Suspect.id.asc()).all()
        all_evidence = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        evidence_linked_to_suspects = set()
        suspects_by_id = {}
        suspect_map = {suspect.id: suspect for suspect in suspects}
        
        for suspect in suspects:
            suspect_status = getattr(suspect, 'status', None)
            person_type = suspect_status if suspect_status else None
            
            suspects_by_id[suspect.id] = {
                "suspect_id": suspect.id,
                "name": suspect.name,
                "person_type": person_type,
                "evidence": []
            }
            
        for evidence in all_evidence:
            evidence_suspect_id = getattr(evidence, 'suspect_id', None)
            evidence_num = getattr(evidence, 'evidence_number', None)
            
            linked_suspect_id = None
            if evidence_suspect_id and evidence_suspect_id in suspect_map:
                linked_suspect_id = evidence_suspect_id
            elif evidence_num:
                for suspect_id, suspect in suspect_map.items():
                    suspect_evidence_number = getattr(suspect, 'evidence_number', None)
                    if suspect_evidence_number and suspect_evidence_number == evidence_num:
                        linked_suspect_id = suspect_id
                        break
            
            if linked_suspect_id is not None and linked_suspect_id in suspects_by_id:
                suspect = suspect_map[linked_suspect_id]
                evidence_items = suspects_by_id[linked_suspect_id]["evidence"]
                
                if evidence_num:
                    evidence_linked_to_suspects.add(evidence_num)
                
                notes_text = None
                evidence_notes = getattr(evidence, 'notes', None)
                evidence_desc = getattr(evidence, 'description', None) or ''
                
                if evidence_notes:
                    if isinstance(evidence_notes, dict):
                        notes_text = evidence_notes.get('text', '') or evidence_desc
                    elif isinstance(evidence_notes, str):
                        notes_text = evidence_notes
                else:
                    notes_text = evidence_desc
                
                evidence_item = {
                    "id": evidence.id,
                    "evidence_number": evidence_num or "",
                    "evidence_summary": notes_text or "No description available"
                }
                
                evidence_file_path = getattr(evidence, 'file_path', None)
                if evidence_file_path:
                    evidence_item["file_path"] = evidence_file_path
                
                evidence_source = getattr(evidence, 'source', None)
                if evidence_source:
                    evidence_item["source"] = evidence_source
                else:
                    suspect_source = getattr(suspect, 'evidence_source', None)
                    if suspect_source:
                        evidence_item["source"] = suspect_source
                
                if evidence_num and not any(item.get("evidence_number") == evidence_num for item in evidence_items):
                    evidence_items.append(evidence_item)
        
        for suspect_id, suspect_data in suspects_by_id.items():
            evidence_items = suspect_data["evidence"]
            evidence_items.sort(key=lambda x: x.get("id") or 0)
        
        persons_of_interest = [
            suspect_data for suspect_data in suspects_by_id.values() 
            if suspect_data.get("suspect_id") is not None
        ]
        persons_of_interest.sort(key=lambda x: x.get("suspect_id") or 0, reverse=False)
        case_notes_value = getattr(case, 'notes', None)
        person_count = len(persons_of_interest)
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
            "person_count": person_count,
            "case_notes": case_notes_value
        }
        
        return case_data
    
    def export_case_detail_pdf(self, db: Session, case_id: int, output_dir: Optional[str] = None, current_user=None) -> str:
        if output_dir is None:
            output_dir = settings.REPORTS_DIR
  
        case_data = self.get_case_detail_comprehensive(db, case_id, current_user)

        os.makedirs(output_dir, exist_ok=True)

        case_info = case_data.get("case", {})
        case_number = str(case_info.get("case_number", case_info.get("id", "unknown")))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"case_detail_{case_number}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)

        generate_case_detail_pdf(case_data, output_path)
        return output_path

class CaseLogService:
    def create_log(self, db: Session, log_data: dict) -> dict:
        notes = log_data.get('notes', '') or ''
        log_data['notes'] = notes
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
    
    def update_case_log(self, db: Session, case_id: int, log_data: dict, current_user=None) -> dict:
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Case not found")
            new_status = log_data['status']
            old_status = case.status
            case.status = new_status
            db.commit()
            db.refresh(case)
            
            notes = log_data.get('notes', '')
            if not notes or not notes.strip():
                raise HTTPException(status_code=400, detail="Notes/alasan wajib diisi ketika mengubah status case")
            notes = notes.strip()
            
            changed_by_value = ""
            change_detail_value = ""
            
            if new_status == "Re-open":
                if current_user:
                    changed_by_value = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                    changed_by_value = f"By: {changed_by_value}"
                else:
                    changed_by_value = "By: "
                
                change_detail_value = f"Change: Adding Status {new_status}"
            
            log_entry = CaseLog(
                case_id=case_id,
                action=new_status,
                changed_by=changed_by_value,
                change_detail=change_detail_value,
                notes=notes,
                status=new_status
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger = logging.getLogger(__name__)
            logger.error(f"Error in update_case_log: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        created_at_value = getattr(log_entry, 'created_at', None)
        if created_at_value:
            if isinstance(created_at_value, datetime):
                formatted_date = format_date_indonesian(created_at_value)
            else:
                formatted_date = str(created_at_value)
        else:
            formatted_date = None
        
        current_case_status = case.status
        
        log_action = getattr(log_entry, 'action', '')
        log_status = getattr(log_entry, 'status', '')
        
        result = {
            "id": log_entry.id,
            "case_id": log_entry.case_id,
            "action": log_entry.action,
            "created_at": formatted_date
        }
        
        if log_action == "Edit" and log_status == current_case_status:
            changed_by = getattr(log_entry, 'changed_by', '') or ''
            change_detail = getattr(log_entry, 'change_detail', '') or ''
            if changed_by or change_detail:
                edit_array = [{
                    "changed_by": changed_by,
                    "change_detail": change_detail
                }]
                result["edit"] = edit_array
        else:
            result["status"] = log_entry.status
            notes_value = getattr(log_entry, 'notes', None)
            if notes_value is not None and isinstance(notes_value, str) and notes_value.strip() != '':
                result["notes"] = notes_value
        
        return result
    
    def get_case_logs(self, db: Session, case_id: int, skip: int = 0, limit: int = 10, current_user=None) -> List[dict]:
        try:
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
                        formatted_date = format_date_indonesian(created_at_value)
                    else:
                        formatted_date = str(created_at_value)
                else:
                    formatted_date = None
                
                log_action = getattr(log, 'action', '')
                log_status = getattr(log, 'status', '')
                
                log_dict = {
                    "id": log.id,
                    "case_id": log.case_id,
                    "action": log.action,
                    "created_at": formatted_date
                }
                
                if log_action == "Edit":
                    changed_by = getattr(log, 'changed_by', '') or ''
                    change_detail = getattr(log, 'change_detail', '') or ''
                    if changed_by or change_detail:
                        edit_array = [{
                            "changed_by": changed_by,
                            "change_detail": change_detail
                        }]
                        log_dict["edit"] = edit_array
                elif log_action == "Re-open":
                    changed_by = getattr(log, 'changed_by', '') or ''
                    change_detail = getattr(log, 'change_detail', '') or ''
                    
                    if not changed_by or not changed_by.strip():
                        if current_user:
                            user_name = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', '') or getattr(current_user, 'username', 'Unknown User')
                            changed_by = f"By: {user_name}"
                        else:
                            changed_by = "By: Unknown User"
                    elif changed_by and changed_by.strip() and not changed_by.strip().startswith("By: "):
                        changed_by = f"By: {changed_by.strip()}"
                    
                    if not change_detail or not change_detail.strip():
                        change_detail = f"Change: Adding Status {log_status}"
                    elif not change_detail.strip().startswith("Change: "):
                        change_detail = f"Change: {change_detail.strip()}"
                    
                    edit_array = [{
                        "changed_by": changed_by,
                        "change_detail": change_detail
                    }]
                    log_dict["edit"] = edit_array
                    log_dict["status"] = log.status
                    notes_value = getattr(log, 'notes', None)
                    if notes_value is not None and isinstance(notes_value, str) and notes_value.strip() != '':
                        log_dict["notes"] = notes_value
                else:
                    log_dict["status"] = log.status
                    notes_value = getattr(log, 'notes', None)
                    if notes_value is not None and isinstance(notes_value, str) and notes_value.strip() != '':
                        log_dict["notes"] = notes_value
                
                result.append(log_dict)
            return result
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_case_logs: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error retrieving case logs: {str(e)}")
    
    def get_log_count(self, db: Session, case_id: int) -> int:
        return db.query(CaseLog).filter(CaseLog.case_id == case_id).count()

    def get_case_log_detail(self, db: Session, log_id: int, current_user=None) -> dict:
        try:
            log = db.query(CaseLog).filter(CaseLog.id == log_id).first()
            if not log:
                raise HTTPException(status_code=404, detail="Case log not found")
            case = db.query(Case).filter(Case.id == log.case_id).first()
            current_case_status = case.status if case else None
            created_at_value = getattr(log, 'created_at', None)
            if created_at_value:
                if isinstance(created_at_value, datetime):
                    formatted_date = format_date_indonesian(created_at_value)
                else:
                    formatted_date = str(created_at_value)
            else:
                formatted_date = None
            
            log_action = getattr(log, 'action', '')
            log_status = getattr(log, 'status', '')
            
            result = {
                "id": log.id,
                "case_id": log.case_id,
                "action": log.action,
                "created_at": formatted_date
            }
            
            if log_action == "Edit":
                changed_by = getattr(log, 'changed_by', '') or ''
                change_detail = getattr(log, 'change_detail', '') or ''
                if changed_by or change_detail:
                    edit_array = [{
                        "changed_by": changed_by,
                        "change_detail": change_detail
                    }]
                    result["edit"] = edit_array
            elif log_action == "Re-open":
                changed_by = getattr(log, 'changed_by', '') or ''
                change_detail = getattr(log, 'change_detail', '') or ''

                if not changed_by or not changed_by.strip():
                    if current_user:
                        user_name = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', '') or getattr(current_user, 'username', 'Unknown User')
                        changed_by = f"By: {user_name}"
                    else:
                        changed_by = "By: Unknown User"

                elif not changed_by.strip().startswith("By: "):
                    changed_by = f"By: {changed_by.strip()}"
                
                if not change_detail or not change_detail.strip():
                    change_detail = f"Change: Adding Status {log_status}"

                elif not change_detail.strip().startswith("Change: "):
                    change_detail = f"Change: {change_detail.strip()}"
                
                edit_array = [{
                    "changed_by": changed_by,
                    "change_detail": change_detail
                }]
                result["edit"] = edit_array
                result["status"] = log.status
                notes_value = getattr(log, 'notes', None)
                if notes_value is not None and isinstance(notes_value, str) and notes_value.strip() != '':
                    result["notes"] = notes_value
            else:
                result["status"] = log.status
                notes_value = getattr(log, 'notes', None)
                if notes_value is not None and isinstance(notes_value, str) and notes_value.strip() != '':
                    result["notes"] = notes_value
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_case_log_detail: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

class PersonService:
    def create_person(self, db: Session, person_data: PersonCreate, changed_by: str = "") -> dict:
        person_dict = person_data.dict()
        suspect_dict = {
            "name": person_dict.get("name", ""),
            "case_id": person_dict.get("case_id"),
            "case_name": None,
            "investigator": person_dict.get("investigator"),
            "status": person_dict.get("suspect_status") or "Suspect",
            "is_unknown": person_dict.get("is_unknown", False),
            "evidence_id": person_dict.get("evidence_id"),
            "evidence_source": person_dict.get("evidence_source"),
            "evidence_summary": person_dict.get("evidence_summary"),
            "created_by": person_dict.get("created_by", "")
        }
        
        try:
            suspect = Suspect(**suspect_dict)
            db.add(suspect)
            db.commit()
            db.refresh(suspect)
            try:
                case = db.query(Case).filter(Case.id == suspect.case_id).first()
                current_status = case.status if case else "Open"
                changed_by_value = changed_by if changed_by else ""
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by_value}",
                    change_detail=f"Change: Adding person {suspect.name}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create case log for suspect: {str(e)}")
                
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
            )
        
        return {
            "id": suspect.id,
            "name": suspect.name,
            "is_unknown": suspect.is_unknown,
            "suspect_status": suspect.status,
            "evidence_id": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "investigator": suspect.investigator,
            "case_id": suspect.case_id,
            "created_by": suspect.created_by,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def get_person(self, db: Session, person_id: int) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            raise Exception(f"Person with ID {person_id} not found")
        
        return {
            "id": suspect.id,
            "name": suspect.name,
            "is_unknown": suspect.is_unknown,
            "evidence_id": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "investigator": suspect.investigator,
            "case_id": suspect.case_id,
            "created_by": suspect.created_by,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def get_persons_by_case(self, db: Session, case_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        suspects = db.query(Suspect).filter(Suspect.case_id == case_id)\
            .order_by(Suspect.created_at.desc())\
            .offset(skip).limit(limit).all()
        
        result = []
        for suspect in suspects:
            person_dict = {
                "id": suspect.id,
                "name": suspect.name,
                "is_unknown": suspect.is_unknown,
                "evidence_number": suspect.evidence_number,
                "evidence_source": suspect.evidence_source,
                "evidence_summary": suspect.evidence_summary,
                "investigator": suspect.investigator,
                "case_id": suspect.case_id,
                "created_by": suspect.created_by,
                "created_at": suspect.created_at,
                "updated_at": suspect.updated_at
            }
            result.append(person_dict)
        
        return result
    
    def get_person_count_by_case(self, db: Session, case_id: int) -> int:
        return db.query(Suspect).filter(Suspect.case_id == case_id).count()
    
    def update_person(self, db: Session, person_id: int, person_data: PersonUpdate) -> dict:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            raise Exception(f"Person with ID {person_id} not found")
        
        update_data = person_data.dict(exclude_unset=True)
        if "suspect_status" in update_data:
            update_data["status"] = update_data.pop("suspect_status")
        
        for field, value in update_data.items():
            if hasattr(suspect, field):
                setattr(suspect, field, value)
        
        db.commit()
        db.refresh(suspect)
        
        return {
            "id": suspect.id,
            "name": suspect.name,
            "is_unknown": suspect.is_unknown,
            "evidence_id": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "investigator": suspect.investigator,
            "case_id": suspect.case_id,
            "created_by": suspect.created_by,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
        }
    
    def delete_person(self, db: Session, person_id: int) -> bool:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            return False
        
        db.delete(suspect)
        db.commit()
        return True

case_service = CaseService()
case_log_service = CaseLogService()
person_service = PersonService()
