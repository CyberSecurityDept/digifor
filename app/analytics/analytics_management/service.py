from sqlalchemy.orm import Session
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.device_management.models import Device
from typing import List
from app.utils.timezone import get_indonesia_time

def store_analytic(db: Session, analytic_name: str, type: str = None, method: str = None):
    new_analytic = Analytic(
        analytic_name=analytic_name,
        type=type,
        method=method,
        created_at=get_indonesia_time()
    )
    db.add(new_analytic)
    db.commit()
    db.refresh(new_analytic)
    return new_analytic

def get_all_analytics(db: Session):
    analytics = db.query(Analytic).order_by(Analytic.id.desc()).all()
    
    formatted_analytics = []
    for analytic in analytics:
        formatted_analytic = {
            "id": analytic.id,
            "analytic_name": analytic.analytic_name,
            "type": analytic.type,
            "method": analytic.method,
            "summary": analytic.summary,
            "created_at": analytic.created_at,
            "updated_at": analytic.updated_at
        }
        formatted_analytics.append(formatted_analytic)
    
    return formatted_analytics

def get_analytic_by_id(db: Session, analytic_id: int):
    return db.query(Analytic).filter(Analytic.id == analytic_id).first()

def link_device_to_analytic(db: Session, device_id: int, analytic_id: int):
    existing_link = db.query(AnalyticDevice).filter(
        AnalyticDevice.device_id == device_id,
        AnalyticDevice.analytic_id == analytic_id
    ).first()
    
    if existing_link:
        return {"status": 409, "message": "Device already linked to this analytic"}
    
    new_link = AnalyticDevice(
        device_id=device_id,
        analytic_id=analytic_id,
        created_at=get_indonesia_time()
    )
    db.add(new_link)
    db.commit()
    return {"status": 200, "message": "Linked successfully"}

def get_analytic_devices(db: Session, analytic_id: int):
    devices = db.query(Device).filter(Device.analytic_id == analytic_id).all()
    return devices
