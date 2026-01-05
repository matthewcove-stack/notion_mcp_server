"""
Database models for persistence
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer
from sqlalchemy.sql import func
from app.db.database import Base
import uuid


class Connection(Base):
    """
    Stores Notion workspace connections and OAuth tokens
    """
    __tablename__ = "connections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(100), nullable=True)
    workspace_name = Column(String(200), nullable=True)
    bot_id = Column(String(100), nullable=True)
    
    # Encrypted tokens
    access_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """
    Audit trail for all write operations
    """
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String(36), nullable=True)
    request_id = Column(String(36), nullable=False)
    
    # Actor information
    actor = Column(String(50), nullable=False)  # 'chatgpt_action' or 'chatgpt_mcp'
    
    # Operation details
    method = Column(String(20), nullable=True)  # HTTP method or 'tool'
    endpoint = Column(String(200), nullable=True)  # Endpoint or tool name
    
    # Notion objects touched
    notion_ids = Column(JSON, nullable=True)
    
    # Summary
    summary = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())


class IdempotencyKey(Base):
    """
    Stores idempotency keys for write operations
    """
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
    connection_id = Column(String(36), nullable=False)
    
    # Request hash for validation
    request_hash = Column(String(64), nullable=False)
    
    # Cached response
    response_body = Column(JSON, nullable=False)
    response_status = Column(Integer, default=200)
    
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)


class OSState(Base):
    """
    Optional: Track Second Brain / OS state
    """
    __tablename__ = "os_state"
    
    connection_id = Column(String(36), primary_key=True)
    root_page_id = Column(String(100), nullable=True)
    spec_version = Column(String(20), nullable=True)
    
    # Databases created
    created_ids = Column(JSON, nullable=True)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

