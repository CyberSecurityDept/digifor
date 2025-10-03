from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4
import hashlib
from datetime import datetime

from app.api.deps import get_database
from app.evidence_management.schemas import (
    CustodyLogCreate, CustodyLogUpdate, CustodyLogResponse, 
    CustodyLogListResponse, CustodyChainResponse,
    CustodyReportCreate, CustodyReportResponse, CustodyReportListResponse
)

router = APIRouter(prefix="/evidence", tags=["Evidence Management"])


@router.get("/get-evidence-list")
async def get_evidence_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    evidence_type_id: Optional[UUID] = Query(None),
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
    return {
        "status": 201,
        "message": "Evidence created successfully",
        "data": evidence_data
    }


@router.get("/get-evidence-by-id{evidence_id}")
async def get_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_database)
):
    return {
        "status": 200,
        "message": "Evidence retrieved successfully",
        "data": {"id": str(evidence_id)}
    }


@router.post("/{evidence_id}/custody-events")
async def log_custody_event(
    evidence_id: UUID,
    custody_data: CustodyLogCreate,
    db: Session = Depends(get_database)
):
    try:
        log_data = f"{evidence_id}_{custody_data.event_type}_{custody_data.event_date}_{custody_data.person_name}_{custody_data.location}"
        log_hash = hashlib.sha256(log_data.encode()).hexdigest()

        custody_log = {
            "id": str(uuid4()),
            "evidence_id": str(evidence_id),
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
            "created_at": datetime.now(),
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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{evidence_id}/custody-chain")
async def get_custody_chain(
    evidence_id: UUID,
    db: Session = Depends(get_database)
):
    try:
        custody_chain = [
            {
                "id": "custody-1",
                "evidence_id": str(evidence_id),
                "event_type": "acquisition",
                "event_date": "2023-10-13T10:00:00Z",
                "person_name": "Nanda Maqpul",
                "location": "TKP Pembunuhan",
                "action_description": "Evidence collected from crime scene",
                "is_verified": True,
                "created_at": "2023-10-13T10:00:00Z"
            },
            {
                "id": "custody-2", 
                "evidence_id": str(evidence_id),
                "event_type": "preparation",
                "event_date": "2023-10-13T11:00:00Z",
                "person_name": "Nanda Maqpul",
                "location": "Lab Forensik",
                "action_description": "Evidence prepared for analysis",
                "tools_used": ["FTK Imager", "Autopsy"],
                "is_verified": True,
                "created_at": "2023-10-13T11:00:00Z"
            }
        ]
        
        return {
            "evidence_id": str(evidence_id),
            "evidence_number": "32342223",
            "evidence_title": "GPS Smartphone Samsung S21",
            "custody_chain": custody_chain,
            "chain_integrity": True,
            "total_events": len(custody_chain),
            "first_event": custody_chain[0] if custody_chain else None,
            "last_event": custody_chain[-1] if custody_chain else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{evidence_id}/custody-events")
async def get_custody_events(
    evidence_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        events = [
            {
                "id": "custody-1",
                "evidence_id": str(evidence_id),
                "event_type": "acquisition",
                "event_date": "2023-10-13T10:00:00Z",
                "person_name": "Nanda Maqpul",
                "location": "TKP Pembunuhan",
                "action_description": "Evidence collected from crime scene",
                "is_verified": True,
                "created_at": "2023-10-13T10:00:00Z"
            }
        ]
        
        return {
            "status": 200,
            "message": "Custody events retrieved successfully",
            "data": events,
            "total": len(events),
            "page": 1,
            "size": limit
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{evidence_id}/custody-events/{custody_id}")
async def update_custody_event(
    evidence_id: UUID,
    custody_id: UUID,
    custody_update: CustodyLogUpdate,
    db: Session = Depends(get_database)
):
    try:
        
        return {
            "status": 200,
            "message": "Custody event updated successfully",
            "data": {
                "id": str(custody_id),
                "evidence_id": str(evidence_id),
                "updated_fields": custody_update.dict(exclude_unset=True)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{evidence_id}/custody-report")
async def generate_custody_report(
    evidence_id: UUID,
    report_data: CustodyReportCreate,
    db: Session = Depends(get_database)
):
    try:
        report = {
            "id": str(uuid4()),
            "evidence_id": str(evidence_id),
            "report_type": report_data.report_type,
            "report_title": report_data.report_title,
            "report_description": report_data.report_description,
            "compliance_standard": report_data.compliance_standard,
            "generated_by": report_data.generated_by,
            "generated_date": datetime.now(),
            "report_file_path": f"/data/reports/custody_evidence_{evidence_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "is_verified": False,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        return {
            "status": 201,
            "message": "Custody report generated successfully",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{evidence_id}/custody-reports")
async def get_custody_reports(
    evidence_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    try:
        reports = [
            {
                "id": "report-1",
                "evidence_id": str(evidence_id),
                "report_type": "iso_27037",
                "report_title": "Chain of Custody Report - ISO 27037",
                "generated_by": "System",
                "generated_date": "2023-10-13T15:00:00Z",
                "is_verified": True,
                "created_at": "2023-10-13T15:00:00Z"
            }
        ]
        
        return {
            "status": 200,
            "message": "Custody reports retrieved successfully",
            "data": reports,
            "total": len(reports),
            "page": 1,
            "size": limit
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{evidence_id}/custody-report/{report_id}")
async def get_custody_report(
    evidence_id: UUID,
    report_id: UUID,
    db: Session = Depends(get_database)
):
    try:
        report = {
            "id": str(report_id),
            "evidence_id": str(evidence_id),
            "report_type": "iso_27037",
            "report_title": "Chain of Custody Report - ISO 27037",
            "report_description": "Comprehensive chain of custody report following ISO/IEC 27037 standards",
            "compliance_standard": "iso_27037",
            "generated_by": "System",
            "generated_date": "2023-10-13T15:00:00Z",
            "report_file_path": f"/data/reports/custody_evidence_{evidence_id}_20231013_150000.pdf",
            "is_verified": True,
            "verified_by": "Supervisor",
            "verification_date": "2023-10-13T16:00:00Z",
            "created_at": "2023-10-13T15:00:00Z",
            "is_active": True
        }
        
        return {
            "status": 200,
            "message": "Custody report retrieved successfully",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
