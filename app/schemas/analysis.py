from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisResultBase(BaseModel):
    result_type: str
    result_data: Dict[str, Any]
    confidence: float = 1.0
    category: Optional[str] = None
    severity: Optional[str] = None


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating an analysis result"""
    pass


class AnalysisResult(AnalysisResultBase):
    id: int
    analysis_id: int
    created_at: datetime
    is_verified: bool
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CorrelationBase(BaseModel):
    correlation_type: str
    source_data: Dict[str, Any]
    target_data: Dict[str, Any]
    match_score: float
    match_type: Optional[str] = None
    match_confidence: float = 1.0
    context: Optional[str] = None
    significance: Optional[str] = None


class CorrelationCreate(CorrelationBase):
    """Schema for creating a correlation"""
    pass


class Correlation(CorrelationBase):
    id: int
    case_id: int
    created_at: datetime
    created_by: int
    is_verified: bool

    class Config:
        from_attributes = True


class AnalysisBase(BaseModel):
    analysis_type: str
    analysis_name: str
    description: Optional[str] = None
    analysis_config: Optional[Dict[str, Any]] = None
    is_automated: bool = True


class AnalysisCreate(AnalysisBase):
    """Schema for creating an analysis"""
    evidence_id: Optional[int] = None


class AnalysisUpdate(BaseModel):
    analysis_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    analysis_config: Optional[Dict[str, Any]] = None
    findings: Optional[str] = None
    confidence_score: Optional[float] = None


class Analysis(AnalysisBase):
    id: int
    case_id: int
    evidence_id: Optional[int] = None
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    results: Optional[Dict[str, Any]] = None
    findings: Optional[str] = None
    confidence_score: Optional[float] = None
    algorithm_version: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_by: int
    results_list: List[AnalysisResult] = []
    correlations: List[Correlation] = []

    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    id: int
    analysis_type: str
    analysis_name: str
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    analysis_type: str
    evidence_ids: Optional[List[int]] = None
    analysis_config: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, urgent


class AnalysisStatus(BaseModel):
    analysis_id: int
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
