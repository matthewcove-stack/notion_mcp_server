"""
Metrics endpoint
"""
from fastapi import APIRouter, Depends
from app.security import verify_bearer_token

router = APIRouter(prefix="/v1", tags=["metrics"])


@router.get("/metrics")
async def get_metrics(
    token: str = Depends(verify_bearer_token),
):
    """
    Get server metrics (requires authentication)
    """
    from app.middleware.metrics import MetricsMiddleware
    
    # Get metrics from middleware if available
    # Note: In production, use a proper metrics library like Prometheus
    return {
        "ok": True,
        "result": {
            "message": "Metrics endpoint - implement with Prometheus or similar",
            "note": "Basic metrics are logged via structured logging",
        },
    }

