import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.auth import models
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(
    db: Session,
    email: str,
    password: str,
    fullname: str,
    role: str = "user",
) -> models.User:
    hashed_pw = get_password_hash(password)
    user = models.User(
        email=email,
        fullname=fullname,
        password=password,
        hashed_password=hashed_pw,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_refresh_token(db: Session, user: models.User) -> models.RefreshToken:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = models.RefreshToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def revoke_refresh_token(db: Session, token_str: str) -> None:
    rt = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token_str)
        .first()
    )
    if rt is not None and rt.revoked is False:
        setattr(rt, 'revoked', True)
        db.commit()


def use_refresh_token(db: Session, token_str: str) -> Optional[models.User]:
    rt = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token_str)
        .first()
    )
    if rt is None:
        return None
    if rt.revoked is True:
        return None
    expires_at = rt.expires_at
    if expires_at is not None:
        if expires_at < datetime.utcnow():
            return None
    return db.query(models.User).filter(models.User.id == rt.user_id).first()


def blacklist_access_token(db: Session, token: str, user_id: int, expires_at: datetime) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    existing = db.query(models.BlacklistedToken).filter(
        models.BlacklistedToken.token_hash == token_hash
    ).first()
    
    if not existing:
        blacklisted = models.BlacklistedToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(blacklisted)
        db.commit()

def is_token_blacklisted(db: Session, token: str) -> bool:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    blacklisted = db.query(models.BlacklistedToken).filter(
        models.BlacklistedToken.token_hash == token_hash
    ).first()
    
    if blacklisted is not None:
        expires_at = blacklisted.expires_at
        if expires_at is not None:
            if expires_at < datetime.utcnow():
                db.delete(blacklisted)
                db.commit()
                return False
        return True
    return False
