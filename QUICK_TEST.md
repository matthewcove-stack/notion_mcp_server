# Quick Test Instructions

## Current Status

✅ **Code Structure**: Verified - All files compile without errors
✅ **Endpoints Registered**: 3 endpoints found:
   - `GET /health` (public)
   - `GET /openapi.json` (public)  
   - `GET /v1/meta` (requires bearer token)

## To Test (Once Docker is Running)

### Step 1: Start Docker Desktop

### Step 2: Start Services
```powershell
docker compose up -d --build
```

### Step 3: Wait for Health Check
```powershell
# Check service status
docker compose ps

# Watch logs
docker compose logs -f api
```

### Step 4: Test Endpoints

**Local Testing:**
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:3333/health" | Select-Object StatusCode, @{Name='Content';Expression={$_.Content}}

# OpenAPI spec
Invoke-WebRequest -Uri "http://localhost:3333/openapi.json" | Select-Object StatusCode

# Meta without auth (should fail)
Invoke-WebRequest -Uri "http://localhost:3333/v1/meta" -ErrorAction SilentlyContinue

# Meta with auth (if ACTION_API_TOKEN is set)
$headers = @{Authorization = "Bearer YOUR_TOKEN_HERE"}
Invoke-WebRequest -Uri "http://localhost:3333/v1/meta" -Headers $headers
```

**Cloudflare Tunnel Testing:**
```powershell
# Health check via tunnel
Invoke-WebRequest -Uri "https://notionmcp.nowhere-else.co.uk/health"

# OpenAPI via tunnel
Invoke-WebRequest -Uri "https://notionmcp.nowhere-else.co.uk/openapi.json"
```

### Step 5: Run Automated Tests
```powershell
# Install requests if needed
pip install requests

# Run test script
python test_endpoints.py
```

## Expected Results

| Endpoint | Auth Required | Expected Status | Expected Response |
|----------|--------------|-----------------|-------------------|
| `GET /health` | No | 200 | `{"ok": true}` |
| `GET /openapi.json` | No | 200 | OpenAPI 3.1 JSON |
| `GET /v1/meta` | No | 401 | Error envelope |
| `GET /v1/meta` | Yes | 200 | Metadata response |

## Troubleshooting

If services don't start:
1. Check Docker Desktop is running
2. Check `.env` file exists and has required variables
3. Check logs: `docker compose logs api`
4. Check database: `docker compose logs postgres`

If Cloudflare tunnel fails:
1. Check tunnel logs: `docker compose logs cloudflared`
2. Verify `cloudflared/notionmcp.json` exists
3. Verify tunnel is running: `docker compose ps cloudflared`

