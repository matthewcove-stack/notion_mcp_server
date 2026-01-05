# Cloudflare Setup Instructions for notionmcp.nowhere-else.co.uk

**Domain:** `notionmcp.nowhere-else.co.uk`  
**Tunnel ID:** `da1d47b4-6623-4552-b6f8-0a40bbab2bb8`  
**Tunnel Name:** `notionmcp`

---

## ✅ Domain Name Confirmed

**`notionmcp.nowhere-else.co.uk`** is an excellent choice:
- ✅ Clear purpose (Notion MCP server)
- ✅ Well-organized subdomain structure
- ✅ Easy to remember and type
- ✅ Keeps main domain free for other services
- ✅ Follows standard naming conventions

---

## Step 1: Configure DNS Record

### In Cloudflare Dashboard:

1. **Go to:** Cloudflare Dashboard → **DNS** → **Records**
2. **Select domain:** `nowhere-else.co.uk`
3. **Click:** "Add record"
4. **Configure:**
   - **Type:** `CNAME`
   - **Name:** `notionmcp`
   - **Target:** `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`
   - **Proxy status:** ✅ **Proxied** (orange cloud icon)
   - **TTL:** Auto
5. **Click:** "Save"

**Result:** This creates `notionmcp.nowhere-else.co.uk` → Tunnel

---

## Step 2: Configure Tunnel Public Hostname

### Option A: Try DNS-Only First (Simplest)

**Good news:** We've already configured the hostname in `cloudflared/config.yml`. 

**Try this first:**
1. Complete Step 1 (add DNS CNAME record)
2. Wait 10 minutes
3. Test: `https://notionmcp.nowhere-else.co.uk/health`

**If it works, you're done!** If not, proceed to Option B.

### Option B: Configure via Dashboard

**Note:** The tab name may vary. Look for:
- "Public Hostname" tab
- "Routes" tab
- "Ingress" tab  
- "Hostnames" tab

1. **Go to:** Cloudflare Dashboard → **Zero Trust** → **Networks** → **Tunnels**
2. **Find tunnel:** `notionmcp` (ID: `da1d47b4-6623-4552-b6f8-0a40bbab2bb8`)
3. **Click** on the tunnel name to open details
4. **Look for** any tab related to hostnames/routes
5. **Add hostname:**
   - **Hostname:** `notionmcp.nowhere-else.co.uk`
   - **Service:** `http://localhost:8000`

**If you can't find the tab:** See `CLOUDFLARE_HOSTNAME_ALTERNATIVE_METHODS.md` for API/CLI methods.

---

## Step 3: Verify Configuration

### Check DNS Record:
```powershell
# Test DNS resolution (may take 5-10 minutes to propagate)
nslookup notionmcp.nowhere-else.co.uk
```

Expected: Should resolve to Cloudflare IP addresses

### Check Tunnel Status:
```bash
docker-compose logs cloudflared | Select-String "Registered tunnel"
```

Expected: Should show "Registered tunnel connection"

### Test Endpoint:
```powershell
# Wait 5-10 minutes after DNS configuration, then test:
Invoke-WebRequest -Uri "https://notionmcp.nowhere-else.co.uk/health" -UseBasicParsing
```

Expected response:
```json
{"ok":true,"status":"healthy"}
```

---

## Step 4: Update ChatGPT MCP Connector

Once the domain is working, configure ChatGPT:

**MCP Server URL:** `https://notionmcp.nowhere-else.co.uk/mcp/sse`

(Adjust the path `/mcp/sse` based on your actual MCP endpoint implementation)

---

## Current Status

### ✅ Completed:
- [x] Tunnel configuration file updated (`cloudflared/config.yml`)
- [x] Tunnel service restarted
- [x] Tunnel is running and connected

### ⏳ Pending (You need to do these):
- [ ] Add DNS CNAME record in Cloudflare Dashboard
- [ ] Add public hostname in Tunnel settings
- [ ] Wait for DNS propagation (5-10 minutes)
- [ ] Test the domain

---

## Troubleshooting

### DNS not resolving:
- **Wait:** DNS changes can take 5-10 minutes
- **Check:** CNAME record is correct and proxied (orange cloud)
- **Verify:** Target is exactly `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`

### 502 Bad Gateway:
- **Check tunnel:** `docker-compose ps cloudflared` (should be "Up")
- **Check MCP service:** `docker-compose ps mcp` (should be "Up")
- **Check logs:** `docker-compose logs cloudflared`
- **Verify:** Service URL in tunnel hostname is `http://localhost:8000`

### Tunnel not connecting:
- **Check credentials:** Verify `cloudflared/notionmcp.json` exists and is valid
- **Check config:** Verify `cloudflared/config.yml` syntax
- **Restart:** `docker-compose restart cloudflared`

### Hostname not found:
- **Verify:** Public hostname is configured in Cloudflare dashboard
- **Check:** Subdomain matches exactly: `notionmcp` (case-sensitive)
- **Ensure:** Service URL is `http://localhost:8000`

---

## Quick Reference

**Domain:** `notionmcp.nowhere-else.co.uk`  
**Tunnel ID:** `da1d47b4-6623-4552-b6f8-0a40bbab2bb8`  
**CNAME Target:** `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`  
**Service:** `http://localhost:8000`

**Endpoints after setup:**
- Health: `https://notionmcp.nowhere-else.co.uk/health`
- API Docs: `https://notionmcp.nowhere-else.co.uk/docs`
- Version: `https://notionmcp.nowhere-else.co.uk/version`
- Notion: `https://notionmcp.nowhere-else.co.uk/notion/me`
- Databases: `https://notionmcp.nowhere-else.co.uk/databases`
- Second Brain: `https://notionmcp.nowhere-else.co.uk/second-brain/status`

---

## Summary

**Configuration Status:** ⚠️ **PARTIALLY COMPLETE**

✅ **Done:**
- Tunnel configuration file updated
- Tunnel service running

⏳ **You Need To:**
1. Add DNS CNAME record: `notionmcp` → `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`
2. Add public hostname in tunnel: `notionmcp.nowhere-else.co.uk` → `http://localhost:8000`
3. Wait 5-10 minutes for DNS propagation
4. Test: `https://notionmcp.nowhere-else.co.uk/health`

Follow the steps above to complete the setup!

