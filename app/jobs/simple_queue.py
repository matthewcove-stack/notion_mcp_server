"""
Simplified in-memory job queue
For production, replace with Celery + Redis
"""
import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()


class Job:
    """Represents a queued job"""
    
    def __init__(self, job_id: str, kind: str, args: Dict[str, Any]):
        self.id = job_id
        self.kind = kind
        self.args = args
        self.status = "queued"  # queued, running, succeeded, failed
        self.progress = 0.0
        self.output = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None


class SimpleJobQueue:
    """
    Simple in-memory job queue
    In production, use Celery with Redis/RabbitMQ
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, job_kind: str, handler: Callable):
        """Register a handler for a job type"""
        self.handlers[job_kind] = handler
        logger.info("job_handler_registered", kind=job_kind)
    
    async def enqueue(self, kind: str, args: Dict[str, Any]) -> str:
        """
        Enqueue a new job
        
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id, kind, args)
        self.jobs[job_id] = job
        
        logger.info("job_enqueued", job_id=job_id, kind=kind)
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        
        return job_id
    
    async def _process_job(self, job_id: str):
        """Process a job"""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = "running"
        job.started_at = datetime.utcnow()
        
        try:
            handler = self.handlers.get(job.kind)
            if not handler:
                raise ValueError(f"No handler for job kind: {job.kind}")
            
            # Execute handler
            result = await handler(job.args, job)
            
            job.status = "succeeded"
            job.progress = 1.0
            job.output = result
            logger.info("job_succeeded", job_id=job_id)
        
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.error("job_failed", job_id=job_id, error=str(e), exc_info=True)
        
        finally:
            job.completed_at = datetime.utcnow()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "id": job.id,
            "kind": job.kind,
            "status": job.status,
            "progress": job.progress,
            "output": job.output,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }


# Global job queue instance
job_queue = SimpleJobQueue()

