from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
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
# --------------------------------------------------
# Login
# --------------------------------------------------
@router.post("/login")
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = service.get_user_by_email(db, data.email)
    if not user or not service.verify_password(data.password, user.hashed_password):
        return JSONResponse(
            {"status": 401, "message": "Invalid credentials", "data": None},
            status_code=401
        )

    # 🔥 Token tanpa expired (lifetime)
    access_token = security.create_access_token(subject=str(user.id))

    # ✅ Jangan pakai koma di sini
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

# --------------------------------------------------
# Current User (protected)
# --------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
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

# --------------------------------------------------
# Logout (Revoke All Refresh Tokens)
# --------------------------------------------------
@router.post(
    "/logout",
    summary="Logout",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def logout(current_user: User = Security(get_current_user), db: Session = Depends(get_db)):

    try:
        # revoke semua refresh token milik user ini
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
                "message": "Logout successful. All refresh tokens revoked.",
                "data": None
            },
            status_code=200
        )
    except Exception as e:
        db.rollback()
        print("❌ Logout error:", e)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to logout user",
                "data": None
            },
            status_code=500
        )