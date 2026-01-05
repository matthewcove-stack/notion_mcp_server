"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
import os


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    os.environ["NOTION_API_TOKEN"] = "test_token_for_testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["ENVIRONMENT"] = "testing"
    yield


@pytest.fixture
def client(test_env):
    """Create test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_notion_client(mocker):
    """Mock Notion API client"""
    mock = mocker.patch("app.services.notion_client.NotionClientWrapper")
    return mock

