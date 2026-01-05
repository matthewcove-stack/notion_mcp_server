"""Test that all modules can be imported"""
import pytest


def test_import_main():
    """Test main app imports"""
    from app import main
    assert hasattr(main, "app")


def test_import_config():
    """Test config imports"""
    from app import config
    assert hasattr(config, "settings")


def test_import_core():
    """Test core engine imports"""
    from app.core import engine
    assert hasattr(engine, "NotionEngine")


def test_import_services():
    """Test services import"""
    from app.services import notion_client
    from app.services import property_normalizer
    from app.services import token_encryption
    assert notion_client is not None
    assert property_normalizer is not None
    assert token_encryption is not None


def test_import_models():
    """Test models import"""
    from app.models import schemas
    assert hasattr(schemas, "StandardResponse")


def test_import_routers():
    """Test routers import"""
    from app.routers import databases
    from app.routers import pages
    from app.routers import operations
    from app.routers import mcp
    assert databases.router is not None
    assert pages.router is not None
    assert operations.router is not None
    assert mcp.router is not None

