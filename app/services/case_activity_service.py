from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from app.models.case import Case
from app.models.case_activity import CaseActivity, CaseStatusHistory
from app.models.user import User
from app.schemas.case_activity import CaseActivityCreate, CaseStatusHistoryCreate


class CaseActivityService:
    """Service for managing case activities and status tracking"""
    
    @staticmethod
    def create_activity(
        db: Session,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        activity_type: str,
        description: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[List[str]] = None,
        status_change_reason: Optional[str] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CaseActivity:
        """Create a new case activity"""
        
        activity = CaseActivity(
            case_id=case_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
            changed_fields=changed_fields,
            status_change_reason=status_change_reason,
            previous_status=previous_status,
            new_status=new_status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return activity
    
    @staticmethod
    def create_status_history(
        db: Session,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        previous_status: str,
        new_status: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> CaseStatusHistory:
        """Create a new status history entry"""
        
        status_history = CaseStatusHistory(
            case_id=case_id,
            user_id=user_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            notes=notes,
            ip_address=ip_address
        )
        
        db.add(status_history)
        db.commit()
        db.refresh(status_history)
        
        return status_history
    
    @staticmethod
    def update_case_status(
        db: Session,
        case: Case,
        new_status: str,
        user_id: uuid.UUID,
        reason: str,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Case:
        """Update case status with activity tracking"""
        
        previous_status = case.status
        old_value = {"status": previous_status}
        new_value = {"status": new_status}
        
        # Update case status
        case.status = new_status
        case.last_status_change = datetime.utcnow()
        case.status_change_reason = reason
        
        # Update reopened count if reopening
        if previous_status == "closed" and new_status == "reopened":
            case.reopened_count += 1
        
        # Update closed_at timestamp
        if new_status == "closed":
            case.closed_at = datetime.utcnow()
        
        # Update status history in JSON field
        if not case.status_history:
            case.status_history = []
        
        status_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "previous_status": previous_status,
            "new_status": new_status,
            "reason": reason,
            "notes": notes,
            "user_id": str(user_id)
        }
        case.status_history.append(status_entry)
        
        # Create activity log
        activity_description = f"Case status changed from '{previous_status}' to '{new_status}'"
        if reason:
            activity_description += f" - Reason: {reason}"
        
        CaseActivityService.create_activity(
            db=db,
            case_id=case.id,
            user_id=user_id,
            activity_type="status_change",
            description=activity_description,
            old_value=old_value,
            new_value=new_value,
            changed_fields=["status"],
            status_change_reason=reason,
            previous_status=previous_status,
            new_status=new_status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create status history entry
        CaseActivityService.create_status_history(
            db=db,
            case_id=case.id,
            user_id=user_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            notes=notes,
            ip_address=ip_address
        )
        
        db.commit()
        db.refresh(case)
        
        return case
    
    @staticmethod
    def get_case_activities(
        db: Session,
        case_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[CaseActivity]:
        """Get case activities with pagination"""
        
        activities = db.query(CaseActivity)\
            .filter(CaseActivity.case_id == case_id)\
            .order_by(CaseActivity.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return activities
    
    @staticmethod
    def get_case_status_history(
        db: Session,
        case_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[CaseStatusHistory]:
        """Get case status history with pagination"""
        
        history = db.query(CaseStatusHistory)\
            .filter(CaseStatusHistory.case_id == case_id)\
            .order_by(CaseStatusHistory.changed_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return history
    
    @staticmethod
    def get_recent_activities(
        db: Session,
        case_id: uuid.UUID,
        limit: int = 10
    ) -> List[CaseActivity]:
        """Get recent case activities"""
        
        activities = db.query(CaseActivity)\
            .filter(CaseActivity.case_id == case_id)\
            .order_by(CaseActivity.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return activities
