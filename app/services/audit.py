"""
Audit logging service
"""
from sqlalchemy.orm import Session
from app.db.models import AuditLog
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger()


class AuditService:
    """
    Service for recording audit logs
    """
    
    @staticmethod
    def log_operation(
        db: Session,
        request_id: str,
        actor: str,
        summary: str,
        success: bool,
        connection_id: Optional[str] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        notion_ids: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an operation to audit trail
        
        Args:
            db: Database session
            request_id: Request ID
            actor: Actor type ('chatgpt_action' or 'chatgpt_mcp')
            summary: Human-readable operation summary
            success: Whether operation succeeded
            connection_id: Connection ID
            method: HTTP method or 'tool'
            endpoint: Endpoint path or tool name
            notion_ids: Notion object IDs touched
            error_code: Error code if failed
            error_message: Error message if failed
        
        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            request_id=request_id,
            connection_id=connection_id,
            actor=actor,
            method=method,
            endpoint=endpoint,
            notion_ids=notion_ids or {},
            summary=summary,
            success=success,
            error_code=error_code,
            error_message=error_message
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        logger.info(
            "audit_log_created",
            audit_id=audit_log.id,
            request_id=request_id,
            actor=actor,
            success=success
        )
        
        return audit_log
    
    @staticmethod
    def get_logs(
        db: Session,
        connection_id: Optional[str] = None,
        actor: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs
        
        Args:
            db: Database session
            connection_id: Filter by connection ID
            actor: Filter by actor type
            success: Filter by success status
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of audit logs
        """
        query = db.query(AuditLog)
        
        if connection_id:
            query = query.filter(AuditLog.connection_id == connection_id)
        if actor:
            query = query.filter(AuditLog.actor == actor)
        if success is not None:
            query = query.filter(AuditLog.success == success)
        
        query = query.order_by(AuditLog.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()


# Global instance
audit_service = AuditService()

