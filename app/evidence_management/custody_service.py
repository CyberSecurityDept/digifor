import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.evidence_management.models import CustodyLog, CustodyReport, Evidence
from app.evidence_management.schemas import (
    CustodyLogCreate, CustodyLogUpdate, CustodyReportCreate
)


class CustodyService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_custody_log(self, custody_data: CustodyLogCreate) -> CustodyLog:
        try:
            # Generate hash for integrity verification
            log_data = f"{custody_data.evidence_id}_{custody_data.event_type}_{custody_data.event_date}_{custody_data.person_name}_{custody_data.location}"
            log_hash = hashlib.sha256(log_data.encode()).hexdigest()
            
            # Create custody log
            custody_log = CustodyLog(
                evidence_id=custody_data.evidence_id,
                event_type=custody_data.event_type,
                event_date=custody_data.event_date,
                person_name=custody_data.person_name,
                person_title=custody_data.person_title,
                person_id=custody_data.person_id,
                location=custody_data.location,
                location_type=custody_data.location_type,
                action_description=custody_data.action_description,
                tools_used=custody_data.tools_used,
                conditions=custody_data.conditions,
                duration=custody_data.duration,
                transferred_to=custody_data.transferred_to,
                transferred_from=custody_data.transferred_from,
                transfer_reason=custody_data.transfer_reason,
                witness_name=custody_data.witness_name,
                witness_signature=custody_data.witness_signature,
                verification_method=custody_data.verification_method,
                is_immutable=True,
                is_verified=False,
                created_by=custody_data.created_by,
                notes=custody_data.notes,
                log_hash=log_hash
            )
            
            self.db.add(custody_log)
            self.db.commit()
            self.db.refresh(custody_log)
            
            return custody_log
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_custody_chain(self, evidence_id: UUID) -> Dict[str, Any]:
        try:
            # Get all custody logs for evidence
            custody_logs = self.db.query(CustodyLog).filter(
                CustodyLog.evidence_id == evidence_id
            ).order_by(CustodyLog.event_date).all()
            
            # Get evidence details
            evidence = self.db.query(Evidence).filter(
                Evidence.id == evidence_id
            ).first()
            
            if not evidence:
                raise ValueError("Evidence not found")
            
            # Check chain integrity
            chain_integrity = self._check_chain_integrity(custody_logs)
            
            return {
                "evidence_id": str(evidence_id),
                "evidence_number": evidence.evidence_number,
                "evidence_title": evidence.title,
                "custody_chain": [self._custody_log_to_dict(log) for log in custody_logs],
                "chain_integrity": chain_integrity,
                "total_events": len(custody_logs),
                "first_event": self._custody_log_to_dict(custody_logs[0]) if custody_logs else None,
                "last_event": self._custody_log_to_dict(custody_logs[-1]) if custody_logs else None
            }
            
        except Exception as e:
            raise e
    
    def get_custody_events(self, evidence_id: UUID, skip: int = 0, limit: int = 50, event_type: Optional[str] = None) -> Dict[str, Any]:
        try:
            query = self.db.query(CustodyLog).filter(
                CustodyLog.evidence_id == evidence_id
            )
            
            if event_type:
                query = query.filter(CustodyLog.event_type == event_type)
            
            total = query.count()
            events = query.order_by(desc(CustodyLog.event_date)).offset(skip).limit(limit).all()
            
            return {
                "events": [self._custody_log_to_dict(event) for event in events],
                "total": total,
                "page": (skip // limit) + 1,
                "size": limit
            }
            
        except Exception as e:
            raise e
    
    def update_custody_log(self, custody_id: UUID, custody_update: CustodyLogUpdate) -> CustodyLog:
        try:
            custody_log = self.db.query(CustodyLog).filter(
                CustodyLog.id == custody_id
            ).first()
            
            if not custody_log:
                raise ValueError("Custody log not found")
            
            # Check if log is immutable
            if custody_log.is_immutable:
                raise ValueError("Cannot modify immutable custody log")
            
            # Update only allowed fields
            update_data = custody_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(custody_log, field, value)
            
            self.db.commit()
            self.db.refresh(custody_log)
            
            return custody_log
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def create_custody_report(self, report_data: CustodyReportCreate) -> CustodyReport:
        try:
            # Get custody chain data
            chain_data = self.get_custody_chain(report_data.evidence_id)
            
            # Create report
            report = CustodyReport(
                evidence_id=report_data.evidence_id,
                report_type=report_data.report_type,
                report_title=report_data.report_title,
                report_description=report_data.report_description,
                compliance_standard=report_data.compliance_standard,
                generated_by=report_data.generated_by,
                report_data=chain_data,
                is_verified=False,
                is_active=True
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            return report
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_custody_reports(self, evidence_id: UUID, skip: int = 0, limit: int = 10, report_type: Optional[str] = None) -> Dict[str, Any]:
        try:
            query = self.db.query(CustodyReport).filter(
                CustodyReport.evidence_id == evidence_id
            )
            
            if report_type:
                query = query.filter(CustodyReport.report_type == report_type)
            
            total = query.count()
            reports = query.order_by(desc(CustodyReport.created_at)).offset(skip).limit(limit).all()
            
            return {
                "reports": [self._custody_report_to_dict(report) for report in reports],
                "total": total,
                "page": (skip // limit) + 1,
                "size": limit
            }
            
        except Exception as e:
            raise e
    
    def get_custody_report(self, report_id: UUID) -> CustodyReport:
        try:
            report = self.db.query(CustodyReport).filter(
                CustodyReport.id == report_id
            ).first()
            
            if not report:
                raise ValueError("Custody report not found")
            
            return report
            
        except Exception as e:
            raise e
    
    def verify_custody_log(self, custody_id: UUID, verified_by: str) -> CustodyLog:
        try:
            custody_log = self.db.query(CustodyLog).filter(
                CustodyLog.id == custody_id
            ).first()
            
            if not custody_log:
                raise ValueError("Custody log not found")
            
            custody_log.is_verified = True
            custody_log.verified_by = verified_by
            from datetime import timezone, timedelta
            WIB = timezone(timedelta(hours=7))
            custody_log.verification_date = datetime.now(WIB)
            
            self.db.commit()
            self.db.refresh(custody_log)
            
            return custody_log
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _check_chain_integrity(self, custody_logs: List[CustodyLog]) -> bool:
        if not custody_logs:
            return True
        
        # Check for gaps in custody
        for i in range(1, len(custody_logs)):
            prev_log = custody_logs[i-1]
            curr_log = custody_logs[i]
            
            # Check if there's a reasonable time gap
            time_diff = (curr_log.event_date - prev_log.event_date).total_seconds()
            if time_diff > 86400:  # More than 24 hours
                return False
        
        return True
    
    def _custody_log_to_dict(self, custody_log: CustodyLog) -> Dict[str, Any]:
        return {
            "id": custody_log.id,
            "evidence_id": custody_log.evidence_id,
            "event_type": custody_log.event_type,
            "event_date": custody_log.event_date.isoformat(),
            "person_name": custody_log.person_name,
            "person_title": custody_log.person_title,
            "person_id": custody_log.person_id,
            "location": custody_log.location,
            "location_type": custody_log.location_type,
            "action_description": custody_log.action_description,
            "tools_used": custody_log.tools_used,
            "conditions": custody_log.conditions,
            "duration": custody_log.duration,
            "transferred_to": custody_log.transferred_to,
            "transferred_from": custody_log.transferred_from,
            "transfer_reason": custody_log.transfer_reason,
            "witness_name": custody_log.witness_name,
            "witness_signature": custody_log.witness_signature,
            "verification_method": custody_log.verification_method,
            "is_immutable": custody_log.is_immutable,
            "is_verified": custody_log.is_verified,
            "verification_date": custody_log.verification_date.isoformat() if custody_log.verification_date else None,
            "verified_by": custody_log.verified_by,
            "created_at": custody_log.created_at.isoformat(),
            "created_by": custody_log.created_by,
            "notes": custody_log.notes,
            "log_hash": custody_log.log_hash
        }
    
    def _custody_report_to_dict(self, report: CustodyReport) -> Dict[str, Any]:
        return {
            "id": report.id,
            "evidence_id": report.evidence_id,
            "report_type": report.report_type,
            "report_title": report.report_title,
            "report_description": report.report_description,
            "compliance_standard": report.compliance_standard,
            "generated_by": report.generated_by,
            "generated_date": report.generated_date.isoformat(),
            "report_data": report.report_data,
            "report_file_path": report.report_file_path,
            "report_file_hash": report.report_file_hash,
            "is_verified": report.is_verified,
            "verified_by": report.verified_by,
            "verification_date": report.verification_date.isoformat() if report.verification_date else None,
            "created_at": report.created_at.isoformat(),
            "is_active": report.is_active
        }
