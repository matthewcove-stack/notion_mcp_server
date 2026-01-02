"""
MCP Notion Server - Fresh Implementation
"""
from fastapi import FastAPI

app = FastAPI(
    title="Notion MCP Server",
    description="MCP server for Notion integration",
    version="0.1.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
