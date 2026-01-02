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
    SERVER_DESCRIPTION: str = "REST-based MCP for Notion (Actions-ready)"
    VERSION: str = "0.1.0"
    
    # ChatGPT Actions Authentication
    ACTION_API_TOKEN: Optional[str] = None
    
    # Notion OAuth
    NOTION_OAUTH_CLIENT_ID: Optional[str] = None
    NOTION_OAUTH_CLIENT_SECRET: Optional[str] = None
    NOTION_OAUTH_REDIRECT_URI: Optional[str] = None
    
    # Token Encryption
    TOKEN_ENCRYPTION_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://notionmcp:notionmcp@postgres:5432/notionmcp"
    
    # Notion API
    NOTION_API_VERSION: str = "2022-06-28"
    
    # Public URL (for Cloudflare tunnel)
    PUBLIC_BASE_URL: Optional[str] = None
    
    # Rate Limiting & Retries
    NOTION_MAX_RETRIES: int = 3
    NOTION_RETRY_BACKOFF_FACTOR: float = 2.0
    
    # Idempotency
    IDEMPOTENCY_TTL_SECONDS: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
