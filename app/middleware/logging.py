import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
<<<<<<< HEAD
        # Create a more structured log message
        log_message = f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
        
        # Log with appropriate level based on status code
=======
        log_message = f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
        
>>>>>>> analytics-fix
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return response
