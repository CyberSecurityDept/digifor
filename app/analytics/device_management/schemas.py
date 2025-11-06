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
    total_size: Optional[int] = None
    total_size_formatted: Optional[str] = None
    created_at: datetime

class SelectedFile(BaseModel):
    file_id: int
    tools: List[str]

class AddDeviceRequest(BaseModel):
    owner_name: str
    phone_number: str
    selected_files: List[SelectedFile]

class DeviceResponse(BaseModel):
    device_id: int
    file_id: int
    owner_name: str
    phone_number: str
    device_name: str
    file_info: dict
    created_at: datetime