"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Server
    base_url: str = "https://notionmcp.nowhere-else.co.uk"
    
    # Notion API
    notion_api_token: Optional[str] = None
    notion_api_version: str = "2022-06-28"
    
    # OAuth
    notion_oauth_client_id: Optional[str] = None
    notion_oauth_client_secret: Optional[str] = None
    notion_oauth_redirect_uri: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    
    # Security
    token_encryption_key: Optional[str] = None
    mcp_api_key: Optional[str] = None
    action_api_token: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./notion_mcp.db"
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379/0"
    
    # Rate limiting
    notion_api_max_retries: int = 3
    notion_api_retry_delay: float = 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()

