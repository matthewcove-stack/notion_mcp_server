# ChatGPT Actions Setup Guide

## Overview

This guide explains how to configure your Notion MCP server with ChatGPT Actions (Custom GPT).

## Prerequisites

1. **Server Running**: Your server must be running and accessible via Cloudflare tunnel
2. **OAuth Setup**: Notion OAuth application configured
3. **Environment Variables**: All required env vars set in `.env`

## Step 1: Get Your Server URL

Your server is accessible at:
```
https://notionmcp.nowhere-else.co.uk
```

## Step 2: Get Your Action API Token

The `ACTION_API_TOKEN` from your `.env` file is used for authentication.

**Example:**
```
ACTION_API_TOKEN=your_secure_action_api_token_here
```

**Important:** Keep this token secret. It's used to authenticate all requests from ChatGPT.

## Step 3: Configure ChatGPT Actions

### 3.1 OpenAPI Schema URL

In ChatGPT Actions configuration, use:
```
https://notionmcp.nowhere-else.co.uk/openapi.json
```

### 3.2 Authentication

**Type:** Bearer Token  
**Token:** Your `ACTION_API_TOKEN` value

**Example:**
- Authentication Type: `Bearer`
- Token: `your_secure_action_api_token_here`

## Step 4: Connect Notion Workspace

### 4.1 Start OAuth Flow

Visit this URL in your browser (or have ChatGPT open it):
```
https://notionmcp.nowhere-else.co.uk/oauth/start?return_url=https://chat.openai.com
```

This will:
1. Redirect you to Notion authorization
2. Ask you to authorize the integration
3. Redirect back and create a connection
4. Return connection information

### 4.2 Get Connection ID

After OAuth completes, you'll receive a `connection_id` (UUID). Save this - you'll need it for all API calls.

**Example response:**
```json
{
  "ok": true,
  "result": {
    "connection_id": "123e4567-e89b-12d3-a456-426614174000",
    "workspace_id": "workspace-123",
    "workspace_name": "My Workspace"
  }
}
```

## Step 5: Available Actions

Once configured, ChatGPT will have access to these actions:

### Core Operations
- **Search Notion** - `POST /v1/notion/search`
- **Create Database** - `POST /v1/databases`
- **Get Database** - `GET /v1/databases/{database_id}`
- **Update Database** - `PATCH /v1/databases/{database_id}`
- **Query Database** - `POST /v1/databases/{database_id}/query`
- **Create Page** - `POST /v1/pages`
- **Get Page** - `GET /v1/pages/{page_id}`
- **Update Page** - `PATCH /v1/pages/{page_id}`
- **Archive Page** - `POST /v1/pages/{page_id}/archive`
- **Get Block Children** - `GET /v1/blocks/{block_id}/children`
- **Update Block** - `PATCH /v1/blocks/{block_id}`
- **Append Block Children** - `POST /v1/blocks/{block_id}/children`

### High-Level Operations
- **Upsert** - `POST /v1/upsert` (create or update page by unique property)
- **Link Pages** - `POST /v1/link` (link pages via relation)
- **Bulk Operations** - `POST /v1/bulk` (execute multiple operations)
- **Create Job** - `POST /v1/jobs` (long-running operations)
- **Get Job Status** - `GET /v1/jobs/{job_id}`

## Step 6: Using Actions in ChatGPT

### Example: Create a Database

ChatGPT will call:
```json
POST /v1/databases
{
  "connection_id": "your-connection-id",
  "parent_page_id": "page-id",
  "title": "My Database",
  "properties": {
    "Name": {"type": "title"},
    "Status": {"type": "select"}
  }
}
```

### Example: Upsert a Page

ChatGPT will call:
```json
POST /v1/upsert
{
  "connection_id": "your-connection-id",
  "database_id": "database-id",
  "unique": {
    "property": "Name",
    "value": "Project X"
  },
  "properties": {
    "Status": {
      "type": "select",
      "value": "In Progress"
    },
    "Due": {
      "type": "date",
      "value": "2026-01-10"
    }
  }
}
```

## Important Notes

### Connection ID Required

**All API calls require `connection_id` in the request body** (for POST/PATCH) or query parameter (for GET).

ChatGPT Actions doesn't reliably support custom headers, so `connection_id` must be included in:
- Request body for POST/PATCH/DELETE
- Query parameter for GET requests

### Idempotency

For write operations, you can include an `Idempotency-Key` header to prevent duplicate operations:
```
Idempotency-Key: unique-key-here
```

### Error Handling

All errors return standard response envelope:
```json
{
  "ok": false,
  "error": {
    "code": "error_code",
    "message": "Human-readable message",
    "details": {}
  }
}
```

## Troubleshooting

### "401 Unauthorized" or "403 Forbidden"
- Check that `ACTION_API_TOKEN` is correctly set in ChatGPT Actions
- Verify the token matches your `.env` file

### "Connection not found"
- Ensure OAuth flow completed successfully
- Verify `connection_id` is correct
- Check database for connection record

### "OAuth not configured"
- Verify `NOTION_OAUTH_CLIENT_ID` and `NOTION_OAUTH_CLIENT_SECRET` are set
- Check `NOTION_OAUTH_REDIRECT_URI` matches your server URL

### Server not accessible
- Verify Cloudflare tunnel is running: `docker compose ps cloudflared`
- Check tunnel logs: `docker compose logs cloudflared`
- Verify tunnel credentials in `cloudflared/notionmcp.json`

## Quick Reference

### Server URLs
- **Base URL:** `https://notionmcp.nowhere-else.co.uk`
- **OpenAPI:** `https://notionmcp.nowhere-else.co.uk/openapi.json`
- **Health:** `https://notionmcp.nowhere-else.co.uk/health`
- **OAuth Start:** `https://notionmcp.nowhere-else.co.uk/oauth/start`

### Required Environment Variables
```bash
ACTION_API_TOKEN=your_secure_token_here
NOTION_OAUTH_CLIENT_ID=your_client_id
NOTION_OAUTH_CLIENT_SECRET=your_client_secret
NOTION_OAUTH_REDIRECT_URI=https://notionmcp.nowhere-else.co.uk/oauth/callback
TOKEN_ENCRYPTION_KEY=your_fernet_key
DATABASE_URL=postgresql+psycopg2://notionmcp:notionmcp@postgres:5432/notionmcp
PUBLIC_BASE_URL=https://notionmcp.nowhere-else.co.uk
```

## Next Steps

1. Test the connection: Ask ChatGPT to check server status
2. Connect workspace: Use OAuth flow to connect your Notion workspace
3. Start using: Ask ChatGPT to create databases, pages, or perform operations

