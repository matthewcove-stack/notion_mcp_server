"""
OAuth endpoints for Notion workspace connection
"""
import uuid
import httpx
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import structlog

from app.config import settings
from app.db.database import get_db
from app.db.models import Connection
from app.services.token_encryption import get_token_encryption
from app.models.schemas import StandardResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/oauth", tags=["oauth"])

NOTION_OAUTH_BASE = "https://api.notion.com/v1/oauth"
NOTION_AUTHORIZE_URL = f"{NOTION_OAUTH_BASE}/authorize"
NOTION_TOKEN_URL = f"{NOTION_OAUTH_BASE}/token"


@router.get("/start")
async def oauth_start(
    request: Request,
    state: Optional[str] = Query(None),
    return_url: Optional[str] = Query(None),
    connection_hint: Optional[str] = Query(None),
):
    """
    Start OAuth flow - redirects to Notion authorization
    
    Query params:
    - state: Optional state parameter for CSRF protection
    - return_url: Optional URL to redirect to after OAuth completes
    - connection_hint: Optional hint for connection identification
    """
    if not settings.NOTION_OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured"
        )
    
    if not settings.NOTION_OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth redirect URI not configured"
        )
    
    # Generate state if not provided
    if not state:
        state = str(uuid.uuid4())
    
    # Build authorization URL
    params = {
        "client_id": settings.NOTION_OAUTH_CLIENT_ID,
        "redirect_uri": settings.NOTION_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "state": state,
    }
    
    # Add return_url to state or store separately (simplified: append to state)
    if return_url:
        params["state"] = f"{state}|{return_url}"
    
    # Build query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{NOTION_AUTHORIZE_URL}?{query_string}"
    
    logger.info(
        "oauth_start",
        state=state,
        return_url=return_url,
        connection_hint=connection_hint,
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    OAuth callback - exchanges code for tokens and creates/updates connection
    """
    if not settings.NOTION_OAUTH_CLIENT_ID or not settings.NOTION_OAUTH_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured"
        )
    
    request_id = getattr(request.state, "request_id", None)
    
    try:
        # Extract return_url from state if present
        return_url = None
        if state and "|" in state:
            state, return_url = state.split("|", 1)
        
        # Exchange code for tokens
        logger.info("oauth_callback_exchange", code_prefix=code[:10] if code else None, state=state)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                NOTION_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.NOTION_OAUTH_REDIRECT_URI,
                },
                auth=(settings.NOTION_OAUTH_CLIENT_ID, settings.NOTION_OAUTH_CLIENT_SECRET),
                timeout=30.0,
            )
            
            if response.status_code != 200:
                logger.error(
                    "oauth_token_exchange_failed",
                    status_code=response.status_code,
                    response=response.text[:200],
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token exchange failed: {response.status_code}"
                )
            
            token_data = response.json()
        
        # Extract token information
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")  # May not be present
        expires_in = token_data.get("expires_in")  # May not be present
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token in response"
            )
        
        # Get workspace information
        encryption = get_token_encryption()
        
        async with httpx.AsyncClient() as client:
            workspace_response = await client.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": settings.NOTION_API_VERSION,
                },
                timeout=30.0,
            )
            
            if workspace_response.status_code != 200:
                logger.warning(
                    "oauth_workspace_info_failed",
                    status_code=workspace_response.status_code,
                )
                # Continue without workspace info
        
        # Extract workspace info (simplified - Notion API may return different structure)
        workspace_id = None
        workspace_name = None
        
        if workspace_response.status_code == 200:
            workspace_data = workspace_response.json()
            # Notion API structure may vary - adjust as needed
            if "bot" in workspace_data:
                bot = workspace_data["bot"]
                workspace_id = bot.get("workspace", {}).get("id") if isinstance(bot.get("workspace"), dict) else None
                workspace_name = bot.get("workspace", {}).get("name") if isinstance(bot.get("workspace"), dict) else None
        
        # Encrypt tokens
        access_token_enc = encryption.encrypt(access_token)
        refresh_token_enc = encryption.encrypt(refresh_token) if refresh_token else None
        
        # Calculate expiration
        token_expires_at = None
        if expires_in:
            token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if connection already exists (by workspace_id)
        connection = None
        if workspace_id:
            connection = db.query(Connection).filter(Connection.workspace_id == workspace_id).first()
        
        if connection:
            # Update existing connection
            connection.access_token_enc = access_token_enc
            connection.refresh_token_enc = refresh_token_enc
            connection.token_expires_at = token_expires_at
            if workspace_name:
                connection.workspace_name = workspace_name
            connection.updated_at = datetime.utcnow()
            logger.info("oauth_connection_updated", connection_id=str(connection.id), workspace_id=workspace_id)
        else:
            # Create new connection
            connection = Connection(
                workspace_id=workspace_id or str(uuid.uuid4()),
                workspace_name=workspace_name,
                access_token_enc=access_token_enc,
                refresh_token_enc=refresh_token_enc,
                token_expires_at=token_expires_at,
            )
            db.add(connection)
            logger.info("oauth_connection_created", connection_id=str(connection.id), workspace_id=workspace_id)
        
        db.commit()
        
        # Redirect to return_url or return success
        if return_url:
            return RedirectResponse(url=return_url)
        
        return StandardResponse(
            ok=True,
            result={
                "connection_id": str(connection.id),
                "workspace_id": connection.workspace_id,
                "workspace_name": connection.workspace_name,
            },
            meta={"request_id": request_id} if request_id else {},
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("oauth_callback_error", error=str(e), exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )

