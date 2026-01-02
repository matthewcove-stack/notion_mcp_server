"""
Configuration management
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    PORT: int = 3333
    SERVER_NAME: str = "Notion MCP Server"
    SERVER_DESCRIPTION: str = "MCP server for Notion integration"
    VERSION: str = "0.1.0"
    
    # Notion API
    NOTION_API_TOKEN: Optional[str] = None
    NOTION_API_VERSION: str = "2022-06-28"
    
    # Public URL (for Cloudflare tunnel)
    PUBLIC_BASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
