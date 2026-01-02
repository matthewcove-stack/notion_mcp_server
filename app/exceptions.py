"""
Custom exceptions and exception handlers
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.models.schemas import StandardResponse, ErrorDetail

logger = structlog.get_logger()


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standard response envelope"""
    request_id = getattr(request.state, "request_id", None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse(
            ok=False,
            result=None,
            error=ErrorDetail(
                code=f"http_{exc.status_code}",
                message=exc.detail or "HTTP error occurred",
                details={}
            ).dict(),
            meta={"request_id": request_id} if request_id else {}
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with standard response envelope"""
    request_id = getattr(request.state, "request_id", None)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=StandardResponse(
            ok=False,
            result=None,
            error=ErrorDetail(
                code="validation_error",
                message="Request validation failed",
                details={"errors": exc.errors()}
            ).dict(),
            meta={"request_id": request_id} if request_id else {}
        ).dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standard response envelope"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        "unexpected_error",
        request_id=request_id,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=StandardResponse(
            ok=False,
            result=None,
            error=ErrorDetail(
                code="internal_error",
                message="An internal error occurred",
                details={}
            ).dict(),
            meta={"request_id": request_id} if request_id else {}
        ).dict()
    )

