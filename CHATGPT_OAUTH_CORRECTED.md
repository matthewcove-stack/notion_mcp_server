# ChatGPT OAuth Configuration - Corrected Instructions

## What You Need to Configure in ChatGPT

When creating an MCP connector with OAuth authentication in ChatGPT, you only need to provide **TWO fields**:

### 1. Authorization URL
```
https://notionmcp.nowhere-else.co.uk/oauth/authorize
```

### 2. Client Secret
- Generate using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Add to your `.env` file as `OAUTH_CLIENT_SECRET`
- Enter this value in ChatGPT's Client Secret field

---

## What You DON'T Need to Configure

ChatGPT automatically discovers these through the OAuth metadata endpoint:

- ❌ Token URL (auto-discovered)
- ❌ Client ID (managed by ChatGPT)
- ❌ Redirect URI (managed by ChatGPT)
- ❌ Scopes (auto-discovered)

---

## How It Works

1. **You provide:** Authorization URL + Client Secret
2. **ChatGPT discovers:** Token URL from `https://notionmcp.nowhere-else.co.uk/.well-known/oauth-authorization-server`
3. **ChatGPT handles:** OAuth flow automatically

The metadata endpoint returns:
```json
{
  "authorization_endpoint": "https://notionmcp.nowhere-else.co.uk/oauth/authorize",
  "token_endpoint": "https://notionmcp.nowhere-else.co.uk/oauth/token",
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "response_types_supported": ["code"]
}
```

ChatGPT reads this automatically and uses the `token_endpoint` value.

---

## Corrected Setup Steps

### 1. Add to `.env` file:
```env
OAUTH_CLIENT_SECRET=<your_generated_secret>
BASE_URL=https://notionmcp.nowhere-else.co.uk
```

### 2. In ChatGPT, configure connector:
- **Name:** Notion MCP Server
- **MCP Server URL:** `https://notionmcp.nowhere-else.co.uk/mcp/sse`
- **Authentication:** OAuth
- **Authorization URL:** `https://notionmcp.nowhere-else.co.uk/oauth/authorize`
- **Client Secret:** (paste from your `.env` file)

### 3. Save and authorize:
- Click Create/Save
- ChatGPT will redirect you to authorize
- After authorization, you're connected

---

## Why Previous Instructions Were Wrong

**Incorrect:** Instructions said to manually enter Token URL  
**Correct:** Token URL is auto-discovered via OAuth metadata

ChatGPT implements OAuth 2.0 discovery, so it automatically fetches the token endpoint from the `.well-known` endpoint.

---

## Verification

Test that ChatGPT can discover your OAuth configuration:

```bash
curl https://notionmcp.nowhere-else.co.uk/.well-known/oauth-authorization-server
```

Expected response includes:
- `authorization_endpoint`
- `token_endpoint`
- `grant_types_supported`
- `response_types_supported`

---

## Files Updated

- ✅ `CHATGPT_MCP_SETUP.md` — Corrected OAuth instructions
- ✅ `CHATGPT_OAUTH_SETUP.md` — Removed Token URL field
- ✅ This file created as reference

---

## Summary

**In ChatGPT, you only need:**
1. Authorization URL: `https://notionmcp.nowhere-else.co.uk/oauth/authorize`
2. Client Secret: `<from your .env file>`

Everything else is handled automatically.

