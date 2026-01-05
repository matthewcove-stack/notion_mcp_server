"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class StandardResponse(BaseModel):
    """Standard API response envelope"""
    ok: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response details"""
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


# Database operations
class DatabaseCreateRequest(BaseModel):
    connection_id: Optional[str] = None
    parent_page_id: str
    title: str
    properties: Dict[str, Any]
    icon: Optional[Dict] = None
    cover: Optional[Dict] = None


class DatabaseUpdateRequest(BaseModel):
    connection_id: Optional[str] = None
    title: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class DatabaseQueryRequest(BaseModel):
    connection_id: Optional[str] = None
    filter: Optional[Dict] = None
    sorts: Optional[List] = None
    page_size: int = 100


# Page operations
class PageCreateRequest(BaseModel):
    connection_id: Optional[str] = None
    parent: Dict[str, Any]  # {type: database_id|page_id, database_id|page_id: ...}
    properties: Dict[str, Any]
    children: Optional[List] = None
    icon: Optional[Dict] = None
    cover: Optional[Dict] = None


class PageUpdateRequest(BaseModel):
    connection_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None
    icon: Optional[Dict] = None
    cover: Optional[Dict] = None


# Block operations
class BlockAppendRequest(BaseModel):
    connection_id: Optional[str] = None
    children: List[Dict]


# Search
class SearchRequest(BaseModel):
    connection_id: Optional[str] = None
    query: str = ""
    filter: Optional[Dict] = None
    sort: Optional[Dict] = None
    page_size: int = 100


# Upsert
class UpsertRequest(BaseModel):
    connection_id: Optional[str] = None
    database_id: str
    unique_property: str
    unique_value: str
    properties: Dict[str, Any]
    children: Optional[List] = None


# Link pages
class LinkRequest(BaseModel):
    connection_id: Optional[str] = None
    from_page_id: str
    to_page_id: str
    relation_property: str


# Bulk operations
class BulkOperation(BaseModel):
    op: str
    args: Dict[str, Any]


class BulkRequest(BaseModel):
    connection_id: Optional[str] = None
    mode: str = "stop_on_error"  # or "continue_on_error"
    operations: List[BulkOperation]


# Connection service
class ConnectionService:
    """Helper to get Notion client from connection"""
    
    @staticmethod
    def get_token() -> str:
        """Get token - for now use environment variable"""
        from app.config import settings
        return settings.notion_api_token or ""

