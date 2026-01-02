"""
Bulk operations and Jobs endpoints
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from datetime import datetime
import structlog
import uuid

from app.db.database import get_db
from app.core.engine import CoreEngine
from app.models.schemas import StandardResponse, BulkRequest, JobRequest, JobStatus
from app.services.notion_client import NotionAPIError
from app.routers.upsert import upsert, link
from app.decorators.audit import audit_write_operation

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["bulk"])


def get_core_engine(db: Session, connection_id: str) -> CoreEngine:
    """Get core engine instance"""
    try:
        return CoreEngine(db, connection_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/bulk", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def bulk_operations(
    request: Request,
    bulk_req: BulkRequest,
    db: Session = Depends(get_db),
):
    """
    Execute multiple operations in sequence
    
    Operations can be: upsert, link, notion.request
    Mode: stop_on_error (default) or continue_on_error
    """
    request_id = getattr(request.state, "request_id", None)
    
    results = []
    errors = []
    
    try:
        with get_core_engine(db, bulk_req.connection_id) as engine:
            for idx, op in enumerate(bulk_req.ops):
                try:
                    op_result = None
                    
                    if op.op == "upsert":
                        # Import here to avoid circular dependency
                        from app.models.schemas import UpsertRequest
                        upsert_req = UpsertRequest(**op.args)
                        # Call upsert logic directly
                        op_result = await _execute_upsert(engine, upsert_req, request_id)
                    
                    elif op.op == "link":
                        from app.models.schemas import LinkRequest
                        link_req = LinkRequest(**op.args)
                        op_result = await _execute_link(engine, link_req, request_id)
                    
                    elif op.op == "notion.request":
                        # Generic Notion API request
                        method = op.args.get("method", "GET").upper()
                        path = op.args.get("path", "")
                        body = op.args.get("body")
                        params = op.args.get("query")
                        
                        if method == "GET":
                            op_result = engine.client.get(path, params=params)
                        elif method == "POST":
                            op_result = engine.client.post(path, json=body)
                        elif method == "PATCH":
                            op_result = engine.client.patch(path, json=body)
                        elif method == "DELETE":
                            op_result = engine.client.delete(path)
                        else:
                            raise ValueError(f"Unsupported method: {method}")
                    
                    else:
                        raise ValueError(f"Unknown operation: {op.op}")
                    
                    results.append({
                        "op": op.op,
                        "index": idx,
                        "success": True,
                        "result": op_result,
                    })
                
                except Exception as e:
                    error_info = {
                        "op": op.op,
                        "index": idx,
                        "success": False,
                        "error": str(e),
                    }
                    errors.append(error_info)
                    results.append(error_info)
                    
                    if bulk_req.mode == "stop_on_error":
                        logger.warning("bulk_stopped_on_error", index=idx, op=op.op, error=str(e))
                        break
                    else:
                        logger.warning("bulk_continue_after_error", index=idx, op=op.op, error=str(e))
        
        return StandardResponse(
            ok=len(errors) == 0,
            result={
                "total": len(bulk_req.ops),
                "succeeded": len([r for r in results if r.get("success")]),
                "failed": len(errors),
                "results": results,
            },
            error={"errors": errors} if errors else None,
            meta={"request_id": request_id} if request_id else {},
        )
    
    except Exception as e:
        logger.error("bulk_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operations failed: {str(e)}"
        )


async def _execute_upsert(engine: CoreEngine, upsert_req, request_id):
    """Execute upsert operation"""
    from app.services.property_normalizer import normalize_properties
    
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
            result = engine.update_page(page_id=page_id, properties=normalized_properties)
        else:
            result = existing_pages[0]
        if upsert_req.content_blocks:
            engine.append_block_children(block_id=page_id, children=upsert_req.content_blocks)
        return {"action": "updated", "page": result}
    else:
        create_properties = normalized_properties or {}
        if unique_prop.lower() in ["name", "title"]:
            create_properties[unique_prop] = {"title": [{"type": "text", "text": {"content": str(unique_value)}}]}
        else:
            create_properties[unique_prop] = {"rich_text": [{"type": "text", "text": {"content": str(unique_value)}}]}
        result = engine.create_page(properties=create_properties, parent_database_id=upsert_req.database_id, children=upsert_req.content_blocks)
        return {"action": "created", "page": result}


async def _execute_link(engine: CoreEngine, link_req, request_id):
    """Execute link operation"""
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
        result = engine.update_page(
            page_id=from_id,
            properties={link_req.relation_property: {"relation": current_relations}},
        )
        return {"action": "linked", "page": result}
    else:
        return {"action": "already_linked", "page": from_page}


@router.post("/jobs", response_model=StandardResponse)
@audit_write_operation(actor="chatgpt_action")
async def create_job(
    request: Request,
    job_req: JobRequest,
    db: Session = Depends(get_db),
):
    """
    Create a job for long-running operations
    
    Job kinds: bulk, os_plan_apply, migration, export
    """
    request_id = getattr(request.state, "request_id", None)
    
    from app.jobs.models import Job
    
    try:
        # Create job record
        job = Job(
            connection_id=job_req.connection_id,
            kind=job_req.kind,
            status="queued",
            progress=0.0,
            args=job_req.args,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info("job_created", job_id=str(job.id), kind=job_req.kind)
        
        # For now, execute synchronously (in production, use background task queue)
        # TODO: Implement async job execution with background workers
        if job_req.kind == "bulk":
            # Execute bulk operation synchronously
            from app.models.schemas import BulkRequest
            bulk_req = BulkRequest(**job_req.args)
            bulk_req.connection_id = job_req.connection_id
            
            job.status = "running"
            job.progress = 0.1
            db.commit()
            
            try:
                with get_core_engine(db, bulk_req.connection_id) as engine:
                    # Execute bulk operations
                    bulk_result = await bulk_operations(request, bulk_req, db)
                    
                    job.status = "succeeded"
                    job.progress = 1.0
                    job.output = bulk_result.dict()
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
                raise
        
        return StandardResponse(
            ok=True,
            result={
                "job_id": str(job.id),
                "status": job.status,
                "progress": job.progress,
            },
            meta={"request_id": request_id} if request_id else {},
        )
    
    except Exception as e:
        db.rollback()
        logger.error("job_create_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job creation failed: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=StandardResponse)
async def get_job(
    request: Request,
    job_id: str = Path(...),
    db: Session = Depends(get_db),
):
    """Get job status"""
    request_id = getattr(request.state, "request_id", None)
    
    from app.jobs.models import Job
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return StandardResponse(
            ok=True,
            result={
                "job_id": str(job.id),
                "status": job.status,
                "progress": job.progress,
                "output": job.output,
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            },
            meta={"request_id": request_id} if request_id else {},
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("job_get_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get job failed: {str(e)}"
        )

