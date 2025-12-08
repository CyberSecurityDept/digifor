from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.evidence_management.models import Evidence
from app.case_management.models import Case, CaseLog
from app.suspect_management.models import Suspect
from app.api.deps import get_database, get_current_user
from app.auth.models import User
from fastapi.responses import JSONResponse
import os, hashlib
import logging

logger = logging.getLogger(__name__)
from app.case_management.service import check_case_access
from app.utils.security import sanitize_input, validate_sql_injection_patterns, validate_file_name

class SuspectNotesBody(BaseModel):
    notes: str | None = Field(..., description="Suspect notes text")

VALID_SUSPECT_STATUSES = ["Witness", "Reported", "Suspected", "Suspect", "Defendant"]

def normalize_suspect_status(status: Optional[str]) -> Optional[str]:
    if not status or not isinstance(status, str):
        return None
    
    status_clean = status.strip()
    if not status_clean:
        return None
    
    for valid_status in VALID_SUSPECT_STATUSES:
        if status_clean.lower() == valid_status.lower():
            return valid_status
    
    status_capitalized = status_clean.capitalize()
    for valid_status in VALID_SUSPECT_STATUSES:
        if status_capitalized.lower() == valid_status.lower():
            return valid_status
    
    return None

router = APIRouter(prefix="/persons", tags=["Person Management"])

@router.post("/create-person")
async def create_person(
    case_id: int = Form(...),
    person_name: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    evidence_number: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(False),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        logger.info(f"[SECURITY] create_person - person_name: {repr(person_name)}, is_unknown_person: {is_unknown_person}, type: {type(is_unknown_person)}")
        
        if not is_unknown_person:
            logger.info(f"[SECURITY] is_unknown_person is False, validation will run")
            if not person_name or not person_name.strip():
                raise HTTPException(status_code=400, detail="person_name is required when is_unknown_person is false")
            
            # Validate SQL injection - CRITICAL SECURITY CHECK
            validation_result = validate_sql_injection_patterns(person_name)
            logger.info(f"[SECURITY] SQL injection validation result for person_name: {validation_result} (False = blocked, True = allowed)")
            
            if not validation_result:
                logger.warning(f"[SECURITY] SQL injection attempt BLOCKED in person_name: {person_name[:50]}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in person_name. Please remove any SQL injection attempts or malicious code."
                )
            person_name = sanitize_input(person_name)
            logger.info(f"[SECURITY] person_name after sanitization: {repr(person_name)}")
            
            if not suspect_status or not suspect_status.strip():
                raise HTTPException(status_code=400, detail="suspect_status is required when is_unknown_person is false")
            if not validate_sql_injection_patterns(suspect_status):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in suspect_status. Please remove any SQL injection attempts or malicious code."
                )
            suspect_status = sanitize_input(suspect_status, max_length=50)
        
        if evidence_summary and evidence_summary.strip():
            if not validate_sql_injection_patterns(evidence_summary):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_summary. Please remove any SQL injection attempts or malicious code."
                )
        
        if evidence_source and evidence_source.strip():
            if not validate_sql_injection_patterns(evidence_source):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_source. Please remove any SQL injection attempts or malicious code."
                )
        
        if evidence_number is not None:
            evidence_number = evidence_number.strip() if isinstance(evidence_number, str) else str(evidence_number).strip()
            if not evidence_number:
                raise HTTPException(status_code=400, detail="evidence_number cannot be empty when provided manually")
            if len(evidence_number) > 100:
                raise HTTPException(
                    status_code=400,
                    detail="evidence_number cannot exceed 100 characters. Please use evidence_summary for longer text."
                )
            if not validate_sql_injection_patterns(evidence_number):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_number. Please remove any SQL injection attempts or malicious code."
                )
            evidence_number = sanitize_input(evidence_number, max_length=100)
            
            existing_evidence = db.query(Evidence).filter(
                Evidence.evidence_number == evidence_number
            ).first()
            
            if existing_evidence:
                raise HTTPException(
                    status_code=400,
                    detail=f"Evidence number '{evidence_number}' already exists"
                )
        
        if not evidence_number:
            if not evidence_file:
                raise HTTPException(status_code=400, detail="evidence_file atau evidence_number harus disediakan untuk create person")
            date_str = datetime.now().strftime("%Y%m%d")
            evidence_count = db.query(Evidence).filter(Evidence.case_id == case_id).count()
            evidence_number = f"EVID-{case_id}-{date_str}-{evidence_count + 1:04d}"
            
        file_path = None
        file_size = None
        file_hash = None
        file_type = None
        file_extension = None
        
        if evidence_file:
            if not validate_file_name(evidence_file.filename):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file name. File name contains dangerous characters."
                )
            
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
            file_extension = ''
            if evidence_file.filename and '.' in evidence_file.filename:
                file_extension = evidence_file.filename.split('.')[-1].lower()
            
            if file_extension and file_extension not in allowed_extensions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 400,
                        "detail": f"File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: {', '.join(allowed_extensions)})"
                    }
                )
            
            upload_dir = "data/evidence"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evidence_{timestamp}_{evidence_number}.{file_extension}" if file_extension else f"evidence_{timestamp}_{evidence_number}"
            file_path = os.path.join(upload_dir, filename)
            
            file_content = await evidence_file.read()
            file_size = len(file_content)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_type = evidence_file.content_type or 'application/octet-stream'

        evidence_title = case.title if case else evidence_number
        investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        if investigator_name:
            investigator_name = sanitize_input(investigator_name, max_length=100)
        existing_evidence = db.query(Evidence).filter(
            Evidence.evidence_number == evidence_number,
            Evidence.case_id == case_id
        ).first()
    
        if existing_evidence and (not evidence_summary or not evidence_summary.strip()):
            evidence_desc = getattr(existing_evidence, 'description', None) or ''
            evidence_notes = getattr(existing_evidence, 'notes', None)
            if evidence_notes:
                if isinstance(evidence_notes, dict):
                    notes_text = evidence_notes.get('text', '') or evidence_desc
                elif isinstance(evidence_notes, str):
                    notes_text = evidence_notes
                else:
                    notes_text = evidence_desc
            else:
                notes_text = evidence_desc
            
            if notes_text and notes_text.strip():
                evidence_summary = notes_text.strip()
        
        if existing_evidence and evidence_summary and evidence_summary.strip():
            if not validate_sql_injection_patterns(evidence_summary):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_summary. Please remove any SQL injection attempts or malicious code."
                )
            # evidence_summary disimpan di Evidence.description (Text type, unlimited)
            evidence_summary_clean = sanitize_input(evidence_summary.strip(), max_length=None)
            setattr(existing_evidence, 'description', evidence_summary_clean)
            db.commit()
        
        suspect_id_value = None
        if is_unknown_person:
            logger.info(f"[SECURITY] is_unknown_person is True, but validating person_name if provided")
            if person_name and person_name.strip():
                validation_result = validate_sql_injection_patterns(person_name)
                logger.info(f"[SECURITY] SQL injection validation result for person_name (unknown person): {validation_result}")
                if not validation_result:
                    logger.warning(f"[SECURITY] SQL injection attempt BLOCKED in person_name (unknown person): {person_name[:50]}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in person_name. Please remove any SQL injection attempts or malicious code."
                    )
                person_name = sanitize_input(person_name)
            final_name = person_name.strip() if person_name and person_name.strip() else "Unknown"
            final_suspect_status = normalize_suspect_status(suspect_status) if suspect_status else None
            if suspect_status and final_suspect_status is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                )
            
            # Sanitize case_name to match Suspect model constraint (String(500))
            case_name_value = None
            if case and case.title:
                case_name_value = sanitize_input(case.title, max_length=500)
            
            # Sanitize created_by to match Suspect model constraint (String(255))
            created_by_value = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            created_by_value = sanitize_input(created_by_value, max_length=255)
            
            suspect_dict = {
                "name": final_name,
                "case_id": case_id,
                "case_name": case_name_value,
                "investigator": investigator_name,
                "status": final_suspect_status,
                "is_unknown": True,
                "evidence_number": evidence_number,
                "evidence_source": evidence_source,
                "created_by": created_by_value
            }
            
            suspect = Suspect(**suspect_dict)
            db.add(suspect)
            db.commit()
            db.refresh(suspect)
            suspect_id_value = suspect.id
            
            try:
                current_status = case.status if case else "Open"
                changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                
                case_log = CaseLog(
                    case_id=case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Adding person {final_name}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                    logger.warning(f"Could not create case log for suspect: {str(e)}")
        else:
            person_name_clean = person_name.strip() if person_name else None
            final_suspect_status = normalize_suspect_status(suspect_status) if suspect_status else None
            if suspect_status and final_suspect_status is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                )
            
            case_name_value = None
            if case and case.title:
                case_name_value = sanitize_input(case.title, max_length=500)
            
            created_by_value = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            created_by_value = sanitize_input(created_by_value, max_length=255)
            
            suspect_dict = {
                "name": person_name_clean,
                "case_id": case_id,
                "case_name": case_name_value,
                "investigator": investigator_name,
                "status": final_suspect_status,
                "is_unknown": False,
                "evidence_number": evidence_number,
                "evidence_source": evidence_source,
                "created_by": created_by_value
            }
            
            suspect = Suspect(**suspect_dict)
            db.add(suspect)
            db.commit()
            db.refresh(suspect)
            suspect_id_value = suspect.id
            
            try:
                current_status = case.status if case else "Open"
                changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                
                case_log = CaseLog(
                    case_id=case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Adding person {person_name_clean}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                    logger.warning(f"Could not create case log for suspect: {str(e)}")
        
        if existing_evidence:
            if file_path:
                setattr(existing_evidence, 'file_path', file_path)
                setattr(existing_evidence, 'file_size', file_size)
                setattr(existing_evidence, 'file_hash', file_hash)
                setattr(existing_evidence, 'file_type', file_type)
                setattr(existing_evidence, 'file_extension', file_extension)
            if evidence_source:
                if not validate_sql_injection_patterns(evidence_source):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in evidence_source. Please remove any SQL injection attempts or malicious code."
                    )
                source_value = sanitize_input(evidence_source.strip() if isinstance(evidence_source, str) and evidence_source.strip() else None, max_length=100)
                setattr(existing_evidence, 'source', source_value)
            setattr(existing_evidence, 'suspect_id', suspect_id_value)
            if evidence_summary and evidence_summary.strip():
                if not validate_sql_injection_patterns(evidence_summary):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in evidence_summary. Please remove any SQL injection attempts or malicious code."
                    )
                # evidence_summary disimpan di Evidence.description (Text type, unlimited)
                evidence_summary_clean = sanitize_input(evidence_summary.strip(), max_length=None)
                setattr(existing_evidence, 'description', evidence_summary_clean)
            db.commit()
            evidence = existing_evidence
        else:
            if evidence_source:
                if not validate_sql_injection_patterns(evidence_source):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in evidence_source. Please remove any SQL injection attempts or malicious code."
                    )
            source_value = sanitize_input(evidence_source.strip() if evidence_source and isinstance(evidence_source, str) and evidence_source.strip() else None, max_length=100)
            
            # Sanitize evidence_summary jika ada (Text type, unlimited)
            evidence_summary_sanitized = None
            if evidence_summary and evidence_summary.strip():
                evidence_summary_sanitized = sanitize_input(evidence_summary.strip(), max_length=None)
            
            evidence_dict = {
                "evidence_number": evidence_number,
                "title": evidence_title,
                "description": evidence_summary_sanitized,
                "source": source_value,
                "evidence_type": None,
                "case_id": case_id,
                "suspect_id": suspect_id_value,
                "file_path": file_path,
                "file_size": file_size,
                "file_hash": file_hash,
                "file_type": file_type,
                "file_extension": file_extension,
                "investigator": investigator_name,
                "collected_date": datetime.now(timezone.utc),
            }
            
            evidence = Evidence(**evidence_dict)
            db.add(evidence)
            db.commit()
            db.refresh(evidence)
            
            try:
                current_status = case.status if case else "Open"
                changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                
                case_log = CaseLog(
                    case_id=case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Adding evidence {evidence_number}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                    logger.warning(f"Could not create case log for evidence: {str(e)}")
        
        created_at_str = None
        updated_at_str = None
        try:
            created_at_str = suspect.created_at.isoformat()
        except (AttributeError, TypeError):
            pass
        try:
            updated_at_str = suspect.updated_at.isoformat()
        except (AttributeError, TypeError):
            pass
        
        evidence_summary_value = None
        if evidence:
            evidence_summary_value = getattr(evidence, 'description', None)
        
        person_response = {
            "id": suspect.id,
            "case_id": suspect.case_id,
            "name": suspect.name,
            "suspect_status": suspect.status,
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": evidence_summary_value,
            "investigator": suspect.investigator,
            "created_by": suspect.created_by,
            "created_at": created_at_str,
            "updated_at": updated_at_str
        }
        
        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Person created successfully",
                "data": person_response
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_person: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating person. Please try again later."
        )

@router.put("/update-person/{person_id}")
async def update_person(
    person_id: int,
    person_name: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            raise HTTPException(status_code=404, detail=f"Person with ID {person_id} not found")
        
        old_name = getattr(suspect, 'name', None)
        old_status = getattr(suspect, 'status', None)
        old_notes = getattr(suspect, 'notes', None)
        name_changed = False
        status_changed = False
        notes_changed = False
        
        case = db.query(Case).filter(Case.id == suspect.case_id).first()
        if case:
            print("case found")

        if is_unknown_person is not None:
            setattr(suspect, 'is_unknown', is_unknown_person)

            if is_unknown_person:
                if old_name != "Unknown":
                    name_changed = True
                if old_status is not None:
                    status_changed = True
                setattr(suspect, 'name', "Unknown")
                setattr(suspect, 'status', None)
            else:
                if not person_name or not person_name.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="person_name is required when is_unknown_person is false"
                    )
                if not suspect_status or not suspect_status.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="suspect_status is required when is_unknown_person is false"
                    )
                new_name = person_name.strip()
                if old_name != new_name:
                    name_changed = True
                setattr(suspect, 'name', new_name)
                normalized_status = normalize_suspect_status(suspect_status)
                if normalized_status is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                    )
                if old_status != normalized_status:
                    status_changed = True
                setattr(suspect, 'status', normalized_status)
        else:
            current_is_unknown = getattr(suspect, 'is_unknown', False)
            if not current_is_unknown:
                if person_name is not None:
                    if not person_name.strip():
                        raise HTTPException(
                            status_code=400,
                            detail="person_name cannot be empty"
                        )
                    if not validate_sql_injection_patterns(person_name):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid characters detected in person_name. Please remove any SQL injection attempts or malicious code."
                        )
                    new_name = sanitize_input(person_name.strip())
                    if old_name != new_name:
                        name_changed = True
                    setattr(suspect, 'name', new_name)
                if suspect_status is not None:
                    if not suspect_status.strip():
                        raise HTTPException(
                            status_code=400,
                            detail="suspect_status cannot be empty"
                        )
                    if not validate_sql_injection_patterns(suspect_status):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid characters detected in suspect_status. Please remove any SQL injection attempts or malicious code."
                        )
                    normalized_status = normalize_suspect_status(suspect_status)
                    if normalized_status is None:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                        )
                    if old_status != normalized_status:
                        status_changed = True
                    setattr(suspect, 'status', normalized_status)
            else:
                if person_name is not None and person_name.strip() and suspect_status is not None and suspect_status.strip():
                    setattr(suspect, 'is_unknown', False)
                    new_name = person_name.strip()
                    if old_name != new_name:
                        name_changed = True
                    setattr(suspect, 'name', new_name)
                    normalized_status = normalize_suspect_status(suspect_status)
                    if normalized_status is None:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                        )
                    if old_status != normalized_status:
                        status_changed = True
                    setattr(suspect, 'status', normalized_status)
                elif person_name is not None or suspect_status is not None:
                    raise HTTPException(
                        status_code=400,
                        detail="Both person_name and suspect_status are required to change from unknown person to known person"
                    )
        
        if notes is not None:
            new_notes = notes.strip() if notes else None
            if new_notes:
                if not validate_sql_injection_patterns(new_notes):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code."
                    )
                new_notes = sanitize_input(new_notes)
            if old_notes != new_notes:
                notes_changed = True
            setattr(suspect, 'notes', new_notes)
        
        db.commit()
        db.refresh(suspect)
        
        try:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            suspect_name = getattr(suspect, 'name', 'Unknown')
            
            if name_changed:
                old_name_display = old_name if old_name else "Unknown"
                new_name_display = getattr(suspect, 'name', 'Unknown')
                case_log_name = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Updating person {old_name_display} | {new_name_display}",
                    notes="",
                    status=current_status
                )
                db.add(case_log_name)
            
            if status_changed:
                old_status_display = old_status if old_status else "Unknown"
                new_status_display = getattr(suspect, 'status', None) if getattr(suspect, 'status', None) else "Unknown"
                case_log_status = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Updating status person: {old_status_display} | {new_status_display}",
                    notes="",
                    status=current_status
                )
                db.add(case_log_status)
            
            if notes_changed:
                old_notes_display = old_notes if old_notes and old_notes.strip() else "None"
                new_notes_display = getattr(suspect, 'notes', None)
                new_notes_display = new_notes_display if new_notes_display and new_notes_display.strip() else "None"
                case_log_notes = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Updating notes person: {old_notes_display} | {new_notes_display}",
                    notes="",
                    status=current_status
                )
                db.add(case_log_notes)
            
            if not name_changed and not status_changed and not notes_changed and (person_name is not None or suspect_status is not None or is_unknown_person is not None or notes is not None):
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Updating person {suspect_name}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
            
            db.commit()
        except Exception as e:
                    logger.warning(f"Could not create case log: {str(e)}")
        
        created_at_str = None
        updated_at_str = None
        try:
            created_at_str = suspect.created_at.isoformat()
        except (AttributeError, TypeError):
            pass
        try:
            updated_at_str = suspect.updated_at.isoformat()
        except (AttributeError, TypeError):
            pass
        
        person_response = {
            "id": suspect.id,
            "case_id": suspect.case_id,
            "name": suspect.name,
            "suspect_status": suspect.status,
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "investigator": suspect.investigator,
            "created_by": suspect.created_by,
            "created_at": created_at_str,
            "updated_at": updated_at_str
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Person updated successfully",
                "data": person_response
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_person: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating person. Please try again later."
            )

@router.delete("/delete-person/{person_id}")
async def delete_person(
    person_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            raise HTTPException(status_code=404, detail=f"Person with ID {person_id} not found")
        
        case = db.query(Case).filter(Case.id == suspect.case_id).first()
        if case:
            print("case found")
        
        suspect_name = suspect.name
        case_id = suspect.case_id
        evidence_list = db.query(Evidence).filter(Evidence.suspect_id == person_id).all()
        for evidence in evidence_list:
            setattr(evidence, 'suspect_id', None)
        db.commit()
        
        db.delete(suspect)
        db.commit()
        
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            
            case_log = CaseLog(
                case_id=case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Deleting person {suspect_name}",
                notes="",
                status=current_status
            )
            db.add(case_log)
            db.commit()
        except Exception as e:
                    logger.warning(f"Could not create case log: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Person deleted successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in create_person: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating person. Please try again later."
        )

@router.post("/save-suspect-notes/{suspect_id}")
async def save_suspect_notes(
    suspect_id: int,
    request: SuspectNotesBody = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        notes_trimmed = request.notes.strip() if request.notes else ""

        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "message": f"Suspect with ID {suspect_id} not found"}
            )

        if suspect.case_id:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case and not check_case_access(case, current_user):
                return JSONResponse(
                    status_code=403,
                    content={"status": 403, "message": "You do not have permission to access this case"}
                )

        if suspect.notes and suspect.notes.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": f"Notes already exist for this suspect. Use PUT /edit-suspect-notes/{suspect_id} to update."
                }
            )

        suspect.notes = notes_trimmed
        db.commit()
        db.refresh(suspect)

        try:
            if suspect.case_id:
                changed_by = getattr(current_user, "fullname", "") or current_user.email
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Added notes for suspect {suspect.name}",
                    notes="",
                    status=case.status if case else "Open"
                )
                db.add(case_log)
                db.commit()
        except:
            pass

        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Suspect notes saved successfully",
                "data": {"suspect_id": suspect_id, "notes": notes_trimmed}
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in person routes: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": 500, "message": "An unexpected error occurred. Please try again later."})

@router.put("/edit-suspect-notes/{suspect_id}")
async def edit_suspect_notes(
    suspect_id: int,
    request: SuspectNotesBody = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        notes_trimmed = request.notes.strip() if request.notes else ""
        
        if notes_trimmed:
            if not validate_sql_injection_patterns(notes_trimmed):
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 400,
                        "message": "Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    }
                )
            notes_trimmed = sanitize_input(notes_trimmed)

        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "message": f"Suspect with ID {suspect_id} not found"}
            )

        if suspect.case_id:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case and not check_case_access(case, current_user):
                return JSONResponse(
                    status_code=403,
                    content={"status": 403, "message": "You do not have permission to access this case"}
                )

        if not suspect.notes or not suspect.notes.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": f"No notes found for this suspect. Use POST /save-suspect-notes/{suspect_id} to create notes."
                }
            )

        suspect.notes = notes_trimmed
        db.commit()
        db.refresh(suspect)

        try:
            if suspect.case_id:
                changed_by = getattr(current_user, "fullname", "") or current_user.email
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Updated notes for suspect {suspect.name}",
                    notes="",
                    status=case.status if case else "Open"
                )
                db.add(case_log)
                db.commit()
        except:
            pass

        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Suspect notes updated successfully",
                "data": {"suspect_id": suspect_id, "notes": notes_trimmed}
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in person routes: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": 500, "message": "An unexpected error occurred. Please try again later."})