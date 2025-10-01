from fastapi import APIRouter
from .auth_login import router as auth_login_router
from .auth_user import router as auth_user_router
from .auth_password import router as auth_password_router
from .auth_session import router as auth_session_router

# Create main router for authentication
router = APIRouter()

# Include all sub-routers
router.include_router(auth_login_router)
router.include_router(auth_user_router)
router.include_router(auth_password_router)
router.include_router(auth_session_router)
