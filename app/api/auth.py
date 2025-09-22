from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
    UserProfileResponse,
    UserProfileData,
    UserRegistration,
    UserRegistrationResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    SessionInfo,
    SessionResponse,
    RefreshTokenData,
    RefreshTokenResponse,
    TokenPair,
    RefreshTokenRequest,
)
from app.utils.security import (
    verify_password, 
    create_access_token, 
    verify_token, 
    verify_token_with_error_info,
    get_password_hash,
    validate_password_strength,
    get_session_info,
    revoke_session,
    revoke_all_user_sessions,
    cleanup_expired_sessions,
    get_active_sessions_count,
    create_password_reset_token,
    verify_password_reset_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    cleanup_expired_refresh_tokens,
    get_refresh_tokens_count,
    create_token_pair
)
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/oauth2/token")

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # print("DEBUG TOKEN:", token)

    # Debugging helper
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "401", "message": "Token not provided"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, error_type = verify_token_with_error_info(token)
    
    if username is None:
        if error_type == "invalid_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_not_found":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session not found"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_inactive":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session is inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_expired":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "401", "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=RefreshTokenResponse, responses={401: {"model": LoginErrorResponse, "description": "Invalid credentials"}})
def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login endpoint that accepts JSON body and returns token pair"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"status": "401", "messages": "Invalid username or password"},
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


@router.post("/token-form", response_model=LoginSuccessResponse, responses={401: {"model": LoginErrorResponse, "description": "Invalid credentials"}}, include_in_schema=False)
def login_for_access_token_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login endpoint that accepts form data (OAuth2 standard)"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"status": "401", "messages": "Invalid username or password"},
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


@router.post("/oauth2/token", response_model=Token, include_in_schema=False)
def oauth2_login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
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


@router.get("/me", response_model=UserProfileResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
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


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    refresh_token = refresh_data.refresh_token
    
    # Verify refresh token
    username, role, error_type = verify_refresh_token(refresh_token)
    
    if username is None:
        if error_type == "invalid_token":
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Invalid refresh token"}
            )
        elif error_type == "invalid_token_type":
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Invalid token type"}
            )
        elif error_type == "refresh_token_not_found":
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Refresh token not found"}
            )
        elif error_type == "refresh_token_inactive":
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Refresh token is inactive"}
            )
        elif error_type == "refresh_token_expired":
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Refresh token has expired"}
            )
        else:
            raise HTTPException(
                status_code=401,
                detail={"status": "401", "message": "Could not validate refresh token"}
            )
    
    # Get user from database
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"status": "401", "message": "User not found"}
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


@router.post("/register", response_model=UserRegistrationResponse, status_code=201)
def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Validate password strength
    password_validation = validate_password_strength(user_data.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "422",
                "message": "Password validation failed",
                "errors": password_validation["errors"],
                "strength": password_validation["strength"]
            }
        )
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=400,
            detail={"status": "400", "message": "Username already exists"}
        )
    
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=400,
            detail={"status": "400", "message": "Email already exists"}
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


@router.post("/change-password", response_model=dict)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail={"status": "400", "message": "Current password is incorrect"}
        )
    
    # Validate new password strength
    password_validation = validate_password_strength(password_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "422",
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


@router.post("/request-password-reset", response_model=dict)
def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset"""
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


@router.post("/reset-password", response_model=dict)
def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    # Verify reset token
    email = verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail={"status": "400", "message": "Invalid or expired reset token"}
        )
    
    # Find user by email
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"status": "404", "message": "User not found"}
        )
    
    # Validate new password strength
    password_validation = validate_password_strength(reset_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "422",
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


@router.get("/session", response_model=SessionResponse)
def get_session_info_endpoint(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme)
):
    """Get current session information"""
    session_info = get_session_info(token)
    if not session_info:
        raise HTTPException(
            status_code=401,
            detail={"status": "401", "message": "Session not found"}
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


@router.post("/logout", response_model=dict)
def logout(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme)
):
    """Logout and revoke current session"""
    success = revoke_session(token)
    if not success:
        raise HTTPException(
            status_code=400,
            detail={"status": "400", "message": "Failed to revoke session"}
        )
    
    return {
        "status": 200,
        "message": "Logged out successfully"
    }


@router.post("/logout-all", response_model=dict)
def logout_all_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Logout from all sessions and revoke all refresh tokens"""
    revoked_sessions = revoke_all_user_sessions(current_user.username)
    revoked_refresh_tokens = revoke_all_refresh_tokens(current_user.username)
    
    return {
        "status": 200,
        "message": f"Logged out from {revoked_sessions} sessions and {revoked_refresh_tokens} refresh tokens"
    }


@router.get("/sessions/cleanup", response_model=dict)
def cleanup_sessions():
    """Clean up expired sessions and refresh tokens (admin only)"""
    cleaned_sessions = cleanup_expired_sessions()
    cleaned_refresh_tokens = cleanup_expired_refresh_tokens()
    
    return {
        "status": 200,
        "message": f"Cleaned up {cleaned_sessions} expired sessions and {cleaned_refresh_tokens} expired refresh tokens",
        "active_sessions": get_active_sessions_count(),
        "active_refresh_tokens": get_refresh_tokens_count()
    }
