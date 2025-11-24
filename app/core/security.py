# app/core/security.py
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_access_token(subject: str, expires_delta=None) -> str:
    now = datetime.now(timezone.utc)
    
    if expires_delta is None:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        if expire_minutes < 1440:
            logger.warning(f"ACCESS_TOKEN_EXPIRE_MINUTES is {expire_minutes} minutes, expected 1440 minutes (24 hours). Using 1440 minutes instead.")
            expire_minutes = 1440
        expires_delta = timedelta(minutes=expire_minutes)
    
    expire = now + expires_delta
    
    logger.info(f"Creating access token for user {subject}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES from config: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    logger.info(f"Token created at (UTC): {now.isoformat()}")
    logger.info(f"Token expires at (UTC): {expire.isoformat()}")
    logger.info(f"Expiration duration: {expires_delta.total_seconds() / 3600:.2f} hours ({expires_delta.total_seconds() / 60:.0f} minutes)")
    
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
    exp_timestamp = decoded.get("exp")
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    actual_duration_hours = (exp_datetime - now).total_seconds() / 3600
    actual_duration_minutes = (exp_datetime - now).total_seconds() / 60
    
    logger.info(f"Verified token expiration: {exp_datetime.isoformat()}")
    logger.info(f"Actual duration: {actual_duration_hours:.2f} hours ({actual_duration_minutes:.0f} minutes)")
    
    if abs(actual_duration_minutes - 1440) > 1:
        logger.error(f"WARNING: Token expiration is {actual_duration_minutes:.0f} minutes, expected 1440 minutes (24 hours)!")
    
    return token


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_exp": True},
    )
