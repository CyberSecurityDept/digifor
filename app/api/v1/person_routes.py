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
    person_name: str = Form(...),
    suspect_status: Optional[str] = Form(None),
    evidence_id: Optional[str] = Form(None),
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
        
        if evidence_id is not None:
            evidence_id = evidence_id.strip() if isinstance(evidence_id, str) else str(evidence_id).strip()
            if not evidence_id:
                raise HTTPException(status_code=400, detail="evidence_id cannot be empty when provided manually")
        
        if not evidence_id:
            if not evidence_file:
                raise HTTPException(status_code=400, detail="evidence_file atau evidence_id harus disediakan untuk create person")
            date_str = datetime.now().strftime("%Y%m%d")
            evidence_count = db.query(Evidence).filter(Evidence.case_id == case_id).count()
            evidence_id = f"EVID-{case_id}-{date_str}-{evidence_count + 1:04d}"
            
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
            filename = f"evidence_{timestamp}_{evidence_id}.{file_extension}" if file_extension else f"evidence_{timestamp}_{evidence_id}"
            file_path = os.path.join(upload_dir, filename)
            
            file_content = await evidence_file.read()
            file_size = len(file_content)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_type = evidence_file.content_type or 'application/octet-stream'
        
        evidence_number = evidence_id
        evidence_title = case.title if case else evidence_number
        
        investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        existing_evidence = db.query(Evidence).filter(
            Evidence.evidence_number == evidence_number,
            Evidence.case_id == case_id
        ).first()
        
        # Jika evidence_id ada dan evidence_summary tidak diisi, ambil dari evidence yang ada
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
                db.commit()
        else:
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
                    change_detail=f"Change: Adding evidence {evidence_id}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create case log for evidence: {str(e)}")
        
        final_suspect_status = None if is_unknown_person else suspect_status
        
        suspect_dict = {
            "name": "Unknown Person" if is_unknown_person else person_name,
            "case_id": case_id,
            "case_name": case.title if case else None,
            "investigator": investigator_name,
            "status": final_suspect_status,
            "is_unknown": is_unknown_person,
            "evidence_id": evidence_number,
            "evidence_source": evidence_source,
            "evidence_summary": evidence_summary,
            "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User')
        }
        
        suspect = Suspect(**suspect_dict)
        db.add(suspect)
        db.commit()
        db.refresh(suspect)
        
        try:
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            
            case_log = CaseLog(
                case_id=case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Adding person {person_name}",
                notes="",
                status=current_status
            )
            db.add(case_log)
            db.commit()
        except Exception as e:
            print(f"Warning: Could not create case log for suspect: {str(e)}")
    
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
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
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
        
        if person_name is not None:
            if is_unknown_person:
                setattr(suspect, 'name', "Unknown Person")
            else:
                setattr(suspect, 'name', person_name)
        
        if is_unknown_person is not None:
            setattr(suspect, 'is_unknown', is_unknown_person)
            if is_unknown_person:
                setattr(suspect, 'name', "Unknown Person")
                # Jika is_unknown_person = true, suspect_status harus null
                setattr(suspect, 'status', None)
            else:
                # Jika is_unknown_person = false, update status sesuai input user
                if suspect_status is not None:
                    setattr(suspect, 'status', suspect_status)
        else:
            # Jika is_unknown_person tidak diubah, update status sesuai input user
            if suspect_status is not None:
                setattr(suspect, 'status', suspect_status)
        
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
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
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
                change_detail=f"Change: Deleting suspect {suspect_name}",
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

