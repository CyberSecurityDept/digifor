from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
)
from app.utils.security import (
    verify_password, 
    get_password_hash,
    validate_password_strength,
    create_password_reset_token,
    verify_password_reset_token,
    revoke_all_user_sessions,
)
from .helpers import get_user_by_username, get_user_by_email, get_current_active_user_safe_auth

router = APIRouter()


@router.post("/change-password", response_model=dict, tags=["Authentication - Password Management"])
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user_safe_auth),
    db: Session = Depends(get_db)
):
    """Change user password (requires current password)"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Current password is incorrect"}
        )
    
    # Validate new password strength
    password_validation = validate_password_strength(password_data.new_password)
    if not password_validation["is_valid"]:
        return JSONResponse(
            status_code=422,
            content={
                "status": 422,
                "message": "Password validation failed",
                "errors": password_validation["errors"],
                "strength": password_validation["strength"]
            }
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    # Revoke all existing sessions for security
    revoked_count = revoke_all_user_sessions(current_user.username)
    
    return {
        "status": 200,
        "message": "Password changed successfully",
        "revoked_sessions": revoked_count
    }


@router.post("/request-password-reset", response_model=dict, tags=["Authentication - Password Management"])
def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset (sends reset token to email)"""
    user = get_user_by_email(db, reset_data.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {
            "status": 200,
            "message": "If the email exists, a password reset link has been sent"
        }
    
    # Generate reset token
    reset_token = create_password_reset_token(reset_data.email)
    
    # In production, send email with reset link
    # For now, just return the token (remove in production)
    return {
        "status": 200,
        "message": "Password reset link sent to email",
        "reset_token": reset_token  # Remove this in production
    }


@router.post("/reset-password", response_model=dict, tags=["Authentication - Password Management"])
def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    # Verify reset token
    email = verify_password_reset_token(reset_data.token)
    if not email:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Invalid or expired reset token"}
        )
    
    # Find user by email
    user = get_user_by_email(db, email)
    if not user:
        return JSONResponse(
            status_code=404,
            content={"status": 404, "message": "User not found"}
        )
    
    # Validate new password strength
    password_validation = validate_password_strength(reset_data.new_password)
    if not password_validation["is_valid"]:
        return JSONResponse(
            status_code=422,
            content={
                "status": 422,
                "message": "Password validation failed",
                "errors": password_validation["errors"],
                "strength": password_validation["strength"]
            }
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Revoke all existing sessions for security
    revoked_count = revoke_all_user_sessions(user.username)
    
    return {
        "status": 200,
        "message": "Password reset successfully",
        "revoked_sessions": revoked_count
    }
