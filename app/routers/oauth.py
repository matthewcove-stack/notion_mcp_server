"""
OAuth 2.0 endpoints for ChatGPT MCP connector authentication
Compatible with ChatGPT Personal Pro developer mode
"""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import Optional
from pydantic import BaseModel
import os
import secrets
import httpx
from urllib.parse import urlencode
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/oauth", tags=["oauth"])


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class OAuthErrorResponse(BaseModel):
    error: str
    error_description: Optional[str] = None


@router.get("/authorize")
async def authorize(
    response_type: str = Query(..., description="Must be 'code' for authorization code flow"),
    client_id: str = Query(..., description="ChatGPT's client ID"),
    redirect_uri: str = Query(..., description="ChatGPT's redirect URI"),
    scope: Optional[str] = Query(None, description="Requested scopes"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    code_challenge: Optional[str] = Query(None, description="PKCE code challenge"),
    code_challenge_method: Optional[str] = Query(None, description="PKCE method (S256 or plain)"),
):
    """
    OAuth 2.0 Authorization endpoint
    ChatGPT will redirect users here to authorize access to the MCP server.
    
    For ChatGPT Personal Pro, this endpoint handles the OAuth authorization flow.
    """
    # Validate response_type
    if response_type != "code":
        raise HTTPException(
            status_code=400,
            detail="response_type must be 'code' for authorization code flow"
        )
    
    # Validate redirect_uri (in production, validate against registered redirect URIs)
    # For ChatGPT, we'll accept the redirect_uri as provided
    
    # Store authorization request parameters
    # In production: Store in Redis/database with TTL (10 minutes)
    # For now: Generate code immediately (simplified flow)
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store code with metadata (in production, use Redis)
    # Store: code -> {client_id, redirect_uri, code_challenge, expires_at}
    # For now, we'll proceed with code generation
    
    # Build redirect URL with authorization code
    redirect_params = {
        "code": auth_code,
    }
    if state:
        redirect_params["state"] = state
    
    redirect_url = f"{redirect_uri}?{urlencode(redirect_params)}"
    
    logger.info(
        "oauth_authorize",
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        has_code_challenge=bool(code_challenge)
    )
    
    # For ChatGPT MCP, we can auto-approve and redirect immediately
    # In production, you might want to show a consent screen first
    # Redirect back to ChatGPT with authorization code
    return RedirectResponse(url=redirect_url)


@router.post("/token", response_model=OAuthTokenResponse)
async def token(request: Request):
    """
    OAuth 2.0 Token endpoint
    ChatGPT exchanges authorization code for access token.
    
    Supports both authorization_code and refresh_token grant types.
    Compatible with ChatGPT Personal Pro MCP connector OAuth flow.
    
    Accepts form-encoded POST data (standard OAuth 2.0 format).
    """
    # Read form data (standard OAuth 2.0 format)
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        grant_type = form_data.get("grant_type")
        code = form_data.get("code")
        refresh_token = form_data.get("refresh_token")
        redirect_uri = form_data.get("redirect_uri")
        client_id = form_data.get("client_id")
        client_secret = form_data.get("client_secret")
        code_verifier = form_data.get("code_verifier")
    elif "application/json" in content_type:
        # Also support JSON for compatibility
        json_data = await request.json()
        grant_type = json_data.get("grant_type")
        code = json_data.get("code")
        refresh_token = json_data.get("refresh_token")
        redirect_uri = json_data.get("redirect_uri")
        client_id = json_data.get("client_id")
        client_secret = json_data.get("client_secret")
        code_verifier = json_data.get("code_verifier")
    else:
        raise HTTPException(
            status_code=400,
            detail="Content-Type must be application/x-www-form-urlencoded or application/json"
        )
    
    if not grant_type:
        raise HTTPException(status_code=400, detail="grant_type parameter required")
    
    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(status_code=400, detail="code parameter required for authorization_code grant")
        
        # Validate authorization code (in production, check against stored codes in Redis/DB)
        # Verify code hasn't been used and hasn't expired
        # For now, we'll accept any code format
        
        # Validate PKCE if code_challenge was provided during authorization
        # if code_challenge was S256, verify code_verifier matches
        
        # Generate access token
        access_token = secrets.token_urlsafe(64)
        refresh_token_value = secrets.token_urlsafe(64)
        
        # Store tokens (in production, encrypt and store in database)
        # Map: access_token -> {user_id, client_id, expires_at, scopes}
        
        logger.info(
            "oauth_token_exchange",
            grant_type=grant_type,
            client_id=client_id,
            has_code_verifier=bool(code_verifier)
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,  # 1 hour
            refresh_token=refresh_token_value,
            scope="read write"
        )
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token parameter required for refresh_token grant")
        
        # Validate refresh token and issue new access token
        # In production, validate against stored tokens
        
        new_access_token = secrets.token_urlsafe(64)
        
        logger.info("oauth_token_refresh", grant_type=grant_type)
        
        return OAuthTokenResponse(
            access_token=new_access_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token,  # Optionally rotate refresh token
            scope="read write"
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {grant_type}")


# Note: .well-known routes need to be registered at app level, not router level
# These will be added to main.py

