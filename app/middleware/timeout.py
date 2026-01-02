"""
Timeout middleware for request handling
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog
import asyncio

from app.models.schemas import StandardResponse

logger = structlog.get_logger()

# Default timeout: 30 seconds for most endpoints, 60 seconds for jobs
DEFAULT_TIMEOUT = 30.0
JOB_TIMEOUT = 60.0


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts"""
    
    def __init__(self, app, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        """Dispatch with timeout"""
        # Determine timeout based on endpoint
        timeout = self.timeout
        if "/jobs" in request.url.path or "/bulk" in request.url.path:
            timeout = JOB_TIMEOUT
        
        try:
            # Run with timeout
            response = await asyncio.wait_for(call_next(request), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(
                "request_timeout",
                path=request.url.path,
                method=request.method,
                timeout=timeout,
            )
            return JSONResponse(
                status_code=504,
                content=StandardResponse(
                    ok=False,
                    error={
                        "code": "timeout",
                        "message": f"Request timed out after {timeout}s",
                        "details": {},
                    },
                    meta={"request_id": getattr(request.state, "request_id", None)},
                ).dict()
            )

