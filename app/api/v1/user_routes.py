from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.responses import JSONResponse
from app.db.session import get_db
from app.auth.models import User
from app.api.deps import require_admin
from app.user_management import service as user_service
from app.user_management.schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["User Management"])

@router.get(
    "/get-all-users",
    summary="Get all users (Admin Only)",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def get_all_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search keyword (searches in name, email)"),
    tag: Optional[str] = Query(None, description="Filter by tag: Admin, Investigator, Ahli Forensic"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        result = user_service.get_all_users(db, skip, limit, search, tag)
        users_data = []
        for user in result["users"]:
            created_at_value = getattr(user, 'created_at', None)
            created_at_str = created_at_value.isoformat() if created_at_value is not None else None
            
            users_data.append({
                "id": user.id,
                "fullname": user.fullname,
                "email": user.email,
                "role": user.role,
                "tag": user.tag,
                "is_active": user.is_active,
                "created_at": created_at_str
            })
        
        return JSONResponse(
            {
                "status": 200,
                "message": "Users retrieved successfully",
                "data": users_data,
                "total": result["total"],
                "page": skip // limit + 1 if limit > 0 else 1,
                "size": limit
            },
            status_code=200
        )
    except Exception as e:
        print(f"Get all users error: {e}")
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to retrieve users",
                "data": None
            },
            status_code=500
        )

@router.post(
    "/create-user",
    summary="Create user (Admin Only)",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        user = user_service.create_user(db, user_data)
        created_at_value = getattr(user, 'created_at', None)
        created_at_str = created_at_value.isoformat() if created_at_value is not None else None
        
        return JSONResponse(
            {
                "status": 201,
                "message": "User created successfully",
                "data": {
                    "id": user.id,
                    "fullname": user.fullname,
                    "email": user.email,
                    "role": user.role,
                    "tag": user.tag,
                    "is_active": user.is_active,
                    "created_at": created_at_str
                }
            },
            status_code=201
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Create user error: {e}")
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to create user",
                "data": None
            },
            status_code=500
        )

@router.put(
    "/update-user/{user_id}",
    summary="Update user (Admin Only)",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def update_user(
    request: Request,
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        user = user_service.update_user(db, user_id, user_data)
        created_at_value = getattr(user, 'created_at', None)
        created_at_str = created_at_value.isoformat() if created_at_value is not None else None
        
        return JSONResponse(
            {
                "status": 200,
                "message": "User updated successfully",
                "data": {
                    "id": user.id,
                    "fullname": user.fullname,
                    "email": user.email,
                    "role": user.role,
                    "tag": user.tag,
                    "is_active": user.is_active,
                    "created_at": created_at_str
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Update user error: {e}")
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to update user",
                "data": None
            },
            status_code=500
        )

@router.delete(
    "/delete-user/{user_id}",
    summary="Delete user (Admin Only)",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        user_service.delete_user(db, user_id)
        
        return JSONResponse(
            {
                "status": 200,
                "message": "User deleted successfully",
                "data": None
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Delete user error: {e}")
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to delete user",
                "data": None
            },
            status_code=500
        )

