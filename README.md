# REST-based MCP for Notion (Actions-ready)

REST API service for ChatGPT Actions to manage Notion workspaces.

## Setup

1. Copy `env.example` to `.env` and configure:
   ```bash
   cp env.example .env
   ```

2. Generate encryption key for token storage:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Configure required environment variables in `.env`:
   - `ACTION_API_TOKEN` - Bearer token for ChatGPT Actions authentication
   - `NOTION_OAUTH_CLIENT_ID` - Notion OAuth client ID
   - `NOTION_OAUTH_CLIENT_SECRET` - Notion OAuth client secret
   - `NOTION_OAUTH_REDIRECT_URI` - OAuth redirect URI
   - `TOKEN_ENCRYPTION_KEY` - Fernet encryption key (from step 2)
   - `DATABASE_URL` - PostgreSQL connection string (default works with docker-compose)

4. Start the services:
   ```bash
   docker compose up -d
   ```

This will start:
- PostgreSQL database
- API server (FastAPI)
- Cloudflare tunnel

## Cloudflare Tunnel

The Cloudflare tunnel is already configured and will expose the server at:
- `https://notionmcp.nowhere-else.co.uk`

Configuration files:
- `cloudflared/config.yml` - Tunnel configuration
- `cloudflared/notionmcp.json` - Tunnel credentials

## API Endpoints

### Public (no auth):
- `GET /health` - Health check
- `GET /openapi.json` - OpenAPI 3.1 specification

### Secured (bearer token required):
- `GET /v1/meta` - Server metadata and status

## Development

Run locally without Docker (requires Postgres running):
```bash
python -m uvicorn app.main:app --reload --port 3333
```
