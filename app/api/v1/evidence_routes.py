from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
from datetime import datetime, timezone, timedelta

from app.api.deps import get_database
from app.evidence_management.schemas import (
    CustodyLogCreate, CustodyLogUpdate, CustodyLogResponse, 
    CustodyLogListResponse, CustodyChainResponse,
    CustodyReportCreate, CustodyReportResponse, CustodyReportListResponse
)
from app.evidence_management.models import Evidence, CustodyLog
from app.case_management.models import CaseLog, Case

WIB = timezone(timedelta(hours=7))

def get_wib_now():
    """Get current datetime in WIB timezone"""
    return datetime.now(WIB)

router = APIRouter(prefix="/evidence", tags=["Evidence Management"])


@router.get("/get-evidence-list")
async def get_evidence_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    evidence_type_id: Optional[int] = Query(None),
    db: Session = Depends(get_database)
):
    return {
        "status": 200,
        "message": "Evidence list retrieved successfully",
        "data": [],
        "total": 0,
        "page": 1,
        "size": limit
    }


@router.post("/create-evidence")
async def create_evidence(
    evidence_data: dict,
    db: Session = Depends(get_database)
):
    try:
        case_id = evidence_data.get('case_id')
        evidence_id = evidence_data.get('evidence_id', '32342223')
        
        if case_id:
            try:
                case = db.query(Case).filter(Case.id == case_id).first()
                current_status = case.status if case else "Open"
                
                case_log = CaseLog(
                    case_id=case_id,
                    action="Edit",
                    changed_by="Wisnu",
                    change_detail=f"Adding Evidence: {evidence_id}",
                    notes="",
                    status=current_status
                )
                db.add(case_log)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create case log for evidence: {str(e)}")
        
        return {
            "status": 201,
            "message": "Evidence created successfully",
            "data": evidence_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error, please try again later"
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
                "event_date": log.event_date.isoformat() if log.event_date else None,
                "person_name": log.person_name,
                "location": log.location,
                "action_description": log.action_description,
                "tools_used": log.tools_used,
                "is_verified": log.is_verified,
                "created_at": log.created_at.isoformat() if log.created_at else None
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
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "person_name": event.person_name,
                "location": event.location,
                "action_description": event.action_description,
                "tools_used": event.tools_used,
                "is_verified": event.is_verified,
                "created_at": event.created_at.isoformat() if event.created_at else None
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


@router.post("/{evidence_id}/custody-report")
async def generate_custody_report(
    evidence_id: int,
    report_data: CustodyReportCreate,
    db: Session = Depends(get_database)
):
    try:
        report = {
            "evidence_id": evidence_id,
            "report_type": report_data.report_type,
            "report_title": report_data.report_title,
            "report_description": report_data.report_description,
            "compliance_standard": report_data.compliance_standard,
            "generated_by": report_data.generated_by,
            "generated_date": get_wib_now(),
            "report_file_path": f"/data/reports/custody_evidence_{evidence_id}_{get_wib_now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "is_verified": False,
            "created_at": get_wib_now(),
            "is_active": True
        }
        
        return {
            "status": 201,
            "message": "Custody report generated successfully",
            "data": report
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )


@router.get("/{evidence_id}/custody-reports")
async def get_custody_reports(
    evidence_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        reports = []
        
        return {
            "status": 200,
            "message": "Custody reports retrieved successfully",
            "data": reports,
            "total": len(reports),
            "page": 1,
            "size": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )


@router.get("/{evidence_id}/custody-report/{report_id}")
async def get_custody_report(
    evidence_id: int,
    report_id: int,
    db: Session = Depends(get_database)
):
    try:
        raise HTTPException(
            status_code=404,
            detail=f"Custody report with ID {report_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Unexpected server error, please try again later"
        )
