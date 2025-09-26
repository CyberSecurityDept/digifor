from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.models.user import User
from app.utils.security import verify_token_with_error_info
from app.utils.token_manager import get_token_manager, TokenManager
from app.api.auth import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/oauth2/token")


async def get_current_user_with_auto_refresh(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": "401", "message": "Token not provided"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get token manager
    token_manager = get_token_manager()
    
    # Get refresh token from request
    refresh_token = _get_refresh_token_from_request(request)
    
    # Validate and refresh if needed
    validation_result = token_manager.validate_and_refresh_if_needed(token, refresh_token, db)
    
    if not validation_result["token_valid"]:
        if validation_result["refresh_attempted"] and validation_result["refresh_success"]:
            # Token was refreshed successfully, add new tokens to request state
            refresh_result = validation_result["refresh_result"]
            request.state.new_tokens = refresh_result["tokens"]
            request.state.token_refreshed = True
            
            # Use new access token
            token = refresh_result["tokens"]["access_token"]
        else:
            # Token invalid and refresh failed
            error_msg = validation_result.get("error", "Could not validate credentials")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": error_msg},
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif validation_result["refresh_attempted"] and validation_result["refresh_success"]:
        # Token was valid but refreshed anyway, add new tokens to request state
        refresh_result = validation_result["refresh_result"]
        request.state.new_tokens = refresh_result["tokens"]
        request.state.token_refreshed = True

    # Verify the token (either original or new)
    username, error_type = verify_token_with_error_info(token)
    
    if username is None:
        if error_type == "invalid_token":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_not_found":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session not found"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_inactive":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session is inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_expired":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = get_user_by_username(db, username)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": "401", "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user_with_auto_refresh(
    current_user: User = Depends(get_current_user_with_auto_refresh)
) -> User:
    if not current_user.is_active:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "400", "message": "Inactive user"}
        )
    return current_user


def _get_refresh_token_from_request(request: Request) -> Optional[str]:
    # Try to get from custom header
    refresh_token = request.headers.get("X-Refresh-Token")
    if refresh_token:
        return refresh_token
    
    # Try to get from cookies
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        return refresh_token
    
    return None


def get_token_refresh_info(request: Request) -> Dict[str, Any]:
    return {
        "token_refreshed": getattr(request.state, "token_refreshed", False),
        "new_tokens": getattr(request.state, "new_tokens", None)
    }


class TokenRefreshResponse:
    @staticmethod
    def add_refresh_headers(response, request: Request):
        refresh_info = get_token_refresh_info(request)
        
        if refresh_info["token_refreshed"] and refresh_info["new_tokens"]:
            tokens = refresh_info["new_tokens"]
            response.headers["X-New-Access-Token"] = tokens["access_token"]
            response.headers["X-New-Refresh-Token"] = tokens["refresh_token"]
            response.headers["X-Token-Expires-In"] = str(tokens["expires_in"])
            response.headers["X-Token-Refreshed"] = "true"
        
        return response


# Legacy dependencies untuk backward compatibility
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": "401", "message": "Token not provided"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, error_type = verify_token_with_error_info(token)
    
    if username is None:
        if error_type == "invalid_token":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_not_found":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session not found"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_inactive":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session is inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_expired":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Session has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "401", "message": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = get_user_by_username(db, username)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": "401", "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "400", "message": "Inactive user"}
        )
    return current_user


async def get_current_active_user_safe(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "401", "message": "Token not provided"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, error_type = verify_token_with_error_info(token)
    
    if username is None:
        if error_type == "invalid_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_not_found":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session not found"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_inactive":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session is inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif error_type == "session_expired":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Session has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "401", "message": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "401", "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "400", "message": "Inactive user"}
        )
    
    return user
