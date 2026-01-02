"""
REST-based MCP for Notion (Actions-ready)
"""
import structlog
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import StandardResponse, MetaResponse
from app.middleware import add_request_id_middleware
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.db.database import init_db
from app.security import verify_bearer_token
from app.routers import oauth, notion, upsert
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.SERVER_NAME,
    description=settings.SERVER_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.middleware("http")(add_request_id_middleware)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register routers
app.include_router(oauth.router)
app.include_router(notion.router)
app.include_router(upsert.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("server_starting", version=settings.VERSION, port=settings.PORT)
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e), exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("server_shutting_down")


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint (public, no auth required)
    Returns: { "ok": true }
    """
    return {"ok": True}


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """
    OpenAPI 3.1 specification endpoint (public, no auth required)
    """
    return JSONResponse(content=app.openapi())


@app.get("/v1/meta", response_model=StandardResponse)
async def get_meta(
    request: Request,
    token: str = Depends(verify_bearer_token)
):
    """
    Get server metadata and status
    Requires bearer token authentication
    """
    request_id = getattr(request.state, "request_id", None)
    
    # TODO: Check Notion API status
    notion_api_status = "unknown"
    
    meta_data = MetaResponse(
        version=settings.VERSION,
        build_hash=None,
        notion_api_status=notion_api_status,
        timestamp=datetime.utcnow()
    )
    
    return StandardResponse(
        ok=True,
        result=meta_data.dict(),
        meta={"request_id": request_id} if request_id else {}
    )
