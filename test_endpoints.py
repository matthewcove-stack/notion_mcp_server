"""Quick endpoint test script"""
import httpx
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(url, method="GET", json_data=None):
    """Test an endpoint and print results"""
    full_url = f"{BASE_URL}{url}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    print('='*60)
    
    try:
        if method == "GET":
            response = httpx.get(full_url, timeout=10.0)
        elif method == "POST":
            response = httpx.post(full_url, json=json_data, timeout=10.0)
        
        print(f"Status: {response.status_code}")
        print(f"Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        return response
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Run tests
print("\n" + "="*60)
print("NOTION MCP SERVER - ENDPOINT TESTS")
print("="*60)

# Basic endpoints
test_endpoint("/health")
test_endpoint("/version")
test_endpoint("/notion/me")

# Database endpoints
test_endpoint("/databases")

# MCP endpoint
test_endpoint("/mcp")

print("\n" + "="*60)
print("Tests complete!")
print("="*60)

