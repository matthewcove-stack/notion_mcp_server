"""
Core Notion engine - shared business logic for REST and MCP
"""
from typing import Dict, Any, Optional, List
from app.services.notion_client import NotionClientWrapper
from app.services.property_normalizer import property_normalizer
from app.exceptions import NotionAPIError, ValidationError
from notion_client.errors import APIResponseError
import structlog

logger = structlog.get_logger()


class NotionEngine:
    """
    Core engine implementing all Notion operations
    Shared by both REST endpoints and MCP tools
    """
    
    def __init__(self, notion_client: NotionClientWrapper):
        """
        Initialize engine with Notion client
        
        Args:
            notion_client: Configured Notion client wrapper
        """
        self.client = notion_client
    
    # ========== SEARCH ==========
    
    async def search(
        self,
        query: str = "",
        filter: Optional[Dict] = None,
        sort: Optional[Dict] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Search for pages and databases
        
        Args:
            query: Search query
            filter: Filter object (e.g., {"property": "object", "value": "database"})
            sort: Sort object (e.g., {"direction": "ascending", "timestamp": "last_edited_time"})
            page_size: Results per page
        
        Returns:
            Search results with results array
        """
        try:
            results = await self.client.search(
                query=query,
                filter=filter,
                sort=sort,
                page_size=page_size
            )
            return results
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    # ========== DATABASES ==========
    
    async def database_list(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        List all databases (via search)
        """
        try:
            results = await self.client.search(
                filter={"property": "object", "value": "database"},
                page_size=page_size
            )
            return results.get("results", [])
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def database_get(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve database by ID
        """
        try:
            return await self.client.databases_retrieve(database_id)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def database_create(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any],
        icon: Optional[Dict] = None,
        cover: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new database
        
        Args:
            parent_page_id: Parent page ID
            title: Database title
            properties: Property schema
            icon: Optional icon
            cover: Optional cover
        
        Returns:
            Created database object
        """
        try:
            # Format title
            title_array = [{"type": "text", "text": {"content": title}}]
            
            # Format parent
            parent = {"type": "page_id", "page_id": parent_page_id}
            
            # Create database
            kwargs = {}
            if icon:
                kwargs["icon"] = icon
            if cover:
                kwargs["cover"] = cover
            
            return await self.client.databases_create(
                parent=parent,
                title=title_array,
                properties=properties,
                **kwargs
            )
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def database_update(
        self,
        database_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update database title or properties
        """
        try:
            update_data = {}
            
            if title:
                update_data["title"] = [{"type": "text", "text": {"content": title}}]
            
            if properties:
                update_data["properties"] = properties
            
            update_data.update(kwargs)
            
            return await self.client.databases_update(database_id, **update_data)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def database_query(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Query a database
        """
        try:
            return await self.client.databases_query(
                database_id=database_id,
                filter=filter,
                sorts=sorts,
                page_size=page_size
            )
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    # ========== PAGES ==========
    
    async def page_get(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve page by ID
        """
        try:
            return await self.client.pages_retrieve(page_id)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def page_create(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List] = None,
        icon: Optional[Dict] = None,
        cover: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new page
        
        Args:
            parent: Parent reference (database_id or page_id)
            properties: Page properties
            children: Optional content blocks
            icon: Optional icon
            cover: Optional cover
        
        Returns:
            Created page object
        """
        try:
            # Normalize properties
            normalized_props = property_normalizer.normalize_properties(properties)
            
            kwargs = {}
            if icon:
                kwargs["icon"] = icon
            if cover:
                kwargs["cover"] = cover
            
            return await self.client.pages_create(
                parent=parent,
                properties=normalized_props,
                children=children,
                **kwargs
            )
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def page_update(
        self,
        page_id: str,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None,
        icon: Optional[Dict] = None,
        cover: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Update page properties
        """
        try:
            kwargs = {}
            
            if properties:
                kwargs["properties"] = property_normalizer.normalize_properties(properties)
            
            if archived is not None:
                kwargs["archived"] = archived
            
            if icon:
                kwargs["icon"] = icon
            
            if cover:
                kwargs["cover"] = cover
            
            return await self.client.pages_update(page_id, **kwargs)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def page_archive(self, page_id: str) -> Dict[str, Any]:
        """
        Archive (soft delete) a page
        """
        return await self.page_update(page_id, archived=True)
    
    async def page_unarchive(self, page_id: str) -> Dict[str, Any]:
        """
        Unarchive a page
        """
        return await self.page_update(page_id, archived=False)
    
    # ========== BLOCKS ==========
    
    async def block_get(self, block_id: str) -> Dict[str, Any]:
        """
        Retrieve block by ID
        """
        try:
            return await self.client.blocks_retrieve(block_id)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def block_update(self, block_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a block
        """
        try:
            return await self.client.blocks_update(block_id, **kwargs)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def block_delete(self, block_id: str) -> Dict[str, Any]:
        """
        Delete a block
        """
        try:
            return await self.client.blocks_delete(block_id)
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def block_children_list(
        self,
        block_id: str,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        List children of a block
        """
        try:
            return await self.client.blocks_children_list(
                block_id=block_id,
                page_size=page_size
            )
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def block_children_append(
        self,
        block_id: str,
        children: List[Dict]
    ) -> Dict[str, Any]:
        """
        Append children blocks
        """
        try:
            return await self.client.blocks_children_append(
                block_id=block_id,
                children=children
            )
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    # ========== HIGH-LEVEL OPERATIONS ==========
    
    async def upsert_page(
        self,
        database_id: str,
        unique_property: str,
        unique_value: str,
        properties: Dict[str, Any],
        children: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Create or update a page based on unique property
        
        Args:
            database_id: Database to upsert in
            unique_property: Property to match on (e.g., "Name")
            unique_value: Value to match
            properties: Properties to set
            children: Optional content blocks
        
        Returns:
            Created or updated page
        """
        try:
            # Search for existing page
            filter_obj = {
                "property": unique_property,
                "rich_text": {"equals": unique_value}
            }
            
            results = await self.database_query(
                database_id=database_id,
                filter=filter_obj,
                page_size=1
            )
            
            existing_pages = results.get("results", [])
            
            if existing_pages:
                # Update existing
                page_id = existing_pages[0]["id"]
                logger.info("upsert_update", page_id=page_id, unique_value=unique_value)
                
                updated = await self.page_update(page_id, properties=properties)
                
                # Append children if provided
                if children:
                    await self.block_children_append(page_id, children)
                
                return updated
            else:
                # Create new
                logger.info("upsert_create", database_id=database_id, unique_value=unique_value)
                
                return await self.page_create(
                    parent={"type": "database_id", "database_id": database_id},
                    properties=properties,
                    children=children
                )
        
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def link_pages(
        self,
        from_page_id: str,
        to_page_id: str,
        relation_property: str
    ) -> Dict[str, Any]:
        """
        Link two pages via a relation property
        
        Args:
            from_page_id: Source page ID
            to_page_id: Target page ID
            relation_property: Name of relation property
        
        Returns:
            Updated page
        """
        try:
            # Get current page to read existing relations
            page = await self.page_get(from_page_id)
            current_relations = page.get("properties", {}).get(relation_property, {}).get("relation", [])
            
            # Add new relation if not already present
            relation_ids = [rel["id"] for rel in current_relations]
            if to_page_id not in relation_ids:
                current_relations.append({"id": to_page_id})
            
            # Update page
            return await self.page_update(
                from_page_id,
                properties={
                    relation_property: {"relation": current_relations}
                }
            )
        
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)
    
    async def bulk_operations(
        self,
        operations: List[Dict[str, Any]],
        mode: str = "stop_on_error"
    ) -> Dict[str, Any]:
        """
        Execute multiple operations in sequence
        
        Args:
            operations: List of operations
                Each: {"op": "upsert|link|create_page|update_page|...", "args": {...}}
            mode: "stop_on_error" or "continue_on_error"
        
        Returns:
            Results summary
        """
        results = []
        errors = []
        
        for i, operation in enumerate(operations):
            op_type = operation.get("op")
            op_args = operation.get("args", {})
            
            try:
                if op_type == "upsert":
                    result = await self.upsert_page(**op_args)
                elif op_type == "link":
                    result = await self.link_pages(**op_args)
                elif op_type == "create_page":
                    result = await self.page_create(**op_args)
                elif op_type == "update_page":
                    result = await self.page_update(**op_args)
                elif op_type == "create_database":
                    result = await self.database_create(**op_args)
                elif op_type == "query_database":
                    result = await self.database_query(**op_args)
                else:
                    raise ValidationError(f"Unknown operation: {op_type}")
                
                results.append({
                    "index": i,
                    "operation": op_type,
                    "success": True,
                    "result": result
                })
            
            except Exception as e:
                error_info = {
                    "index": i,
                    "operation": op_type,
                    "success": False,
                    "error": str(e)
                }
                errors.append(error_info)
                results.append(error_info)
                
                if mode == "stop_on_error":
                    break
        
        return {
            "total": len(operations),
            "succeeded": len([r for r in results if r.get("success")]),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    # ========== USERS ==========
    
    async def users_me(self) -> Dict[str, Any]:
        """
        Get current bot user info
        """
        try:
            return await self.client.users_me()
        except APIResponseError as e:
            raise NotionAPIError(str(e), e.code)

