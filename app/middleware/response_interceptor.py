from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class TokenRefreshResponseInterceptor(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Check if request has token refresh info
        if hasattr(request.state, "token_refreshed") and request.state.token_refreshed:
            if hasattr(request.state, "new_tokens") and request.state.new_tokens:
                tokens = request.state.new_tokens
                
                # Add new token headers
                response.headers["X-New-Access-Token"] = tokens["access_token"]
                response.headers["X-New-Refresh-Token"] = tokens["refresh_token"]
                response.headers["X-Token-Expires-In"] = str(tokens["expires_in"])
                response.headers["X-Token-Refreshed"] = "true"
                
                logger.info(f"Token refreshed for user: {tokens.get('user_info', {}).get('username', 'unknown')}")
        
        return response
