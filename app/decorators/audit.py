"""
Decorator for audit logging
"""
from functools import wraps
from typing import Callable, Any
from fastapi import Request
from sqlalchemy.orm import Session

from app.services.audit import log_audit, extract_notion_ids


def audit_write_operation(actor: str = "chatgpt_action"):
    """
    Decorator to audit write operations
    
    Usage:
        @audit_write_operation(actor="chatgpt_action")
        async def endpoint(request: Request, db: Session, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and db from kwargs
            request = None
            db = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
            
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                elif isinstance(value, Session):
                    db = value
            
            if not request or not db:
                # Can't audit without request/db, just call function
                return await func(*args, **kwargs)
            
            # Extract connection_id from request body or kwargs
            connection_id = None
            request_id = getattr(request.state, "request_id", None)
            
            # Get connection_id from kwargs (endpoints receive it)
            for key, value in kwargs.items():
                if key == "connection_id" or (isinstance(value, dict) and "connection_id" in value):
                    if isinstance(value, str):
                        connection_id = value
                    elif isinstance(value, dict):
                        connection_id = value.get("connection_id")
                    break
            
            # Also check request body models
            for arg in args:
                if hasattr(arg, "connection_id"):
                    connection_id = getattr(arg, "connection_id")
                    break
            
            # Call the function
            try:
                result = await func(*args, **kwargs)
                
                # Extract response data
                response_data = None
                if hasattr(result, "dict"):
                    response_data = result.dict()
                elif isinstance(result, dict):
                    response_data = result
                
                # Extract notion IDs and summary
                notion_ids = None
                summary = None
                success = True
                
                if response_data:
                    result_data = response_data.get("result") if isinstance(response_data, dict) else response_data
                    if isinstance(result_data, dict):
                        notion_ids = extract_notion_ids(result_data)
                        summary = f"{func.__name__} operation"
                        success = response_data.get("ok", True) if isinstance(response_data, dict) else True
                
                # Log audit
                log_audit(
                    db=db,
                    connection_id=connection_id,
                    request_id=request_id,
                    actor=actor,
                    method=request.method,
                    path=request.url.path,
                    notion_ids=notion_ids if notion_ids.get("created") or notion_ids.get("updated") else None,
                    summary=summary,
                    success=success,
                )
                
                return result
            
            except Exception as e:
                # Log failed operation
                log_audit(
                    db=db,
                    connection_id=connection_id,
                    request_id=request_id,
                    actor=actor,
                    method=request.method,
                    path=request.url.path,
                    summary=f"{func.__name__} failed: {str(e)}",
                    success=False,
                    error_code=type(e).__name__,
                )
                raise
        
        return wrapper
    return decorator

