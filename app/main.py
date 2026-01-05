"""
Main FastAPI application for Notion MCP Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Notion MCP Server",
    description="MCP server for managing Notion Second Brain workspace",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import middleware
from app.middleware.request_id import add_request_id_middleware
app.middleware("http")(add_request_id_middleware)

# Import routers
from app.routers import databases, second_brain, oauth, mcp

# Include routers
app.include_router(databases.router)
app.include_router(second_brain.router)
app.include_router(oauth.router)
app.include_router(mcp.router)


# OAuth metadata endpoints (must be at app level for .well-known paths)
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """
    OAuth 2.0 Authorization Server Metadata
    Returns server capabilities and endpoints
    Compatible with ChatGPT Personal Pro OAuth discovery
    """
    base_url = os.getenv("BASE_URL", "https://notionmcp.nowhere-else.co.uk")
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "scopes_supported": ["read", "write", "read write"],
    }


@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """
    OpenID Connect Discovery endpoint
    Some OAuth clients expect this endpoint
    """
    return await oauth_metadata()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"ok": True, "status": "healthy"}


@app.get("/version")
async def get_version():
    """Get service version"""
    return {
        "version": "0.1.0",
        "service": "notion-mcp-server"
    }


@app.get("/notion/me")
async def notion_me():
    """Verify Notion token and return user info"""
    notion_token = os.getenv("NOTION_API_TOKEN")
    
    if not notion_token:
        return {
            "ok": False,
            "error": "NOTION_API_TOKEN not configured"
        }
    
    # TODO: Implement actual Notion API call to verify token
    # For now, just return that token is configured
    return {
        "ok": True,
        "message": "Notion token is configured",
        "token_configured": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

