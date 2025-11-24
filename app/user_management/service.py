from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.auth.models import User
from app.auth import service as auth_service
from app.user_management.schemas import UserCreate, UserUpdate
from fastapi import HTTPException

def _tag_to_role(tag: str) -> str:
    tag_lower = tag.strip().lower()
    if tag_lower == "admin":
        return "admin"
    else:
        return "user"

def get_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    tag: Optional[str] = None
) -> Dict:
    query = db.query(User)
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.fullname).like(search_term),
                func.lower(User.email).like(search_term)
            )
        )
    
    if tag:
        query = query.filter(func.lower(User.tag).like(f"%{tag.lower()}%"))

    total = query.count()
    query = query.order_by(User.id.desc())
    users = query.offset(skip).limit(limit).all()
    return {
        "users": users,
        "total": total
    }

def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = auth_service.get_user_by_email(db, user_data.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )

    role = _tag_to_role(user_data.tag)
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        fullname=user_data.fullname,
        tag=user_data.tag,
        role=role,
        password=user_data.password,  # Store plain text password
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if new email already exists (excluding current user)
    existing_user = auth_service.get_user_by_email(db, user_data.email)
    if existing_user is not None:
        existing_id = getattr(existing_user, 'id', None)
        if existing_id is not None and existing_id != user_id:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )
    
    # Update all fields (all required)
    setattr(user, 'email', user_data.email)
    setattr(user, 'fullname', user_data.fullname)
    setattr(user, 'tag', user_data.tag)
    setattr(user, 'role', _tag_to_role(user_data.tag))
    setattr(user, 'password', user_data.password)  # Store plain text password
    setattr(user, 'hashed_password', auth_service.get_password_hash(user_data.password))
    
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found"
        )
    db.delete(user)
    db.commit()
    return True

