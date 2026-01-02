"""
Upsert and Link endpoints
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.core.engine import CoreEngine
from app.models.schemas import StandardResponse, UpsertRequest, LinkRequest
from app.services.notion_client import NotionAPIError
from app.services.property_normalizer import normalize_properties
from app.decorators.audit import audit_write_operation

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["upsert"])


def get_core_engine(db: Session, connection_id: str) -> CoreEngine:
    """Get core engine instance"""
    try:
        return CoreEngine(db, connection_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/upsert", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def upsert(
    request: Request,
    upsert_req: UpsertRequest,
    db: Session = Depends(get_db),
):
    """
    Upsert a page in a database
    
    Finds a page by unique property value, creates if missing, updates if exists.
    """
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, upsert_req.connection_id) as engine:
            # Normalize properties if provided
            normalized_properties = None
            if upsert_req.properties:
                normalized_properties = normalize_properties(upsert_req.properties)
            
            # Query database to find existing page by unique property
            unique_prop = upsert_req.unique.get("property")
            unique_value = upsert_req.unique.get("value")
            
            if not unique_prop or unique_value is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="unique.property and unique.value are required"
                )
            
            # Build filter to find existing page
            filter_obj = {
                "property": unique_prop,
                "title": {"equals": str(unique_value)} if unique_prop.lower() in ["name", "title"] else {
                    "equals": str(unique_value)
                }
            }
            
            # Try to find existing page
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
                # Update existing page
                page_id = existing_pages[0]["id"]
                
                if normalized_properties:
                    result = engine.update_page(
                        page_id=page_id,
                        properties=normalized_properties,
                    )
                else:
                    result = existing_pages[0]
                
                # Append content blocks if provided
                if upsert_req.content_blocks:
                    engine.append_block_children(
                        block_id=page_id,
                        children=upsert_req.content_blocks,
                    )
                
                logger.info("upsert_updated", page_id=page_id, database_id=upsert_req.database_id)
                
                return StandardResponse(
                    ok=True,
                    result={"action": "updated", "page": result},
                    meta={"request_id": request_id} if request_id else {},
                )
            else:
                # Create new page
                # Build properties with unique property
                create_properties = normalized_properties or {}
                if unique_prop.lower() in ["name", "title"]:
                    create_properties[unique_prop] = {
                        "title": [{"type": "text", "text": {"content": str(unique_value)}}]
                    }
                else:
                    create_properties[unique_prop] = {
                        "rich_text": [{"type": "text", "text": {"content": str(unique_value)}}]
                    }
                
                result = engine.create_page(
                    properties=create_properties,
                    parent_database_id=upsert_req.database_id,
                    children=upsert_req.content_blocks,
                )
                
                logger.info("upsert_created", page_id=result.get("id"), database_id=upsert_req.database_id)
                
                return StandardResponse(
                    ok=True,
                    result={"action": "created", "page": result},
                    meta={"request_id": request_id} if request_id else {},
                )
    
    except HTTPException:
        raise
    except NotionAPIError as e:
        logger.error("upsert_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("upsert_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upsert failed: {str(e)}"
        )


@router.post("/link", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def link(
    request: Request,
    link_req: LinkRequest,
    db: Session = Depends(get_db),
):
    """
    Link two pages via a relation property
    """
    request_id = getattr(request.state, "request_id", None)
    
    try:
        with get_core_engine(db, link_req.connection_id) as engine:
            # Get the "from" page to update its relation property
            from_type = link_req.from_obj.get("type")
            from_id = link_req.from_obj.get("id")
            to_type = link_req.to_obj.get("type")
            to_id = link_req.to_obj.get("id")
            
            if from_type != "page" or to_type != "page":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both from and to must be pages"
                )
            
            # Get the "from" page to see current relations
            from_page = engine.get_page(from_id)
            current_properties = from_page.get("properties", {})
            
            # Get current relation values
            relation_prop = current_properties.get(link_req.relation_property, {})
            relation_data = relation_prop.get("relation", {})
            current_relations = relation_data.get("relation", []) if isinstance(relation_data, dict) else []
            
            # Check if relation already exists
            existing_ids = [r.get("id") for r in current_relations if isinstance(r, dict)]
            if to_id not in existing_ids:
                # Add the new relation
                current_relations.append({"id": to_id})
                
                # Update the page
                result = engine.update_page(
                    page_id=from_id,
                    properties={
                        link_req.relation_property: {
                            "relation": current_relations
                        }
                    },
                )
                
                logger.info("link_created", from_id=from_id, to_id=to_id, property=link_req.relation_property)
                
                return StandardResponse(
                    ok=True,
                    result={"action": "linked", "page": result},
                    meta={"request_id": request_id} if request_id else {},
                )
            else:
                # Relation already exists
                logger.info("link_exists", from_id=from_id, to_id=to_id, property=link_req.relation_property)
                
                return StandardResponse(
                    ok=True,
                    result={"action": "already_linked", "page": from_page},
                    meta={"request_id": request_id} if request_id else {},
                )
    
    except HTTPException:
        raise
    except NotionAPIError as e:
        logger.error("link_error", error=str(e), status_code=e.status_code)
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error("link_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Link failed: {str(e)}"
        )

