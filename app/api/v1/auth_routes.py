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


router = APIRouter(prefix="/auth")
@router.post("/login")
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = service.get_user_by_email(db, data.email)
    if not user:
        print(f"Login failed: User with email '{data.email}' not found")
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )
    
    if not user.is_active:
        print(f"Login failed: User '{data.email}' is inactive")
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )
    
    password_valid = service.verify_password(data.password, user.hashed_password)
    if not password_valid:
        print(f"Login failed: Invalid password for user '{data.email}'")
        try:
            new_hash = service.get_password_hash(data.password)
            print(f"New hash would be: {new_hash[:50]}...")
        except Exception as e:
            print(f"Error generating new hash: {e}")
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )

    access_token = security.create_access_token(subject=str(user.id))

    token_data = access_token

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
                "access_token": token_data
            }
        },
        status_code=200
    )

# @router.post("/refresh")
# def refresh_token(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
#     user = service.use_refresh_token(db, data.refresh_token)
#     if not user:
#         return JSONResponse(
#             {"status": 401, "message": "Invalid or expired refresh token", "data": None},
#             status_code=401
#         )

#     service.revoke_refresh_token(db, data.refresh_token)
#     new_rt = service.create_refresh_token(db, user)

#     access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = security.create_access_token(subject=str(user.id), expires_delta=access_expires)

#     token_data = schemas.Token(access_token=access_token, refresh_token=new_rt.token)
#     return JSONResponse(
#         {"status": 200, "message": "Token refreshed successfully", "data": token_data.model_dump()},
#         status_code=200
#     )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        if service.is_token_blacklisted(db, token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        payload = security.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = int(payload["sub"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user

@router.post(
    "/logout",
    summary="Logout",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def logout(
    request: Request,
    current_user: User = Security(get_current_user),
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
            token.revoked = True
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