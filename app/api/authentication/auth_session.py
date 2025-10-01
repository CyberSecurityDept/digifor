from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    SessionInfo,
    SessionResponse,
)
from app.utils.security import (
    get_session_info,
    revoke_all_user_sessions,
    revoke_all_refresh_tokens,
    cleanup_expired_sessions,
    cleanup_expired_refresh_tokens,
    get_active_sessions_count,
    get_refresh_tokens_count,
)
from app.utils.token_manager import get_token_manager
from .helpers import get_current_active_user_safe_auth, oauth2_scheme

router = APIRouter()


@router.get("/token-status", tags=["Authentication - Session Management"])
def get_token_status(
    token: str = Depends(oauth2_scheme)
):
    """Get current token status and information"""
    token_manager = get_token_manager()
    token_status = token_manager.check_token_status(token)
    
    return {
        "status": 200,
        "message": "Token status retrieved successfully",
        "data": token_status
    }


@router.get("/session", response_model=SessionResponse, tags=["Authentication - Session Management"])
def get_session_info_endpoint(
    current_user: User = Depends(get_current_active_user_safe_auth),
    token: str = Depends(oauth2_scheme)
):
    """Get current session information"""
    try:
        session_info = get_session_info(token)
        if not session_info:
            return JSONResponse(
                status_code=401,
                content={"status": 401, "message": "Session not found"}
            )
        
        return SessionResponse(
            status=200,
            message="Session information retrieved successfully",
            data=SessionInfo(
                user_id=current_user.id,
                username=session_info["username"],
                role=session_info["role"],
                login_time=session_info["login_time"],
                last_activity=session_info["last_activity"],
                expires_at=session_info["expires_at"],
                is_active=session_info["is_active"]
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Failed to retrieve session info: {str(e)}"}
        )


@router.post("/logout-all", response_model=dict, tags=["Authentication - Session Management"])
def logout_all_sessions(current_user: User = Depends(get_current_active_user_safe_auth)):
    """Logout from all sessions and revoke all tokens"""
    try:
        revoked_sessions = revoke_all_user_sessions(current_user.username)
        revoked_refresh_tokens = revoke_all_refresh_tokens(current_user.username)
        
        return {
            "status": 200,
            "message": f"Logged out from {revoked_sessions} sessions and {revoked_refresh_tokens} refresh tokens"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Failed to logout all sessions: {str(e)}"}
        )


@router.get("/sessions/cleanup", response_model=dict, tags=["Authentication - Session Management"])
def cleanup_sessions():
    """Clean up expired sessions and refresh tokens"""
    cleaned_sessions = cleanup_expired_sessions()
    cleaned_refresh_tokens = cleanup_expired_refresh_tokens()
    
    return {
        "status": 200,
        "message": f"Cleaned up {cleaned_sessions} expired sessions and {cleaned_refresh_tokens} expired refresh tokens",
        "active_sessions": get_active_sessions_count(),
        "active_refresh_tokens": get_refresh_tokens_count()
    }
