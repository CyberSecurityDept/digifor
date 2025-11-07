from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Generator

from app.db.session import get_db


def get_database(db: Session = Depends(get_db)) -> Session:
    return db

def get_current_user():
    return {"id": "system", "username": "system", "role": "admin"}

def require_permission(permission: str):
    def permission_checker(current_user: dict = Depends(get_current_user)):
        return current_user
    return permission_checker