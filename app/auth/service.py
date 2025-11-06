import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.auth import models
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password menggunakan bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password plain terhadap hash tersimpan."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Ambil user berdasarkan email."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    fullname: str,
    role: str = "user",
) -> models.User:
    """Buat user baru (default role='user')."""
    hashed_pw = get_password_hash(password)
    user = models.User(
        email=email,
        fullname=fullname,
        hashed_password=hashed_pw,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_refresh_token(db: Session, user: models.User) -> models.RefreshToken:
    """Buat refresh token baru untuk user tertentu."""
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
    """Revoke refresh token agar tidak bisa dipakai lagi."""
    rt = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token_str)
        .first()
    )
    if rt and not rt.revoked:
        rt.revoked = True
        db.commit()


def use_refresh_token(db: Session, token_str: str) -> Optional[models.User]:
    """Gunakan refresh token dan kembalikan user jika token valid."""
    rt = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token_str)
        .first()
    )
    if not rt or rt.revoked or rt.expires_at < datetime.utcnow():
        return None
    return db.query(models.User).filter(models.User.id == rt.user_id).first()
