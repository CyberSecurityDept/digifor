import uuid
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class CaseActivityBase(BaseModel):
    activity_type: str
    description: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    status_change_reason: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class CaseActivityCreate(CaseActivityBase):
    case_id: uuid.UUID
    user_id: uuid.UUID


class CaseActivity(CaseActivityBase):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime

    class Config:
        from_attributes = True


class CaseStatusHistoryBase(BaseModel):
    previous_status: str
    new_status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None


class CaseStatusHistoryCreate(CaseStatusHistoryBase):
    case_id: uuid.UUID
    user_id: uuid.UUID


class CaseStatusHistory(CaseStatusHistoryBase):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    changed_at: datetime

    class Config:
        from_attributes = True


class CaseCloseRequest(BaseModel):
    reason: str
    notes: Optional[str] = None


class CaseReopenRequest(BaseModel):
    reason: str
    notes: Optional[str] = None


class CaseStatusChangeRequest(BaseModel):
    status: str
    reason: str
    notes: Optional[str] = None


class CaseActivitySummary(BaseModel):
    id: uuid.UUID
    activity_type: str
    description: str
    timestamp: datetime
    user_name: str
    user_role: str

    class Config:
        from_attributes = True
