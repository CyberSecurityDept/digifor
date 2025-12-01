from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Type
from datetime import datetime, timezone, timedelta
import uuid
from app.api.deps import get_database, get_current_user
from app.auth.models import User
from app.evidence_management.schemas import (
    CustodyLogCreate, CustodyLogUpdate, CustodyLogResponse, 
    CustodyLogListResponse, CustodyChainResponse,
    CustodyReportCreate, CustodyReportListResponse,
    EvidenceNotesRequest
)
from fastapi.responses import JSONResponse, FileResponse
from app.evidence_management.models import Evidence, CustodyLog, CustodyReport
from app.evidence_management.custody_service import CustodyService
from app.case_management.models import CaseLog, Case, Agency
from app.case_management.pdf_export import generate_evidence_detail_pdf
from app.core.config import settings
import traceback, os, hashlib, re
from app.suspect_management.models import Suspect
WIB = timezone(timedelta(hours=7))

def get_wib_now():
    return datetime.now(WIB)

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

router = APIRouter(prefix="/evidence", tags=["Evidence Management"])

@router.get("/get-evidence-list")
async def get_evidence_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by. Valid values: 'created_at', 'id'"),
    sort_order: Optional[str] = Query(None, description="Sort order. Valid values: 'asc' (oldest first), 'desc' (newest first)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        query = db.query(Evidence).options(joinedload(Evidence.case))

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Evidence.evidence_number.ilike(search_pattern),
                    Evidence.title.ilike(search_pattern),
                    Evidence.description.ilike(search_pattern)
                )
            )
        
        if sort_by == "created_at":
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(Evidence.created_at.asc())
            else:
                query = query.order_by(Evidence.created_at.desc())
        else:
            query = query.order_by(Evidence.id.desc())
        
        total = query.count()
        evidence_list = query.offset(skip).limit(limit).all()
        evidence_data = []
        for evidence in evidence_list:
            created_at_value = getattr(evidence, 'created_at', None)
            created_at_str = None
            if created_at_value:
                if isinstance(created_at_value, datetime):
                    created_at_str = created_at_value.strftime("%d/%m/%Y")
                else:
                    try:
                        created_at_dt = datetime.fromisoformat(str(created_at_value).replace('Z', '+00:00'))
                        created_at_str = created_at_dt.strftime("%d/%m/%Y")
                    except:
                        created_at_str = str(created_at_value)
            
            case_title = None
            investigator_name = None
            agency_name = None
            
            if evidence.case:
                case_title = evidence.case.title
                investigator_name = evidence.case.main_investigator
                
                if evidence.case.agency_id:
                    agency = db.query(Agency).filter(Agency.id == evidence.case.agency_id).first()
                    if agency:
                        agency_name = agency.name
            
            if not investigator_name:
                investigator_name = getattr(evidence, 'investigator', None) or investigator_name
            
            evidence_data.append({
                "id": evidence.id,
                "case_id": evidence.case_id,
                "evidence_number": evidence.evidence_number,
                "title": case_title,
                "investigator": investigator_name,
                "agency": agency_name,
                "created_at": created_at_str
            })
        
        return JSONResponse(
            status_code=200,
            content={
        "status": 200,
        "message": "Evidence list retrieved successfully",
                "data": evidence_data,
                "total": total,
                "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit
    }
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.get("/get-evidence-summary")
async def get_evidence_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        case_query = db.query(Case)
        evidence_query = db.query(Evidence)
        
        total_cases = case_query.count()
        total_evidence = evidence_query.count()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Evidence summary retrieved successfully",
                "data": {
                    "total_case": total_cases,
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

@router.post("/create-evidence")
async def create_evidence(
    case_id: int = Form(...),
    evidence_number: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    investigator: str = Form(...),
    person_name: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(False),
    suspect_id: Optional[int] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        if is_unknown_person:
            pass
        elif not is_unknown_person:
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
        
        if evidence_number is not None:
            evidence_number = evidence_number.strip() if isinstance(evidence_number, str) else str(evidence_number).strip()
            if not evidence_number:
                raise HTTPException(status_code=400, detail="evidence_number cannot be empty when provided manually")
            
            existing_evidence = db.query(Evidence).filter(
                Evidence.evidence_number == evidence_number
            ).first()
            
            if existing_evidence:
                raise HTTPException(
                    status_code=400,
                    detail=f"Evidence number '{evidence_number}' already exists"
                )
        
        if not evidence_number:
            date_str = datetime.now().strftime("%Y%m%d")
            evidence_count = db.query(Evidence).filter(Evidence.case_id == case_id).count()
            evidence_number = f"EVID-{case_id}-{date_str}-{evidence_count + 1:04d}"
        evidence_title = case.title if case else evidence_number
        
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
        
        source_value = source.strip() if source and isinstance(source, str) and source.strip() else None
        
        evidence_dict = {
            "evidence_number": evidence_number,
            "title": evidence_title,
            "description": evidence_summary,
            "source": source_value,
            "evidence_type": None,
            "case_id": case_id,
            "file_path": file_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "file_type": file_type,
            "file_extension": file_extension,
            "investigator": investigator,
            "collected_date": datetime.now(timezone.utc),
        }
        
        suspect_id_value = None
        
        if suspect_id is not None:
            selected_suspect = db.query(Suspect).filter(
                Suspect.id == suspect_id,
                Suspect.case_id == case_id
            ).first()
            
            if not selected_suspect:
                raise HTTPException(
                    status_code=404,
                    detail=f"Suspect with ID {suspect_id} not found for this case"
                )
            
            if person_name and person_name.strip():
                setattr(selected_suspect, 'name', person_name.strip())
                setattr(selected_suspect, 'is_unknown', False)
            
            if suspect_status is not None:
                normalized_status = normalize_suspect_status(suspect_status)
                if normalized_status is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                    )
                setattr(selected_suspect, 'status', normalized_status)
            
            db.commit()
            db.refresh(selected_suspect)
            suspect_id_value = selected_suspect.id
        elif is_unknown_person:
            existing_unknown_suspect = db.query(Suspect).filter(
                Suspect.case_id == case_id,
                Suspect.name == "Unknown",
                Suspect.is_unknown == True
            ).order_by(Suspect.id.desc()).first()
            
            if existing_unknown_suspect:
                suspect_id_value = existing_unknown_suspect.id
            else:
                investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                new_suspect = Suspect(
                    name="Unknown",
                    case_id=case_id,
                    case_name=case.title if case else None,
                    evidence_number=evidence_number,
                    evidence_source=source,
                    investigator=investigator_name,
                    status=None,
                    is_unknown=True,
                    created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                )
                db.add(new_suspect)
                db.commit()
                db.refresh(new_suspect)
                suspect_id_value = new_suspect.id
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
                    print(f"Warning: Could not create case log for auto-created suspect: {str(e)}")
        elif person_name and person_name.strip():
            person_name_clean = person_name.strip()
            existing_suspect = db.query(Suspect).filter(
                Suspect.case_id == case_id,
                Suspect.name == person_name_clean
            ).first()
            
            if existing_suspect:
                suspect_id_value = existing_suspect.id
            else:
                investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                new_suspect = Suspect(
                    name=person_name_clean,
                    case_id=case_id,
                    case_name=case.title if case else None,
                    evidence_number=evidence_number,
                    evidence_source=source,
                    investigator=investigator_name,
                    status=None,
                    is_unknown=False,
                    created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                )
                db.add(new_suspect)
                db.commit()
                db.refresh(new_suspect)
                suspect_id_value = new_suspect.id
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
                    print(f"Warning: Could not create case log for auto-created suspect: {str(e)}")
        
        evidence_dict["suspect_id"] = suspect_id_value
        
        try:
            evidence = Evidence(**evidence_dict)
            db.add(evidence)
            db.commit()
            db.refresh(evidence)
        except IntegrityError as e:
            db.rollback()
            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "duplicate key" in error_str.lower() or "unique constraint" in error_str.lower() or "already exists" in error_str.lower():
                if "evidence_number" in error_str.lower():
                    match = re.search(r"evidence_number\)=\(([^)]+)\)", error_str)
                    evidence_num = match.group(1) if match else evidence_number
                    raise HTTPException(
                        status_code=400,
                        detail=f"Evidence number '{evidence_num}' already exists"
                    )
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate entry. This value already exists in the database"
                )
            raise
        
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
        
        case_title = case.title if case else None
        agency_name = None
        if case:
            case_agency_id = getattr(case, 'agency_id', None)
            if case_agency_id:
                agency = db.query(Agency).filter(Agency.id == case_agency_id).first()
                if agency:
                    agency_name = agency.name
        
        created_at_value = getattr(evidence, 'created_at', None)
        created_at_str = None
        if created_at_value:
            if isinstance(created_at_value, datetime):
                created_at_str = created_at_value.strftime("%d/%m/%Y")
            else:
                try:
                    created_at_dt = datetime.fromisoformat(str(created_at_value).replace('Z', '+00:00'))
                    created_at_str = created_at_dt.strftime("%d/%m/%Y")
                except:
                    created_at_str = str(created_at_value)
        
        investigator_name = investigator or (case.main_investigator if case else None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        response_data = {
            "id": evidence.id,
            "case_id": evidence.case_id,
            "evidence_number": evidence_number,
            "source": source,
            "file_path": evidence.file_path,
            "description": evidence.description,
            "title": case_title,
            "investigator": investigator_name,
            "agency": agency_name,
            "person_name": person_name if person_name and person_name.strip() else None,
            "created_at": created_at_str
        }
        
        return JSONResponse(
            status_code=201,
            content={
            "status": 201,
            "message": "Evidence created successfully",
                "data": response_data
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

@router.get("/{evidence_id}/detail")
async def get_evidence_detail(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    evidence = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id)
        .first()
    )

    if not evidence:
        return {
            "status": 404,
            "message": f"Evidence with ID {evidence_id} not found",
            "data": None
        }

    case_name = evidence.case.title if evidence.case else None
    case_id = evidence.case.case_number if evidence.case else None

    suspect_name = None
    suspect_status = None
    suspect_id = None
    if evidence.suspect_id:
        suspect = db.query(Suspect).filter(Suspect.id == evidence.suspect_id).first()
        if suspect:
            suspect_name = suspect.name
            suspect_status = suspect.status
            suspect_id = suspect.id

    evidence_source = getattr(evidence, 'source', None)  

    custody_logs_query = db.query(CustodyLog).filter(
        CustodyLog.evidence_id == evidence_id
    ).order_by(CustodyLog.id.asc()).all()
    
    custody_logs = [
        {
            "id": log.id,
            "custody_type": log.custody_type,
            "notes": log.notes,
            "created_by": log.created_by,
            "created_at": log.created_at
        }
        for log in custody_logs_query
    ]

    custody_reports_query = db.query(CustodyReport).filter(
        CustodyReport.evidence_id == evidence_id
    ).order_by(CustodyReport.id.asc()).all()
    
    custody_reports = [
        {
            "id": rpt.id,
            "custody_type": rpt.custody_type,
            "investigator": rpt.investigator,
            "location": rpt.location,
            "notes": rpt.notes,
            "details": rpt.details,
            "evidence_source": rpt.evidence_source,
            "evidence_type": rpt.evidence_type,
            "evidence_detail": rpt.evidence_detail,
            "created_at": rpt.created_at,
            "updated_at": rpt.updated_at,
        }
        for rpt in custody_reports_query
    ]

    data = {
        "id": evidence.id,
        "evidence_number": evidence.evidence_number,
        "title": evidence.title,
        "file_path": evidence.file_path,
        "description": evidence.description,
        "suspect_name": suspect_name,
        "suspect_status": suspect_status,
        "suspect_id": suspect_id,
        "case_name": case_name,
        "case_id": case_id,
        "source": evidence_source,
        "evidence_type": getattr(evidence, 'evidence_type', None),
        "investigator": evidence.investigator,
        "notes": evidence.notes,
        "created_at": evidence.created_at,
        "updated_at": evidence.updated_at,
        "custody_logs": custody_logs,
        "custody_reports": custody_reports
    }
    
    return {
        "status": 200,
        "message": "Success",
        "data": data
    }

@router.get("/export-evidence-detail-pdf/{evidence_id}")
async def export_evidence_detail_pdf(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        evidence = (
            db.query(Evidence)
            .options(joinedload(Evidence.case))
            .filter(Evidence.id == evidence_id)
            .first()
        )

        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence with ID {evidence_id} not found"
            )

        case = evidence.case
        if not case:
            raise HTTPException(
                status_code=404,
                detail=f"Case not found for evidence {evidence_id}"
            )

        suspect = None
        if getattr(evidence, 'suspect_id', None) is not None:
            suspect = db.query(Suspect).filter(Suspect.id == evidence.suspect_id).first()

        custody_reports = db.query(CustodyReport).filter(
            CustodyReport.evidence_id == evidence_id
        ).order_by(CustodyReport.created_at.asc()).all()

        evidence_type_from_custody = None
        evidence_detail_from_custody = None
        if custody_reports:
            for report in custody_reports:
                evidence_type_value = getattr(report, 'evidence_type', None)
                evidence_detail_value = getattr(report, 'evidence_detail', None)
                if evidence_type_value:
                    evidence_type_from_custody = evidence_type_value
                if evidence_detail_value:
                    evidence_detail_from_custody = evidence_detail_value
                
                if evidence_type_from_custody and evidence_detail_from_custody:
                    break

        case_created_date = "N/A"
        if case.created_at:
            try:
                if isinstance(case.created_at, datetime):
                    case_created_date = case.created_at.strftime("%d/%m/%Y")
                else:
                    case_created_date = str(case.created_at)
            except (AttributeError, TypeError):
                case_created_date = "N/A"

        custody_reports_data = []
        for report in custody_reports:
            created_by_value = report.created_by
            user_fullname = created_by_value
            
            if created_by_value:
                user = db.query(User).filter(User.email == created_by_value).first()
                if not user:
                    try:
                        user_id = int(created_by_value)
                        user = db.query(User).filter(User.id == user_id).first()
                    except (ValueError, TypeError):
                        pass
                
                if user and hasattr(user, 'fullname') and user.fullname:
                    user_fullname = user.fullname
            
            details_value = report.details if report.details is not None else ({} if report.custody_type != "acquisition" else [])
            
            custody_reports_data.append({
                "id": report.id,
                "custody_type": report.custody_type,
                "created_by": user_fullname,
                "location": report.location,
                "notes": report.notes,
                "details": details_value,
                "evidence_source": report.evidence_source,
                "evidence_type": report.evidence_type,
                "evidence_detail": report.evidence_detail,
                "created_at": report.created_at.isoformat() if getattr(report, 'created_at', None) is not None else None,
                "updated_at": report.updated_at.isoformat() if getattr(report, 'updated_at', None) is not None else None,
            })

        evidence_data = {
            "evidence": {
                "id": evidence.id,
                "evidence_number": evidence.evidence_number,
                "title": evidence.title,
                "description": evidence.description or "No description available",
                "investigator": evidence.investigator or "N/A",
                "source": getattr(evidence, 'source', None),
                "evidence_type": evidence_type_from_custody or getattr(evidence, 'evidence_type', None),
                "evidence_detail": evidence_detail_from_custody or getattr(evidence, 'evidence_detail', None),
                "file_path": evidence.file_path,
                "file_size": evidence.file_size,
            },
            "case": {
                "id": case.id,
                "title": case.title,
                "case_number": getattr(case, 'case_number', None) or str(case.id),
                "case_officer": getattr(case, 'case_officer', None) or evidence.investigator or "N/A",
                "created_date": case_created_date,
            },
            "suspect": {
                "name": suspect.name if suspect else "N/A",
            },
            "custody_reports": custody_reports_data
        }

        os.makedirs(settings.REPORTS_DIR, exist_ok=True)
        pdf_filename = f"evidence_detail_{evidence_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)

        generate_evidence_detail_pdf(evidence_data, pdf_path)

        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PDF file"
            )

        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export evidence detail PDF: {str(e)}"
        )

def _handle_suspect_id_update(evidence, suspect_id, current_case_id, person_name, suspect_status, db):
    selected_suspect = db.query(Suspect).filter(
        Suspect.id == suspect_id,
        Suspect.case_id == current_case_id
    ).first()
    
    if not selected_suspect:
        raise HTTPException(
            status_code=404,
            detail=f"Suspect with ID {suspect_id} not found for this case"
        )
    
    if person_name and person_name.strip():
        setattr(selected_suspect, 'name', person_name.strip())
        setattr(selected_suspect, 'is_unknown', False)
    
    if suspect_status is not None:
        normalized_status = normalize_suspect_status(suspect_status)
        if normalized_status is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
            )
        setattr(selected_suspect, 'status', normalized_status)
    
    setattr(evidence, 'suspect_id', selected_suspect.id)

def _handle_unknown_person_update(evidence, current_case_id, current_user, db):
    current_suspect_id = getattr(evidence, 'suspect_id', None)
    if current_suspect_id:
        current_suspect = db.query(Suspect).filter(Suspect.id == current_suspect_id).first()
        if current_suspect:
            setattr(current_suspect, 'name', "Unknown")
            setattr(current_suspect, 'is_unknown', True)
            setattr(current_suspect, 'status', None)
    else:
        existing_unknown_suspect = db.query(Suspect).filter(
            Suspect.case_id == current_case_id,
            Suspect.name == "Unknown",
            Suspect.is_unknown == True
        ).order_by(Suspect.id.desc()).first()
        
        if existing_unknown_suspect:
            setattr(evidence, 'suspect_id', existing_unknown_suspect.id)
        else:
            case = db.query(Case).filter(Case.id == current_case_id).first()
            investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            new_suspect = Suspect(
                name="Unknown",
                case_id=current_case_id,
                case_name=case.title if case else None,
                evidence_number=evidence.evidence_number,
                evidence_source=evidence.source,
                investigator=investigator_name,
                status=None,
                is_unknown=True,
                created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            )
            db.add(new_suspect)
            db.flush()
            setattr(evidence, 'suspect_id', new_suspect.id)

def _handle_known_person_update(evidence, current_case_id, person_name, suspect_status, current_user, db):
    if not person_name or not person_name.strip():
        raise HTTPException(
            status_code=400,
            detail="person_name is required when is_unknown_person is false"
        )
    
    person_name_clean = person_name.strip()
    current_suspect_id = getattr(evidence, 'suspect_id', None)
    
    if current_suspect_id:
        current_suspect = db.query(Suspect).filter(Suspect.id == current_suspect_id).first()
        if current_suspect:
            setattr(current_suspect, 'name', person_name_clean)
            setattr(current_suspect, 'is_unknown', False)
            if suspect_status is not None:
                normalized_status = normalize_suspect_status(suspect_status)
                if normalized_status is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                    )
                setattr(current_suspect, 'status', normalized_status)
            else:
                setattr(current_suspect, 'status', None)
    else:
        existing_suspect = db.query(Suspect).filter(
            Suspect.case_id == current_case_id,
            Suspect.name == person_name_clean
        ).first()
        
        if existing_suspect:
            if suspect_status is not None:
                normalized_status = normalize_suspect_status(suspect_status)
                if normalized_status is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                    )
                setattr(existing_suspect, 'status', normalized_status)
            setattr(evidence, 'suspect_id', existing_suspect.id)
        else:
            case = db.query(Case).filter(Case.id == current_case_id).first()
            investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            new_suspect = Suspect(
                name=person_name_clean,
                case_id=current_case_id,
                case_name=case.title if case else None,
                evidence_number=evidence.evidence_number,
                evidence_source=evidence.source,
                investigator=investigator_name,
                status=normalize_suspect_status(suspect_status) if suspect_status else None,
                is_unknown=False,
                created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
            )
            db.add(new_suspect)
            db.flush()
            setattr(evidence, 'suspect_id', new_suspect.id)

def _handle_person_name_update(evidence, current_case_id, person_name, suspect_status, current_user, db):
    person_name_clean = person_name.strip()
    existing_suspect = db.query(Suspect).filter(
        Suspect.case_id == current_case_id,
        Suspect.name == person_name_clean
    ).first()
    
    if existing_suspect:
        if suspect_status is not None:
            normalized_status = normalize_suspect_status(suspect_status)
            if normalized_status is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid suspect_status value: '{suspect_status}'. Valid values are: {', '.join(VALID_SUSPECT_STATUSES)}"
                )
            setattr(existing_suspect, 'status', normalized_status)
        setattr(evidence, 'suspect_id', existing_suspect.id)
    else:
        case = db.query(Case).filter(Case.id == current_case_id).first()
        investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        new_suspect = Suspect(
            name=person_name_clean,
            case_id=current_case_id,
            case_name=case.title if case else None,
            evidence_number=evidence.evidence_number,
            evidence_source=evidence.source,
            investigator=investigator_name,
            status=normalize_suspect_status(suspect_status) if suspect_status else None,
            is_unknown=False,
            created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        )
        db.add(new_suspect)
        setattr(evidence, 'suspect_id', new_suspect.id)

@router.put("/update-evidence/{evidence_id}")
async def update_evidence(
    evidence_id: int,
    case_id: Optional[int] = Form(None),
    evidence_number: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    investigator: Optional[str] = Form(None),
    person_name: Optional[str] = Form(None),
    suspect_status: Optional[str] = Form(None),
    is_unknown_person: Optional[bool] = Form(None),
    suspect_id: Optional[int] = Form(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence with ID {evidence_id} not found")
    
        if case_id is not None:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
            setattr(evidence, 'case_id', case_id)
        
        if evidence_number is not None:
            evidence_number = evidence_number.strip() if isinstance(evidence_number, str) else str(evidence_number).strip()
            if not evidence_number:
                raise HTTPException(status_code=400, detail="evidence_number cannot be empty when provided manually")
            
            current_evidence_number = getattr(evidence, 'evidence_number', None)
            
            if current_evidence_number != evidence_number:
                existing_evidence = db.query(Evidence).filter(
                    Evidence.evidence_number == evidence_number,
                    Evidence.id != evidence_id
                ).first()
                
                if existing_evidence:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Evidence number '{evidence_number}' already exists for another evidence (ID: {existing_evidence.id})"
                    )
                else:
                    setattr(evidence, 'evidence_number', evidence_number)
        
        if type is not None:
            type_name = type.strip()
            if type_name:
                setattr(evidence, 'evidence_type', type_name)
        
        if source is not None:
            setattr(evidence, 'source', source)
        
        if evidence_summary is not None:
            setattr(evidence, 'description', evidence_summary)
        
        if investigator is not None:
            setattr(evidence, 'investigator', investigator)
        
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
            evidence_num = evidence.evidence_number or str(evidence_id)
            filename = f"evidence_{timestamp}_{evidence_num}.{file_extension}" if file_extension else f"evidence_{timestamp}_{evidence_num}"
            file_path = os.path.join(upload_dir, filename)
            file_content = await evidence_file.read()
            file_size = len(file_content)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_type = evidence_file.content_type or 'application/octet-stream'
            
            setattr(evidence, 'file_path', file_path)
            setattr(evidence, 'file_size', file_size)
            setattr(evidence, 'file_hash', file_hash)
            setattr(evidence, 'file_type', file_type)
            setattr(evidence, 'file_extension', file_extension)
        
        current_case_id = evidence.case_id
        
        is_unknown_person_bool = None
        if is_unknown_person is not None:
            if isinstance(is_unknown_person, str):
                is_unknown_person_bool = is_unknown_person.lower() in ('true', '1', 'yes')
            else:
                is_unknown_person_bool = bool(is_unknown_person)
        
        if suspect_id is not None:
            _handle_suspect_id_update(evidence, suspect_id, current_case_id, person_name, suspect_status, db)
        elif is_unknown_person_bool is not None:
            if is_unknown_person_bool:
                _handle_unknown_person_update(evidence, current_case_id, current_user, db)
            else:
                _handle_known_person_update(evidence, current_case_id, person_name, suspect_status, current_user, db)
        elif person_name and person_name.strip():
            _handle_person_name_update(evidence, current_case_id, person_name, suspect_status, current_user, db)
        
        db.commit()
        db.refresh(evidence)
        
        db.expire_all()
        
        case = db.query(Case).filter(Case.id == evidence.case_id).first()
        case_title = case.title if case else None
        agency_name = None
        if case:
            case_agency_id = getattr(case, 'agency_id', None)
            if case_agency_id:
                agency = db.query(Agency).filter(Agency.id == case_agency_id).first()
                if agency:
                    agency_name = agency.name
        
        updated_at_value = getattr(evidence, 'updated_at', None)
        updated_at_str = None
        if updated_at_value:
            if isinstance(updated_at_value, datetime):
                updated_at_str = updated_at_value.strftime("%d/%m/%Y")
            else:
                try:
                    updated_at_dt = datetime.fromisoformat(str(updated_at_value).replace('Z', '+00:00'))
                    updated_at_str = updated_at_dt.strftime("%d/%m/%Y")
                except:
                    updated_at_str = str(updated_at_value)
        
        investigator_name = evidence.investigator or (case.main_investigator if case else None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        person_name_from_db = None
        suspect_id_from_evidence = getattr(evidence, 'suspect_id', None)
        if suspect_id_from_evidence:
            suspect = db.query(Suspect).filter(Suspect.id == suspect_id_from_evidence).first()
            if suspect:
                db.refresh(suspect)
                is_unknown = getattr(suspect, 'is_unknown', False)
                if not is_unknown:
                    person_name_from_db = suspect.name
        
        response_data = {
            "id": evidence.id,
            "case_id": evidence.case_id,
            "evidence_number": evidence.evidence_number,
            "source": evidence.source,
            "file_path": evidence.file_path,
            "description": evidence.description,
            "title": case_title,
            "investigator": investigator_name,
            "agency": agency_name,
            "person_name": person_name_from_db,
            "updated_at": updated_at_str
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Evidence updated successfully",
                "data": response_data
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
                raise HTTPException(
                    status_code=400,
                    detail=f"Evidence number '{evidence_num}' already exists for another evidence"
                )
            raise HTTPException(
                status_code=400,
                detail="Duplicate entry. This value already exists in the database"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error_str}"
        )
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )

@router.post("/save-notes")
async def save_evidence_notes(
    request: EvidenceNotesRequest,
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == request.evidence_id).first()
        if not evidence:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Evidence with ID {request.evidence_id} not found",
                    "data": None
                },
                status_code=404
            )
        
        if not request.notes or not isinstance(request.notes, dict):
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Notes cannot be empty and must be a JSON object",
                    "data": None
                },
                status_code=400
            )
        
        setattr(evidence, 'notes', request.notes)
        db.commit()
        db.refresh(evidence)
        updated_at_value = getattr(evidence, 'updated_at', None)
        updated_at_str = updated_at_value.isoformat() if updated_at_value is not None else None
        return JSONResponse(
            content={
                "status": 200,
                "message": "Evidence notes saved successfully",
                "data": {
                    "evidence_id": evidence.id,
                    "evidence_number": evidence.evidence_number,
                    "evidence_title": evidence.title,
                    "notes": getattr(evidence, 'notes', None),
                    "updated_at": updated_at_str
                }
            },
            status_code=200
        )
    except Exception as e:
        db.rollback()
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Evidence with ID {request.evidence_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": f"Failed to save evidence notes: {str(e)}",
                    "data": None
                },
                status_code=500
            )

@router.put("/edit-notes")
async def edit_evidence_notes(
    request: EvidenceNotesRequest,
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == request.evidence_id).first()
        if not evidence:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Evidence with ID {request.evidence_id} not found",
                    "data": None
                },
                status_code=404
            )
        
        if not request.notes or not isinstance(request.notes, dict):
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Notes cannot be empty and must be a JSON object",
                    "data": None
                },
                status_code=400
            )
        
        setattr(evidence, 'notes', request.notes)
        db.commit()
        db.refresh(evidence)
        updated_at_value = getattr(evidence, 'updated_at', None)
        updated_at_str = updated_at_value.isoformat() if updated_at_value is not None else None
        return JSONResponse(
            content={
                "status": 200,
                "message": "Evidence notes updated successfully",
                "data": {
                    "evidence_id": evidence.id,
                    "evidence_number": evidence.evidence_number,
                    "evidence_title": evidence.title,
                    "notes": getattr(evidence, 'notes', None),
                    "updated_at": updated_at_str
                }
            },
            status_code=200
        )
    except Exception as e:
        db.rollback()
        error_message = str(e).lower()
        if "not found" in error_message:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Evidence with ID {request.evidence_id} not found",
                    "data": None
                },
                status_code=404
            )
        else:
            return JSONResponse(
                content={
                    "status": 500,
                    "message": f"Failed to edit evidence notes: {str(e)}",
                    "data": None
                },
                status_code=500
        )

BASE_UPLOAD_DIR = "data/custody"
def save_uploaded_file(file, custody_type: str):
    folder_path = os.path.join(BASE_UPLOAD_DIR, custody_type)
    os.makedirs(folder_path, exist_ok=True)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(folder_path, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path

@router.get('/custody/download-file')
async def download_file(path: str):
    file_path = os.path.join(BASE_UPLOAD_DIR, path)

    real_base = os.path.realpath(BASE_UPLOAD_DIR)
    real_target = os.path.realpath(file_path)

    if not real_target.startswith(real_base):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not os.path.isfile(real_target):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(real_target, filename=os.path.basename(real_target))

@router.get("/{evidence_id}/custody-logs")
async def get_custody_logs(
    evidence_id: int,
    type: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_database)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    query = db.query(CustodyLog).filter(CustodyLog.evidence_id == evidence_id)

    if type:
        query = query.filter(CustodyLog.custody_type == type)

    logs = query.order_by(CustodyLog.created_at.asc()).all()

    if not logs:
        return {
            "status": 200,
            "message": "Success",
            "data": []
        }

    return {
        "status": 200,
        "message": "Success",
        "data": logs
    }

@router.get("/{evidence_id}/custody")
def get_custody_reports(
    evidence_id: int,
    type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    query = db.query(CustodyReport).filter(
        CustodyReport.evidence_id == evidence_id
    )

    if type:
        query = query.filter(CustodyReport.custody_type == type)
        report = query.order_by(CustodyReport.created_at.asc()).first()
        return {
            "status": 200,
            "message": "Success",
            "data": report if report else {}
        }

    reports = query.order_by(CustodyReport.created_at.asc()).all()

    return {
        "status": 200,
        "message": "Success",
        "data": reports
    }

def sa_to_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in obj.__table__.columns
    }

def human_readable_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    p = 1024
    while size_bytes >= p and i < len(size_name) - 1:
        size_bytes /= p
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

@router.post("/{evidence_id}/custody/acquisition")
async def create_acquisition_report(
    evidence_id: int,
    investigator: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    evidence_detail: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    steps: List[str] = Form(...),
    photos: List[UploadFile] = File(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    photo_paths = []
    for ph in photos:
        saved_path = save_uploaded_file(ph, "acquisition")
        photo_paths.append(saved_path)

    details = []
    for idx, step in enumerate(steps):
        details.append({
            "steps": step,
            "photo": photo_paths[idx] if idx < len(photo_paths) else None
        })
    if not evidence_source:
        evidence_source = getattr(evidence, 'source', None)
    
    created_by = getattr(current_user, 'email', None)
    if not created_by:
        created_by = str(current_user.id)

    if not investigator:
        investigator = getattr(current_user, 'fullname', None) or getattr(current_user, 'email', None) or str(current_user.id)
    
    report = CustodyReport(
        evidence_id=evidence_id,
        custody_type="acquisition",
        created_by=created_by,
        investigator=investigator,
        location=location,
        evidence_source=evidence_source,
        evidence_type=evidence_type,
        evidence_detail=evidence_detail,
        notes=notes,
        details=details
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    log = CustodyLog(
        evidence_id=evidence_id,
        custody_type="acquisition",
        notes=notes,
        created_by=investigator
    )
    db.add(log)
    db.commit()

    return {
        "status": 201,
        "message": "Success",
        "data": sa_to_dict(report)
    }

@router.post("/{evidence_id}/custody/preparation")
async def create_preparation_report(
    evidence_id: int,
    investigator: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    evidence_detail: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    hypothesis: List[str] = Form(...),
    tools: List[str] = Form(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    details = []
    max_items = max(len(hypothesis), len(tools))

    for i in range(max_items):
        details.append({
            "hypothesis": hypothesis[i] if i < len(hypothesis) else None,
            "tools": tools[i] if i < len(tools) else None
        })
    
    if not evidence_source:
        evidence_source = getattr(evidence, 'source', None)

    created_by = getattr(current_user, 'email', None)
    if not created_by:
        created_by = str(current_user.id)

    if not investigator:
        investigator = getattr(current_user, 'fullname', None) or getattr(current_user, 'email', None) or str(current_user.id)
    
    report = CustodyReport(
        evidence_id=evidence_id,
        custody_type="preparation",
        created_by=created_by,
        investigator=investigator,
        location=location,
        evidence_source=evidence_source,
        evidence_type=evidence_type,
        evidence_detail=evidence_detail,
        notes=notes,
        details=details
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    log = CustodyLog(
        evidence_id=evidence_id,
        custody_type="preparation",
        notes=notes,
        created_by=investigator
    )
    db.add(log)
    db.commit()

    return {
        "status": 201,
        "message": "Success",
        "data": sa_to_dict(report)
    }

@router.post("/{evidence_id}/custody/extraction")
async def create_extraction_report(
    evidence_id: int,
    investigator: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    evidence_detail: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    extraction_file: UploadFile = File(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    file_path = save_uploaded_file(extraction_file, "extraction")
    file_name = file_path.split("/")[-1]

    extraction_file.file.seek(0, 2)
    file_size_bytes = extraction_file.file.tell()
    extraction_file.file.seek(0)

    file_size_human = human_readable_size(file_size_bytes)

    details = {
        "extraction_file": file_path,
        "file_name": file_name,
        "file_size": file_size_human,
    }

    if not evidence_source:
        evidence_source = getattr(evidence, 'source', None)

    created_by = getattr(current_user, 'email', None)
    if not created_by:
        created_by = str(current_user.id)

    if not investigator:
        investigator = getattr(current_user, 'fullname', None) or getattr(current_user, 'email', None) or str(current_user.id)
    
    report = CustodyReport(
        evidence_id=evidence_id,
        custody_type="extraction",
        created_by=created_by,
        investigator=investigator,
        location=location,
        evidence_source=evidence_source,
        evidence_type=evidence_type,
        evidence_detail=evidence_detail,
        notes=notes,
        details=details
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    log = CustodyLog(
        evidence_id=evidence_id,
        custody_type="extraction",
        notes=notes,
        created_by=investigator
    )
    db.add(log)
    db.commit()

    return {
        "status": 200,
        "message": "Extraction custody report created",
        "data": sa_to_dict(report)
    }

@router.post("/{evidence_id}/custody/analysis")
async def create_analysis_report(
    evidence_id: int,
    location: Optional[str] = Form(None),
    evidence_source: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    evidence_detail: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    hypothesis: List[str] = Form(...),
    tools: List[str] = Form(...),
    result: List[str] = Form(...),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    results = []
    max_items = max(len(hypothesis), len(tools), len(result))
    for i in range(max_items):
        results.append({
            "hypothesis": hypothesis[i] if i < len(hypothesis) else None,
            "tools": tools[i] if i < len(tools) else None,
            "result": result[i] if i < len(result) else None
        })

    files_meta = []
    print("DEBUG FILES:", files)
    for f in files:
        saved_path = save_uploaded_file(f, "analysis")

        f.file.seek(0, 2)
        file_size = f.file.tell()
        f.file.seek(0)

        files_meta.append({
            "file_name": f.filename,
            "file_size": human_readable_size(file_size),
            "file_path": saved_path
        })

    details = {
        "results": results,
        "files": files_meta
    }

    if not evidence_source:
        evidence_source = getattr(evidence, 'source', None)
    
    created_by = getattr(current_user, 'email', None)
    if not created_by:
        created_by = str(current_user.id)
    
    investigator = getattr(current_user, 'fullname', None) or getattr(current_user, 'email', None) or str(current_user.id)
    
    report = CustodyReport(
        evidence_id=evidence_id,
        custody_type="analysis",
        created_by=created_by,
        investigator=investigator,
        location=location,
        evidence_source=evidence_source,
        evidence_type=evidence_type,
        evidence_detail=evidence_detail,
        notes=notes,
        details=details
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    db.add(CustodyLog(
        evidence_id=evidence_id,
        custody_type="analysis",
        notes=notes,
        created_by=investigator
    ))
    db.commit()

    return {
        "status": 201,
        "message": "Analysis report created",
        "data": sa_to_dict(report)
    }

@router.put("/{evidence_id}/custody/{report_id}/notes")
async def update_custody_notes(
    evidence_id: int,
    report_id: int,
    notes: str | None = Form(""),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return {
            "status": 404,
            "message": "Evidence not found",
            "data": None
        }

    report = (
        db.query(CustodyReport)
        .filter(CustodyReport.id == report_id, CustodyReport.evidence_id == evidence_id)
        .first()
    )

    if not report:
        return {
            "status": 404,
            "message": "Custody report not found",
            "data": None
        }

    report.notes = notes
    db.commit()
    db.refresh(report)

    return {
        "status": 200,
        "message": "Notes updated",
        "data": {
            "id": report.id,
            "notes": report.notes,
            "updated_at": report.updated_at
        }
    }
