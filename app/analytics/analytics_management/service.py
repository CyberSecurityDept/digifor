from sqlalchemy.orm import Session
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.analytics_management.schemas import AnalyticCreate
from datetime import datetime
from typing import List

def store_analytic(db: Session, analytic_name: str, type: str = None, notes: str = None):
    new_analytic = Analytic(
        analytic_name=analytic_name,
        type=type,
        notes=notes,
        created_at=datetime.utcnow()
    )
    db.add(new_analytic)
    db.commit()
    db.refresh(new_analytic)
    return new_analytic

def get_all_analytics(db: Session):
    analytics = db.query(Analytic).order_by(Analytic.created_at.desc()).all()
    return analytics

def get_analytic_by_id(db: Session, analytic_id: int):
    return db.query(Analytic).filter(Analytic.id == analytic_id).first()

def link_device_to_analytic(db: Session, device_id: int, analytic_id: int):
    # Check if link already exists
    existing_link = db.query(AnalyticDevice).filter(
        AnalyticDevice.device_id == device_id,
        AnalyticDevice.analytic_id == analytic_id
    ).first()
    
    if existing_link:
        return {"status": 409, "message": "Device already linked to this analytic"}
    
    new_link = AnalyticDevice(
        device_id=device_id,
        analytic_id=analytic_id,
        created_at=datetime.utcnow()
    )
    db.add(new_link)
    db.commit()
    return {"status": 200, "message": "Linked successfully"}

def get_analytic_devices(db: Session, analytic_id: int):
    from app.analytics.device_management.models import Device
    
    devices = db.query(Device).filter(Device.analytic_id == analytic_id).all()
    return devices
