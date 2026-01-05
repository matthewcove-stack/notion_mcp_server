"""
High-level operations: search, upsert, link, bulk
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.models.schemas import (
    StandardResponse,
    SearchRequest,
    UpsertRequest,
    LinkRequest,
    BulkRequest,
    ConnectionService
)
from app.core.engine import NotionEngine
from app.services.notion_client import get_notion_client
from app.services.audit import audit_service
from app.db import get_db
import structlog

logger = structlog.get_logger()
router = APIRouter(tags=["operations"])


def get_engine() -> NotionEngine:
    """Get Notion engine with token"""
    token = ConnectionService.get_token()
    client = get_notion_client(token)
    return NotionEngine(client)


@router.post("/search")
async def search(
    req_body: SearchRequest,
    request: Request
) -> StandardResponse:
    """
    Search for pages and databases
    """
    engine = get_engine()
    
    results = await engine.search(
        query=req_body.query,
        filter=req_body.filter,
        sort=req_body.sort,
        page_size=req_body.page_size
    )
    
    return StandardResponse(
        ok=True,
        result=results,
        meta={"request_id": request.state.request_id}
    )


@router.post("/upsert")
async def upsert(
    req_body: UpsertRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Create or update a page
    """
    engine = get_engine()
    
    page = await engine.upsert_page(
        database_id=req_body.database_id,
        unique_property=req_body.unique_property,
        unique_value=req_body.unique_value,
        properties=req_body.properties,
        children=req_body.children
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint="/upsert",
        notion_ids={"page_id": page["id"]},
        summary=f"Upserted page: {req_body.unique_value}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )


@router.post("/link")
async def link_pages(
    req_body: LinkRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Link two pages via relation property
    """
    engine = get_engine()
    
    page = await engine.link_pages(
        from_page_id=req_body.from_page_id,
        to_page_id=req_body.to_page_id,
        relation_property=req_body.relation_property
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint="/link",
        notion_ids={
            "from_page_id": req_body.from_page_id,
            "to_page_id": req_body.to_page_id
        },
        summary=f"Linked pages via {req_body.relation_property}",
        success=True
    )
    
    return StandardResponse(
        ok=True,
        result=page,
        meta={"request_id": request.state.request_id}
    )


@router.post("/bulk")
async def bulk_operations(
    req_body: BulkRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Execute multiple operations
    """
    engine = get_engine()
    
    # Convert BulkOperation models to dicts
    ops = [{"op": op.op, "args": op.args} for op in req_body.operations]
    
    results = await engine.bulk_operations(
        operations=ops,
        mode=req_body.mode
    )
    
    audit_service.log_operation(
        db=db,
        request_id=request.state.request_id,
        actor="chatgpt_action",
        method="POST",
        endpoint="/bulk",
        notion_ids={},
        summary=f"Bulk: {results['succeeded']}/{results['total']} succeeded",
        success=results['failed'] == 0
    )
    
    return StandardResponse(
        ok=True,
        result=results,
        meta={"request_id": request.state.request_id}
    )

