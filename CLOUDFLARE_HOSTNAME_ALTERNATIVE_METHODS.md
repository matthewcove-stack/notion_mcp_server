# Alternative Methods to Configure Cloudflare Tunnel Hostname

If you don't see the "Public Hostname" tab, try these alternative methods:

---

## Method 1: Check Different Tab Names

The tab might be named differently:
- **"Routes"** tab
- **"Public Routes"** tab  
- **"Ingress"** tab
- **"Hostnames"** tab (without "Public")
- **"DNS"** tab within tunnel settings

**Try this:**
1. Go to: Cloudflare Dashboard → **Zero Trust** → **Networks** → **Tunnels**
2. Click on tunnel **`notionmcp`**
3. Look for any of the tab names above

---

## Method 2: Use Cloudflare API (Recommended)

If the UI doesn't show the option, use the API directly:

### Get Your API Token

1. Go to: Cloudflare Dashboard → **My Profile** → **API Tokens**
2. Click **"Create Token"**
3. Use **"Edit Cloudflare Tunnel"** template
4. Or create custom token with these permissions:
   - **Account** → **Cloudflare Tunnel** → **Edit**
5. Copy the token

### Add Public Hostname via API

```powershell
# Set your variables
$accountId = "39cd36506b29c58e3cd376ce72b194d7"  # From notionmcp.json
$tunnelId = "da1d47b4-6623-4552-b6f8-0a40bbab2bb8"
$apiToken = "YOUR_API_TOKEN_HERE"

# Add public hostname
$body = @{
    hostname = "notionmcp.nowhere-else.co.uk"
    service = "http://localhost:8000"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $apiToken"
    "Content-Type" = "application/json"
}

$url = "https://api.cloudflare.com/client/v4/accounts/$accountId/cfd_tunnel/$tunnelId/routes"
Invoke-RestMethod -Uri $url -Method POST -Headers $headers -Body $body
```

---

## Method 3: Configure via Config File (Already Done)

**Good news:** We've already configured the hostname in `cloudflared/config.yml`:

```yaml
ingress:
  - hostname: notionmcp.nowhere-else.co.uk
    service: http://mcp:8000
```

**However:** For Cloudflare to recognize this, you typically still need to:
1. Add the DNS CNAME record (Step 1 - still required)
2. Either configure via dashboard/API OR the config file might work if Cloudflare auto-discovers it

---

## Method 4: Use Cloudflare CLI (cloudflared)

If you have `cloudflared` installed locally:

```bash
# Login to Cloudflare
cloudflared tunnel login

# Add route
cloudflared tunnel route dns notionmcp da1d47b4-6623-4552-b6f8-0a40bbab2bb8 notionmcp.nowhere-else.co.uk
```

---

## Method 5: Check if DNS-Only Configuration Works

Sometimes, if you:
1. ✅ Add the DNS CNAME record
2. ✅ Have the config file set up correctly
3. ✅ Tunnel is running

The tunnel might automatically route traffic. **Try this:**

1. **First, add the DNS record** (Step 1 from instructions)
2. **Wait 5-10 minutes**
3. **Test:** `https://notionmcp.nowhere-else.co.uk/health`

If it works, you might not need to configure the hostname separately!

---

## Method 6: Check Your Cloudflare Plan

Some features require:
- **Cloudflare Zero Trust** (free tier available)
- **Cloudflare Tunnel** access

**Verify:**
1. Go to: Cloudflare Dashboard → **Zero Trust**
2. Check if you see "Networks" → "Tunnels"
3. If not, you may need to enable Zero Trust (free tier works)

---

## Quick Diagnostic

**Answer these questions:**

1. **Can you see the tunnel?**
   - Go to: Zero Trust → Networks → Tunnels
   - Do you see tunnel `notionmcp`?

2. **What tabs do you see when you click the tunnel?**
   - List all tabs you see

3. **Do you have Zero Trust enabled?**
   - Check: Zero Trust dashboard access

4. **What's your Cloudflare account type?**
   - Free, Pro, Business, Enterprise?

---

## Recommended Next Steps

**Try in this order:**

1. ✅ **Add DNS CNAME record** (Step 1 - do this first)
2. ✅ **Verify config file** is correct (already done)
3. ✅ **Restart tunnel:** `docker-compose restart cloudflared`
4. ⏳ **Wait 10 minutes** for DNS propagation
5. ⏳ **Test:** `https://notionmcp.nowhere-else.co.uk/health`

**If it doesn't work after DNS + config file:**
- Use Method 2 (API) or Method 4 (CLI) to explicitly add the route

---

## What You Need Right Now

**Minimum required:**
1. ✅ DNS CNAME record: `notionmcp` → `da1d47b4-6623-4552-b6f8-0a40bbab2bb8.cfargotunnel.com`
2. ✅ Config file: Already configured
3. ✅ Tunnel running: Already running

**The DNS record is the most critical step.** Once that's added, test if it works. If not, we'll use the API method.

