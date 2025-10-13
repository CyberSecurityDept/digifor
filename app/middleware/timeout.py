import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from app.core.config import settings


class TimeoutMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app, timeout_seconds: int = 3600):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        self.last_activity = {}
    
    async def dispatch(self, request: Request, call_next):
        # Skip timeout for file upload endpoints
        if request.url.path in ["/api/v1/analytics/upload-data", "/api/v1/analytics/add-device"]:
            response = await call_next(request)
            return response
        
        client_ip = request.client.host
        
        current_time = time.time()
        if client_ip in self.last_activity:
            if current_time - self.last_activity[client_ip] > self.timeout_seconds:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Session has timed out"
                )
        
        self.last_activity[client_ip] = current_time
        
        response = await call_next(request)
        
        return response
