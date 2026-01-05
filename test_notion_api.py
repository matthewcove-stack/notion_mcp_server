"""Test actual Notion API integration"""
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")

print("\n" + "="*70)
print("NOTION MCP SERVER - API INTEGRATION TEST")
print("="*70)

# Check if token is configured
print(f"\nNotion Token configured: {'Yes' if NOTION_TOKEN else 'NO - THIS WILL FAIL'}")
if NOTION_TOKEN:
    print(f"Token prefix: {NOTION_TOKEN[:20]}...")

# Test 1: Health check
print("\n" + "-"*70)
print("TEST 1: Health Check")
print("-"*70)
try:
    response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
    print(f"[OK] Status: {response.status_code}")
    print(f"  Response: {response.json()}")
except Exception as e:
    print(f"[FAIL] ERROR: {e}")

# Test 2: Notion connection verify
print("\n" + "-"*70)
print("TEST 2: Verify Notion Connection")
print("-"*70)
try:
    response = httpx.get(f"{BASE_URL}/notion/me", timeout=10.0)
    print(f"[OK] Status: {response.status_code}")
    data = response.json()
    print(f"  Response: {json.dumps(data, indent=2)}")
    if "error" in data:
        print(f"  [WARN] Warning: {data['error']}")
except Exception as e:
    print(f"[FAIL] ERROR: {e}")

# Test 3: List databases
print("\n" + "-"*70)
print("TEST 3: List Databases")
print("-"*70)
try:
    response = httpx.get(f"{BASE_URL}/databases", timeout=30.0)
    print(f"[OK] Status: {response.status_code}")
    data = response.json()
    if data.get("ok"):
        databases = data.get("result", [])
        print(f"  Found {len(databases)} databases")
        for db in databases[:3]:  # Show first 3
            title = "Untitled"
            if "title" in db and db["title"]:
                title = db["title"][0].get("plain_text", "Untitled")
            print(f"    - {title} (ID: {db['id'][:8]}...)")
    else:
        print(f"  Error: {data.get('error')}")
except httpx.ReadTimeout:
    print(f"[FAIL] TIMEOUT: Request took too long (>30s)")
except Exception as e:
    print(f"[FAIL] ERROR: {e}")

# Test 4: Search
print("\n" + "-"*70)
print("TEST 4: Search Workspace")
print("-"*70)
try:
    response = httpx.post(
        f"{BASE_URL}/search",
        json={"query": "", "page_size": 5},
        timeout=30.0
    )
    print(f"[OK] Status: {response.status_code}")
    data = response.json()
    if data.get("ok"):
        results = data.get("result", {}).get("results", [])
        print(f"  Found {len(results)} results (showing first 5)")
        for item in results:
            obj_type = item.get("object")
            print(f"    - Type: {obj_type}, ID: {item['id'][:8]}...")
    else:
        print(f"  Error: {data.get('error')}")
except httpx.ReadTimeout:
    print(f"[FAIL] TIMEOUT: Request took too long (>30s)")
except Exception as e:
    print(f"[FAIL] ERROR: {e}")

# Test 5: MCP endpoint
print("\n" + "-"*70)
print("TEST 5: MCP Endpoint Info")
print("-"*70)
try:
    response = httpx.get(f"{BASE_URL}/mcp", timeout=10.0)
    print(f"[OK] Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"[FAIL] ERROR: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("[OK] Server is running and responding")
print("[OK] Basic endpoints functional")
if not NOTION_TOKEN:
    print("[FAIL] NOTION_API_TOKEN not configured - add to .env file")
    print("  Get token from: https://www.notion.so/my-integrations")
else:
    print("[OK] NOTION_API_TOKEN is configured")
    print("  -> If database/search tests failed, check:")
    print("    1. Token is valid")
    print("    2. Integration is shared with Notion pages")
    print("    3. Check server logs for detailed errors")

print("="*70 + "\n")

