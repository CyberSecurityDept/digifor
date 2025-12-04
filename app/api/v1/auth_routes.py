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


router = APIRouter(prefix="/auth")
@router.post("/login")
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = service.get_user_by_email(db, data.email)
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
    
    password_valid = service.verify_password(data.password, user.hashed_password)
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
    user = service.use_refresh_token(db, data.refresh_token)
    if not user:
        return JSONResponse(
            {"status": 401, "message": "Invalid or expired refresh token", "data": None},
            status_code=401
        )

    service.revoke_refresh_token(db, data.refresh_token)
    
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
def get_me(
    request: Request,
    current_user: User = Depends(get_current_user)
):
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
        print(f"Get me error - Missing user attribute: {e}")
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to retrieve user profile - missing user data",
                "data": None
            },
            status_code=500
        )
    except Exception as e:
        print(f"Get me error: {e}")
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
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        print("Logout error:", e)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to logout user",
                "data": None
            },
            status_code=500
        )