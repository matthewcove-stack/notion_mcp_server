"""
Custom exceptions and error handling
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class NotionMCPException(Exception):
    """Base exception for Notion MCP errors"""
    
    def __init__(
        self,
        message: str,
        code: str = "unknown_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConnectionNotFoundError(NotionMCPException):
    """Connection ID not found"""
    
    def __init__(self, connection_id: str):
        super().__init__(
            message=f"Connection {connection_id} not found",
            code="connection_not_found",
            status_code=404,
            details={"connection_id": connection_id}
        )


class NotionAPIError(NotionMCPException):
    """Notion API error"""
    
    def __init__(self, message: str, notion_code: Optional[str] = None):
        super().__init__(
            message=f"Notion API error: {message}",
            code=notion_code or "notion_api_error",
            status_code=502,
            details={"notion_error": message}
        )


class ValidationError(NotionMCPException):
    """Request validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details=details
        )


class AuthenticationError(NotionMCPException):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="authentication_error",
            status_code=401
        )


class AuthorizationError(NotionMCPException):
    """Authorization error"""
    
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            message=message,
            code="authorization_error",
            status_code=403
        )


class IdempotencyConflictError(NotionMCPException):
    """Idempotency key conflict"""
    
    def __init__(self):
        super().__init__(
            message="Idempotency key used for different request",
            code="idempotency_conflict",
            status_code=409
        )


def create_error_response(
    request_id: str,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standard error response envelope
    """
    return {
        "ok": False,
        "result": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        },
        "meta": {
            "request_id": request_id
        }
    }


async def notion_mcp_exception_handler(request: Request, exc: NotionMCPException):
    """
    Global exception handler for NotionMCPException
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "exception_handled",
        request_id=request_id,
        error_code=exc.code,
        error_message=exc.message,
        status_code=exc.status_code,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            request_id=request_id,
            code=exc.code,
            message=exc.message,
            details=exc.details
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            request_id=request_id,
            code="internal_error",
            message="An unexpected error occurred",
            details={"error": str(exc)}
        )
    )

