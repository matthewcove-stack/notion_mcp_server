"""
Job management endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.jobs.simple_queue import job_queue
from app.models.schemas import StandardResponse
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    kind: str
    args: Dict[str, Any]
    connection_id: Optional[str] = None


@router.post("")
async def create_job(
    req_body: JobCreateRequest,
    request: Request
) -> StandardResponse:
    """
    Create a new background job
    """
    job_id = await job_queue.enqueue(req_body.kind, req_body.args)
    
    return StandardResponse(
        ok=True,
        result={"job_id": job_id},
        meta={"request_id": request.state.request_id}
    )


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request
) -> StandardResponse:
    """
    Get job status
    """
    job = job_queue.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return StandardResponse(
        ok=True,
        result=job_queue.to_dict(job),
        meta={"request_id": request.state.request_id}
    )

