from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.analysis import Analysis
from app.models.evidence import EvidenceItem
from app.api.auth import get_current_active_user

router = APIRouter()


@router.get("/")
async def get_main_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    return {
        "status": 200,
        "message": "Main dashboard retrieved successfully",
        "data": {
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "full_name": current_user.full_name,
                "role": current_user.role
            },
            "menu_options": [
                {
                    "id": "analytics",
                    "name": "Analytics",
                    "description": "Digital forensics analytics and analysis tools",
                    "icon": "analytics",
                    "route": "/analytics"
                },
                {
                    "id": "case",
                    "name": "Case",
                    "description": "Case management and investigation tools",
                    "icon": "case",
                    "route": "/case"
                }
            ]
        }
    }


@router.get("/analytics")
async def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Get analysis statistics
    total_analyses = db.query(Analysis).count()
    completed_analyses = db.query(Analysis).filter(Analysis.status == "completed").count()
    in_progress_analyses = db.query(Analysis).filter(Analysis.status == "in_progress").count()
    pending_analyses = db.query(Analysis).filter(Analysis.status == "pending").count()
    
    # Get evidence statistics
    total_evidence = db.query(EvidenceItem).count()
    processed_evidence = db.query(EvidenceItem).filter(
        EvidenceItem.status == "processed"
    ).count()
    
    # Get analysis types distribution
    analysis_types = db.query(
        Analysis.analysis_type,
        func.count(Analysis.id).label('count')
    ).group_by(Analysis.analysis_type).all()
    
    # Get recent analyses
    recent_analyses = db.query(Analysis).order_by(
        Analysis.created_at.desc()
    ).limit(10).all()
    
    # Format recent analyses for response
    analysis_list = []
    for analysis in recent_analyses:
        analysis_list.append({
            "id": str(analysis.id),
            "analysis_type": analysis.analysis_type,
            "status": analysis.status,
            "progress": analysis.progress,
            "created_at": analysis.created_at.isoformat(),
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "case_id": str(analysis.case_id) if analysis.case_id else None
        })
    
    return {
        "status": 200,
        "message": "Analytics dashboard retrieved successfully",
        "data": {
            "statistics": {
                "total_analyses": total_analyses,
                "completed_analyses": completed_analyses,
                "in_progress_analyses": in_progress_analyses,
                "pending_analyses": pending_analyses,
                "total_evidence": total_evidence,
                "processed_evidence": processed_evidence
            },
            "analysis_types": [
                {"type": stat.analysis_type, "count": stat.count} 
                for stat in analysis_types
            ],
            "recent_analyses": analysis_list
        }
    }
