"""
Security and authentication utilities
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()

security = HTTPBearer(auto_error=True)


async def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify bearer token for ChatGPT Actions authentication
    
    Returns the token if valid, raises HTTPException if invalid
    """
    if not settings.ACTION_API_TOKEN:
        logger.error("ACTION_API_TOKEN not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server authentication not configured"
        )
    
    token = credentials.credentials
    
    if token != settings.ACTION_API_TOKEN:
        logger.warning("invalid_bearer_token", token_prefix=token[:10] if token else None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

