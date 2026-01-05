"""
Notion API client with retry/backoff logic
"""
from notion_client import AsyncClient
from notion_client.errors import APIResponseError
import asyncio
import structlog
from typing import Dict, Any, Optional
from app.config import settings

logger = structlog.get_logger()


class NotionClientWrapper:
    """
    Wrapper around Notion SDK with retry logic and rate limiting
    """
    
    def __init__(self, auth_token: str):
        """
        Initialize Notion client with auth token
        
        Args:
            auth_token: Notion API token or OAuth access token
        """
        self.client = AsyncClient(
            auth=auth_token,
            notion_version=settings.notion_api_version
        )
        self.max_retries = settings.notion_api_max_retries
        self.retry_delay = settings.notion_api_retry_delay
    
    async def _retry_request(self, func, *args, **kwargs):
        """
        Execute request with exponential backoff retry logic
        """
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except APIResponseError as e:
                # Rate limited or transient error
                if e.code in ("rate_limited", "service_unavailable") and attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        "notion_api_retry",
                        error_code=e.code,
                        attempt=attempt + 1,
                        delay=delay
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                logger.error("notion_api_error", error=str(e), exc_info=True)
                raise
        
        # Should not reach here, but just in case
        raise Exception(f"Max retries ({self.max_retries}) exceeded")
    
    # Search
    async def search(self, query: str = "", filter: Optional[Dict] = None, 
                    sort: Optional[Dict] = None, start_cursor: Optional[str] = None,
                    page_size: int = 100) -> Dict[str, Any]:
        """Search for pages and databases"""
        return await self._retry_request(
            self.client.search,
            query=query,
            filter=filter,
            sort=sort,
            start_cursor=start_cursor,
            page_size=page_size
        )
    
    # Databases
    async def databases_retrieve(self, database_id: str) -> Dict[str, Any]:
        """Retrieve a database"""
        return await self._retry_request(
            self.client.databases.retrieve,
            database_id=database_id
        )
    
    async def databases_create(self, parent: Dict, title: list, 
                               properties: Dict, **kwargs) -> Dict[str, Any]:
        """Create a database"""
        return await self._retry_request(
            self.client.databases.create,
            parent=parent,
            title=title,
            properties=properties,
            **kwargs
        )
    
    async def databases_update(self, database_id: str, **kwargs) -> Dict[str, Any]:
        """Update a database"""
        return await self._retry_request(
            self.client.databases.update,
            database_id=database_id,
            **kwargs
        )
    
    async def databases_query(self, database_id: str, filter: Optional[Dict] = None,
                             sorts: Optional[list] = None, start_cursor: Optional[str] = None,
                             page_size: int = 100) -> Dict[str, Any]:
        """Query a database"""
        return await self._retry_request(
            self.client.databases.query,
            database_id=database_id,
            filter=filter,
            sorts=sorts,
            start_cursor=start_cursor,
            page_size=page_size
        )
    
    # Pages
    async def pages_retrieve(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page"""
        return await self._retry_request(
            self.client.pages.retrieve,
            page_id=page_id
        )
    
    async def pages_create(self, parent: Dict, properties: Dict, 
                          children: Optional[list] = None, **kwargs) -> Dict[str, Any]:
        """Create a page"""
        return await self._retry_request(
            self.client.pages.create,
            parent=parent,
            properties=properties,
            children=children,
            **kwargs
        )
    
    async def pages_update(self, page_id: str, properties: Optional[Dict] = None,
                          **kwargs) -> Dict[str, Any]:
        """Update a page"""
        return await self._retry_request(
            self.client.pages.update,
            page_id=page_id,
            properties=properties,
            **kwargs
        )
    
    # Blocks
    async def blocks_retrieve(self, block_id: str) -> Dict[str, Any]:
        """Retrieve a block"""
        return await self._retry_request(
            self.client.blocks.retrieve,
            block_id=block_id
        )
    
    async def blocks_update(self, block_id: str, **kwargs) -> Dict[str, Any]:
        """Update a block"""
        return await self._retry_request(
            self.client.blocks.update,
            block_id=block_id,
            **kwargs
        )
    
    async def blocks_delete(self, block_id: str) -> Dict[str, Any]:
        """Delete a block"""
        return await self._retry_request(
            self.client.blocks.delete,
            block_id=block_id
        )
    
    async def blocks_children_list(self, block_id: str, start_cursor: Optional[str] = None,
                                   page_size: int = 100) -> Dict[str, Any]:
        """List block children"""
        return await self._retry_request(
            self.client.blocks.children.list,
            block_id=block_id,
            start_cursor=start_cursor,
            page_size=page_size
        )
    
    async def blocks_children_append(self, block_id: str, children: list) -> Dict[str, Any]:
        """Append children to a block"""
        return await self._retry_request(
            self.client.blocks.children.append,
            block_id=block_id,
            children=children
        )
    
    # Users
    async def users_me(self) -> Dict[str, Any]:
        """Get current bot user info"""
        return await self._retry_request(
            self.client.users.me
        )
    
    async def users_list(self, start_cursor: Optional[str] = None,
                        page_size: int = 100) -> Dict[str, Any]:
        """List all users"""
        return await self._retry_request(
            self.client.users.list,
            start_cursor=start_cursor,
            page_size=page_size
        )


def get_notion_client(token: str) -> NotionClientWrapper:
    """
    Factory function to create Notion client
    
    Args:
        token: Decrypted Notion API token
    
    Returns:
        Configured NotionClientWrapper instance
    """
    return NotionClientWrapper(token)

