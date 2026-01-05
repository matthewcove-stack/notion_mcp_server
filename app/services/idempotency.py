"""
Idempotency key service
"""
from sqlalchemy.orm import Session
from app.db.models import IdempotencyKey
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import structlog

logger = structlog.get_logger()


class IdempotencyService:
    """
    Service for handling idempotency keys
    """
    
    DEFAULT_TTL_HOURS = 24
    
    @staticmethod
    def compute_request_hash(request_data: Dict[str, Any]) -> str:
        """
        Compute hash of request data for validation
        """
        data_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @staticmethod
    def check_idempotency(
        db: Session,
        key: str,
        connection_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if idempotency key exists and return cached response
        
        Args:
            db: Database session
            key: Idempotency key
            connection_id: Connection ID
            request_data: Request data for validation
        
        Returns:
            Cached response if key exists and valid, None otherwise
        """
        # Clean up expired keys
        IdempotencyService._cleanup_expired(db)
        
        # Look up key
        idem = db.query(IdempotencyKey).filter(
            IdempotencyKey.key == key,
            IdempotencyKey.connection_id == connection_id
        ).first()
        
        if not idem:
            return None
        
        # Check expiration
        if idem.expires_at < datetime.utcnow():
            db.delete(idem)
            db.commit()
            return None
        
        # Validate request hash
        request_hash = IdempotencyService.compute_request_hash(request_data)
        if idem.request_hash != request_hash:
            logger.warning(
                "idempotency_hash_mismatch",
                key=key,
                expected=idem.request_hash,
                got=request_hash
            )
            # Different request with same key - return conflict
            return {
                "error": "idempotency_key_conflict",
                "message": "Same key used for different request"
            }
        
        logger.info("idempotency_cache_hit", key=key)
        return idem.response_body
    
    @staticmethod
    def store_response(
        db: Session,
        key: str,
        connection_id: str,
        request_data: Dict[str, Any],
        response_body: Dict[str, Any],
        response_status: int = 200,
        ttl_hours: int = DEFAULT_TTL_HOURS
    ):
        """
        Store response for idempotency key
        
        Args:
            db: Database session
            key: Idempotency key
            connection_id: Connection ID
            request_data: Request data
            response_body: Response to cache
            response_status: HTTP status code
            ttl_hours: Time to live in hours
        """
        request_hash = IdempotencyService.compute_request_hash(request_data)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        idem = IdempotencyKey(
            key=key,
            connection_id=connection_id,
            request_hash=request_hash,
            response_body=response_body,
            response_status=response_status,
            expires_at=expires_at
        )
        
        db.add(idem)
        db.commit()
        
        logger.info("idempotency_stored", key=key, expires_at=expires_at)
    
    @staticmethod
    def _cleanup_expired(db: Session):
        """
        Remove expired idempotency keys
        """
        deleted = db.query(IdempotencyKey).filter(
            IdempotencyKey.expires_at < datetime.utcnow()
        ).delete()
        
        if deleted > 0:
            db.commit()
            logger.info("idempotency_cleanup", deleted=deleted)


# Global instance
idempotency_service = IdempotencyService()

