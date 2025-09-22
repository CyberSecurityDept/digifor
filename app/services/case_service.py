"""
Case Management Service for status transitions and business logic
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.case import Case, CaseStatusHistory
from app.models.user import User


class CaseStatusTransitionError(Exception):
    """Exception raised for invalid status transitions"""
    pass


class CaseService:
    """Service class for case management operations"""
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        "open": ["in_progress", "closed"],
        "in_progress": ["open", "closed"],
        "closed": ["reopened"],
        "reopened": ["in_progress", "closed"],
        "archived": []  # No transitions from archived
    }
    
    @staticmethod
    def validate_status_transition(old_status: str, new_status: str) -> bool:
        """Validate if status transition is allowed"""
        if old_status not in CaseService.VALID_TRANSITIONS:
            return False
        
        return new_status in CaseService.VALID_TRANSITIONS[old_status]
    
    @staticmethod
    def change_case_status(
        db: Session,
        case: Case,
        new_status: str,
        reason: str,
        changed_by: User,
        notes: Optional[str] = None
    ) -> CaseStatusHistory:
        """
        Change case status with validation and logging
        
        Args:
            db: Database session
            case: Case object to update
            new_status: New status to set
            reason: Reason for status change (required)
            changed_by: User making the change
            notes: Additional notes (optional)
        
        Returns:
            CaseStatusHistory: The created status history record
        
        Raises:
            CaseStatusTransitionError: If transition is not valid
        """
        old_status = case.status
        
        # Validate transition
        if not CaseService.validate_status_transition(old_status, new_status):
            raise CaseStatusTransitionError(
                f"Invalid status transition from '{old_status}' to '{new_status}'"
            )
        
        # Validate reason is provided
        if not reason or not reason.strip():
            raise CaseStatusTransitionError("Reason is required for status change")
        
        # Update case status
        case.status = new_status
        case.updated_at = datetime.utcnow()
        
        # Set closed_at timestamp if closing case
        if new_status == "closed" and old_status != "closed":
            case.closed_at = datetime.utcnow()
        
        # Create status history record
        status_history = CaseStatusHistory(
            case_id=case.id,
            old_status=old_status,
            new_status=new_status,
            reason=reason.strip(),
            notes=notes,
            changed_by=changed_by.id
        )
        
        db.add(status_history)
        db.commit()
        db.refresh(status_history)
        
        return status_history
    
    @staticmethod
    def close_case(
        db: Session,
        case: Case,
        reason: str,
        changed_by: User,
        notes: Optional[str] = None
    ) -> CaseStatusHistory:
        """Close a case with validation"""
        return CaseService.change_case_status(
            db=db,
            case=case,
            new_status="closed",
            reason=reason,
            changed_by=changed_by,
            notes=notes
        )
    
    @staticmethod
    def reopen_case(
        db: Session,
        case: Case,
        reason: str,
        changed_by: User,
        notes: Optional[str] = None
    ) -> CaseStatusHistory:
        """Reopen a case with validation"""
        return CaseService.change_case_status(
            db=db,
            case=case,
            new_status="reopened",
            reason=reason,
            changed_by=changed_by,
            notes=notes
        )
    
    @staticmethod
    def get_case_status_history(
        db: Session,
        case_id: uuid.UUID,
        limit: int = 50
    ) -> List[CaseStatusHistory]:
        """Get status history for a case"""
        return db.query(CaseStatusHistory)\
            .filter(CaseStatusHistory.case_id == case_id)\
            .order_by(CaseStatusHistory.changed_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_case_by_id(db: Session, case_id: uuid.UUID) -> Optional[Case]:
        """Get case by ID"""
        return db.query(Case).filter(Case.id == case_id).first()
