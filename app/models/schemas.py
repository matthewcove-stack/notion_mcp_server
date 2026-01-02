"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class StandardResponse(BaseModel):
    """Standard response envelope"""
    ok: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = {}


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool


class MetaResponse(BaseModel):
    """Meta/version information"""
    version: str
    build_hash: Optional[str] = None
    notion_api_status: str
    timestamp: datetime

