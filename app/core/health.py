from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.core.config import settings

WIB = timezone(timedelta(hours=7))

def get_wib_now():
    return datetime.now(WIB)

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": get_wib_now().isoformat(),
        "version": settings.VERSION,
        "database": db_status,
        "services": {
            "database": db_status,
            "api": "running"
        }
    }


@router.get("/health/ready")
async def readiness_check():
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
