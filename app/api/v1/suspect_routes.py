from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
import os
import hashlib
import traceback
from app.api.deps import get_database, get_current_user
from app.suspect_management.service import suspect_service
from app.suspect_management.schemas import SuspectCreate, SuspectUpdate, SuspectResponse, SuspectListResponse, SuspectNotesRequest
from app.case_management.models import Case, CaseLog
from app.auth.models import User
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/suspects", tags=["Suspect Management"])

@router.get("/", response_model=SuspectListResponse)
async def get_suspects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        suspects = suspect_service.get_suspects(db, skip, limit, search, status)
        total = len(suspects)
        
        return SuspectListResponse(
            status=200,
            message="Suspects retrieved successfully",
            data=suspects,
            total=total,
            page=skip // limit + 1,
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
    status: Optional[str] = Form(None),
    evidence_id: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    investigator: Optional[str] = Form(None),
    case_name: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    place_of_birth: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    height: Optional[int] = Form(None),
    weight: Optional[int] = Form(None),
    eye_color: Optional[str] = Form(None),
    hair_color: Optional[str] = Form(None),
    distinguishing_marks: Optional[str] = Form(None),
    has_criminal_record: Optional[bool] = Form(False),
    criminal_record_details: Optional[str] = Form(None),
    risk_level: Optional[str] = Form("medium"),
    risk_assessment_notes: Optional[str] = Form(None),
    is_confidential: Optional[bool] = Form(False),
    notes: Optional[str] = Form(None),
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
        
        suspect_dict = {
            "name": name if not is_unknown else "Unknown Person",
            "case_id": case_id,
            "case_name": case_name or case.title if case else None,
            "investigator": investigator or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User'),
            "status": status,
            "is_unknown": is_unknown,
            "custody_stage": None,
            "evidence_id": evidence_id,
            "evidence_source": evidence_source,
            "evidence_summary": evidence_summary,
            "created_by": getattr(current_user, 'email', '') or getattr(current_user, 'fullname', 'Unknown User'),
        }
        
        if date_of_birth:
            try:
                suspect_dict["date_of_birth"] = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            except:
                pass
        
        if place_of_birth:
            suspect_dict["place_of_birth"] = place_of_birth
        if nationality:
            suspect_dict["nationality"] = nationality
        if phone_number:
            suspect_dict["phone_number"] = phone_number
        if email:
            suspect_dict["email"] = email
        if address:
            suspect_dict["address"] = address
        if height:
            suspect_dict["height"] = height
        if weight:
            suspect_dict["weight"] = weight
        if eye_color:
            suspect_dict["eye_color"] = eye_color
        if hair_color:
            suspect_dict["hair_color"] = hair_color
        if distinguishing_marks:
            suspect_dict["distinguishing_marks"] = distinguishing_marks
        if has_criminal_record is not None:
            suspect_dict["has_criminal_record"] = has_criminal_record
        if criminal_record_details:
            suspect_dict["criminal_record_details"] = criminal_record_details
        if risk_level:
            suspect_dict["risk_level"] = risk_level
        if risk_assessment_notes:
            suspect_dict["risk_assessment_notes"] = risk_assessment_notes
        if is_confidential is not None:
            suspect_dict["is_confidential"] = is_confidential
        if notes:
            suspect_dict["notes"] = notes
        
        suspect_data = SuspectCreate(**suspect_dict)
        suspect = suspect_service.create_suspect(db, suspect_data)
        
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

@router.post("/save-notes")
async def save_suspect_notes(
    request: SuspectNotesRequest,
    db: Session = Depends(get_database)
):
    try:
        result = suspect_service.save_suspect_notes(db, request.suspect_id, request.notes)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Suspect notes saved successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": 400,
                "message": str(e),
                "data": None
            },
            status_code=400
        )
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Suspect with ID {request.suspect_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": f"Failed to save suspect notes: {str(e)}",
                    "data": None
                },
                status_code=500
            )

@router.put("/edit-notes")
async def edit_suspect_notes(
    request: SuspectNotesRequest,
    db: Session = Depends(get_database)
):
    try:
        result = suspect_service.edit_suspect_notes(db, request.suspect_id, request.notes)
        return JSONResponse(
            content={
                "status": 200,
                "message": "Suspect notes updated successfully",
                "data": result
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": 400,
                "message": str(e),
                "data": None
            },
            status_code=400
        )
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Suspect with ID {request.suspect_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": f"Failed to edit suspect notes: {str(e)}",
                    "data": None
                },
                status_code=500
            )