from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.session import get_db
from app.auth.models import User
from app.auth.service import get_password_hash as hash_password

router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)

class UserBase(BaseModel):
    email: EmailStr
    fullname: str
    tag: str
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    tag: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
@router.get("/get-users")
def get_users(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Jumlah user per halaman"),
    offset: int = Query(0, ge=0, description="Mulai dari index ke-berapa"),
    search: Optional[str] = Query(None, description="Kata kunci pencarian (fullname, email, atau tag)")
):
    query = db.query(User)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (User.fullname.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.tag.ilike(search_term))
        )

    total_users = query.count()
    users = query.offset(offset).limit(limit).all()

    users_data = [
        {
            "id": user.id,
            "email": user.email,
            "fullname": user.fullname,
            "tag": user.tag,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]

    return {
        "status": status.HTTP_200_OK,
        "message": "Success get users",
        "data": {
            "total": total_users,
            "limit": limit,
            "offset": offset,
            "users": users_data
        }
    }



@router.post("/add-user", status_code=status.HTTP_201_CREATED)
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Email already registered",
            "data": None
        }
    
    new_user = User(
        email=user.email,
        fullname=user.fullname,
        tag=user.tag,
        hashed_password=hash_password(user.password),
        role=user.role if user.role else "user",
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_data = {
        "id": new_user.id,
        "email": new_user.email,
        "fullname": new_user.fullname,
        "tag": new_user.tag,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at
    }

    return {
        "status": status.HTTP_201_CREATED,
        "message": "User created successfully",
        "data": user_data
    }

@router.put("/update-user/{user_id}")
def update_user(
    user_id: int = Path(..., description="ID user yang ingin diupdate"),
    user_update: UserUpdate = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "User not found",
            "data": None
        }

    if user_update.fullname is not None:
        setattr(user, 'fullname', user_update.fullname)
    if user_update.tag is not None:
        setattr(user, 'tag', user_update.tag)
    if user_update.role is not None:
        setattr(user, 'role', user_update.role)
    if user_update.password is not None:
        setattr(user, 'hashed_password', hash_password(user_update.password))
    if user_update.is_active is not None:
        setattr(user, 'is_active', user_update.is_active)

    db.commit()
    db.refresh(user)

    updated_data = {
        "id": user.id,
        "email": user.email,
        "fullname": user.fullname,
        "tag": user.tag,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

    return {
        "status": status.HTTP_200_OK,
        "message": "User updated successfully",
        "data": updated_data
    }

@router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: int = Path(..., description="ID user yang ingin dihapus"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "User not found",
            "data": None
        }

    db.delete(user)
    db.commit()

    return {
        "status": status.HTTP_200_OK,
        "message": f"User with id {user_id} deleted successfully",
        "data": None
    }
