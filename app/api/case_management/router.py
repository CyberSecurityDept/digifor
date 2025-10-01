from fastapi import APIRouter
from .case_list import router as case_list_router
from .case_detail import router as case_detail_router
from .case_persons import router as case_persons_router
from .case_evidence import router as case_evidence_router
from .case_log_notes import router as case_log_notes_router

# Create main router for case management
router = APIRouter()

# Include all sub-routers
router.include_router(case_list_router)
router.include_router(case_detail_router)
router.include_router(case_persons_router)
router.include_router(case_evidence_router)
router.include_router(case_log_notes_router)
