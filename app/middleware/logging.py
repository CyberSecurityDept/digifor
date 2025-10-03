import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        # Log request
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log response - simplified
        process_time = time.time() - start_time
        status_emoji = "" if response.status_code < 400 else ""
        logger.info(f"{status_emoji} {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        return response
