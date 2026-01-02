"""
Job models for database storage
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Job(Base):
    """Job storage"""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    kind = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="queued", index=True)  # queued, running, succeeded, failed
    progress = Column(Float, nullable=False, default=0.0)
    args = Column(JSON, nullable=False)
    output = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

