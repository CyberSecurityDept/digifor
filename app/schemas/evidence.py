from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CustodyTransferBase(BaseModel):
    from_custodian: str
    to_custodian: str
    transfer_reason: Optional[str] = None
    transfer_method: Optional[str] = None
    transfer_location: Optional[str] = None
    evidence_condition: Optional[str] = None
    witness: Optional[str] = None
    notes: Optional[str] = None


class CustodyTransferCreate(CustodyTransferBase):
    """Schema for creating a custody transfer"""
    pass


class CustodyTransfer(CustodyTransferBase):
    id: int
    evidence_id: int
    transfer_date: datetime
    from_signature: Optional[str] = None
    to_signature: Optional[str] = None
    witness_signature: Optional[str] = None

    class Config:
        from_attributes = True


class EvidenceItemBase(BaseModel):
    evidence_number: str
    item_type: str
    description: str
    source: Optional[str] = None
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_extension: Optional[str] = None
    is_encrypted: bool = False
    encryption_method: Optional[str] = None
    current_custodian: Optional[str] = None
    analysis_notes: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    is_sensitive: bool = False


class EvidenceItemCreate(EvidenceItemBase):
    pass


class EvidenceItemUpdate(BaseModel):
    evidence_number: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    analysis_status: Optional[str] = None
    analysis_notes: Optional[str] = None
    current_custodian: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    is_sensitive: Optional[bool] = None


class EvidenceItem(EvidenceItemBase):
    id: int
    case_id: int
    file_path: str
    file_size: Optional[int] = None
    md5_hash: Optional[str] = None
    sha1_hash: Optional[str] = None
    sha256_hash: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    analysis_status: str
    custody_chain: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class EvidenceItemSummary(BaseModel):
    id: int
    evidence_number: str
    item_type: str
    description: str
    file_size: Optional[int] = None
    status: str
    analysis_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceUpload(BaseModel):
    evidence_number: str
    item_type: str
    description: str
    source: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    is_sensitive: bool = False
