"""
Middleware for audit logging and idempotency
"""
from fastapi import Request, Response
from typing import Callable
import structlog
import uuid

from app.services.audit import log_audit, extract_notion_ids
from app.services.idempotency import check_idempotency, store_idempotency

logger = structlog.get_logger()

# Write operations that should be audited
WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

# Endpoints that should be audited (write operations)
AUDIT_ENDPOINTS = {
    "/v1/databases",
    "/v1/pages",
    "/v1/blocks",
    "/v1/upsert",
    "/v1/link",
    "/v1/bulk",
    "/v1/jobs",
}


async def audit_and_idempotency_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle audit logging and idempotency for write operations
    """
    # Skip for non-write operations
    if request.method not in WRITE_METHODS:
        return await call_next(request)
    
    # Skip for non-audited endpoints
    path = request.url.path
    if not any(path.startswith(ep) for ep in AUDIT_ENDPOINTS):
        return await call_next(request)
    
    # Get idempotency key from header
    idempotency_key = request.headers.get("Idempotency-Key")
    
    # Get connection_id from request (will be in body for POST/PATCH)
    connection_id = None
    request_body = None
    
    # Try to get connection_id and body for idempotency check
    if request.method in {"POST", "PATCH"}:
        try:
            # Read body (FastAPI will parse it later, but we need it for idempotency)
            # Note: This is a simplified approach - in production, you might want to
            # cache the parsed body or use a different approach
            pass  # Will handle in endpoint decorators instead
        except Exception:
            pass
    
    # Check idempotency if key provided
    cached_response = None
    if idempotency_key:
        # Note: We'll handle idempotency in individual endpoints since we need
        # access to parsed request body
        pass
    
    # Process request
    response = await call_next(request)
    
    # Audit logging will be handled in endpoint decorators
    # since we need access to the response body and parsed request
    
    return response

