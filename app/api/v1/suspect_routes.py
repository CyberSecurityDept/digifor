from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime, timezone
import traceback, os, hashlib, re
from app.api.deps import get_database, get_current_user
from app.suspect_management.service import suspect_service
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate, SuspectResponse, SuspectListResponse
from app.case_management.models import Case, CaseLog
from app.auth.models import User
from fastapi.responses import JSONResponse
from app.evidence_management.models import Evidence
from app.suspect_management.models import Suspect

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
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.get("/get-suspect-summary")
async def get_suspect_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect_query = db.query(Suspect)
        evidence_query = db.query(Evidence)
        
        total_person = suspect_query.count()
        total_evidence = evidence_query.count()
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
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
            if not final_status or not final_status.strip():
                raise HTTPException(
                    status_code=400,
                    detail="suspect_status is required when is_unknown_person is false"
                )
        
        if evidence_number is not None:
            evidence_number = evidence_number.strip() if isinstance(evidence_number, str) else str(evidence_number).strip()
            if not evidence_number:
                raise HTTPException(status_code=400, detail="evidence_number cannot be empty when provided manually")
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
            "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User'),
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
            print(f"Warning: Could not create case log for suspect: {str(e)}")
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.get("/get-suspect-by-id/{suspect_id}", response_model=SuspectResponse)
async def get_suspect(
    suspect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.get_suspect(db, suspect_id, current_user)
        return SuspectResponse(
            status=200,
            message="Suspect retrieved successfully",
            data=suspect
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected server error, please try again later"
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
        
        suspect_detail = {
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
                "message": "Suspect detail retrieved successfully",
                "data": suspect_detail
            }
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": f"Unexpected server error: {str(e)}"
            }
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
            print(f"Warning: Could not create case log: {str(e)}")
        
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
                    "message": f"Database error: {error_str}"
                }
            )
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": f"Unexpected server error: {str(e)}"
            }
        )

