from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import analyze_apk_from_file
from app.analytics.analytics_management.models import ApkAnalytic

router = APIRouter()
@router.get("/analytics/{analytic_id}/apk-analytic")
def get_apk_analysis(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    apk_records = (
        db.query(ApkAnalytic)
        .filter(ApkAnalytic.analytic_id == analytic_id)
        .order_by(ApkAnalytic.created_at.desc())
        .all()
    )
    
    if not apk_records:
        return {
            "status": 404,
            "message": f"No APK analysis found for analytic_id={analytic_id}",
            "data": {}
        }

    malware_scoring = apk_records[0].malware_scoring if apk_records else None

    permissions = [
        {
            "id": r.id,
            "item": r.item,
            "status": r.status,
            "description": r.description,
        }
        for r in apk_records
    ]

    return {
        "status": 200,
        "message": "Success",
        "data": {
            "analytic_name": apk_records[0].analytic.analytic_name if apk_records else None,
            "method": apk_records[0].analytic.type if apk_records else None,
            "malware_scoring": malware_scoring,
            "permissions": permissions
        }
    }

@router.post("/analytics/analyze-apk")
def analyze_apk(file_id: int, analytic_id: int, db: Session = Depends(get_db)):
    try:
        result = analyze_apk_from_file(db, file_id=file_id, analytic_id=analytic_id)
        return {"status": 200, "message":"Success", "data": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))