# ChatGPT MCP OAuth Setup Guide

This guide explains how to configure OAuth authentication for your ChatGPT MCP connector using **Personal Pro** developer mode.

## Overview

OAuth 2.0 authentication allows ChatGPT to securely connect to your MCP server without requiring API keys. This is the recommended authentication method for ChatGPT Personal Pro.

---

## Step 1: Configure Environment Variables

Add these to your `.env` file:

```env
# Base URL of your MCP server
BASE_URL=https://notionmcp.nowhere-else.co.uk

# OAuth Client Secret (shared secret with ChatGPT)
# Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
OAUTH_CLIENT_SECRET=your_oauth_client_secret_here

# Token Encryption Key (for storing OAuth tokens securely)
# Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
TOKEN_ENCRYPTION_KEY=your_token_encryption_key_here
```

---

## Step 2: Restart the MCP Server

After updating `.env`, restart the server:

```bash
docker-compose restart mcp
```

---

## Step 3: Configure ChatGPT MCP Connector

### In ChatGPT Developer Mode:

1. **Go to:** Settings → Apps & Connectors → Advanced Settings
2. **Enable:** Developer Mode (toggle ON)
3. **Click:** Create Connector (or Add Connector)

### Configure the Connector:

**Name:** `Notion MCP Server`

**Description:** `MCP server for managing Notion Second Brain workspace`

**MCP Server URL:** 
```
https://notionmcp.nowhere-else.co.uk/mcp/sse
```

**Authentication Method:** Select **OAuth**

**OAuth Configuration:**
- **Authorization URL:** `https://notionmcp.nowhere-else.co.uk/oauth/authorize`
- **Client Secret:** Enter the `OAUTH_CLIENT_SECRET` from your `.env` file

**Note:** 
- ChatGPT automatically discovers the Token URL via the OAuth metadata endpoint (`/.well-known/oauth-authorization-server`)
- You only need to provide the Authorization URL and Client Secret
- Redirect URI and other OAuth parameters are handled automatically by ChatGPT

4. **Click:** Save or Create

---

## Step 4: OAuth Flow

When you use the connector in ChatGPT:

1. **First Use:** ChatGPT redirects you to the authorization page
2. **Authorization:** You authorize ChatGPT to access your MCP server
3. **Redirect:** You're redirected back to ChatGPT with an authorization code
4. **Token Exchange:** ChatGPT exchanges the code for an access token
5. **Connected:** ChatGPT can now use the MCP server with the access token

---

## OAuth Endpoints

Your MCP server now exposes these OAuth endpoints:

### Authorization Endpoint
```
GET /oauth/authorize
```
- Used by ChatGPT to initiate OAuth flow
- Redirects user to authorization page
- Returns authorization code

### Token Endpoint
```
POST /oauth/token
```
- Exchanges authorization code for access token
- Supports refresh token flow
- Returns access token and refresh token

### Metadata Endpoint
```
GET /.well-known/oauth-authorization-server
```
- Returns OAuth server capabilities
- Used by ChatGPT to discover endpoints

---

## Testing OAuth

### Test Authorization Endpoint:
```bash
curl "https://notionmcp.nowhere-else.co.uk/oauth/authorize?response_type=code&client_id=test&redirect_uri=https://example.com/callback"
```

### Test Token Endpoint:
```bash
curl -X POST "https://notionmcp.nowhere-else.co.uk/oauth/token" \
  -d "grant_type=authorization_code" \
  -d "code=your_auth_code" \
  -d "redirect_uri=https://example.com/callback" \
  -d "client_id=test"
```

### Test Metadata:
```bash
curl https://notionmcp.nowhere-else.co.uk/.well-known/oauth-authorization-server
```

---

## Security Notes

1. **Client Secret:** Keep `OAUTH_CLIENT_SECRET` secure and never expose it
2. **Token Encryption:** `TOKEN_ENCRYPTION_KEY` encrypts stored tokens
3. **HTTPS Required:** OAuth requires HTTPS (already configured via Cloudflare)
4. **Token Expiry:** Access tokens expire after 1 hour
5. **Refresh Tokens:** Use refresh tokens to get new access tokens

---

## Troubleshooting

### "Invalid client" error
- Verify `OAUTH_CLIENT_SECRET` matches in both `.env` and ChatGPT connector settings
- Check client_id is correct

### "Invalid authorization code"
- Authorization codes expire after 10 minutes
- Codes can only be used once
- Try re-authorizing

### "Redirect URI mismatch"
- Ensure redirect_uri in token request matches authorization request
- ChatGPT should handle this automatically

### OAuth flow not starting
- Verify endpoints are accessible: `https://notionmcp.nowhere-else.co.uk/oauth/authorize`
- Check server logs: `docker-compose logs mcp`
- Ensure Developer Mode is enabled in ChatGPT

---

## Compatibility

✅ **Compatible with:**
- ChatGPT Personal Pro (Developer Mode)
- Standard OAuth 2.0 clients
- PKCE (code challenge) flow

✅ **Tested for:**
- Personal Pro accounts
- Standard OAuth 2.0 Authorization Code flow
- Token refresh flow

---

## Next Steps

After OAuth is configured:

1. **Test the connector** in ChatGPT
2. **Authorize** when prompted
3. **Use MCP tools** in ChatGPT conversations
4. **Monitor logs** for OAuth activity: `docker-compose logs -f mcp`

---

## Additional Resources

- OAuth 2.0 Specification: https://oauth.net/2/
- ChatGPT Developer Mode: https://platform.openai.com/docs/guides/developer-mode
- MCP Protocol: https://modelcontextprotocol.io

