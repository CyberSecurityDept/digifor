from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AnalyticCreate(BaseModel):
    analytic_name: str
    type: Optional[str] = None
    notes: Optional[str] = None

class AnalyticResponse(BaseModel):
    id: int
    analytic_name: str
    type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticDeviceLink(BaseModel):
    device_id: int
    analytic_id: int

class AnalyticWithDevices(BaseModel):
    id: int
    analytic_name: str
    type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    devices: List[dict] = []

    class Config:
        from_attributes = True
