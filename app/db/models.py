"""
SQLAlchemy database models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Connection(Base):
    """Notion workspace connection with encrypted tokens"""
    __tablename__ = "connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Text, nullable=False, index=True)
    workspace_name = Column(Text, nullable=True)
    access_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit log for all write operations"""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    request_id = Column(Text, nullable=True, index=True)
    actor = Column(Text, nullable=False, default="chatgpt_action")
    method = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    notion_ids = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class IdempotencyKey(Base):
    """Idempotency key storage"""
    __tablename__ = "idempotency_keys"
    
    key = Column(Text, primary_key=True)
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    request_hash = Column(Text, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

