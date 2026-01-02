"""
Idempotency key management
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import json
import structlog

from app.db.models import IdempotencyKey
from app.config import settings

logger = structlog.get_logger()


def generate_request_hash(method: str, path: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a hash for a request to detect duplicates
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body (optional)
        params: Query parameters (optional)
    
    Returns:
        SHA256 hash string
    """
    data = {
        "method": method,
        "path": path,
        "body": body or {},
        "params": params or {},
    }
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


def check_idempotency(
    db: Session,
    idempotency_key: str,
    connection_id: Optional[str],
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Check if request is idempotent (already processed)
    
    Returns:
        Cached response if found, None otherwise
    """
    try:
        # Look up idempotency key
        key_record = db.query(IdempotencyKey).filter(
            IdempotencyKey.key == idempotency_key
        ).first()
        
        if not key_record:
            return None
        
        # Check if expired
        if key_record.expires_at < datetime.utcnow():
            logger.info("idempotency_key_expired", key=idempotency_key[:10])
            db.delete(key_record)
            db.commit()
            return None
        
        # Verify request hash matches
        request_hash = generate_request_hash(method, path, body, params)
        if key_record.request_hash != request_hash:
            logger.warning(
                "idempotency_key_hash_mismatch",
                key=idempotency_key[:10],
                expected=key_record.request_hash[:10],
                actual=request_hash[:10],
            )
            return None
        
        # Return cached response
        logger.info("idempotency_key_hit", key=idempotency_key[:10])
        return key_record.response_body
    
    except Exception as e:
        logger.error("idempotency_check_error", error=str(e), exc_info=True)
        return None


def store_idempotency(
    db: Session,
    idempotency_key: str,
    connection_id: Optional[str],
    method: str,
    path: str,
    body: Optional[Dict[str, Any]],
    params: Optional[Dict[str, Any]],
    response_body: Dict[str, Any],
) -> None:
    """
    Store idempotency key and response
    
    Args:
        db: Database session
        idempotency_key: Idempotency key string
        connection_id: Connection UUID string (optional)
        method: HTTP method
        path: Request path
        body: Request body
        params: Query parameters
        response_body: Response to cache
    """
    try:
        import uuid
        
        # Convert connection_id to UUID if provided
        conn_uuid = None
        if connection_id:
            try:
                conn_uuid = uuid.UUID(connection_id) if isinstance(connection_id, str) else connection_id
            except ValueError:
                logger.warning("invalid_connection_id_for_idempotency", connection_id=connection_id)
        
        request_hash = generate_request_hash(method, path, body, params)
        expires_at = datetime.utcnow() + timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS)
        
        # Check if key already exists
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.key == idempotency_key
        ).first()
        
        if existing:
            # Update existing record
            existing.connection_id = conn_uuid
            existing.request_hash = request_hash
            existing.response_body = response_body
            existing.expires_at = expires_at
        else:
            # Create new record
            key_record = IdempotencyKey(
                key=idempotency_key,
                connection_id=conn_uuid,
                request_hash=request_hash,
                response_body=response_body,
                expires_at=expires_at,
            )
            db.add(key_record)
        
        db.commit()
        logger.info("idempotency_stored", key=idempotency_key[:10])
    
    except Exception as e:
        logger.error("idempotency_store_error", error=str(e), exc_info=True)
        db.rollback()
        # Don't fail the request if idempotency storage fails

