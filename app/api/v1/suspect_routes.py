from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
import traceback, os, hashlib
from app.api.deps import get_database, get_current_user
from app.suspect_management.service import suspect_service
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate, SuspectResponse, SuspectListResponse
from app.case_management.models import Case, CaseLog
from app.auth.models import User
from fastapi.responses import JSONResponse
from app.evidence_management.models import Evidence

router = APIRouter(prefix="/suspects", tags=["Suspect Management"])

@router.get("/", response_model=SuspectListResponse)
async def get_suspects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by. Valid values: 'created_at', 'id'"),
    sort_order: Optional[str] = Query(None, description="Sort order. Valid values: 'asc' (oldest first), 'desc' (newest first)"),
    db: Session = Depends(get_database)
):
    try:
        suspects, total = suspect_service.get_suspects(db, skip, limit, search, status, sort_by, sort_order)
        
        return SuspectListResponse(
            status=200,
            message="Suspects retrieved successfully",
            data=suspects,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
        )

@router.post("/create-suspect", response_model=SuspectResponse)
async def create_suspect(
    case_id: int = Form(...),
    name: str = Form(...),
    is_unknown: bool = Form(False),
    is_unknown_person: Optional[bool] = Form(None),
    status: Optional[str] = Form(None),
    evidence_id: Optional[str] = Form(None),
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
        
        if evidence_id is not None:
            evidence_id = evidence_id.strip() if isinstance(evidence_id, str) else str(evidence_id).strip()
            if not evidence_id:
                raise HTTPException(status_code=400, detail="evidence_id cannot be empty when provided manually")
        
        if not evidence_id and evidence_file:
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

        investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        evidence_number = None
        if evidence_id:
            existing_evidence = db.query(Evidence).filter(
                Evidence.evidence_number == evidence_id,
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
                evidence_number = evidence_id
                if file_path:
                    setattr(existing_evidence, 'file_path', file_path)
                    setattr(existing_evidence, 'file_size', file_size)
                    setattr(existing_evidence, 'file_hash', file_hash)
                    setattr(existing_evidence, 'file_type', file_type)
                    setattr(existing_evidence, 'file_extension', file_extension)
                    db.commit()
            else:
                if evidence_file:
                    evidence_number = evidence_id
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
                            change_detail=f"Change: Adding evidence {evidence_id}",
                            notes="",
                            status=current_status
                        )
                        db.add(case_log)
                        db.commit()
                    except Exception as e:
                        print(f"Warning: Could not create case log for evidence: {str(e)}")
                else:
                    evidence_number = evidence_id
        
        # Use is_unknown_person if provided, otherwise fallback to is_unknown for backward compatibility
        is_unknown_flag = is_unknown_person if is_unknown_person is not None else is_unknown
        
        # Jika is_unknown_person = true, suspect_status harus null
        final_status = None if is_unknown_flag else status
        
        suspect_dict = {
            "name": name if not is_unknown_flag else "Unknown Person",
            "case_id": case_id,
            "case_name": case_name or case.title if case else None,
            "investigator": investigator_name,
            "status": final_status,
            "is_unknown": is_unknown_flag,
            "evidence_id": evidence_number,
            "evidence_source": evidence_source,
            "evidence_summary": evidence_summary,
            "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User'),
        }
        
        
        suspect_data = SuspectCreate(**suspect_dict)
        suspect = suspect_service.create_suspect(db, suspect_data)
        
        try:
            current_status = case.status if case else "Open"
            changed_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            
            case_log = CaseLog(
                case_id=case_id,
                action="Edit",
                changed_by=f"By: {changed_by}",
                change_detail=f"Change: Adding person {name}",
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
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.get_suspect(db, suspect_id)
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

@router.put("/update-suspect/{suspect_id}", response_model=SuspectResponse)
async def update_suspect(
    suspect_id: int,
    suspect_data: SuspectUpdate,
    db: Session = Depends(get_database)
):
    try:
        suspect = suspect_service.update_suspect(db, suspect_id, suspect_data)
        return SuspectResponse(
            status=200,
            message="Suspect updated successfully",
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

@router.delete("/delete-suspect/{suspect_id}")
async def delete_suspect(
    suspect_id: int,
    db: Session = Depends(get_database)
):
    try:
        success = suspect_service.delete_suspect(db, suspect_id)
        if success:
            return {"status": 200, "message": "Suspect deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Suspect with ID {suspect_id} not found"
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
