import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from app.core.config import settings


class TimeoutMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app, timeout_seconds: int = 3600):  # 1 hour default
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        self.last_activity = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Check if session has timed out
        current_time = time.time()
        if client_ip in self.last_activity:
            if current_time - self.last_activity[client_ip] > self.timeout_seconds:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Session has timed out"
                )
        
        # Update last activity
        self.last_activity[client_ip] = current_time
        
        # Process request
        response = await call_next(request)
        
        return response
