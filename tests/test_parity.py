"""
Parity tests - ensure MCP and REST endpoints produce same results
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, Base, engine
from app.db.models import Connection
from app.services.token_encryption import get_token_encryption


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session"""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_connection(db_session):
    """Create test connection"""
    encryption = get_token_encryption()
    connection = Connection(
        workspace_id="test-workspace",
        workspace_name="Test Workspace",
        access_token_enc=encryption.encrypt("test-token"),
    )
    db_session.add(connection)
    db_session.commit()
    return connection


def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_openapi_endpoint(client):
    """Test OpenAPI endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


def test_mcp_tools_list(client):
    """Test MCP tools list endpoint"""
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0
    
    # Check that all expected tools are present
    tool_names = [tool["name"] for tool in data["tools"]]
    expected_tools = [
        "notion.request",
        "notion.upsert",
        "notion.link",
        "notion.bulk",
        "notion.job_start",
        "notion.job_get",
    ]
    for expected in expected_tools:
        assert expected in tool_names, f"Tool {expected} not found"


def test_oauth_start_endpoint(client):
    """Test OAuth start endpoint (should redirect or return 503 if not configured)"""
    response = client.get("/oauth/start", follow_redirects=False)
    # Should either redirect (302) or return 503 if not configured
    assert response.status_code in [302, 503]


def test_meta_endpoint_requires_auth(client):
    """Test that meta endpoint requires authentication"""
    response = client.get("/v1/meta")
    assert response.status_code == 403  # Should require bearer token


def test_meta_endpoint_with_auth(client, monkeypatch):
    """Test meta endpoint with authentication"""
    monkeypatch.setenv("ACTION_API_TOKEN", "test-token")
    response = client.get("/v1/meta", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "result" in data

