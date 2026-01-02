#!/usr/bin/env python3
"""
Test script for API endpoints
Tests both local and Cloudflare tunnel endpoints
"""
import requests
import json
import sys
from typing import Dict, Any


def test_endpoint(url: str, method: str = "GET", headers: Dict[str, str] = None, data: Dict[str, Any] = None) -> tuple[bool, str]:
    """Test an endpoint and return (success, message)"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        success = response.status_code < 400
        message = f"{method} {url} -> {response.status_code}\n{json.dumps(response.json(), indent=2) if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]}"
        return success, message
    except requests.exceptions.ConnectionError:
        return False, f"Connection error: Could not connect to {url}"
    except requests.exceptions.Timeout:
        return False, f"Timeout: {url} did not respond"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Run tests"""
    print("=" * 60)
    print("Testing REST-based MCP for Notion API")
    print("=" * 60)
    
    base_urls = [
        ("Local", "http://localhost:3333"),
        ("Cloudflare Tunnel", "https://notionmcp.nowhere-else.co.uk")
    ]
    
    # Get bearer token from environment or use placeholder
    import os
    bearer_token = os.getenv("ACTION_API_TOKEN", "test-token")
    
    all_passed = True
    
    for name, base_url in base_urls:
        print(f"\n{'='*60}")
        print(f"Testing {name}: {base_url}")
        print(f"{'='*60}\n")
        
        # Test 1: Health endpoint (public)
        print("1. Testing GET /health (public)")
        success, message = test_endpoint(f"{base_url}/health")
        print(message)
        if not success:
            print(f"❌ FAILED")
            all_passed = False
        else:
            print(f"✅ PASSED")
        
        # Test 2: OpenAPI endpoint (public)
        print("\n2. Testing GET /openapi.json (public)")
        success, message = test_endpoint(f"{base_url}/openapi.json")
        if success:
            # Check if it's valid JSON
            try:
                data = json.loads(message.split('\n', 1)[1])
                if "openapi" in data:
                    print(f"✅ PASSED - Valid OpenAPI spec")
                else:
                    print(f"⚠️  WARNING - Response is JSON but not OpenAPI format")
                    all_passed = False
            except:
                print(f"⚠️  WARNING - Response is not valid JSON")
                all_passed = False
        else:
            print(f"❌ FAILED")
            all_passed = False
        
        # Test 3: /v1/meta without auth (should fail)
        print("\n3. Testing GET /v1/meta without auth (should fail)")
        success, message = test_endpoint(f"{base_url}/v1/meta")
        if not success:
            print(f"✅ PASSED - Correctly rejected (401)")
        else:
            print(f"❌ FAILED - Should require authentication")
            all_passed = False
        
        # Test 4: /v1/meta with auth (if token is set)
        if bearer_token != "test-token":
            print("\n4. Testing GET /v1/meta with bearer token")
            headers = {"Authorization": f"Bearer {bearer_token}"}
            success, message = test_endpoint(f"{base_url}/v1/meta", headers=headers)
            print(message)
            if success:
                print(f"✅ PASSED")
            else:
                print(f"❌ FAILED")
                all_passed = False
        else:
            print("\n4. Skipping authenticated test (ACTION_API_TOKEN not set)")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

