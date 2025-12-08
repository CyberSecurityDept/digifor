from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime, timezone
import os, hashlib, re
import logging

logger = logging.getLogger(__name__)
from app.api.deps import get_database, get_current_user
from app.suspect_management.service import suspect_service
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate, SuspectResponse, SuspectListResponse, SuspectNotesRequest
from app.case_management.models import Case, CaseLog
from app.auth.models import User
from fastapi.responses import JSONResponse, FileResponse
from app.evidence_management.models import Evidence
from app.suspect_management.models import Suspect
from app.case_management.pdf_export import generate_suspect_detail_pdf
from app.core.config import settings
from app.utils.security import sanitize_input, validate_sql_injection_patterns, validate_file_name

router = APIRouter(prefix="/suspects", tags=["Suspect Management"])

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

@router.get("/", response_model=SuspectListResponse)
async def get_suspects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[List[str]] = Query(None),   # <-- UBAH DI SINI
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        if search:
            if not validate_sql_injection_patterns(search):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code."
                )
            search = sanitize_input(search, max_length=255)
        
        if status:
            sanitized_status = []
            for s in status:
                if isinstance(s, str):
                    if not validate_sql_injection_patterns(s):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid characters detected in status parameter. Please remove any SQL injection attempts or malicious code."
                        )
                    sanitized_s = sanitize_input(s, max_length=50)
                    if sanitized_s:
                        sanitized_status.append(sanitized_s)
            status = sanitized_status if sanitized_status else None
        
        suspects, total = suspect_service.get_suspects(db, skip, limit, search, status, current_user)
        return SuspectListResponse(
            status=200,
            message="Suspects retrieved successfully",
            data=suspects,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
    except Exception as e:
        logger.error(f"Error in get_suspects: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving suspects. Please try again later."
        )

@router.get("/get-suspect-summary")
async def get_suspect_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        total_person = (
            db.query(Suspect)
            .filter(
                Suspect.status.isnot(None),
                Suspect.is_unknown.is_(False)
            )
            .count()
        )

        total_evidence = db.query(Evidence).count()

        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Suspect summary retrieved successfully",
                "data": {
                    "total_person": total_person,
                    "total_evidence": total_evidence
                }
            }
        )

    except Exception as e:
        logger.error(f"Error in get_suspects: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving suspects. Please try again later."
        )

@router.post("/create-suspect", response_model=SuspectResponse)
async def create_suspect(
    case_id: int = Form(...),
    person_name: Optional[str] = Form(None),
    is_unknown_person: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    evidence_number: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    case_name: Optional[str] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        final_name = person_name
 
        final_status = suspect_status

        is_unknown_person_bool = None
        if is_unknown_person is not None:
            if isinstance(is_unknown_person, str):
                is_unknown_person_bool = is_unknown_person.lower() in ('true', '1', 'yes')
            else:
                is_unknown_person_bool = bool(is_unknown_person)
        
        is_unknown_flag = is_unknown_person_bool if is_unknown_person_bool is not None else False
        
        if is_unknown_person_bool is not None and not is_unknown_person_bool:
            if not final_name or not final_name.strip():
                raise HTTPException(
                    status_code=400,
                    detail="person_name is required when is_unknown_person is false"
                )
            if not validate_sql_injection_patterns(final_name):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in person_name. Please remove any SQL injection attempts or malicious code."
                )
            final_name = sanitize_input(final_name)
            
            if not final_status or not final_status.strip():
                raise HTTPException(
                    status_code=400,
                    detail="suspect_status is required when is_unknown_person is false"
                )
            if not validate_sql_injection_patterns(final_status):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in suspect_status. Please remove any SQL injection attempts or malicious code."
                )
            final_status = sanitize_input(final_status, max_length=50)
        
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
        if not evidence_number and evidence_file:
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
            filename = f"evidence_{timestamp}_{evidence_number or 'unknown'}.{file_extension}" if file_extension else f"evidence_{timestamp}_{evidence_number or 'unknown'}"
            file_path = os.path.join(upload_dir, filename)
            file_content = await evidence_file.read()
            file_size = len(file_content)
            with open(file_path, "wb") as f:
                f.write(file_content)
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_type = evidence_file.content_type or 'application/octet-stream'

        investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        suspect_id_to_link = None
        
        if evidence_number:
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
            
            if existing_evidence:
                if file_path:
                    setattr(existing_evidence, 'file_path', file_path)
                    setattr(existing_evidence, 'file_size', file_size)
                    setattr(existing_evidence, 'file_hash', file_hash)
                    setattr(existing_evidence, 'file_type', file_type)
                    setattr(existing_evidence, 'file_extension', file_extension)
            else:
                if evidence_file:
                    evidence_title = case.title if case else evidence_number
                    evidence_dict = {
                        "evidence_number": evidence_number,
                        "title": evidence_title,
                        "description": evidence_summary,
                        "case_id": case_id,
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
                        print(f"Warning: Could not create case log for evidence: {str(e)}")

        # Validate and sanitize optional fields
        if evidence_source:
            if not validate_sql_injection_patterns(evidence_source):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_source. Please remove any SQL injection attempts or malicious code."
                )
            evidence_source = sanitize_input(evidence_source, max_length=100)
        
        if evidence_summary:
            if not validate_sql_injection_patterns(evidence_summary):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in evidence_summary. Please remove any SQL injection attempts or malicious code."
                )
            # evidence_summary disimpan di Evidence.description (Text type, unlimited)
            evidence_summary = sanitize_input(evidence_summary, max_length=None)
        
        if case_name:
            if not validate_sql_injection_patterns(case_name):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid characters detected in case_name. Please remove any SQL injection attempts or malicious code."
                )
            case_name = sanitize_input(case_name)

        final_status_value = None if is_unknown_flag else final_status
        
        suspect_dict = {
            "name": final_name.strip() if (not is_unknown_flag and final_name) else "Unknown",
            "case_id": case_id,
            "case_name": case_name or case.title if case else None,
            "investigator": investigator_name,
            "status": final_status_value,
            "is_unknown": is_unknown_flag,
            "evidence_number": evidence_number,
            "evidence_source": evidence_source,
            "created_by": getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User'),
        }
        suspect_data = SuspectCreate(**suspect_dict)
        suspect = suspect_service.create_suspect(db, suspect_data)
        suspect_id = suspect.get("id")

        if evidence_number and suspect_id:
            existing_evidence = db.query(Evidence).filter(
                Evidence.evidence_number == evidence_number,
                Evidence.case_id == case_id
            ).first()
            
            if existing_evidence:
                setattr(existing_evidence, 'suspect_id', suspect_id)
                if evidence_source:
                    setattr(existing_evidence, 'source', evidence_source)
                db.commit()
            elif evidence_file:

                new_evidence = db.query(Evidence).filter(
                    Evidence.evidence_number == evidence_number,
                    Evidence.case_id == case_id
                ).first()
                if new_evidence:
                    setattr(new_evidence, 'suspect_id', suspect_id)
                    if evidence_source:
                        setattr(new_evidence, 'source', evidence_source)
                    db.commit()
        
        try:
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            case_log = CaseLog(
                case_id=case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Adding person {final_name or 'Unknown'}",
                notes="",
                status=current_status
            )
            db.add(case_log)
            db.commit()
        except Exception as e:
                    logger.warning(f"Could not create case log for suspect: {str(e)}")
        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Suspect created successfully",
                "data": suspect
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in create_suspect: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating suspect. Please try again later."
        )

@router.get("/get-suspect-detail/{suspect_id}")
async def get_suspect_detail(
    suspect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": f"Suspect with ID {suspect_id} not found"
                }
            )

        case = None
        created_at_case_str = None
        if suspect.case_id is not None:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case is not None and hasattr(case, 'created_at') and case.created_at is not None:
                try:
                    if isinstance(case.created_at, datetime):
                        created_at_case_str = case.created_at.strftime("%d/%m/%Y")
                    else:
                        created_at_case_str = str(case.created_at)
                except (AttributeError, TypeError):
                    pass
        
        evidence_list = []
        evidence_records = []
        if suspect_id is not None:
            evidence_records = db.query(Evidence).filter(Evidence.suspect_id == suspect_id).order_by(Evidence.id.asc()).all()
            if suspect.evidence_number is not None and str(suspect.evidence_number).strip():
                evidence_by_number = db.query(Evidence).filter(
                    Evidence.evidence_number == suspect.evidence_number,
                    Evidence.case_id == suspect.case_id
                ).order_by(Evidence.id.asc()).all()
                
                evidence_ids = {e.id for e in evidence_records}
                for evidence in evidence_by_number:
                    if evidence.id not in evidence_ids:
                        evidence_records.append(evidence)
                        
            evidence_records = sorted(evidence_records, key=lambda x: x.id)
            
            for evidence in evidence_records:
                evidence_created_at_str = None
                evidence_updated_at_str = None
                
                try:
                    if hasattr(evidence, 'created_at') and evidence.created_at is not None:
                        if isinstance(evidence.created_at, datetime):
                            evidence_created_at_str = evidence.created_at.isoformat()
                        else:
                            evidence_created_at_str = str(evidence.created_at)
                except (AttributeError, TypeError):
                    pass
                
                try:
                    if hasattr(evidence, 'updated_at') and evidence.updated_at is not None:
                        if isinstance(evidence.updated_at, datetime):
                            evidence_updated_at_str = evidence.updated_at.isoformat()
                        else:
                            evidence_updated_at_str = str(evidence.updated_at)
                except (AttributeError, TypeError):
                    pass
                
                evidence_list.append({
                    "id": evidence.id,
                    "evidence_number": f"Summary {evidence.evidence_number}" if evidence.evidence_number else None,
                    "evidence_summary": evidence.description if hasattr(evidence, 'description') else None,
                    "file_path": evidence.file_path if hasattr(evidence, 'file_path') else None,
                    "created_at": evidence_created_at_str,
                    "updated_at": evidence_updated_at_str
                })
        
        suspect_notes = None
        if hasattr(suspect, 'notes') and suspect.notes is not None:
            if isinstance(suspect.notes, str) and suspect.notes.strip():
                suspect_notes = suspect.notes.strip()
            elif isinstance(suspect.notes, dict):
                suspect_notes = suspect.notes.get('suspect_notes') or suspect.notes.get('text')
                if suspect_notes and isinstance(suspect_notes, str) and not suspect_notes.strip():
                    suspect_notes = None
            else:
                suspect_notes = str(suspect.notes) if suspect.notes else None
        else:
            if evidence_records and len(evidence_records) > 0:
                first_evidence = evidence_records[0]
            elif evidence_list and len(evidence_list) > 0:
                first_evidence = db.query(Evidence).filter(Evidence.id == evidence_list[0]["id"]).first()
            else:
                first_evidence = None
                
            if first_evidence is not None and hasattr(first_evidence, 'notes') and first_evidence.notes is not None:
                if isinstance(first_evidence.notes, dict):
                    suspect_notes = first_evidence.notes.get('suspect_notes')
                    if suspect_notes is None:
                        suspect_notes = first_evidence.notes.get('text')
                    if suspect_notes and isinstance(suspect_notes, str) and not suspect_notes.strip():
                        suspect_notes = None
                elif isinstance(first_evidence.notes, str):
                    suspect_notes = first_evidence.notes.strip() if first_evidence.notes.strip() else None
                else:
                    notes_value = first_evidence.notes
                    suspect_notes = str(notes_value) if notes_value is not None else None
        
        suspect_detail = {
            "id": suspect.id,
            "person_name": suspect.name,
            "suspect_status": suspect.status,
            "investigator": suspect.investigator,
            "case_name": suspect.case_name,
            "case_id": suspect.case_id,
            "created_at_case": created_at_case_str,
            "evidence": [
                {
                    "evidence_count": str(len(evidence_list)),
                    "list_evidence": evidence_list
                }
            ],
            "suspect_notes": suspect.notes
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Suspect detail retrieved successfully",
                "data": suspect_detail
            }
        )
    except Exception as e:
        logger.error(f"Error in get_suspect_detail: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "An unexpected error occurred while retrieving suspect details. Please try again later."
            }
        )

@router.get("/export-suspect-detail-pdf/{suspect_id}")
async def export_suspect_detail_pdf(
    suspect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )

        case = None
        created_at_case_str = None
        if suspect.case_id is not None:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case is not None and hasattr(case, 'created_at') and case.created_at is not None:
                try:
                    if isinstance(case.created_at, datetime):
                        created_at_case_str = case.created_at.strftime("%d/%m/%Y")
                    else:
                        created_at_case_str = str(case.created_at)
                except (AttributeError, TypeError):
                    pass
        
        evidence_list = []
        evidence_records = []
        if suspect_id is not None:
            evidence_records = db.query(Evidence).filter(Evidence.suspect_id == suspect_id).order_by(Evidence.id.asc()).all()
            if suspect.evidence_number is not None and str(suspect.evidence_number).strip():
                evidence_by_number = db.query(Evidence).filter(
                    Evidence.evidence_number == suspect.evidence_number,
                    Evidence.case_id == suspect.case_id
                ).order_by(Evidence.id.asc()).all()
                
                evidence_ids = {e.id for e in evidence_records}
                for evidence in evidence_by_number:
                    if evidence.id not in evidence_ids:
                        evidence_records.append(evidence)
                        
            evidence_records = sorted(evidence_records, key=lambda x: x.id)
            
            for evidence in evidence_records:
                evidence_list.append({
                    "id": evidence.id,
                    "evidence_number": evidence.evidence_number,  # Use original format for PDF
                    "evidence_summary": evidence.description if hasattr(evidence, 'description') else None,
                    "file_path": evidence.file_path if hasattr(evidence, 'file_path') else None,
                })
        
        suspect_notes = None
        if hasattr(suspect, 'notes') and suspect.notes is not None:
            if isinstance(suspect.notes, str) and suspect.notes.strip():
                suspect_notes = suspect.notes.strip()
            elif isinstance(suspect.notes, dict):
                suspect_notes = suspect.notes.get('suspect_notes') or suspect.notes.get('text')
                if suspect_notes and isinstance(suspect_notes, str) and not suspect_notes.strip():
                    suspect_notes = None
            else:
                suspect_notes = str(suspect.notes) if suspect.notes else None
        else:
            if evidence_records and len(evidence_records) > 0:
                first_evidence = evidence_records[0]
            elif evidence_list and len(evidence_list) > 0:
                first_evidence = db.query(Evidence).filter(Evidence.id == evidence_list[0]["id"]).first()
            else:
                first_evidence = None
                
            if first_evidence is not None and hasattr(first_evidence, 'notes') and first_evidence.notes is not None:
                if isinstance(first_evidence.notes, dict):
                    suspect_notes = first_evidence.notes.get('suspect_notes')
                    if suspect_notes is None:
                        suspect_notes = first_evidence.notes.get('text')
                    if suspect_notes and isinstance(suspect_notes, str) and not suspect_notes.strip():
                        suspect_notes = None
                elif isinstance(first_evidence.notes, str):
                    suspect_notes = first_evidence.notes.strip() if first_evidence.notes.strip() else None
                else:
                    notes_value = first_evidence.notes
                    suspect_notes = str(notes_value) if notes_value is not None else None
        
        suspect_detail = {
            "person_name": suspect.name,
            "suspect_status": suspect.status or "Unknown",
            "investigator": suspect.investigator or "N/A",
            "case_name": suspect.case_name or "Unknown Case",
            "created_at_case": created_at_case_str or "N/A",
            "evidence": [
                {
                    "evidence_count": str(len(evidence_list)),
                    "list_evidence": evidence_list
                }
            ],
            "suspect_notes": suspect_notes
        }

        os.makedirs(settings.REPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"suspect_detail_{suspect_id}_{timestamp}.pdf"
        output_path = os.path.join(settings.REPORTS_DIR, filename)

        pdf_path = generate_suspect_detail_pdf(suspect_detail, output_path)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PDF file"
            )

        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting suspect detail PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export suspect detail PDF. Please try again later."
        )

@router.put("/update-suspect/{suspect_id}", response_model=SuspectResponse)
async def update_suspect(
    suspect_id: int,
    case_id: Optional[int] = Form(None),
    person_name: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(None),
    suspect_status: Optional[str] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            raise HTTPException(status_code=404, detail=f"Suspect with ID {suspect_id} not found")
        
        if is_unknown_person is not None:
            is_unknown_flag = is_unknown_person
        else:
            is_unknown_flag = getattr(suspect, 'is_unknown', False)
        
        if case_id is not None:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": 404,
                        "message": f"Case with ID {case_id} not found"
                    }
                )
            setattr(suspect, 'case_id', case_id)
            setattr(suspect, 'case_name', case.title if case else None)
            investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            setattr(suspect, 'investigator', investigator_name)
    
        current_is_unknown = getattr(suspect, 'is_unknown', False)
        
        if is_unknown_flag is not None:
            setattr(suspect, 'is_unknown', is_unknown_flag)
            
            if is_unknown_flag:
                setattr(suspect, 'name', "Unknown")
                setattr(suspect, 'status', None)
            else:
                if person_name is None or not person_name.strip():
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": 400,
                            "message": "person_name is required when is_unknown_person is false"
                        }
                    )
                setattr(suspect, 'name', person_name.strip())
                
                if suspect_status is None or not suspect_status.strip():
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": 400,
                            "message": "suspect_status is required when is_unknown_person is false"
                        }
                    )
                
                normalized_status = normalize_suspect_status(suspect_status)
                if normalized_status is None:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": 400,
                            "message": f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                        }
                    )
                setattr(suspect, 'status', normalized_status)
        else:
            if not current_is_unknown:
                if person_name is not None:
                    if not person_name.strip():
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": 400,
                                "message": "person_name cannot be empty"
                            }
                        )
                    setattr(suspect, 'name', person_name.strip())
                
                if suspect_status is not None:
                    if not suspect_status.strip():
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": 400,
                                "message": "suspect_status cannot be empty"
                            }
                        )
                    normalized_status = normalize_suspect_status(suspect_status)
                    if normalized_status is None:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": 400,
                                "message": f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                            }
                        )
                    setattr(suspect, 'status', normalized_status)
        
        db.commit()
        db.refresh(suspect)
        
        try:
            case = db.query(Case).filter(Case.id == suspect.case_id).first()
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            case_log = CaseLog(
                case_id=suspect.case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Updating suspect {suspect.name}",
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
            created_at_value = getattr(suspect, 'created_at', None)
            if created_at_value:
                if isinstance(created_at_value, datetime):
                    created_at_str = created_at_value.isoformat()
                else:
                    created_at_str = str(created_at_value)
        except (AttributeError, TypeError):
            pass
        
        try:
            updated_at_value = getattr(suspect, 'updated_at', None)
            if updated_at_value:
                if isinstance(updated_at_value, datetime):
                    updated_at_str = updated_at_value.isoformat()
                else:
                    updated_at_str = str(updated_at_value)
        except (AttributeError, TypeError):
            pass
        
        suspect_response = {
            "id": suspect.id,
            "name": suspect.name,
            "case_name": suspect.case_name,
            "investigator": suspect.investigator,
            "status": suspect.status,
            "evidence_number": suspect.evidence_number,
            "evidence_source": suspect.evidence_source,
            "created_at": created_at_str,
            "updated_at": updated_at_str
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Suspect updated successfully",
                "data": suspect_response
            }
        )
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "duplicate key" in error_str.lower() or "unique constraint" in error_str.lower() or "already exists" in error_str.lower():
            if "evidence_number" in error_str.lower():
                match = re.search(r"evidence_number\)=\(([^)]+)\)", error_str)
                evidence_num = match.group(1) if match else "this evidence number"
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 400,
                        "message": f"Evidence number '{evidence_num}' already exists for another evidence"
                    }
                )
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Duplicate entry. This value already exists in the database"
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": 500,
                    "message": "A database error occurred. Please try again later."
                }
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_suspect_detail: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "An unexpected error occurred while retrieving suspect details. Please try again later."
            }
        )

@router.post("/save-suspect-notes")
async def save_suspect_notes(
    request: SuspectNotesRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect_id = request.suspect_id
        notes = request.notes
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": f"Suspect with ID {suspect_id} not found"
                }
            )
        
        notes_trimmed = notes.strip() if notes else ""
        
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
        evidence_list = []
        if suspect_id is not None:
            evidence_records = db.query(Evidence).filter(Evidence.suspect_id == suspect_id).all()
            if suspect.evidence_number is not None and str(suspect.evidence_number).strip():
                evidence_by_number = db.query(Evidence).filter(
                    Evidence.evidence_number == suspect.evidence_number,
                    Evidence.case_id == suspect.case_id
                ).all()
                evidence_ids = {e.id for e in evidence_records}
                for evidence in evidence_by_number:
                    if evidence.id not in evidence_ids:
                        evidence_records.append(evidence)
            evidence_list = evidence_records
        
        if not evidence_list or len(evidence_list) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Cannot save notes: No evidence found for this suspect. Please create evidence first."
                }
            )
        
        first_evidence = evidence_list[0]
        current_notes = first_evidence.notes if hasattr(first_evidence, 'notes') and first_evidence.notes is not None else {}

        existing_notes = None
        if isinstance(current_notes, dict):
            existing_notes = current_notes.get('suspect_notes')
        elif isinstance(current_notes, str):
            existing_notes = current_notes
        
        if existing_notes is not None and str(existing_notes).strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Notes already exist for this suspect. Use PUT /api/v1/suspects/edit-suspect-notes to update existing notes."
                }
            )
        
        if isinstance(current_notes, dict):
            current_notes['suspect_notes'] = notes_trimmed
        elif isinstance(current_notes, str):
            current_notes = {'suspect_notes': notes_trimmed, 'text': current_notes}
        else:
            current_notes = {'suspect_notes': notes_trimmed}
        
        setattr(first_evidence, 'notes', current_notes)
        db.commit()
        db.refresh(first_evidence)
        
        try:
            case = None
            if suspect.case_id is not None:
                case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case:
                current_status = case.status if case else "Open"
                changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Added notes for suspect {suspect.name}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
        except Exception as e:
                    logger.warning(f"Could not create case log: {str(e)}")
        
        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Suspect notes saved successfully",
                "data": {
                    "suspect_id": suspect_id,
                    "notes": notes_trimmed
                }
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_suspect_detail: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "An unexpected error occurred while retrieving suspect details. Please try again later."
            }
        )

@router.put("/edit-suspect-notes")
async def edit_suspect_notes(
    request: SuspectNotesRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect_id = request.suspect_id
        notes = request.notes
        
        suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
        if not suspect:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "message": f"Suspect with ID {suspect_id} not found"
                }
            )
        
        notes_trimmed = notes.strip() if notes else ""
        
        evidence_list = []
        if suspect_id is not None:
            evidence_records = db.query(Evidence).filter(Evidence.suspect_id == suspect_id).all()
            if suspect.evidence_number is not None and str(suspect.evidence_number).strip():
                evidence_by_number = db.query(Evidence).filter(
                    Evidence.evidence_number == suspect.evidence_number,
                    Evidence.case_id == suspect.case_id
                ).all()
                evidence_ids = {e.id for e in evidence_records}
                for evidence in evidence_by_number:
                    if evidence.id not in evidence_ids:
                        evidence_records.append(evidence)
            evidence_list = evidence_records
        
        if not evidence_list or len(evidence_list) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "Cannot edit notes: No evidence found for this suspect. Please create evidence first."
                }
            )
        
        first_evidence = evidence_list[0]
        current_notes = first_evidence.notes if hasattr(first_evidence, 'notes') and first_evidence.notes is not None else {}

        existing_notes = None
        if isinstance(current_notes, dict):
            existing_notes = current_notes.get('suspect_notes')
        elif isinstance(current_notes, str):
            existing_notes = current_notes
        
        if existing_notes is None or not str(existing_notes).strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "No notes found for this suspect. Use POST /api/v1/suspects/save-suspect-notes to create new notes."
                }
            )
        
        if isinstance(current_notes, dict):
            current_notes['suspect_notes'] = notes_trimmed
        elif isinstance(current_notes, str):
            current_notes = {'suspect_notes': notes_trimmed, 'text': current_notes}
        else:
            current_notes = {'suspect_notes': notes_trimmed}
        
        setattr(first_evidence, 'notes', current_notes)
        db.commit()
        db.refresh(first_evidence)
        
        try:
            case = None
            if suspect.case_id is not None:
                case = db.query(Case).filter(Case.id == suspect.case_id).first()
            if case:
                current_status = case.status if case else "Open"
                changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                case_log = CaseLog(
                    case_id=suspect.case_id,
                    action="Edit",
                    changed_by=f"By: {changed_by}",
                    change_detail=f"Change: Updated notes for suspect {suspect.name}",
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
                "message": "Suspect notes updated successfully",
                "data": {
                    "suspect_id": suspect_id,
                    "notes": notes_trimmed
                }
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_suspect_detail: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "An unexpected error occurred while retrieving suspect details. Please try again later."
            }
        )

