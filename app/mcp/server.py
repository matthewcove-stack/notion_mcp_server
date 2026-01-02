"""
MCP Server implementation using SSE (Server-Sent Events)
Provides MCP tools that map to Core Engine operations
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json
import uuid
import structlog

from app.db.database import get_db
from app.core.engine import CoreEngine
from app.services.notion_client import NotionAPIError
from app.services.idempotency import check_idempotency, store_idempotency
from app.services.audit import log_audit, extract_notion_ids

logger = structlog.get_logger()

router = APIRouter(prefix="/mcp", tags=["mcp"])


def get_core_engine(db: Session, connection_id: str) -> CoreEngine:
    """Get core engine instance"""
    try:
        return CoreEngine(db, connection_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/sse")
async def mcp_sse(
    request: Request,
    connection_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    MCP SSE endpoint for tool calls
    
    Uses Server-Sent Events to stream MCP protocol messages
    """
    async def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
            
            # Keep connection alive and handle tool calls
            # In a real implementation, this would parse SSE events from client
            # For now, this is a basic SSE endpoint structure
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Send keepalive
                yield f": keepalive\n\n"
                
                # In production, parse incoming SSE events and handle tool calls
                # For now, just keep connection alive
                import asyncio
                await asyncio.sleep(30)
        
        except Exception as e:
            logger.error("mcp_sse_error", error=str(e), exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/tools/call")
async def mcp_tool_call(
    request: Request,
    tool_name: str,
    arguments: Dict[str, Any],
    connection_id: Optional[str] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """
    MCP tool call endpoint
    
    Handles tool calls from MCP clients
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Get connection_id from arguments if not in header
    if not connection_id:
        connection_id = arguments.get("connection_id")
    
    if not connection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="connection_id is required"
        )
    
    # Check idempotency if key provided
    if idempotency_key:
        cached_response = check_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            connection_id=connection_id,
            method="POST",
            path=f"/mcp/tools/{tool_name}",
            body=arguments,
        )
        if cached_response:
            return cached_response
    
    try:
        with get_core_engine(db, connection_id) as engine:
            result = None
            
            if tool_name == "notion.request":
                # Generic Notion API request
                method = arguments.get("method", "GET").upper()
                path = arguments.get("path", "")
                body = arguments.get("body")
                params = arguments.get("query")
                
                if method == "GET":
                    result = engine.client.get(path, params=params)
                elif method == "POST":
                    result = engine.client.post(path, json=body)
                elif method == "PATCH":
                    result = engine.client.patch(path, json=body)
                elif method == "DELETE":
                    result = engine.client.delete(path)
                else:
                    raise ValueError(f"Unsupported method: {method}")
            
            elif tool_name == "notion.upsert":
                # Upsert operation
                from app.services.property_normalizer import normalize_properties
                from app.models.schemas import UpsertRequest
                
                upsert_req = UpsertRequest(**arguments)
                normalized_properties = None
                if upsert_req.properties:
                    normalized_properties = normalize_properties(upsert_req.properties)
                
                unique_prop = upsert_req.unique.get("property")
                unique_value = upsert_req.unique.get("value")
                
                if not unique_prop or unique_value is None:
                    raise ValueError("unique.property and unique.value are required")
                
                # Query to find existing
                query_result = engine.query_database(
                    database_id=upsert_req.database_id,
                    filter_obj={"property": unique_prop, "title": {"equals": str(unique_value)}} if unique_prop.lower() in ["name", "title"] else {
                        "property": unique_prop,
                        "rich_text": {"equals": str(unique_value)}
                    },
                    page_size=1,
                )
                
                existing_pages = query_result.get("results", [])
                
                if existing_pages:
                    page_id = existing_pages[0]["id"]
                    if normalized_properties:
                        result_obj = engine.update_page(page_id=page_id, properties=normalized_properties)
                    else:
                        result_obj = existing_pages[0]
                    if upsert_req.content_blocks:
                        engine.append_block_children(block_id=page_id, children=upsert_req.content_blocks)
                    result = {"action": "updated", "page": result_obj}
                else:
                    create_properties = normalized_properties or {}
                    if unique_prop.lower() in ["name", "title"]:
                        create_properties[unique_prop] = {"title": [{"type": "text", "text": {"content": str(unique_value)}}]}
                    else:
                        create_properties[unique_prop] = {"rich_text": [{"type": "text", "text": {"content": str(unique_value)}}]}
                    result_obj = engine.create_page(properties=create_properties, parent_database_id=upsert_req.database_id, children=upsert_req.content_blocks)
                    result = {"action": "created", "page": result_obj}
            
            elif tool_name == "notion.link":
                # Link operation
                from app.models.schemas import LinkRequest
                
                link_req = LinkRequest(**arguments)
                from_type = link_req.from_obj.get("type")
                from_id = link_req.from_obj.get("id")
                to_type = link_req.to_obj.get("type")
                to_id = link_req.to_obj.get("id")
                
                if from_type != "page" or to_type != "page":
                    raise ValueError("Both from and to must be pages")
                
                from_page = engine.get_page(from_id)
                current_properties = from_page.get("properties", {})
                relation_prop = current_properties.get(link_req.relation_property, {})
                relation_data = relation_prop.get("relation", {})
                current_relations = relation_data.get("relation", []) if isinstance(relation_data, dict) else []
                
                existing_ids = [r.get("id") for r in current_relations if isinstance(r, dict)]
                if to_id not in existing_ids:
                    current_relations.append({"id": to_id})
                    result_obj = engine.update_page(
                        page_id=from_id,
                        properties={link_req.relation_property: {"relation": current_relations}},
                    )
                    result = {"action": "linked", "page": result_obj}
                else:
                    result = {"action": "already_linked", "page": from_page}
            
            elif tool_name == "notion.bulk":
                # Bulk operations
                from app.models.schemas import BulkRequest
                from app.routers.bulk import bulk_operations
                
                bulk_req = BulkRequest(**arguments)
                bulk_result = await bulk_operations(request, bulk_req, db)
                result = bulk_result.dict()
            
            elif tool_name == "notion.job_start":
                # Start job
                from app.models.schemas import JobRequest
                from app.routers.bulk import create_job
                
                job_req = JobRequest(**arguments)
                job_result = await create_job(request, job_req, db)
                result = job_result.dict()
            
            elif tool_name == "notion.job_get":
                # Get job status
                from app.routers.bulk import get_job
                
                job_id = arguments.get("job_id")
                if not job_id:
                    raise ValueError("job_id is required")
                
                job_result = await get_job(request, job_id, db)
                result = job_result.dict()
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Audit log
            notion_ids = extract_notion_ids(result) if isinstance(result, dict) else None
            log_audit(
                db=db,
                connection_id=connection_id,
                request_id=request_id,
                actor="chatgpt_mcp",
                method="mcp_tool",
                path=tool_name,
                notion_ids=notion_ids if notion_ids and (notion_ids.get("created") or notion_ids.get("updated")) else None,
                summary=f"MCP tool call: {tool_name}",
                success=True,
            )
            
            # Store idempotency if key provided
            if idempotency_key:
                store_idempotency(
                    db=db,
                    idempotency_key=idempotency_key,
                    connection_id=connection_id,
                    method="POST",
                    path=f"/mcp/tools/{tool_name}",
                    body=arguments,
                    params=None,
                    response_body={"ok": True, "result": result},
                )
            
            return {
                "ok": True,
                "result": result,
                "meta": {"request_id": request_id} if request_id else {},
            }
    
    except HTTPException:
        raise
    except NotionAPIError as e:
        logger.error("mcp_tool_error", tool=tool_name, error=str(e), status_code=e.status_code)
        
        # Audit log failure
        log_audit(
            db=db,
            connection_id=connection_id,
            request_id=request_id,
            actor="chatgpt_mcp",
            method="mcp_tool",
            path=tool_name,
            summary=f"MCP tool call failed: {tool_name}",
            success=False,
            error_code=str(e.status_code) if e.status_code else "API_ERROR",
        )
        
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("mcp_tool_unexpected_error", tool=tool_name, error=str(e), exc_info=True)
        
        # Audit log failure
        log_audit(
            db=db,
            connection_id=connection_id,
            request_id=request_id,
            actor="chatgpt_mcp",
            method="mcp_tool",
            path=tool_name,
            summary=f"MCP tool call failed: {tool_name} - {str(e)}",
            success=False,
            error_code=type(e).__name__,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool call failed: {str(e)}"
        )


@router.get("/tools")
async def list_mcp_tools():
    """
    List available MCP tools
    """
    tools = [
        {
            "name": "notion.request",
            "description": "Generic Notion API request proxy",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PATCH", "DELETE"]},
                    "path": {"type": "string"},
                    "body": {"type": "object"},
                    "query": {"type": "object"},
                },
                "required": ["connection_id", "method", "path"],
            },
        },
        {
            "name": "notion.upsert",
            "description": "Upsert a page in a database (create or update)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "database_id": {"type": "string"},
                    "unique": {"type": "object"},
                    "properties": {"type": "object"},
                    "content_blocks": {"type": "array"},
                },
                "required": ["connection_id", "database_id", "unique"],
            },
        },
        {
            "name": "notion.link",
            "description": "Link two pages via relation property",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "from_obj": {"type": "object"},
                    "to_obj": {"type": "object"},
                    "relation_property": {"type": "string"},
                },
                "required": ["connection_id", "from_obj", "to_obj", "relation_property"],
            },
        },
        {
            "name": "notion.bulk",
            "description": "Execute multiple operations in sequence",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "mode": {"type": "string", "enum": ["stop_on_error", "continue_on_error"]},
                    "ops": {"type": "array"},
                },
                "required": ["connection_id", "ops"],
            },
        },
        {
            "name": "notion.job_start",
            "description": "Start a long-running job",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "kind": {"type": "string", "enum": ["bulk", "os_plan_apply", "migration", "export"]},
                    "args": {"type": "object"},
                },
                "required": ["connection_id", "kind", "args"],
            },
        },
        {
            "name": "notion.job_get",
            "description": "Get job status",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string"},
                    "job_id": {"type": "string"},
                },
                "required": ["connection_id", "job_id"],
            },
        },
    ]
    
    return {
        "tools": tools,
        "protocol": "mcp",
        "version": "1.0",
    }

