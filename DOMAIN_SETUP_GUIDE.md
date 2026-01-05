# Domain Setup Guide: nowhere-else.co.uk

This guide explains how to configure the Cloudflare tunnel to use your custom domain `nowhere-else.co.uk`.

## Current Configuration

- **Domain:** `nowhere-else.co.uk`
- **Tunnel ID:** `da1d47b4-6623-4552-b6f8-0a40bbab2bb8`
- **Tunnel Name:** `notionmcp`
- **Service:** `http://mcp:8000` (MCP server)

---

## Step 1: Configure DNS Records

In your Cloudflare DNS settings for `nowhere-else.co.uk`:

### Add CNAME Records

1. Go to **Cloudflare Dashboard** → **DNS** → **Records**
2. Add the following CNAME records:

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | @ | `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com` | ✅ Proxied |
| CNAME | www | `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com` | ✅ Proxied |

**Note:** Make sure "Proxy" is enabled (orange cloud icon) for both records.

---

## Step 2: Configure Tunnel Public Hostname

1. Go to **Cloudflare Dashboard** → **Zero Trust** → **Networks** → **Tunnels**
2. Find and click on tunnel **`notionmcp`** (ID: `da1d47b4-6623-4552-b6f8-0a40bbab2bb8`)
3. Click on the **"Public Hostname"** tab
4. Click **"Add a public hostname"**

### Configure Hostname 1: Root Domain
- **Subdomain:** (leave empty for root domain)
- **Domain:** `nowhere-else.co.uk`
- **Service:** `http://localhost:8000`
- Click **"Save hostname"**

### Configure Hostname 2: WWW Subdomain (Optional)
- **Subdomain:** `www`
- **Domain:** `nowhere-else.co.uk`
- **Service:** `http://localhost:8000`
- Click **"Save hostname"**

---

## Step 3: Verify Configuration

After completing steps 1 and 2, wait a few minutes for DNS propagation, then test:

```powershell
# Test root domain
Invoke-WebRequest -Uri "https://nowhere-else.co.uk/health" -UseBasicParsing

# Test www subdomain
Invoke-WebRequest -Uri "https://www.nowhere-else.co.uk/health" -UseBasicParsing
```

Expected response:
```json
{"ok":true,"status":"healthy"}
```

---

## Step 4: Update ChatGPT MCP Connector

Once the domain is working, update your ChatGPT MCP connector:

**MCP Server URL:** `https://nowhere-else.co.uk/mcp/sse`

(Note: Adjust the path based on your actual MCP endpoint implementation)

---

## Troubleshooting

### Domain not resolving
- Wait 5-10 minutes for DNS propagation
- Verify CNAME records are correct
- Ensure "Proxy" is enabled (orange cloud)

### 502 Bad Gateway
- Check tunnel is running: `docker-compose ps cloudflared`
- Verify MCP service is running: `docker-compose ps mcp`
- Check tunnel logs: `docker-compose logs cloudflared`

### Tunnel not connecting
- Verify tunnel credentials in `cloudflared/notionmcp.json`
- Check tunnel configuration in `cloudflared/config.yml`
- Restart tunnel: `docker-compose restart cloudflared`

### Hostname not found in tunnel
- Verify public hostname is configured in Cloudflare dashboard
- Check hostname matches exactly (case-sensitive)
- Ensure service URL is correct: `http://localhost:8000`

---

## Current Tunnel Status

Check tunnel status:
```bash
docker-compose logs cloudflared | Select-String "Registered tunnel"
```

You should see:
```
INF Registered tunnel connection connIndex=0 ...
```

---

## Endpoints After Setup

Once configured, your endpoints will be:

- Health: `https://nowhere-else.co.uk/health`
- API Docs: `https://nowhere-else.co.uk/docs`
- Version: `https://nowhere-else.co.uk/version`
- Notion: `https://nowhere-else.co.uk/notion/me`
- Databases: `https://nowhere-else.co.uk/databases`
- Second Brain: `https://nowhere-else.co.uk/second-brain/status`

---

## Notes

- DNS changes can take up to 10 minutes to propagate
- Tunnel must be running for the domain to work
- Both root domain and www subdomain are configured
- SSL/TLS is automatically handled by Cloudflare

