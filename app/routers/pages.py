"""
Page management endpoints
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.models.schemas import (
    StandardResponse,
    PageCreateRequest,
    PageUpdateRequest,
    ConnectionService
)
from app.core.engine import NotionEngine
from app.services.notion_client import get_notion_client
from app.services.audit import audit_service
from app.db import get_db
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/pages", tags=["pages"])


def get_engine() -> NotionEngine:
    """Get Notion engine with token"""
    token = ConnectionService.get_token()
    client = get_notion_client(token)
    return NotionEngine(client)


@router.post("")
async def create_page(
    req_body: PageCreateRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Create a new page
    """
    engine = get_engine()
    
    page = await engine.page_create(
        parent=req_body.parent,
        properties=req_body.properties,
        children=req_body.children,
        icon=req_body.icon,
        cover=req_body.cover
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint="/pages",
        notion_ids={"page_id": page["id"]},
        summary=f"Created page {page['id']}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )


@router.get("/{page_id}")
async def get_page(
    page_id: str,
    request: Request
) -> StandardResponse:
    """
    Retrieve a page
    """
    engine = get_engine()
    page = await engine.page_get(page_id)
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )


@router.patch("/{page_id}")
async def update_page(
    page_id: str,
    req_body: PageUpdateRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Update page properties
    """
    engine = get_engine()
    
    page = await engine.page_update(
        page_id=page_id,
        properties=req_body.properties,
        archived=req_body.archived,
        icon=req_body.icon,
        cover=req_body.cover
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="PATCH",
        endpoint=f"/pages/{page_id}",
        notion_ids={"page_id": page_id},
        summary=f"Updated page {page_id}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )


@router.delete("/{page_id}")
async def archive_page(
    page_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Archive (soft delete) a page
    """
    engine = get_engine()
    page = await engine.page_archive(page_id)
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="DELETE",
        endpoint=f"/pages/{page_id}",
        notion_ids={"page_id": page_id},
        summary=f"Archived page {page_id}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )

