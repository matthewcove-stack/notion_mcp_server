"""
Notion API endpoints - core primitives
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.core.engine import CoreEngine
from app.models.schemas import (
    StandardResponse,
    SearchRequest,
    CreateDatabaseRequest,
    UpdateDatabaseRequest,
    QueryDatabaseRequest,
    CreatePageRequest,
    UpdatePageRequest,
    ArchivePageRequest,
    GetBlockChildrenRequest,
    UpdateBlockRequest,
    AppendBlockChildrenRequest,
)
from app.services.notion_client import NotionAPIError
from app.decorators.audit import audit_write_operation

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["notion"])


def get_core_engine(db: Session, connection_id: str) -> CoreEngine:
    """Get core engine instance"""
    try:
        return CoreEngine(db, connection_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Search
@router.post("/notion/search", response_model=StandardResponse)
async def search_notion(
    request: Request,
    search_req: SearchRequest,
    db: Session = Depends(get_db),
):
    """Search Notion workspace"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, search_req.connection_id) as engine:
            result = engine.search(
                query=search_req.query,
                filter_obj=search_req.filter,
                sort=search_req.sort,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_search_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_search_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# Databases
@router.post("/databases", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def create_database(
    request: Request,
    db_req: CreateDatabaseRequest,
    db: Session = Depends(get_db),
):
    """Create a database"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, db_req.connection_id) as engine:
            result = engine.create_database(
                parent_page_id=db_req.parent_page_id,
                title=db_req.title,
                properties=db_req.properties,
                icon=db_req.icon,
                cover=db_req.cover,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_create_database_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_create_database_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create database failed: {str(e)}"
        )


@router.get("/databases/{database_id}", response_model=StandardResponse)
async def get_database(
    request: Request,
    database_id: str = Path(...),
    connection_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Retrieve a database"""
    
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, connection_id) as engine:
            result = engine.get_database(database_id)
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_get_database_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_get_database_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get database failed: {str(e)}"
        )


@router.patch("/databases/{database_id}", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def update_database(
    request: Request,
    database_id: str = Path(...),
    db_req: UpdateDatabaseRequest = ...,
    db: Session = Depends(get_db),
):
    """Update a database"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, db_req.connection_id) as engine:
            result = engine.update_database(
                database_id=database_id,
                title=db_req.title,
                properties=db_req.properties,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_update_database_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_update_database_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update database failed: {str(e)}"
        )


@router.post("/databases/{database_id}/query", response_model=StandardResponse)
async def query_database(
    request: Request,
    database_id: str = Path(...),
    query_req: QueryDatabaseRequest = ...,
    db: Session = Depends(get_db),
):
    """Query a database"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, query_req.connection_id) as engine:
            result = engine.query_database(
                database_id=database_id,
                filter_obj=query_req.filter,
                sorts=query_req.sorts,
                start_cursor=query_req.start_cursor,
                page_size=query_req.page_size,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_query_database_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_query_database_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query database failed: {str(e)}"
        )


# Pages
@router.post("/pages", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def create_page(
    request: Request,
    page_req: CreatePageRequest,
    db: Session = Depends(get_db),
):
    """Create a page"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, page_req.connection_id) as engine:
            result = engine.create_page(
                parent_page_id=page_req.parent_page_id,
                parent_database_id=page_req.parent_database_id,
                properties=page_req.properties,
                children=page_req.children,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotionAPIError as e:
        logger.error("notion_create_page_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_create_page_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create page failed: {str(e)}"
        )


@router.get("/pages/{page_id}", response_model=StandardResponse)
async def get_page(
    request: Request,
    page_id: str = Path(...),
    connection_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Retrieve a page"""
    
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, connection_id) as engine:
            result = engine.get_page(page_id)
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_get_page_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_get_page_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get page failed: {str(e)}"
        )


@router.patch("/pages/{page_id}", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def update_page(
    request: Request,
    page_id: str = Path(...),
    page_req: UpdatePageRequest = ...,
    db: Session = Depends(get_db),
):
    """Update a page"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, page_req.connection_id) as engine:
            result = engine.update_page(
                page_id=page_id,
                properties=page_req.properties,
                archived=page_req.archived,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_update_page_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_update_page_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update page failed: {str(e)}"
        )


@router.post("/pages/{page_id}/archive", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def archive_page(
    request: Request,
    page_id: str = Path(...),
    archive_req: ArchivePageRequest = ...,
    db: Session = Depends(get_db),
):
    """Archive or unarchive a page"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, archive_req.connection_id) as engine:
            if archive_req.archived:
                result = engine.archive_page(page_id)
            else:
                result = engine.unarchive_page(page_id)
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_archive_page_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_archive_page_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Archive page failed: {str(e)}"
        )


# Blocks
@router.get("/blocks/{block_id}/children", response_model=StandardResponse)
async def get_block_children(
    request: Request,
    block_id: str = Path(...),
    connection_id: str = Query(...),
    start_cursor: Optional[str] = Query(None),
    page_size: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get block children"""
    
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, connection_id) as engine:
            result = engine.get_block_children(
                block_id=block_id,
                start_cursor=start_cursor,
                page_size=page_size,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_get_block_children_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_get_block_children_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get block children failed: {str(e)}"
        )


@router.patch("/blocks/{block_id}", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def update_block(
    request: Request,
    block_id: str = Path(...),
    block_req: UpdateBlockRequest = ...,
    db: Session = Depends(get_db),
):
    """Update a block"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, block_req.connection_id) as engine:
            result = engine.update_block(
                block_id=block_id,
                block_data=block_req.block_data,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_update_block_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_update_block_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update block failed: {str(e)}"
        )


@router.post("/blocks/{block_id}/children", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def append_block_children(
    request: Request,
    block_id: str = Path(...),
    append_req: AppendBlockChildrenRequest = ...,
    db: Session = Depends(get_db),
):
    """Append children to a block"""
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, append_req.connection_id) as engine:
            result = engine.append_block_children(
                block_id=block_id,
                children=append_req.children,
            )
        
        return StandardResponse(
            ok=True,
            result=result,
            meta={"request_id": request_id} if request_id else {},
        )
    except NotionAPIError as e:
        logger.error("notion_append_block_children_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("notion_append_block_children_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Append block children failed: {str(e)}"
        )

