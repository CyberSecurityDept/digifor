from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import store_analytic, get_all_analytics
from app.analytics.analytics_management.schemas import AnalyticCreate
from app.analytics.shared.models import Device, Analytic

router = APIRouter()

@router.get("/analytics/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        analytics = get_all_analytics(db)
        return {
            "status": 200,
            "message": "Success",
            "data": analytics
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }

@router.post("/analytics/create-analytic")
def create_analytic(data: AnalyticCreate, db: Session = Depends(get_db)):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        new_analytic = store_analytic(
            db=db,
            analytic_name=data.analytic_name,
            type=data.type,
            notes=data.notes,
        )

        result = {
            "id": new_analytic.id,
            "analytic_name": new_analytic.analytic_name,
            "type": new_analytic.type,
            "notes": new_analytic.notes,
            "created_at": str(new_analytic.created_at)
        }

        return {
            "status": 200,
            "message": "Analytics created successfully",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal membuat analytic: {str(e)}",
            "data": []
        }

@router.post("/analytics/link-device-analytic")
def link_device_to_analytic(device_id: int, analytic_id: int):
    db = next(get_db())
    device = db.query(Device).get(device_id)
    analytic = db.query(Analytic).get(analytic_id)
    if not device or not analytic:
        return {"status": 404, "message": "Device or Analytic not found"}

    analytic.devices.append(device)
    db.commit()
    return {"status": 200, "message": "Linked successfully"}

@router.get("/analytics/{analytic_id}/devices")
def get_analytic_devices(analytic_id: int, db: Session = Depends(get_db)):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return {"status": 404, "message": "Analytic not found", "data": []}

    devices = db.query(Device).filter(Device.analytic_id == analytic_id).all()

    return {
        "status": 200,
        "message": "Success",
        "data": [
            {
                "device_id": d.id,
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
                "created_at": d.created_at,
            }
            for d in devices
        ]
    }
