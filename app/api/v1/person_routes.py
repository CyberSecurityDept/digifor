from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from app.evidence_management.models import Evidence
from app.case_management.models import Case, CaseLog
from app.suspect_management.models import Suspect
from app.api.deps import get_database, get_current_user
from app.auth.models import User
from fastapi.responses import JSONResponse
import traceback, os, hashlib

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
        
        if not is_unknown_person:
            if not person_name or not person_name.strip():
                raise HTTPException(status_code=400, detail="person_name is required when is_unknown_person is false")
            if not suspect_status or not suspect_status.strip():
                raise HTTPException(status_code=400, detail="suspect_status is required when is_unknown_person is false")
        
        if evidence_number is not None:
            evidence_number = evidence_number.strip() if isinstance(evidence_number, str) else str(evidence_number).strip()
            if not evidence_number:
                raise HTTPException(status_code=400, detail="evidence_number cannot be empty when provided manually")
        
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
        
        suspect_id_value = None
        if is_unknown_person:
            suspect_dict = {
                "name": "Unknown",
                "case_id": case_id,
                "case_name": case.title if case else None,
                "investigator": investigator_name,
                "status": None,
                "is_unknown": True,
                "evidence_id": evidence_number,
                "evidence_source": evidence_source,
                "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User')
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
                    change_detail=f"Change: Adding person Unknown",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create case log for suspect: {str(e)}")
        else:
            person_name_clean = person_name.strip() if person_name else None
            final_suspect_status = suspect_status if suspect_status else None
            
            suspect_dict = {
                "name": person_name_clean,
                "case_id": case_id,
                "case_name": case.title if case else None,
                "investigator": investigator_name,
                "status": final_suspect_status,
                "is_unknown": False,
                "evidence_id": evidence_number,
                "evidence_source": evidence_source,
                "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User')
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
                print(f"Warning: Could not create case log for suspect: {str(e)}")
        
        if existing_evidence:
            if file_path:
                setattr(existing_evidence, 'file_path', file_path)
                setattr(existing_evidence, 'file_size', file_size)
                setattr(existing_evidence, 'file_hash', file_hash)
                setattr(existing_evidence, 'file_type', file_type)
                setattr(existing_evidence, 'file_extension', file_extension)
            setattr(existing_evidence, 'suspect_id', suspect_id_value)
            db.commit()
            evidence = existing_evidence
        else:
            evidence_dict = {
                "evidence_number": evidence_number,
                "title": evidence_title,
                "description": evidence_summary,
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
                print(f"Warning: Could not create case log for evidence: {str(e)}")
        
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
            "evidence_number": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected server error: {str(e)}"
        )

@router.put("/update-person/{person_id}")
async def update_person(
    person_id: int,
    person_name: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        suspect = db.query(Suspect).filter(Suspect.id == person_id).first()
        if not suspect:
            raise HTTPException(status_code=404, detail=f"Person with ID {person_id} not found")
        if is_unknown_person is not None:
            setattr(suspect, 'is_unknown', is_unknown_person)

            if is_unknown_person:
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
                setattr(suspect, 'name', person_name.strip())
                setattr(suspect, 'status', suspect_status.strip())
        else:
            current_is_unknown = getattr(suspect, 'is_unknown', False)
            if not current_is_unknown:
                if person_name is not None:
                    if not person_name.strip():
                        raise HTTPException(
                            status_code=400,
                            detail="person_name cannot be empty"
                        )
                    setattr(suspect, 'name', person_name.strip())
                if suspect_status is not None:
                    if not suspect_status.strip():
                        raise HTTPException(
                            status_code=400,
                            detail="suspect_status cannot be empty"
                        )
                    setattr(suspect, 'status', suspect_status.strip())
            else:
                pass
        
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
            "evidence_number": suspect.evidence_id,
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected server error: {str(e)}"
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
            print(f"Warning: Could not create case log: {str(e)}")
        
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected server error: {str(e)}"
        )

