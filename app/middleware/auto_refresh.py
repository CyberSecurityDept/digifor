from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import logging
from typing import Optional, Dict, Any

from app.utils.security import (
    verify_token_with_error_info,
    verify_refresh_token,
    create_token_pair,
    revoke_refresh_token
)

logger = logging.getLogger(__name__)


class AutoRefreshTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, auto_refresh_threshold: int = 300):
        super().__init__(app)
        self.auto_refresh_threshold = auto_refresh_threshold
        
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip middleware untuk endpoint tertentu
        if self._should_skip_middleware(request):
            return await call_next(request)
        
        # Process request first
        response = await call_next(request)
        
        # Only check for auto refresh if request was successful and has token
        if response.status_code == 200:
            token = self._extract_token(request)
            if token:
                # Check if token needs refresh
                refresh_info = self._check_token_refresh_needed(token)
                
                if refresh_info["needs_refresh"]:
                    # Attempt automatic refresh
                    refresh_result = await self._attempt_auto_refresh(token, request)
                    
                    if refresh_result["success"]:
                        # Add new tokens to response headers
                        return self._add_refresh_headers(response, refresh_result["tokens"])
        
        return response
    
    def _should_skip_middleware(self, request: Request) -> bool:
        skip_paths = [
            "/api/v1/auth/token",
            "/api/v1/auth/refresh", 
            "/api/v1/auth/auto-refresh",
            "/api/v1/auth/register",
            "/api/v1/auth/request-password-reset",
            "/api/v1/auth/reset-password",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    def _check_token_refresh_needed(self, token: str) -> Dict[str, Any]:
        try:
            from jose import jwt, JWTError
            from datetime import datetime, timezone
            
            # Decode token without verification to check expiration
            payload = jwt.get_unverified_claims(token)
            exp_timestamp = payload.get("exp")
            
            if not exp_timestamp:
                return {"needs_refresh": False, "reason": "no_exp"}
            
            # Calculate time until expiration
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            time_until_expiry = (exp_datetime - now).total_seconds()
            
            # Check if token expires within threshold
            needs_refresh = time_until_expiry <= self.auto_refresh_threshold
            
            return {
                "needs_refresh": needs_refresh,
                "time_until_expiry": time_until_expiry,
                "expires_at": exp_datetime.isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error checking token refresh: {e}")
            return {"needs_refresh": False, "reason": "error", "error": str(e)}
    
    async def _attempt_auto_refresh(self, token: str, request: Request) -> Dict[str, Any]:
        try:
            # Get refresh token from request (could be in header, cookie, or body)
            refresh_token = self._get_refresh_token_from_request(request)
            
            if not refresh_token:
                return {
                    "success": False,
                    "error": "No refresh token available for automatic refresh"
                }
            
            # Verify refresh token
            username, role, error_type = verify_refresh_token(refresh_token)
            
            if username is None:
                return {
                    "success": False,
                    "error": f"Invalid refresh token: {error_type}"
                }
            
            # Create new token pair
            access_token, new_refresh_token, expires_in = create_token_pair(username, role)
            
            # Revoke old refresh token for security
            revoke_refresh_token(refresh_token)
            
            return {
                "success": True,
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                    "expires_in": expires_in
                }
            }
            
        except Exception as e:
            logger.error(f"Error during auto refresh: {e}")
            return {
                "success": False,
                "error": f"Auto refresh failed: {str(e)}"
            }
    
    def _get_refresh_token_from_request(self, request: Request) -> Optional[str]:
        # Try to get from custom header
        refresh_token = request.headers.get("X-Refresh-Token")
        if refresh_token:
            return refresh_token
        
        # Try to get from cookies
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            return refresh_token
        
        # Try to get from request body (for POST requests)
        if request.method == "POST":
            try:
                # This is a bit tricky as we can't read the body twice
                # In practice, you might want to store refresh token in a more accessible way
                pass
            except:
                pass
        
        return None
    
    def _add_refresh_headers(self, response: Response, tokens: Dict[str, Any]) -> Response:
        # Add new access token
        response.headers["X-New-Access-Token"] = tokens["access_token"]
        response.headers["X-New-Refresh-Token"] = tokens["refresh_token"]
        response.headers["X-Token-Expires-In"] = str(tokens["expires_in"])
        
        # Add informational header
        response.headers["X-Token-Refreshed"] = "true"
        
        return response
    
    def _create_refresh_error_response(self, error: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "status": 401,
                "message": "Token refresh required",
                "error": error,
                "auto_refresh_failed": True
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "X-Token-Refresh-Required": "true"
            }
        )


class TokenRotationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip untuk endpoint tertentu
        if self._should_skip_middleware(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Check if this was a successful authenticated request
        if self._is_authenticated_request(request, response):
            # Add token rotation headers
            response.headers["X-Token-Rotation-Enabled"] = "true"
        
        return response
    
    def _should_skip_middleware(self, request: Request) -> bool:
        skip_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _is_authenticated_request(self, request: Request, response: Response) -> bool:
        # Check if request had authorization header
        has_auth = request.headers.get("Authorization", "").startswith("Bearer ")
        
        # Check if response was successful
        is_successful = 200 <= response.status_code < 300
        
        return has_auth and is_successful
