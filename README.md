# Notion MCP Server

MCP (Model Context Protocol) server for Notion integration.

## Setup

1. Copy `env.example` to `.env` and configure:
   ```bash
   cp env.example .env
   ```

2. Set your Notion API token in `.env`:
   ```
   NOTION_API_TOKEN=your_token_here
   ```

3. Start the server:
   ```bash
   docker compose up -d
   ```

## Cloudflare Tunnel

The Cloudflare tunnel is already configured and will expose the server at:
- `https://notionmcp.nowhere-else.co.uk`

Configuration files:
- `cloudflared/config.yml` - Tunnel configuration
- `cloudflared/notionmcp.json` - Tunnel credentials

## Development

Run locally without Docker:
```bash
python -m uvicorn app.main:app --reload --port 3333
```
