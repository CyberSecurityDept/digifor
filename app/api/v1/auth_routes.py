from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from jose import JWTError, ExpiredSignatureError
from fastapi.responses import JSONResponse
from fastapi import Security
from app.db.session import get_db
from app.auth import schemas, service
from app.auth.models import User
from app.core.config import settings
from app.core import security
from fastapi.security import OAuth2PasswordBearer
from app.api.deps import get_current_user
from app.utils.security import validate_sql_injection_patterns, sanitize_input
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")
@router.post("/login")
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    if not data.email or not data.email.strip():
        return JSONResponse(
            {"status": 400, "message": "Email is required", "data": None},
            status_code=400
        )
    
    if not validate_sql_injection_patterns(data.email):
        return JSONResponse(
            {"status": 400, "message": "Invalid characters detected in email. Please remove any SQL injection attempts or malicious code.", "data": None},
            status_code=400
        )
    
    email = sanitize_input(data.email.strip().lower(), max_length=255)
    if not email or '@' not in email or '.' not in email.split('@')[1]:
        return JSONResponse(
            {"status": 400, "message": "Invalid email format", "data": None},
            status_code=400
        )
    
    if not data.password or not data.password.strip():
        return JSONResponse(
            {"status": 400, "message": "Password is required", "data": None},
            status_code=400
        )
    
    if not validate_sql_injection_patterns(data.password):
        return JSONResponse(
            {"status": 400, "message": "Invalid characters detected in password. Please remove any SQL injection attempts or malicious code.", "data": None},
            status_code=400
        )
    
    password = data.password.strip()
    if len(password) < 8:
        return JSONResponse(
            {"status": 400, "message": "Password must be at least 8 characters long", "data": None},
            status_code=400
        )
    if len(password) > 128:
        return JSONResponse(
            {"status": 400, "message": "Password must not exceed 128 characters", "data": None},
            status_code=400
        )
    
    user = service.get_user_by_email(db, email)
    if not user:
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )
    
    if user.is_active is False:
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )
    
    password_valid = service.verify_password(password, user.hashed_password)
    if not password_valid:
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )

    access_token = security.create_access_token(subject=str(user.id))
    
    refresh_token_obj = service.create_refresh_token(db, user)

    user_data = {
        "id": user.id,
        "email": user.email,
        "fullname": user.fullname,
        "tag": user.tag,
        "role": user.role
    }

    return JSONResponse(
        {
            "status": 200,
            "message": "Login successful",
            "data": {
                "user": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token_obj.token
            }
        },
        status_code=200
    )

@router.post("/refresh")
def refresh_token(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    if not data.refresh_token or not data.refresh_token.strip():
        return JSONResponse(
            {"status": 400, "message": "Refresh token is required", "data": None},
            status_code=400
        )
    
    if not validate_sql_injection_patterns(data.refresh_token):
        return JSONResponse(
            {"status": 400, "message": "Invalid characters detected in refresh token. Please remove any SQL injection attempts or malicious code.", "data": None},
            status_code=400
        )
    
    refresh_token_clean = data.refresh_token.strip()
    
    if len(refresh_token_clean) < 20 or len(refresh_token_clean) > 1000:
        return JSONResponse(
            {"status": 400, "message": "Invalid refresh token format", "data": None},
            status_code=400
        )
    
    user = service.use_refresh_token(db, refresh_token_clean)
    if not user:
        return JSONResponse(
            {"status": 401, "message": "Invalid or expired refresh token", "data": None},
            status_code=401
        )

    service.revoke_refresh_token(db, refresh_token_clean)
    
    new_refresh_token = service.create_refresh_token(db, user)

    access_token = security.create_access_token(subject=str(user.id))

    return JSONResponse(
        {
            "status": 200,
            "message": "Token refreshed successfully",
            "data": {
                "access_token": access_token,
                "refresh_token": new_refresh_token.token
            }
        },
        status_code=200
    )

@router.get(
    "/me",
    summary="Get current user profile",
    openapi_extra={"security": [{"BearerAuth": []}]}
)

def get_me(request: Request, current_user: User = Depends(get_current_user)):
    try:
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "fullname": current_user.fullname,
            "tag": current_user.tag,
            "role": current_user.role,
            "password": current_user.password or ""
        }
        
        return JSONResponse(
            {
                "status": 200,
                "message": "User profile retrieved successfully",
                "data": user_data
            },
            status_code=200
        )
    except AttributeError as e:
        logger.error(f"Get me error - Missing user attribute: {str(e)}", exc_info=True)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to retrieve user profile - missing user data",
                "data": None
            },
            status_code=500
        )
    except Exception as e:
        logger.error(f"Get me error: {str(e)}", exc_info=True)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to retrieve user profile",
                "data": None
            },
            status_code=500
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post(
    "/logout",
    summary="Logout",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1]
            try:
                payload = security.decode_token(access_token)
                exp_timestamp = payload.get("exp")
                if exp_timestamp:
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    service.blacklist_access_token(db, access_token, current_user.id, expires_at)
            except (JWTError, ExpiredSignatureError):
                pass
        
        tokens = db.query(service.models.RefreshToken).filter(
            service.models.RefreshToken.user_id == current_user.id,
            service.models.RefreshToken.revoked == False
        ).all()

        for token in tokens:
            setattr(token, 'revoked', True)
            db.add(token)
        db.commit()

        return JSONResponse(
            {
                "status": 200,
                "message": "Logout successful. Access token revoked.",
                "data": None
            },
            status_code=200
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to logout user",
                "data": None
            },
            status_code=500
        )