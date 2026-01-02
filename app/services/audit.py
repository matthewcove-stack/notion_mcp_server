"""
Audit logging service
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import structlog
import uuid

from app.db.models import AuditLog

logger = structlog.get_logger()


def log_audit(
    db: Session,
    connection_id: Optional[str],
    request_id: Optional[str],
    actor: str,  # "chatgpt_action" or "chatgpt_mcp"
    method: str,  # HTTP method or tool name
    path: str,  # endpoint path or tool name
    notion_ids: Optional[Dict[str, List[str]]] = None,  # {"created": [...], "updated": [...]}
    summary: Optional[str] = None,
    success: bool = True,
    error_code: Optional[str] = None,
) -> None:
    """
    Log an audit entry for a write operation
    
    Args:
        db: Database session
        connection_id: Connection UUID string (optional)
        request_id: Request ID UUID string (optional)
        actor: Actor type ("chatgpt_action" or "chatgpt_mcp")
        method: HTTP method or operation type
        path: Endpoint path or tool name
        notion_ids: Dict with "created" and/or "updated" lists of Notion IDs
        summary: Human-readable summary
        success: Whether operation succeeded
        error_code: Error code if failed
    """
    try:
        # Convert connection_id string to UUID if provided
        conn_uuid = None
        if connection_id:
            try:
                conn_uuid = uuid.UUID(connection_id) if isinstance(connection_id, str) else connection_id
            except ValueError:
                logger.warning("invalid_connection_id", connection_id=connection_id)
        
        audit_entry = AuditLog(
            connection_id=conn_uuid,
            request_id=request_id,
            actor=actor,
            method=method,
            path=path,
            notion_ids=notion_ids,
            summary=summary,
            success=success,
        )
        
        db.add(audit_entry)
        db.commit()
        
        logger.info(
            "audit_logged",
            actor=actor,
            method=method,
            path=path,
            success=success,
        )
    
    except Exception as e:
        logger.error("audit_log_error", error=str(e), exc_info=True)
        db.rollback()
        # Don't fail the request if audit logging fails


def extract_notion_ids(result: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract Notion IDs from operation result
    
    Returns dict with "created" and/or "updated" lists
    """
    notion_ids = {"created": [], "updated": []}
    
    if not isinstance(result, dict):
        return notion_ids
    
    # Check for page/database/block IDs in result
    if "id" in result:
        # Single object result
        obj_id = result["id"]
        if result.get("action") == "created":
            notion_ids["created"].append(obj_id)
        elif result.get("action") == "updated":
            notion_ids["updated"].append(obj_id)
        else:
            # Default to updated if action not specified
            notion_ids["updated"].append(obj_id)
    
    # Check for results array (from queries)
    if "results" in result:
        for item in result.get("results", []):
            if isinstance(item, dict) and "id" in item:
                notion_ids["updated"].append(item["id"])
    
    # Check for page in result
    if "page" in result:
        page = result["page"]
        if isinstance(page, dict) and "id" in page:
            if result.get("action") == "created":
                notion_ids["created"].append(page["id"])
            else:
                notion_ids["updated"].append(page["id"])
    
    return notion_ids

