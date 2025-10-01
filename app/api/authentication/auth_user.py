from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserProfileResponse,
    UserProfileData,
    UserRegistration,
    UserRegistrationResponse,
)
from app.utils.security import (
    get_password_hash,
    validate_password_strength,
)
from .helpers import get_user_by_username, get_user_by_email, get_current_active_user_safe_auth

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, tags=["Authentication - User Profile"])
def read_users_me(current_user: User = Depends(get_current_active_user_safe_auth)):
    """Get current user profile information"""
    try:
        return UserProfileResponse(
            status=200,
            message="User profile retrieved successfully",
            data=UserProfileData(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                full_name=current_user.full_name,
                role=current_user.role,
                department=current_user.department,
                is_active=current_user.is_active,
                is_superuser=current_user.is_superuser,
                last_login=current_user.last_login,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Failed to retrieve user profile: {str(e)}"}
        )


@router.post("/register", response_model=UserRegistrationResponse, status_code=201, tags=["Authentication - User Registration"])
def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    # Validate password strength
    password_validation = validate_password_strength(user_data.password)
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
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Username already exists"}
        )
    
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Email already exists"}
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        department=user_data.department,
        is_active=True,
        is_superuser=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserRegistrationResponse(
        status=201,
        message="User registered successfully",
        data=UserProfileData(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            department=new_user.department,
            is_active=new_user.is_active,
            is_superuser=new_user.is_superuser,
            last_login=new_user.last_login,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )
    )
