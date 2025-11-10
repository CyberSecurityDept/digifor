from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import hashlib
from datetime import datetime, timezone
from app.evidence_management.models import Evidence
from app.case_management.models import Case, CaseLog
from app.suspect_management.models import Suspect
from app.api.deps import get_database, get_current_user
from app.auth.models import User
from fastapi.responses import JSONResponse
import traceback

router = APIRouter(prefix="/persons", tags=["Person Management"])

@router.post("/create-person")
async def create_person(
    case_id: int = Form(...),
    name: str = Form(...),
    is_unknown: bool = Form(False),
    suspect_status: Optional[str] = Form(None),
    custody_stage: Optional[str] = Form(None),
    evidence_id: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    investigator: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        if not created_by:
            created_by = getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User')
        
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        if evidence_id is not None:
            evidence_id = evidence_id.strip() if isinstance(evidence_id, str) else str(evidence_id).strip()
            if not evidence_id:
                raise HTTPException(status_code=400, detail="evidence_id cannot be empty when provided manually")
        
        if not evidence_id and evidence_file:
            from app.evidence_management.models import Evidence
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
            filename = f"evidence_{timestamp}_{evidence_id or 'unknown'}.{file_extension}" if file_extension else f"evidence_{timestamp}_{evidence_id or 'unknown'}"
            file_path = os.path.join(upload_dir, filename)
            
            file_content = await evidence_file.read()
            file_size = len(file_content)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_type = evidence_file.content_type or 'application/octet-stream'
        
        if evidence_id:
            from app.evidence_management.models import Evidence
            existing_evidence = db.query(Evidence).filter(
                Evidence.evidence_number == evidence_id,
                Evidence.case_id == case_id
            ).first()
            
            if not existing_evidence:
                evidence_number = evidence_id
                title = f"Evidence {evidence_id}"
                
                evidence_dict = {
                    "evidence_number": evidence_number,
                    "title": title,
                    "description": evidence_summary,
                    "case_id": case_id,
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "file_type": file_type,
                    "file_extension": file_extension,
                    "collected_by": investigator or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User'),
                    "collected_date": datetime.now(timezone.utc),
                }
                
                evidence = Evidence(**evidence_dict)
                db.add(evidence)
                db.commit()
                db.refresh(evidence)
                
                try:
                    from app.case_management.models import CaseLog
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
            else:
                if file_path and existing_evidence:
                    setattr(existing_evidence, 'file_path', file_path)
                    setattr(existing_evidence, 'file_size', file_size)
                    setattr(existing_evidence, 'file_hash', file_hash)
                    setattr(existing_evidence, 'file_type', file_type)
                    setattr(existing_evidence, 'file_extension', file_extension)
                    db.commit()
        
        # Create Suspect instead of Person
        suspect_dict = {
            "name": name if not is_unknown else "Unknown Person",
            "case_id": case_id,
            "case_name": case.title if case else None,
            "investigator": investigator or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User'),
            "status": suspect_status or "Suspect",
            "is_unknown": is_unknown,
            "custody_stage": custody_stage,
            "evidence_id": evidence_id,
            "evidence_source": evidence_source,
            "evidence_summary": evidence_summary,
            "created_by": created_by
        }
        
        suspect = Suspect(**suspect_dict)
        db.add(suspect)
        db.commit()
        db.refresh(suspect)
        
        # Create case log for adding suspect
        try:
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            
            case_log = CaseLog(
                case_id=case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Adding suspect {name}",
                notes="",
                status=current_status
            )
            db.add(case_log)
            db.commit()
        except Exception as e:
            print(f"Warning: Could not create case log for suspect: {str(e)}")
        
        # Format response
        person_response = {
            "id": suspect.id,
            "name": suspect.name,
            "is_unknown": suspect.is_unknown,
            "suspect_status": suspect.status,
            "custody_stage": suspect.custody_stage,
            "evidence_id": suspect.evidence_id,
            "evidence_source": suspect.evidence_source,
            "evidence_summary": suspect.evidence_summary,
            "investigator": suspect.investigator,
            "case_id": suspect.case_id,
            "created_by": suspect.created_by,
            "created_at": suspect.created_at,
            "updated_at": suspect.updated_at
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

# Note: Other endpoints (get, update, delete) should use suspect endpoints instead
# These endpoints are commented out as Person model has been removed
# Use /api/v1/suspects endpoints for suspect management

# @router.get("/get-person/{person_id}")
# @router.get("/get-persons-by-case/{case_id}")
# @router.put("/update-person/{person_id}")
# @router.delete("/delete-person/{person_id}")
