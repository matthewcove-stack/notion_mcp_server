"""Basic health check tests"""
import pytest


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["status"] == "healthy"


def test_version_endpoint(client):
    """Test version endpoint"""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "service" in data
    assert data["service"] == "notion-mcp-server"


def test_mcp_info_endpoint(client):
    """Test MCP info endpoint"""
    response = client.get("/mcp")
    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "mcp"
    assert data["transport"] == "sse"
    assert "endpoint" in data

