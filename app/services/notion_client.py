"""
Notion API client with retry/backoff logic
"""
import time
import httpx
from typing import Dict, Any, Optional
import structlog

from app.config import settings

logger = structlog.get_logger()

NOTION_API_BASE = "https://api.notion.com"


class NotionAPIError(Exception):
    """Notion API error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class NotionClient:
    """Notion API client with automatic retry and backoff"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client = httpx.Client(
            base_url=NOTION_API_BASE,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": settings.NOTION_API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    def _should_retry(self, status_code: int) -> bool:
        """Determine if a request should be retried"""
        # Retry on 429 (rate limit) and 5xx (server errors)
        return status_code == 429 or (500 <= status_code < 600)
    
    def _make_request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make a request to Notion API with retry logic
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., /v1/databases/{id})
            json: Request body (for POST/PATCH)
            params: Query parameters
            retry_count: Current retry attempt (internal)
        
        Returns:
            Response JSON as dict
        
        Raises:
            NotionAPIError: On API errors that cannot be retried
        """
        try:
            response = self.client.request(
                method=method,
                url=path,
                json=json,
                params=params,
            )
            
            # Success
            if 200 <= response.status_code < 300:
                return response.json()
            
            # Check if we should retry
            if self._should_retry(response.status_code) and retry_count < settings.NOTION_MAX_RETRIES:
                # Calculate backoff delay
                delay = (settings.NOTION_RETRY_BACKOFF_FACTOR ** retry_count)
                
                # For 429, check Retry-After header if available
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            pass
                
                logger.warning(
                    "notion_api_retry",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    retry_count=retry_count,
                    delay=delay,
                )
                
                time.sleep(delay)
                return self._make_request(method, path, json, params, retry_count + 1)
            
            # Non-retryable error or max retries reached
            error_data = None
            try:
                error_data = response.json()
            except Exception:
                pass
            
            raise NotionAPIError(
                message=f"Notion API error: {response.status_code}",
                status_code=response.status_code,
                response=error_data,
            )
        
        except httpx.HTTPError as e:
            logger.error("notion_api_http_error", method=method, path=path, error=str(e))
            raise NotionAPIError(f"HTTP error: {str(e)}")
        except NotionAPIError:
            raise
        except Exception as e:
            logger.error("notion_api_unexpected_error", method=method, path=path, error=str(e), exc_info=True)
            raise NotionAPIError(f"Unexpected error: {str(e)}")
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request"""
        return self._make_request("GET", path, params=params)
    
    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request"""
        return self._make_request("POST", path, json=json)
    
    def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PATCH request"""
        return self._make_request("PATCH", path, json=json)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """DELETE request"""
        return self._make_request("DELETE", path)
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

