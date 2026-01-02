"""
Middleware for request/response processing
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import uuid
import time
import structlog
from typing import Callable

logger = structlog.get_logger()


async def add_request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Add request_id to request state and response"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "request_error",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True
        )
        raise

