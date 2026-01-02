"""
Metrics middleware for request tracking
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
import time
import structlog

logger = structlog.get_logger()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics: Dict[str, int] = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_status": {},
            "requests_by_endpoint": {},
        }
    
    async def dispatch(self, request: Request, call_next):
        """Dispatch with metrics tracking"""
        start_time = time.time()
        
        # Increment total requests
        self.metrics["requests_total"] += 1
        
        # Track by method
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Track by endpoint
        path = request.url.path
        self.metrics["requests_by_endpoint"][path] = self.metrics["requests_by_endpoint"].get(path, 0) + 1
        
        response = await call_next(request)
        
        # Track by status
        status = response.status_code
        status_range = f"{status // 100}xx"
        self.metrics["requests_by_status"][status_range] = self.metrics["requests_by_status"].get(status_range, 0) + 1
        
        duration = time.time() - start_time
        
        logger.info(
            "request_metrics",
            method=method,
            path=path,
            status=status,
            duration_ms=round(duration * 1000, 2),
        )
        
        return response
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.copy()

