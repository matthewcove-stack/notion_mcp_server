"""
Tests for Core Engine functionality
"""
import pytest
from unittest.mock import Mock, patch
from app.core.engine import CoreEngine
from app.services.notion_client import NotionAPIError


def test_core_engine_initialization():
    """Test Core Engine initialization"""
    db = Mock()
    connection_id = "test-connection-id"
    
    with patch("app.core.engine.get_decrypted_access_token", return_value="test-token"):
        with patch("app.core.engine.NotionClient") as mock_client:
            engine = CoreEngine(db, connection_id)
            assert engine.db == db
            assert engine.connection_id == connection_id
            mock_client.assert_called_once_with("test-token")


def test_core_engine_context_manager():
    """Test Core Engine as context manager"""
    db = Mock()
    connection_id = "test-connection-id"
    
    with patch("app.core.engine.get_decrypted_access_token", return_value="test-token"):
        with patch("app.core.engine.NotionClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            with CoreEngine(db, connection_id) as engine:
                assert engine is not None
            
            mock_client.close.assert_called_once()


def test_core_engine_search():
    """Test search operation"""
    db = Mock()
    connection_id = "test-connection-id"
    
    with patch("app.core.engine.get_decrypted_access_token", return_value="test-token"):
        with patch("app.core.engine.NotionClient") as mock_client_class:
            mock_client = Mock()
            mock_client.post.return_value = {"results": []}
            mock_client_class.return_value = mock_client
            
            with CoreEngine(db, connection_id) as engine:
                result = engine.search(query="test", filter_obj={"property": "object", "value": "page"})
                assert "results" in result
                mock_client.post.assert_called_once()

