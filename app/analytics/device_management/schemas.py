from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FileCreate(BaseModel):
    file_name: str
    file_path: str
    notes: Optional[str] = None
    type: str
    tools: str

class FileResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    notes: Optional[str] = None
    type: str
    tools: str
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceCreate(BaseModel):
    owner_name: Optional[str] = None
    phone_number: Optional[str] = None
    file_id: int

class DeviceResponse(BaseModel):
    id: int
    owner_name: Optional[str] = None
    phone_number: Optional[str] = None
    file_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    device_id: int
    direction: Optional[str] = None
    source: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[str] = None
    text: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    details: Optional[str] = None
    thread_id: Optional[str] = None
    attachment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ContactResponse(BaseModel):
    id: int
    device_id: int
    type: Optional[str] = None
    source: Optional[str] = None
    contact: Optional[str] = None
    messages: Optional[str] = None
    phones_emails: Optional[str] = None
    internet: Optional[str] = None
    other: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CallResponse(BaseModel):
    id: int
    device_id: int
    direction: Optional[str] = None
    source: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[str] = None
    duration: Optional[str] = None
    caller: Optional[str] = None
    receiver: Optional[str] = None
    details: Optional[str] = None
    thread_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
