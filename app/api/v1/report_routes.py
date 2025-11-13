from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timezone, timedelta

from app.api.deps import get_database

WIB = timezone(timedelta(hours=7))

def get_wib_now():
    """Get current datetime in WIB timezone"""
    return datetime.now(WIB)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/case-summary/{case_id}")
async def get_case_summary_report(
    case_id: str,
    db: Session = Depends(get_database)
):
    return {
        "status": 200,
        "message": "Case summary report generated successfully",
        "data": {
            "case_id": case_id,
            "generated_at": get_wib_now().isoformat(),
            "report_type": "case_summary"
        }
    }

@router.get("/evidence-chain/{evidence_id}")
async def get_evidence_chain_report(
    evidence_id: str,
    db: Session = Depends(get_database)
):
    return {
        "status": 200,
        "message": "Evidence chain report generated successfully",
        "data": {
            "evidence_id": evidence_id,
            "generated_at": get_wib_now().isoformat(),
            "report_type": "evidence_chain"
        }
    }
