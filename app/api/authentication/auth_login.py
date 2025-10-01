from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    User as UserSchema,
    Token,
    LoginSuccessResponse,
    LoginErrorResponse,
    LoginSuccessData,
    LoginRequest,
    RefreshTokenData,
    RefreshTokenResponse,
    RefreshTokenRequest,
)
from app.utils.security import (
    verify_password, 
    create_access_token, 
    verify_token, 
    create_token_pair,
    verify_refresh_token,
    revoke_refresh_token,
)
from app.utils.token_manager import get_token_manager
from app.config import settings
from .helpers import get_user_by_username

router = APIRouter()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/token", response_model=RefreshTokenResponse, tags=["Authentication - Login"], responses={401: {"model": LoginErrorResponse, "description": "Invalid credentials"}})
def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login with username/password and get access + refresh tokens"""
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"status": 401, "messages": "Invalid username or password"},
            )

        # Create token pair (access + refresh)
        access_token, refresh_token, expires_in = create_token_pair(user.username, user.role)

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        return RefreshTokenResponse(
            status=200,
            message="Login Successfully",
            data=RefreshTokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in
            ),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Login failed: {str(e)}"}
        )


@router.post("/token-form", response_model=LoginSuccessResponse, tags=["Authentication - Login"], responses={401: {"model": LoginErrorResponse, "description": "Invalid credentials"}}, include_in_schema=False)
def login_for_access_token_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"status": 401, "messages": "Invalid username or password"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return LoginSuccessResponse(
        status=200,
        messages="Login Successfully",
        data=LoginSuccessData(access_token=access_token, token_type="bearer"),
    )


@router.post("/oauth2/token", response_model=Token, tags=["Authentication - Login"], include_in_schema=False)
def oauth2_login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 compatible login endpoint"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": 401, "message": "Incorrect username or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=RefreshTokenResponse, tags=["Authentication - Login"])
def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        refresh_token = refresh_data.refresh_token
        
        # Verify refresh token
        username, role, error_type = verify_refresh_token(refresh_token)
        
        if username is None:
            if error_type == "invalid_token":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Invalid refresh token"}
                )
            elif error_type == "invalid_token_type":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Invalid token type"}
                )
            elif error_type == "refresh_token_not_found":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Refresh token not found"}
                )
            elif error_type == "refresh_token_inactive":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Refresh token is inactive"}
                )
            elif error_type == "refresh_token_expired":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Refresh token has expired"}
                )
            else:
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Could not validate refresh token"}
                )
        
        # Get user from database
        user = get_user_by_username(db, username)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"status": 401, "message": "User not found"}
            )
        
        # Create new token pair
        access_token, new_refresh_token, expires_in = create_token_pair(user.username, user.role)
        
        # Revoke old refresh token for security (token rotation)
        revoke_refresh_token(refresh_token)
        
        return RefreshTokenResponse(
            status=200,
            message="Tokens refreshed successfully",
            data=RefreshTokenData(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=expires_in
            ),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Token refresh failed: {str(e)}"}
        )


@router.post("/auto-refresh", response_model=RefreshTokenResponse, tags=["Authentication - Login"])
def auto_refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Automatically refresh tokens using token manager"""
    try:
        token_manager = get_token_manager()
        refresh_token = refresh_data.refresh_token
        
        # Attempt auto refresh
        refresh_result = token_manager.attempt_auto_refresh("", refresh_token, db)
        
        if not refresh_result["success"]:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 401, 
                    "message": "Auto refresh failed",
                    "error": refresh_result["error"]
                }
            )
        
        return RefreshTokenResponse(
            status=200,
            message="Tokens refreshed automatically",
            data=RefreshTokenData(
                access_token=refresh_result["tokens"]["access_token"],
                refresh_token=refresh_result["tokens"]["refresh_token"],
                token_type="bearer",
                expires_in=refresh_result["tokens"]["expires_in"]
            ),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": f"Auto refresh failed: {str(e)}"}
        )
