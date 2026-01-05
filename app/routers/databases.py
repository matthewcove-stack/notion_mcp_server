"""
Database management endpoints
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from typing import Any
from app.models.schemas import (
    StandardResponse,
    DatabaseCreateRequest,
    DatabaseUpdateRequest,
    DatabaseQueryRequest,
    ConnectionService
)
from app.core.engine import NotionEngine
from app.services.notion_client import get_notion_client
from app.services.audit import audit_service
from app.db import get_db
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/databases", tags=["databases"])


def get_engine() -> NotionEngine:
    """Get Notion engine with token"""
    token = ConnectionService.get_token()
    client = get_notion_client(token)
    return NotionEngine(client)


@router.get("")
async def list_databases(
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    List all databases
    """
    engine = get_engine()
    databases = await engine.database_list()
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="GET",
        endpoint="/databases",
        summary=f"Listed {len(databases)} databases",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=databases,
        meta={"request_id": request.state.request_id}
    )


@router.post("")
async def create_database(
    req_body: DatabaseCreateRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Create a new database
    """
    engine = get_engine()
    
    database = await engine.database_create(
        parent_page_id=req_body.parent_page_id,
        title=req_body.title,
        properties=req_body.properties,
        icon=req_body.icon,
        cover=req_body.cover
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint="/databases",
        notion_ids={"database_id": database["id"]},
        summary=f"Created database: {req_body.title}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=database,
        meta={"request_id": request.state.request_id}
    )


@router.get("/{database_id}")
async def get_database(
    database_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get database schema
    """
    engine = get_engine()
    database = await engine.database_get(database_id)
    
    return StandardResponse(
        ok=True,
        result=database,
        meta={"request_id": request.state.request_id}
    )


@router.patch("/{database_id}")
async def update_database(
    database_id: str,
    req_body: DatabaseUpdateRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Update database schema
    """
    engine = get_engine()
    
    database = await engine.database_update(
        database_id=database_id,
        title=req_body.title,
        properties=req_body.properties
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="PATCH",
        endpoint=f"/databases/{database_id}",
        notion_ids={"database_id": database_id},
        summary=f"Updated database {database_id}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=database,
        meta={"request_id": request.state.request_id}
    )


@router.post("/{database_id}/query")
async def query_database(
    database_id: str,
    req_body: DatabaseQueryRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Query a database
    """
    engine = get_engine()
    
    results = await engine.database_query(
        database_id=database_id,
        filter=req_body.filter,
        sorts=req_body.sorts,
        page_size=req_body.page_size
    )
    
    return StandardResponse(
        ok=True,
        result=results,
        meta={"request_id": request.state.request_id}
    )

