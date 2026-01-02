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


# Search schemas
class SearchRequest(BaseModel):
    """Search request"""
    connection_id: str
    query: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, Any]] = None


# Database schemas
class CreateDatabaseRequest(BaseModel):
    """Create database request"""
    connection_id: str
    parent_page_id: str
    title: str
    properties: Dict[str, Any]
    icon: Optional[Dict[str, Any]] = None
    cover: Optional[Dict[str, Any]] = None


class UpdateDatabaseRequest(BaseModel):
    """Update database request"""
    connection_id: str
    title: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class QueryDatabaseRequest(BaseModel):
    """Query database request"""
    connection_id: str
    filter: Optional[Dict[str, Any]] = None
    sorts: Optional[List[Dict[str, Any]]] = None
    start_cursor: Optional[str] = None
    page_size: Optional[int] = None


# Page schemas
class CreatePageRequest(BaseModel):
    """Create page request"""
    connection_id: str
    parent_page_id: Optional[str] = None
    parent_database_id: Optional[str] = None
    properties: Dict[str, Any]
    children: Optional[List[Dict[str, Any]]] = None


class UpdatePageRequest(BaseModel):
    """Update page request"""
    connection_id: str
    properties: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None


class ArchivePageRequest(BaseModel):
    """Archive/unarchive page request"""
    connection_id: str
    archived: bool = True


# Block schemas
class GetBlockChildrenRequest(BaseModel):
    """Get block children request"""
    connection_id: str
    start_cursor: Optional[str] = None
    page_size: Optional[int] = None


class UpdateBlockRequest(BaseModel):
    """Update block request"""
    connection_id: str
    block_data: Dict[str, Any]


class AppendBlockChildrenRequest(BaseModel):
    """Append block children request"""
    connection_id: str
    children: List[Dict[str, Any]]
