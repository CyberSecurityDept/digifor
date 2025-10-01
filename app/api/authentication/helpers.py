"""
Authentication helper functions to avoid duplication across auth modules
"""

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.utils.security import verify_token_with_error_info

# Shared OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/oauth2/token")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


async def get_current_active_user_safe_auth(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current active user with safe authentication"""
    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": 401, "message": "Token not provided"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, error_type = verify_token_with_error_info(token)
    
    if username is None:
        if error_type == "invalid_token":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": 401, "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_not_found":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": 401, "message": "Session not found"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_inactive":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": 401, "message": "Session is inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_expired":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": 401, "message": "Session has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": 401, "message": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = get_user_by_username(db, username)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": 401, "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": 400, "message": "Inactive user"}
        )
    
    return user
