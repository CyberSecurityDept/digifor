# app/core/security.py
from datetime import datetime, timezone
from jose import jwt, JWTError
from app.core.config import settings

def create_access_token(subject: str, expires_delta=None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "type": "access",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    # ⚙️ Nonaktifkan verifikasi kadaluarsa
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_exp": False},  # ⬅️ penting: token tidak akan kadaluarsa
    )
