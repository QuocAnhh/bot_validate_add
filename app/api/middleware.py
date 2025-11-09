"""API middleware for logging"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response"""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} - "
                f"Duration: {duration:.3f}s - "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise

