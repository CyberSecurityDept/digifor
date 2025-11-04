import re
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, ExpiredSignatureError
from starlette.middleware.base import BaseHTTPMiddleware
from app.core import security
from app.db.session import SessionLocal
from app.auth.models import User


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # === daftar endpoint publik (static) ===
        public_paths = [
            "/",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/api/v1/file-encryptor/convert-to-sdp",
            "/api/v1/file-encryptor/list-sdp",
            "/api/v1/file-encryptor/download-sdp",
            '/health/health',
            '/health/health/ready',
            '/health/health/live',
        ]

        # === daftar endpoint publik dengan pola dinamis ===
        public_patterns = [
            r"^/api/v1/file-encryptor/progress/[^/]+$",  # misal: /progress/mydata_csv
        ]

        path = request.url.path

        # === lewati auth kalau cocok salah satu ===
        if path in public_paths or any(re.match(p, path) for p in public_patterns):
            return await call_next(request)

        # === ambil Authorization header ===
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "status": 401,
                    "message": "Unauthorized",
                    "data": None,
                },
            )

        token = auth_header.split(" ", 1)[1]

        # === validasi token ===
        try:
            payload = security.decode_token(token)
            if payload.get("type") != "access":
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Invalid token type", "data": None},
                )
        except ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"status": 401, "message": "Expired token", "data": None},
            )
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"status": 401, "message": "Invalid token", "data": None},
            )

        # === ambil user dari DB ===
        db = SessionLocal()
        try:
            user_id = int(payload.get("sub"))
            user = db.get(User, user_id)
            if not user or not user.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"status": 401, "message": "Inactive or missing user", "data": None},
                )

            request.state.user = user  # simpan user biar bisa diakses di endpoint
        finally:
            db.close()

        # === lanjut ke endpoint ===
        return await call_next(request)
