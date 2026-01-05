"""
Block management endpoints
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.models.schemas import StandardResponse, BlockAppendRequest, ConnectionService
from app.core.engine import NotionEngine
from app.services.notion_client import get_notion_client
from app.services.audit import audit_service
from app.db import get_db
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/blocks", tags=["blocks"])


def get_engine() -> NotionEngine:
    """Get Notion engine with token"""
    token = ConnectionService.get_token()
    client = get_notion_client(token)
    return NotionEngine(client)


@router.get("/{block_id}")
async def get_block(
    block_id: str,
    request: Request
) -> StandardResponse:
    """
    Retrieve a block
    """
    engine = get_engine()
    block = await engine.block_get(block_id)
    
    return StandardResponse(
        ok=True,
        result=block,
        meta={"request_id": request.state.request_id}
    )


@router.get("/{block_id}/children")
async def list_block_children(
    block_id: str,
    request: Request,
    page_size: int = 100
) -> StandardResponse:
    """
    List children of a block
    """
    engine = get_engine()
    children = await engine.block_children_list(block_id, page_size)
    
    return StandardResponse(
        ok=True,
        result=children,
        meta={"request_id": request.state.request_id}
    )


@router.post("/{block_id}/children")
async def append_block_children(
    block_id: str,
    req_body: BlockAppendRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Append children to a block
    """
    engine = get_engine()
    
    result = await engine.block_children_append(
        block_id=block_id,
        children=req_body.children
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint=f"/blocks/{block_id}/children",
        notion_ids={"block_id": block_id},
        summary=f"Appended {len(req_body.children)} blocks to {block_id}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=result,
        meta={"request_id": request.state.request_id}
    )


@router.delete("/{block_id}")
async def delete_block(
    block_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Delete a block
    """
    engine = get_engine()
    result = await engine.block_delete(block_id)
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="DELETE",
        endpoint=f"/blocks/{block_id}",
        notion_ids={"block_id": block_id},
        summary=f"Deleted block {block_id}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=result,
        meta={"request_id": request.state.request_id}
    )

