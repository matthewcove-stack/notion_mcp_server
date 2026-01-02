"""
Smoke tests - basic functionality checks
"""
import requests
import os
import sys
from typing import Dict, Any


def test_health(base_url: str) -> bool:
    """Test health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_openapi(base_url: str) -> bool:
    """Test OpenAPI endpoint"""
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        print(f"✅ OpenAPI check passed ({len(data['paths'])} endpoints)")
        return True
    except Exception as e:
        print(f"❌ OpenAPI check failed: {e}")
        return False


def test_mcp_tools(base_url: str) -> bool:
    """Test MCP tools endpoint"""
    try:
        response = requests.get(f"{base_url}/mcp/tools", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) >= 6  # Should have at least 6 tools
        print(f"✅ MCP tools check passed ({len(data['tools'])} tools)")
        return True
    except Exception as e:
        print(f"❌ MCP tools check failed: {e}")
        return False


def test_oauth_start(base_url: str) -> bool:
    """Test OAuth start endpoint"""
    try:
        response = requests.get(f"{base_url}/oauth/start", allow_redirects=False, timeout=5)
        # Should redirect (302) or return 503 if not configured
        assert response.status_code in [302, 503]
        print("✅ OAuth start check passed")
        return True
    except Exception as e:
        print(f"❌ OAuth start check failed: {e}")
        return False


def test_meta_requires_auth(base_url: str) -> bool:
    """Test that meta endpoint requires auth"""
    try:
        response = requests.get(f"{base_url}/v1/meta", timeout=5)
        assert response.status_code == 403  # Should require bearer token
        print("✅ Meta auth check passed")
        return True
    except Exception as e:
        print(f"❌ Meta auth check failed: {e}")
        return False


def run_smoke_tests(base_url: str = "http://localhost:3333"):
    """Run all smoke tests"""
    print("=" * 60)
    print("Running Smoke Tests")
    print("=" * 60)
    print(f"Base URL: {base_url}\n")
    
    tests = [
        ("Health", test_health),
        ("OpenAPI", test_openapi),
        ("MCP Tools", test_mcp_tools),
        ("OAuth Start", test_oauth_start),
        ("Meta Auth", test_meta_requires_auth),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        result = test_func(base_url)
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3333"
    success = run_smoke_tests(base_url)
    sys.exit(0 if success else 1)

