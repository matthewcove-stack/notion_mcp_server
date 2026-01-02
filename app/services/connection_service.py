"""
Connection service for managing Notion workspace connections
"""
from typing import Optional
from sqlalchemy.orm import Session
import structlog

from app.db.models import Connection
from app.services.token_encryption import get_token_encryption

logger = structlog.get_logger()


def get_connection(db: Session, connection_id: str) -> Optional[Connection]:
    """Get a connection by ID"""
    try:
        return db.query(Connection).filter(Connection.id == connection_id).first()
    except Exception as e:
        logger.error("get_connection_error", connection_id=connection_id, error=str(e))
        return None


def get_decrypted_access_token(db: Session, connection_id: str) -> Optional[str]:
    """Get decrypted access token for a connection"""
    connection = get_connection(db, connection_id)
    if not connection:
        return None
    
    try:
        encryption = get_token_encryption()
        return encryption.decrypt(connection.access_token_enc)
    except Exception as e:
        logger.error("decrypt_token_error", connection_id=connection_id, error=str(e))
        return None

