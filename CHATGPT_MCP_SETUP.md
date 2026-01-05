# ChatGPT MCP Server Configuration Guide

This guide provides **exact steps** to configure ChatGPT to use this Notion MCP server.

## Prerequisites

- Docker Desktop installed and running (or Python 3.12+ for local setup)
- A Notion API token from https://www.notion.so/my-integrations
- Cloudflare account (for public HTTPS access via tunnel)
- ChatGPT account with Developer Mode access

---

## Step 1: Configure Environment Variables

1. **Create a `.env` file** in the project root (copy from `env.example` if needed):
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** and add the following variables:
   ```env
   NOTION_API_TOKEN=your_notion_integration_token_here
   MCP_API_KEY=your_secure_random_api_key_here
   ```

   **To get your Notion token:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "ChatGPT MCP Server")
   - Copy the "Internal Integration Token"
   - Paste it as `NOTION_API_TOKEN`

   **To generate MCP_API_KEY:**
   - Use a secure random string generator
   - Or run: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Save this key securely - you'll need it for ChatGPT configuration

---

## Step 2: Start the MCP Server

### Option A: Using Docker (Recommended)

1. **Start Docker Desktop** (if not already running)

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```

3. **Verify the server is running:**
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

### Option B: Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python run_local.py
   ```

---

## Step 3: Set Up Cloudflare Tunnel (For Public HTTPS Access)

ChatGPT requires HTTPS access to your MCP server. Use Cloudflare Tunnel:

1. **Verify Cloudflare Tunnel configuration:**
   - Check that `cloudflared/notionmcp.json` contains your tunnel credentials
   - If not set up, create a tunnel:
     ```bash
     cloudflared tunnel create notionmcp
     ```

2. **Configure tunnel routing:**
   - The tunnel is already configured in `cloudflared/config.yml`
   - Domain: `notionmcp.nowhere-else.co.uk`
   - Service: `http://mcp:8000`

3. **Verify tunnel is running:**
   - Check tunnel status: `docker-compose ps cloudflared`
   - View tunnel logs: `docker-compose logs cloudflared`
   - Test domain: `https://notionmcp.nowhere-else.co.uk/health`

4. **Domain Configuration:**
   - Domain is already configured: `notionmcp.nowhere-else.co.uk`
   - DNS CNAME record should point to: `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`
   - See `CLOUDFLARE_SETUP_INSTRUCTIONS.md` for detailed setup steps

---

## Step 4: Determine Your MCP Endpoint URL

Based on the spec, the MCP server uses **SSE (Server-Sent Events)** transport. The endpoint should be:

**MCP SSE Endpoint:** `https://notionmcp.nowhere-else.co.uk/mcp/sse`

**Domain:** `notionmcp.nowhere-else.co.uk` (configured and working)

**Note:** Check your FastAPI application code to confirm the exact MCP endpoint path. Common paths:
- `/mcp/sse`
- `/mcp`
- `/sse`
- `/v1/mcp/sse`

To verify, check:
- Your FastAPI router configuration
- Or visit: `https://notionmcp.nowhere-else.co.uk/docs` to see available endpoints

---

## Step 5: Configure ChatGPT Developer Mode

1. **Enable Developer Mode in ChatGPT:**
   - Open ChatGPT (web or app)
   - Go to **Settings** (gear icon)
   - Navigate to **Apps & Connectors** or **Connectors**
   - Under **Advanced Settings**, toggle on **Developer Mode**

2. **Create a New MCP Connector:**
   - In the **Apps & Connectors** section, click **Create** or **Add Connector**
   - Fill in the connector details:

   **Name:** `Notion MCP Server` (or your preferred name)
   
   **Description:** `MCP server for managing Notion Second Brain workspace`
   
   **MCP Server URL:** 
   ```
   https://notionmcp.nowhere-else.co.uk/mcp/sse
   ```
   (Using domain: notionmcp.nowhere-else.co.uk)
   
   **Authentication Method:** Select **OAuth**
   
   **OAuth Configuration:**
   - **Authorization URL:** `https://notionmcp.nowhere-else.co.uk/oauth/authorize`
   - **Client Secret:** Enter the `OAUTH_CLIENT_SECRET` value from your `.env` file
   
   **Note:** 
   - ChatGPT will automatically discover the Token URL from the OAuth metadata endpoint
   - On first use, you'll be redirected to authorize access
   - The OAuth flow is handled automatically by ChatGPT

3. **Save the Connector:**
   - Click **Create** or **Save**
   - ChatGPT will attempt to connect to your MCP server
   - Wait for the connection to be established

---

## Step 6: Verify Connection

1. **Check Connection Status:**
   - In ChatGPT, go back to **Apps & Connectors**
   - Find your "Notion MCP Server" connector
   - Verify it shows as **Connected** or **Active**

2. **Test the Connection:**
   - Start a new chat in ChatGPT
   - The MCP tools should be available automatically
   - Try asking: "What Notion tools are available?"
   - Or: "Check the status of my Notion Second Brain"

3. **Verify Server Logs:**
   - Check your Docker logs: `docker-compose logs -f mcp`
   - Or check local server console
   - You should see MCP tool calls being received

---

## Step 7: Use MCP Tools in ChatGPT

Once connected, ChatGPT can use MCP tools like:

- `notion.request` - Generic Notion API proxy
- `notion.upsert` - Create or update pages/databases
- `notion.link` - Link pages together
- `notion.bulk` - Execute multiple operations
- `notion.job_start` / `notion.job_get` - Long-running jobs

**Example prompts:**
- "Create a task in Notion called 'Review project proposal'"
- "Show me all databases in my Notion workspace"
- "Link the page 'Project X' to the 'Active Projects' database"

---

## Troubleshooting

### Connection Issues

**Problem:** ChatGPT cannot connect to the MCP server
- **Solution:** 
  - Verify the domain is correct and accessible: `https://notionmcp.nowhere-else.co.uk/health`
  - Check Cloudflare tunnel logs: `docker-compose logs cloudflared`
  - Ensure the server is running: `docker-compose ps`
  - Test the endpoint manually: `curl https://notionmcp.nowhere-else.co.uk/health`

### Authentication Errors

**Problem:** "Authentication failed" or "401 Unauthorized"
- **Solution:**
  - Verify `MCP_API_KEY` matches in both `.env` and ChatGPT connector settings
  - Check server logs for authentication errors
  - Ensure Bearer token format is correct in ChatGPT config

### MCP Tools Not Available

**Problem:** ChatGPT doesn't show MCP tools
- **Solution:**
  - Verify Developer Mode is enabled
  - Check connector status is "Connected"
  - Restart ChatGPT session
  - Check server logs for tool registration errors

### Notion API Errors

**Problem:** "Notion API error" or "Invalid token"
- **Solution:**
  - Verify `NOTION_API_TOKEN` is correct in `.env`
  - Ensure the Notion integration has proper permissions
  - Check Notion integration is connected to your workspace
  - Test token: `curl -H "Authorization: Bearer YOUR_TOKEN" https://api.notion.com/v1/users/me`

---

## Security Notes

1. **Keep your `.env` file secure** - Never commit it to version control
2. **Use strong `MCP_API_KEY`** - Generate a secure random string
3. **HTTPS Required** - ChatGPT requires HTTPS, which is why Cloudflare Tunnel is needed
4. **Token Encryption** - The server encrypts Notion tokens at rest (if implemented per spec)

---

## Additional Resources

- Notion API Documentation: https://developers.notion.com
- MCP Protocol Specification: https://modelcontextprotocol.io
- Cloudflare Tunnel Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

## Quick Reference

**Server Health Check:**
```bash
curl http://localhost:8000/health
```

**Test Domain:**
```bash
curl https://notionmcp.nowhere-else.co.uk/health
```

**Check Server Status:**
```bash
docker-compose ps
docker-compose logs mcp
```

**Test Notion Connection:**
```bash
curl http://localhost:8000/notion/me
```

**Test Domain Endpoints:**
```bash
# Health check
curl https://notionmcp.nowhere-else.co.uk/health

# API documentation
curl https://notionmcp.nowhere-else.co.uk/docs

# Version
curl https://notionmcp.nowhere-else.co.uk/version
```

---

## Domain Information

**Production Domain:** `notionmcp.nowhere-else.co.uk`

**Available Endpoints:**
- Health: `https://notionmcp.nowhere-else.co.uk/health`
- API Docs: `https://notionmcp.nowhere-else.co.uk/docs`
- OpenAPI: `https://notionmcp.nowhere-else.co.uk/openapi.json`
- Version: `https://notionmcp.nowhere-else.co.uk/version`
- Notion: `https://notionmcp.nowhere-else.co.uk/notion/me`
- Databases: `https://notionmcp.nowhere-else.co.uk/databases`
- Second Brain: `https://notionmcp.nowhere-else.co.uk/second-brain/status`

**Status:** ✅ Domain is configured and working

---

**Last Updated:** Domain configured as `notionmcp.nowhere-else.co.uk`

