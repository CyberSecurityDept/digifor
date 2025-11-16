from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timezone, timedelta
from app.api.deps import get_database, get_current_user
from app.case_management.service import check_case_access
from app.case_management.models import Case
from app.evidence_management.models import Evidence
from app.auth.models import User

WIB = timezone(timedelta(hours=7))

def get_wib_now():
    return datetime.now(WIB)

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/case-summary/{case_id}")
async def get_case_summary_report(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        case_id_int = int(case_id)
        case = db.query(Case).filter(Case.id == case_id_int).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        return {
            "status": 200,
            "message": "Case summary report generated successfully",
            "data": {
                "case_id": case_id,
                "generated_at": get_wib_now().isoformat(),
                "report_type": "case_summary"
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case_id format")

@router.get("/evidence-chain/{evidence_id}")
async def get_evidence_chain_report(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        evidence_id_int = int(evidence_id)
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id_int).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence with ID {evidence_id} not found")
        
        case = db.query(Case).filter(Case.id == evidence.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {evidence.case_id} not found")
        
        return {
            "status": 200,
            "message": "Evidence chain report generated successfully",
            "data": {
                "evidence_id": evidence_id,
                "generated_at": get_wib_now().isoformat(),
                "report_type": "evidence_chain"
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evidence_id format")
