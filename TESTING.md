# Testing Guide

## Prerequisites

1. **Start Docker Desktop** - Ensure Docker Desktop is running
2. **Configure Environment** - Copy `env.example` to `.env` and set required variables:
   ```bash
   cp env.example .env
   # Edit .env and set at minimum:
   # - ACTION_API_TOKEN (for testing authenticated endpoints)
   # - DATABASE_URL (default works with docker-compose)
   ```

## Quick Test Commands

### 1. Start Services
```bash
docker compose up -d --build
```

Wait for services to be healthy (check with `docker compose ps`)

### 2. Test Local Endpoints

#### Health Check (Public)
```bash
curl http://localhost:3333/health
```
Expected: `{"ok": true}`

#### OpenAPI Spec (Public)
```bash
curl http://localhost:3333/openapi.json | jq .
```
Expected: Valid OpenAPI 3.1 JSON with paths for `/health`, `/openapi.json`, `/v1/meta`

#### Meta Endpoint Without Auth (Should Fail)
```bash
curl -v http://localhost:3333/v1/meta
```
Expected: `401 Unauthorized` with error response

#### Meta Endpoint With Auth
```bash
curl -H "Authorization: Bearer YOUR_ACTION_API_TOKEN" http://localhost:3333/v1/meta | jq .
```
Expected: `200 OK` with metadata response

### 3. Test Cloudflare Tunnel

Once services are running, test through the tunnel:

```bash
curl https://notionmcp.nowhere-else.co.uk/health
curl https://notionmcp.nowhere-else.co.uk/openapi.json | jq .
curl -v https://notionmcp.nowhere-else.co.uk/v1/meta
curl -H "Authorization: Bearer YOUR_ACTION_API_TOKEN" https://notionmcp.nowhere-else.co.uk/v1/meta | jq .
```

### 4. Run Automated Test Script

```bash
# Install requests if needed
pip install requests

# Run test script
python test_endpoints.py
```

## Expected Results

### ✅ Success Indicators

1. **Health Endpoint**
   - Status: `200 OK`
   - Response: `{"ok": true}`

2. **OpenAPI Endpoint**
   - Status: `200 OK`
   - Response: Valid OpenAPI 3.1 JSON
   - Contains: `openapi`, `info`, `paths` sections
   - Paths include: `/health`, `/openapi.json`, `/v1/meta`

3. **Meta Endpoint (Unauthenticated)**
   - Status: `401 Unauthorized`
   - Response: Standard error envelope with `ok: false`

4. **Meta Endpoint (Authenticated)**
   - Status: `200 OK`
   - Response: Standard response envelope with `ok: true` and metadata

### ❌ Common Issues

1. **Connection Refused (Local)**
   - Docker services not running
   - Port 3333 already in use
   - Solution: `docker compose up -d`

2. **503 Service Unavailable**
   - Database not initialized
   - Check logs: `docker compose logs api`

3. **401 Unauthorized (Expected for /v1/meta without token)**
   - This is correct behavior
   - Use `Authorization: Bearer <token>` header

4. **Cloudflare Tunnel Error 1033**
   - Tunnel not running
   - Check: `docker compose logs cloudflared`
   - Verify tunnel credentials in `cloudflared/notionmcp.json`

## Check Logs

```bash
# API logs
docker compose logs -f api

# Database logs
docker compose logs -f postgres

# Cloudflare tunnel logs
docker compose logs -f cloudflared
```

## Database Verification

```bash
# Connect to database
docker compose exec postgres psql -U notionmcp -d notionmcp

# Check tables
\dt

# Should see:
# - connections
# - audit_log
# - idempotency_keys
```

