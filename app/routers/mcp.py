"""
MCP (Model Context Protocol) SSE endpoint for ChatGPT integration
Implements Server-Sent Events transport for MCP protocol
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator, Dict, Any
import json
import asyncio
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/mcp", tags=["mcp"])

# Store active sessions for POST message handling
active_sessions: Dict[str, Dict[str, Any]] = {}


async def mcp_event_stream(request: Request) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for MCP protocol
    ChatGPT connects to this stream to receive MCP tool definitions and responses
    """
    try:
        # Send initial connection message
        yield f"event: connected\n"
        yield f"data: {json.dumps({'status': 'connected', 'protocol': 'mcp', 'version': '1.0'})}\n\n"
        
        # Send available tools
        tools = {
            "event": "tools",
            "tools": [
                {
                    "name": "notion.list_databases",
                    "description": "List all Notion databases",
                    "parameters": {}
                },
                {
                    "name": "notion.get_database",
                    "description": "Get database schema and details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "database_id": {
                                "type": "string",
                                "description": "The database ID"
                            }
                        },
                        "required": ["database_id"]
                    }
                },
                {
                    "name": "notion.create_page",
                    "description": "Create a new page in Notion",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "database_id": {
                                "type": "string",
                                "description": "The database ID to create the page in"
                            },
                            "title": {
                                "type": "string",
                                "description": "The page title"
                            },
                            "properties": {
                                "type": "object",
                                "description": "Page properties"
                            }
                        },
                        "required": ["database_id", "title"]
                    }
                },
                {
                    "name": "second_brain.status",
                    "description": "Check Second Brain structure status",
                    "parameters": {}
                },
                {
                    "name": "second_brain.bootstrap",
                    "description": "Create Second Brain structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "parent_page_id": {
                                "type": "string",
                                "description": "Optional parent page ID"
                            }
                        }
                    }
                }
            ]
        }
        
        yield f"event: tools\n"
        yield f"data: {json.dumps(tools)}\n\n"
        
        # Keep connection alive
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("mcp_client_disconnected")
                break
            
            # Send keepalive ping every 30 seconds
            yield f"event: ping\n"
            yield f"data: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
            await asyncio.sleep(30)
            
    except asyncio.CancelledError:
        logger.info("mcp_stream_cancelled")
    except Exception as e:
        logger.error("mcp_stream_error", error=str(e), exc_info=True)
        yield f"event: error\n"
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.get("/sse")
async def mcp_sse_get(request: Request):
    """
    MCP SSE endpoint - ChatGPT connects here (GET for streaming)
    Returns Server-Sent Events stream with MCP protocol
    """
    logger.info(
        "mcp_connection_started",
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return StreamingResponse(
        mcp_event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/sse")
async def mcp_sse_post(request: Request):
    """
    MCP SSE endpoint - ChatGPT sends messages here (POST for commands)
    Handles MCP protocol messages from ChatGPT
    """
    try:
        # Read the message from ChatGPT
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            message = await request.json()
        else:
            body = await request.body()
            message = json.loads(body.decode('utf-8'))
        
        logger.info(
            "mcp_message_received",
            message_type=message.get("type"),
            method=message.get("method"),
            client_ip=request.client.host if request.client else None
        )
        
        # Handle different MCP message types
        # MCP uses JSON-RPC 2.0 format with "method" field
        method = message.get("method")
        
        if method:
            # Handle tool invocation requests
            if method == "tools/call":
                params = message.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                logger.info("mcp_tool_call", tool=tool_name, args=tool_args)
                
                # Execute the tool (placeholder - will implement actual Notion calls later)
                result = await execute_tool(tool_name, tool_args)
                
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": result
                })
            
            elif method == "initialize":
                # Handle initialization request
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {}
                        },
                        "serverInfo": {
                            "name": "notion-mcp-server",
                            "version": "0.1.0"
                        }
                    }
                })
            
            elif method == "tools/list":
                # Handle tools list request
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "notion.list_databases",
                                "description": "List all Notion databases in the workspace",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "notion.get_database",
                                "description": "Get detailed information about a specific Notion database including its schema",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "database_id": {
                                            "type": "string",
                                            "description": "The ID of the database to retrieve"
                                        }
                                    },
                                    "required": ["database_id"]
                                }
                            },
                            {
                                "name": "notion.create_page",
                                "description": "Create a new page in a Notion database",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "database_id": {
                                            "type": "string",
                                            "description": "The database ID to create the page in"
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "The title of the page"
                                        },
                                        "properties": {
                                            "type": "object",
                                            "description": "Additional properties for the page"
                                        }
                                    },
                                    "required": ["database_id", "title"]
                                }
                            },
                            {
                                "name": "second_brain.status",
                                "description": "Check the status of the Second Brain structure in Notion",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "second_brain.bootstrap",
                                "description": "Create the Second Brain structure in Notion workspace",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "parent_page_id": {
                                            "type": "string",
                                            "description": "Optional parent page ID to create the structure under"
                                        }
                                    },
                                    "required": []
                                }
                            }
                        ]
                    }
                })
        
        # Default response for unknown methods
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        })
        
    except Exception as e:
        logger.error("mcp_message_error", error=str(e), exc_info=True)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": message.get("id") if hasattr(message, 'get') else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            },
            status_code=200  # MCP uses 200 with error object
        )


async def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call from ChatGPT with actual Notion API integration
    """
    from app.core.engine import NotionEngine
    from app.services.notion_client import get_notion_client
    from app.models.schemas import ConnectionService
    
    logger.info("executing_tool", tool=tool_name, args=args)
    
    # Get Notion engine
    token = ConnectionService.get_token()
    if not token:
        return {"error": "NOTION_API_TOKEN not configured"}
    
    client = get_notion_client(token)
    engine = NotionEngine(client)
    
    try:
        # Database operations
        if tool_name == "notion.list_databases":
            databases = await engine.database_list()
            return {"databases": databases, "count": len(databases)}
        
        elif tool_name == "notion.get_database":
            db_id = args.get("database_id")
            database = await engine.database_get(db_id)
            return database
        
        elif tool_name == "notion.create_database":
            database = await engine.database_create(
                parent_page_id=args["parent_page_id"],
                title=args["title"],
                properties=args["properties"],
                icon=args.get("icon"),
                cover=args.get("cover")
            )
            return database
        
        elif tool_name == "notion.query_database":
            results = await engine.database_query(
                database_id=args["database_id"],
                filter=args.get("filter"),
                sorts=args.get("sorts")
            )
            return results
        
        # Page operations
        elif tool_name == "notion.create_page":
            # Handle simplified format
            if "database_id" in args and "title" in args:
                # Convert to full format
                parent = {"type": "database_id", "database_id": args["database_id"]}
                properties = args.get("properties", {})
                if "title" in args:
                    properties["Name"] = {"type": "title", "value": args["title"]}
                page = await engine.page_create(
                    parent=parent,
                    properties=properties,
                    children=args.get("children")
                )
            else:
                # Full format
                page = await engine.page_create(
                    parent=args["parent"],
                    properties=args["properties"],
                    children=args.get("children")
                )
            return page
        
        elif tool_name == "notion.get_page":
            page = await engine.page_get(args["page_id"])
            return page
        
        elif tool_name == "notion.update_page":
            page = await engine.page_update(
                page_id=args["page_id"],
                properties=args.get("properties"),
                archived=args.get("archived")
            )
            return page
        
        # Search
        elif tool_name == "notion.search":
            results = await engine.search(
                query=args.get("query", ""),
                filter=args.get("filter"),
                sort=args.get("sort")
            )
            return results
        
        # High-level operations
        elif tool_name == "notion.upsert":
            page = await engine.upsert_page(
                database_id=args["database_id"],
                unique_property=args["unique_property"],
                unique_value=args["unique_value"],
                properties=args["properties"],
                children=args.get("children")
            )
            return page
        
        elif tool_name == "notion.link":
            page = await engine.link_pages(
                from_page_id=args["from_page_id"],
                to_page_id=args["to_page_id"],
                relation_property=args["relation_property"]
            )
            return page
        
        elif tool_name == "notion.bulk":
            results = await engine.bulk_operations(
                operations=args["operations"],
                mode=args.get("mode", "stop_on_error")
            )
            return results
        
        # Blocks
        elif tool_name == "notion.append_blocks":
            result = await engine.block_children_append(
                block_id=args["block_id"],
                children=args["children"]
            )
            return result
        
        # Second Brain operations
        elif tool_name == "second_brain.status":
            databases = await engine.database_list()
            return {
                "initialized": len(databases) > 0,
                "databases_count": len(databases),
                "databases": [{"id": db["id"], "title": db.get("title", [{}])[0].get("plain_text", "Untitled")} for db in databases[:5]]
            }
        
        elif tool_name == "second_brain.bootstrap":
            return {
                "status": "info",
                "message": "Second Brain bootstrap should be done via direct database creation",
                "note": "Use notion.create_database to create your databases with desired schemas"
            }
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    except Exception as e:
        logger.error("tool_execution_error", tool=tool_name, error=str(e), exc_info=True)
        return {"error": str(e), "tool": tool_name}


@router.get("")
async def mcp_info():
    """
    MCP endpoint info
    Returns information about the MCP server
    """
    return {
        "protocol": "mcp",
        "version": "1.0",
        "transport": "sse",
        "endpoint": "/mcp/sse",
        "status": "active",
        "tools_available": 5
    }

