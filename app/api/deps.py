from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Generator, Optional, List
from app.db.session import get_db
from app.auth.models import User

def get_database(db: Session = Depends(get_db)) -> Session:
    return db

def get_current_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "status": 401,
                "message": "Unauthorized - User not found in request state",
                "data": None
            }
        )
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Use getattr to avoid SQLAlchemy Column type issues
        user_role = getattr(current_user, "role", None)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": 403,
                    "message": f"Forbidden - Required role: {', '.join(allowed_roles)}",
                    "data": None
                }
            )
        return current_user
    return role_checker

def require_any_role(*allowed_roles: str):
    allowed_roles_list = list(allowed_roles)
    return require_role(allowed_roles_list)

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    # Use getattr to avoid SQLAlchemy Column type issues
    user_role = getattr(current_user, "role", None)
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail={
                "status": 403,
                "message": "Forbidden - Admin access required",
                "data": None
            }
        )
    return current_user

def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Check is_active using getattr to avoid SQLAlchemy Column type issues
    is_active = getattr(current_user, "is_active", False)
    if not is_active:
        raise HTTPException(
            status_code=403,
            detail={
                "status": 403,
                "message": "Forbidden - User account is inactive",
                "data": None
            }
        )
    return current_user