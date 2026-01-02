"""
Core engine for Notion operations
Shared by both REST and MCP layers
"""
from typing import Dict, Any, Optional, List
import structlog

from app.services.notion_client import NotionClient, NotionAPIError
from app.services.connection_service import get_decrypted_access_token
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class CoreEngine:
    """Core engine for Notion API operations"""
    
    def __init__(self, db: Session, connection_id: str):
        """
        Initialize core engine with database session and connection
        
        Args:
            db: Database session
            connection_id: Connection UUID string
        """
        self.db = db
        self.connection_id = connection_id
        
        # Get decrypted access token
        access_token = get_decrypted_access_token(db, connection_id)
        if not access_token:
            raise ValueError(f"Connection {connection_id} not found or token unavailable")
        
        self.client = NotionClient(access_token)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    # Search operations
    def search(
        self,
        query: Optional[str] = None,
        filter_obj: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Search Notion workspace"""
        body = {}
        if query:
            body["query"] = query
        if filter_obj:
            body["filter"] = filter_obj
        if sort:
            body["sort"] = sort
        
        return self.client.post("/v1/search", json=body)
    
    # Database operations
    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any],
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a database"""
        body = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        if icon:
            body["icon"] = icon
        if cover:
            body["cover"] = cover
        
        return self.client.post("/v1/databases", json=body)
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve a database"""
        return self.client.get(f"/v1/databases/{database_id}")
    
    def update_database(
        self,
        database_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update a database"""
        body = {}
        if title:
            body["title"] = [{"type": "text", "text": {"content": title}}]
        if properties:
            body["properties"] = properties
        
        return self.client.patch(f"/v1/databases/{database_id}", json=body)
    
    def query_database(
        self,
        database_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        start_cursor: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query a database"""
        body = {}
        if filter_obj:
            body["filter"] = filter_obj
        if sorts:
            body["sorts"] = sorts
        if start_cursor:
            body["start_cursor"] = start_cursor
        if page_size:
            body["page_size"] = page_size
        
        return self.client.post(f"/v1/databases/{database_id}/query", json=body)
    
    # Page operations
    def create_page(
        self,
        properties: Dict[str, Any],
        parent_page_id: Optional[str] = None,
        parent_database_id: Optional[str] = None,
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a page"""
        if not parent_page_id and not parent_database_id:
            raise ValueError("Either parent_page_id or parent_database_id must be provided")
        
        body = {"properties": properties}
        
        if parent_page_id:
            body["parent"] = {"page_id": parent_page_id}
        elif parent_database_id:
            body["parent"] = {"database_id": parent_database_id}
        
        if children:
            body["children"] = children
        
        return self.client.post("/v1/pages", json=body)
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page"""
        return self.client.get(f"/v1/pages/{page_id}")
    
    def update_page(
        self,
        page_id: str,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a page"""
        body = {}
        if properties:
            body["properties"] = properties
        if archived is not None:
            body["archived"] = archived
        
        return self.client.patch(f"/v1/pages/{page_id}", json=body)
    
    def archive_page(self, page_id: str) -> Dict[str, Any]:
        """Archive a page"""
        return self.client.patch(f"/v1/pages/{page_id}", json={"archived": True})
    
    def unarchive_page(self, page_id: str) -> Dict[str, Any]:
        """Unarchive a page"""
        return self.client.patch(f"/v1/pages/{page_id}", json={"archived": False})
    
    # Block operations
    def get_block_children(
        self,
        block_id: str,
        start_cursor: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get block children"""
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        return self.client.get(f"/v1/blocks/{block_id}/children", params=params)
    
    def update_block(
        self,
        block_id: str,
        block_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a block"""
        return self.client.patch(f"/v1/blocks/{block_id}", json=block_data)
    
    def append_block_children(
        self,
        block_id: str,
        children: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Append children to a block"""
        return self.client.patch(f"/v1/blocks/{block_id}/children", json={"children": children})

