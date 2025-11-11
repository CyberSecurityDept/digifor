from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
import hashlib
import os
from datetime import datetime, timezone, timedelta

from app.api.deps import get_database, get_current_user
from app.auth.models import User
from app.evidence_management.schemas import (
    CustodyLogCreate, CustodyLogUpdate, CustodyLogResponse, 
    CustodyLogListResponse, CustodyChainResponse,
    CustodyReportCreate, CustodyReportResponse, CustodyReportListResponse,
    EvidenceNotesRequest
)
from fastapi.responses import JSONResponse
from app.evidence_management.models import Evidence, CustodyLog, EvidenceType
from app.evidence_management.custody_service import CustodyService
from app.case_management.models import CaseLog, Case, Agency
import traceback
from app.suspect_management.models import Suspect

WIB = timezone(timedelta(hours=7))

def get_wib_now():
    return datetime.now(WIB)

router = APIRouter(prefix="/evidence", tags=["Evidence Management"])

@router.get("/get-evidence-list")
async def get_evidence_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="Field to sort by. Valid values: 'created_at', 'id'"),
    sort_order: Optional[str] = Query(None, description="Sort order. Valid values: 'asc' (oldest first), 'desc' (newest first)"),
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
                "evidence_id": evidence.evidence_number,
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

@router.post("/create-evidence")
async def create_evidence(
    case_id: int = Form(...),
    evidence_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    evidence_summary: Optional[str] = Form(None),
    investigator: str = Form(...),
    person_name: Optional[str] = Form(None),
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
            date_str = datetime.now().strftime("%Y%m%d")
            evidence_count = db.query(Evidence).filter(Evidence.case_id == case_id).count()
            evidence_id = f"EVID-{case_id}-{date_str}-{evidence_count + 1:04d}"

        evidence_number = evidence_id
        evidence_title = case.title if case else evidence_number
        evidence_type_id = None
        if type:
            type_name = type.strip()
            if type_name:
                from app.evidence_management.models import EvidenceType
                evidence_type = db.query(EvidenceType).filter(EvidenceType.name.ilike(type_name)).first()
                if not evidence_type:
                    evidence_type = EvidenceType(name=type_name, is_active=True)
                    db.add(evidence_type)
                    db.commit()
                    db.refresh(evidence_type)
                evidence_type_id = evidence_type.id
        
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
        
        evidence_dict = {
            "evidence_number": evidence_number,
            "title": evidence_title,
            "description": evidence_summary,
            "evidence_type_id": evidence_type_id,
            "case_id": case_id,
            "file_path": file_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "file_type": file_type,
            "file_extension": file_extension,
            "investigator": investigator,
            "collected_date": datetime.now(timezone.utc),
        }
        
        evidence = Evidence(**evidence_dict)
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
    
        if is_unknown_person:
            # Jika is_unknown_person = true, tidak perlu create suspect
            pass
        elif person_name and person_name.strip():
            person_name_clean = person_name.strip()
            existing_suspect = db.query(Suspect).filter(
                Suspect.case_id == case_id,
                Suspect.name == person_name_clean
            ).first()
            
            if existing_suspect:
                setattr(existing_suspect, 'evidence_id', evidence_number)
                db.commit()
            else:
                investigator_name = getattr(case, 'main_investigator', None) or getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                
                # Jika is_unknown_person = false (radio person_name), status bisa diisi atau null
                # Tapi karena ini auto-create dari create-evidence, status tetap None
                new_suspect = Suspect(
                    name=person_name_clean,
                    case_id=case_id,
                    case_name=case.title if case else None,
                    evidence_id=evidence_number,
                    evidence_source=source,
                    evidence_summary=evidence_summary,
                    investigator=investigator_name,
                    status=None,  # Auto-created suspect dari create-evidence selalu status = null
                    is_unknown=False,
                    created_by=getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
                )
                db.add(new_suspect)
                db.commit()
                db.refresh(new_suspect)
                
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
            "evidence_id": evidence_id,
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

@router.get("/get-evidence-by-id{evidence_id}")
async def get_evidence(
    evidence_id: int,
    db: Session = Depends(get_database)
):
    return {
        "status": 200,
        "message": "Evidence retrieved successfully",
        "data": {"id": evidence_id}
    }

@router.post("/{evidence_id}/custody-events")
async def log_custody_event(
    evidence_id: int,
    custody_data: CustodyLogCreate,
    db: Session = Depends(get_database)
):
    try:
        log_data = f"{evidence_id}_{custody_data.event_type}_{custody_data.event_date}_{custody_data.person_name}_{custody_data.location}"
        log_hash = hashlib.sha256(log_data.encode()).hexdigest()

        custody_log = {
            "evidence_id": evidence_id,
            "event_type": custody_data.event_type,
            "event_date": custody_data.event_date,
            "person_name": custody_data.person_name,
            "person_title": custody_data.person_title,
            "person_id": custody_data.person_id,
            "location": custody_data.location,
            "location_type": custody_data.location_type,
            "action_description": custody_data.action_description,
            "tools_used": custody_data.tools_used,
            "conditions": custody_data.conditions,
            "duration": custody_data.duration,
            "transferred_to": custody_data.transferred_to,
            "transferred_from": custody_data.transferred_from,
            "transfer_reason": custody_data.transfer_reason,
            "witness_name": custody_data.witness_name,
            "witness_signature": custody_data.witness_signature,
            "verification_method": custody_data.verification_method,
            "is_immutable": True,
            "is_verified": False,
            "created_at": get_wib_now(),
            "created_by": custody_data.created_by,
            "notes": custody_data.notes,
            "log_hash": log_hash
        }
        
        return {
            "status": 201,
            "message": "Custody event logged successfully",
            "data": custody_log
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.get("/{evidence_id}/custody-chain")
async def get_custody_chain(
    evidence_id: int,
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence with ID {evidence_id} not found"
            )
        
        custody_logs = db.query(CustodyLog).filter(
            CustodyLog.evidence_id == evidence_id
        ).order_by(CustodyLog.event_date.asc()).all()
        
        custody_chain = []
        for log in custody_logs:
            custody_chain.append({
                "id": log.id,
                "evidence_id": log.evidence_id,
                "event_type": log.event_type,
                "event_date": log.event_date.isoformat() if log.event_date is not None else None,
                "person_name": log.person_name,
                "location": log.location,
                "action_description": log.action_description,
                "tools_used": log.tools_used,
                "is_verified": log.is_verified,
                "created_at": log.created_at.isoformat() if log.created_at is not None else None
            })
        
        return {
            "evidence_id": evidence_id,
            "evidence_number": evidence.evidence_number,
            "evidence_title": evidence.title,
            "custody_chain": custody_chain,
            "chain_integrity": len(custody_chain) > 0,
            "total_events": len(custody_chain),
            "first_event": custody_chain[0] if custody_chain else None,
            "last_event": custody_chain[-1] if custody_chain else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.get("/{evidence_id}/custody-events")
async def get_custody_events(
    evidence_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence with ID {evidence_id} not found"
            )
        
        query = db.query(CustodyLog).filter(CustodyLog.evidence_id == evidence_id)
        if event_type:
            query = query.filter(CustodyLog.event_type == event_type)
        total = query.count()
        events_query = query.order_by(CustodyLog.event_date.desc()).offset(skip).limit(limit)
        events = events_query.all()
        
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "evidence_id": event.evidence_id,
                "event_type": event.event_type,
                "event_date": event.event_date.isoformat() if event.event_date is not None else None,
                "person_name": event.person_name,
                "location": event.location,
                "action_description": event.action_description,
                "tools_used": event.tools_used,
                "is_verified": event.is_verified,
                "created_at": event.created_at.isoformat() if event.created_at is not None else None
            })
        
        return {
            "status": 200,
            "message": "Custody events retrieved successfully",
            "data": events_data,
            "total": total,
            "page": skip // limit + 1,
            "size": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.put("/{evidence_id}/custody-events/{custody_id}")
async def update_custody_event(
    evidence_id: int,
    custody_id: int,
    custody_update: CustodyLogUpdate,
    db: Session = Depends(get_database)
):
    try:
        
        return {
            "status": 200,
            "message": "Custody event updated successfully",
            "data": {
                "id": custody_id,
                "evidence_id": evidence_id,
                "updated_fields": custody_update.dict(exclude_unset=True)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )

@router.post("/{evidence_id}/custody-report", response_model=CustodyReportResponse)
async def generate_custody_report(
    evidence_id: int,
    report_data: CustodyReportCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence with ID {evidence_id} not found")
        
        report_data.evidence_id = evidence_id
        if not report_data.generated_by:
            report_data.generated_by = getattr(current_user, 'fullname', '') or getattr(current_user, 'email', 'Unknown User')
        
        custody_service = CustodyService(db)
        report = custody_service.create_custody_report(report_data)
        
        return JSONResponse(
            status_code=201,
            content={
                "status": 201,
                "message": "Custody report generated successfully",
                "data": {
                    "id": report.id,
                    "evidence_id": report.evidence_id,
                    "report_type": report.report_type,
                    "report_title": report.report_title,
                    "report_description": report.report_description,
                    "generated_by": getattr(report, 'generated_by', ''),
                    "generated_date": getattr(report, 'generated_date', None).isoformat() if getattr(report, 'generated_date', None) is not None else None,
                    "report_file_path": getattr(report, 'report_file_path', None),
                    "is_verified": getattr(report, 'is_verified', False),
                    "created_at": getattr(report, 'created_at', None).isoformat() if getattr(report, 'created_at', None) is not None else None
                }
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

@router.get("/{evidence_id}/custody-reports", response_model=CustodyReportListResponse)
async def get_custody_reports(
    evidence_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence with ID {evidence_id} not found")
        
        custody_service = CustodyService(db)
        result = custody_service.get_custody_reports(evidence_id, skip, limit, report_type)
    
        reports_data = []
        for report in result.get("reports", []):
            reports_data.append({
                "id": report.get("id"),
                "evidence_id": report.get("evidence_id"),
                "report_type": report.get("report_type"),
                "report_title": report.get("report_title"),
                "report_description": report.get("report_description"),
                "generated_by": report.get("generated_by"),
                "generated_date": report.get("generated_date"),
                "report_file_path": report.get("report_file_path"),
                "is_verified": report.get("is_verified"),
                "created_at": report.get("created_at")
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Custody reports retrieved successfully",
                "data": reports_data,
                "total": result.get("total", 0),
                "page": result.get("page", 1),
                "size": result.get("size", limit)
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

@router.get("/{evidence_id}/custody-report/{report_id}", response_model=CustodyReportResponse)
async def get_custody_report(
    evidence_id: int,
    report_id: int,
    db: Session = Depends(get_database)
):
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence with ID {evidence_id} not found")
        
        custody_service = CustodyService(db)
        report = custody_service.get_custody_report(report_id)
        
        report_evidence_id = getattr(report, 'evidence_id', None)
        if report_evidence_id != evidence_id:
            raise HTTPException(
                status_code=404,
                detail=f"Custody report with ID {report_id} not found for evidence {evidence_id}"
            )
        
        report_dict = custody_service._custody_report_to_dict(report)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "Custody report retrieved successfully",
                "data": {
                    "id": report_dict.get("id"),
                    "evidence_id": report_dict.get("evidence_id"),
                    "report_type": report_dict.get("report_type"),
                    "report_title": report_dict.get("report_title"),
                    "report_description": report_dict.get("report_description"),
                    "generated_by": report_dict.get("generated_by"),
                    "generated_date": report_dict.get("generated_date"),
                    "report_file_path": report_dict.get("report_file_path"),
                    "report_file_hash": report_dict.get("report_file_hash"),
                    "report_data": report_dict.get("report_data"),
                    "compliance_standard": report_dict.get("compliance_standard"),
                    "is_verified": report_dict.get("is_verified"),
                    "verified_by": report_dict.get("verified_by"),
                    "verification_date": report_dict.get("verification_date"),
                    "created_at": report_dict.get("created_at"),
                    "is_active": report_dict.get("is_active")
                }
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
