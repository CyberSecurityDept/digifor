from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.responses import JSONResponse
from app.db.session import get_db
from app.auth.models import User
from app.api.deps import require_admin
from app.user_management import service as user_service
from app.user_management.schemas import UserCreate, UserUpdate
from app.utils.security import sanitize_input, validate_sql_injection_patterns
import logging

logger = logging.getLogger(__name__)

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
        if search:
            if not validate_sql_injection_patterns(search):
                return JSONResponse(
                    {
                        "status": 400,
                        "message": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            search = sanitize_input(search, max_length=255)
        
        if tag:
            if not validate_sql_injection_patterns(tag):
                return JSONResponse(
                    {
                        "status": 400,
                        "message": "Invalid characters detected in tag parameter. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            tag = sanitize_input(tag, max_length=100)
        
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
        logger.error(f"Error in get_all_users: {str(e)}", exc_info=True)
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
        if not validate_sql_injection_patterns(user_data.fullname):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in fullname. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.fullname = sanitize_input(user_data.fullname, max_length=255)
        
        if not validate_sql_injection_patterns(user_data.email):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in email. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.email = sanitize_input(user_data.email.strip().lower(), max_length=255)
        
        if not validate_sql_injection_patterns(user_data.password):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in password. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        
        if not validate_sql_injection_patterns(user_data.confirm_password):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in confirm_password. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        
        if not validate_sql_injection_patterns(user_data.tag):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in tag. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.tag = sanitize_input(user_data.tag, max_length=100)
        
        if '@' not in user_data.email or '.' not in user_data.email.split('@')[1]:
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid email format",
                    "data": None
                },
                status_code=400
            )
        
        if len(user_data.password) < 8 or len(user_data.password) > 128:
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Password must be between 8 and 128 characters long",
                    "data": None
                },
                status_code=400
            )
        
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
        logger.error(f"Error in create_user: {str(e)}", exc_info=True)
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
        if not validate_sql_injection_patterns(user_data.fullname):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in fullname. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.fullname = sanitize_input(user_data.fullname, max_length=255)
        
        if not validate_sql_injection_patterns(user_data.email):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in email. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.email = sanitize_input(user_data.email.strip().lower(), max_length=255)
        
        if not validate_sql_injection_patterns(user_data.password):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in password. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        
        if not validate_sql_injection_patterns(user_data.confirm_password):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in confirm_password. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        
        if not validate_sql_injection_patterns(user_data.tag):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in tag. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400
            )
        user_data.tag = sanitize_input(user_data.tag, max_length=100)
        
        if '@' not in user_data.email or '.' not in user_data.email.split('@')[1]:
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid email format",
                    "data": None
                },
                status_code=400
            )
        
        if len(user_data.password) < 8 or len(user_data.password) > 128:
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Password must be between 8 and 128 characters long",
                    "data": None
                },
                status_code=400
            )
        
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
        logger.error(f"Error in update_user: {str(e)}", exc_info=True)
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
        logger.error(f"Error in delete_user: {str(e)}", exc_info=True)
        return JSONResponse(
            {
                "status": 500,
                "message": "Failed to delete user",
                "data": None
            },
            status_code=500
        )

