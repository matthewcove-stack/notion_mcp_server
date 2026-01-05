# Environment Variables Setup Guide

This guide shows you exactly how to get the correct values for `NOTION_API_TOKEN` and `MCP_API_KEY`.

---

## 1. NOTION_API_TOKEN

### Step-by-Step Instructions

1. **Go to Notion Integrations Page**
   - Open your browser and navigate to: **https://www.notion.so/my-integrations**
   - You may need to log in to your Notion account

2. **Create a New Integration**
   - Click the **"+ New integration"** button (usually in the top right)
   - Or click **"Create new integration"** if you don't have any yet

3. **Configure Your Integration**
   - **Name**: Enter a descriptive name (e.g., "ChatGPT MCP Server" or "Notion MCP Integration")
   - **Logo**: (Optional) Upload a logo if desired
   - **Associated workspace**: Select the Notion workspace you want to connect
   - **Type**: Select **"Internal"** (this is the most common type for personal use)
   - Click **"Submit"** or **"Create integration"**

4. **Copy the Integration Token**
   - After creating the integration, you'll see a page with integration details
   - Look for a section called **"Internal Integration Token"** or **"Token"**
   - You'll see a token that starts with `secret_` followed by a long string of characters
   - **Example format**: `secret_abc123xyz456...` (much longer in reality)
   - Click the **"Show"** or **"Copy"** button next to the token
   - **IMPORTANT**: Copy this entire token - you won't be able to see it again!

5. **Grant Permissions to Your Pages/Databases**
   - Go to any Notion page or database you want the integration to access
   - Click the **"..."** (three dots) menu in the top right
   - Select **"Add connections"** or **"Connections"**
   - Find your integration in the list and select it
   - Repeat this for each page/database you want to manage via ChatGPT

6. **Set the Token in Your .env File**
   ```env
   NOTION_API_TOKEN=secret_your_actual_token_here
   ```
   - Replace `secret_your_actual_token_here` with the token you copied
   - **Do NOT include quotes** around the token value
   - **Do NOT share this token** publicly or commit it to version control

### Verify Your NOTION_API_TOKEN

After setting up your `.env` file and starting the server, you can verify the token works:

```bash
# Test the connection
curl http://localhost:8000/notion/me
```

Or visit: **http://localhost:8000/notion/me** in your browser

You should see information about your Notion user/workspace if the token is valid.

---

## 2. MCP_API_KEY

The `MCP_API_KEY` is a **secret key you generate yourself** to authenticate ChatGPT's requests to your MCP server. It's like a password that protects your server.

### Option A: Generate Using Python (Recommended)

1. **Open a terminal/command prompt**

2. **Run this Python command:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   **On Windows PowerShell:**
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   **On Windows CMD:**
   ```cmd
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Copy the output** - You'll get a long random string like:
   ```
   xK9mP2vQ7wR4tY8uI0oP3aS6dF9gH2jK5lM8nQ1rT4vW7yZ0
   ```

4. **Set it in your .env file:**
   ```env
   MCP_API_KEY=xK9mP2vQ7wR4tY8uI0oP3aS6dF9gH2jK5lM8nQ1rT4vW7yZ0
   ```
   - Replace with your actual generated key
   - **Do NOT include quotes** around the key value

### Option B: Generate Using Online Tool

1. **Use a secure random string generator:**
   - Visit: https://www.random.org/strings/
   - Or: https://1password.com/password-generator/
   - Generate a string that's **at least 32 characters long**
   - Use alphanumeric characters (letters and numbers)
   - **Example length**: 40-64 characters is recommended

2. **Copy the generated string**

3. **Set it in your .env file:**
   ```env
   MCP_API_KEY=your_generated_random_string_here
   ```

### Option C: Generate Using OpenSSL (Linux/Mac)

```bash
openssl rand -base64 32
```

Copy the output and use it as your `MCP_API_KEY`.

---

## Complete .env File Example

Create a `.env` file in your project root with both values:

```env
# Notion API Integration Token
# Get from: https://www.notion.so/my-integrations
NOTION_API_TOKEN=secret_abc123xyz456def789ghi012jkl345mno678pqr901stu234vwx567yz

# MCP API Key for ChatGPT authentication
# Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
MCP_API_KEY=xK9mP2vQ7wR4tY8uI0oP3aS6dF9gH2jK5lM8nQ1rT4vW7yZ0aB3cD6eF9gH2jK5lM8nQ1rT4vW7yZ0
```

**Important Notes:**
- Replace both values with your actual tokens/keys
- **Never commit the `.env` file to git** (it should be in `.gitignore`)
- Keep these values secret and secure
- If you lose the `MCP_API_KEY`, just generate a new one and update ChatGPT's connector settings

---

## Security Best Practices

1. **Never share these values publicly**
   - Don't post them on GitHub, forums, or social media
   - Don't include them in screenshots

2. **Use different keys for different environments**
   - Development: One set of keys
   - Production: Different set of keys

3. **Rotate keys periodically**
   - If you suspect a key is compromised, generate a new one
   - Update your `.env` file and ChatGPT connector settings

4. **Check your .gitignore**
   - Make sure `.env` is listed in `.gitignore`
   - Verify it's not being tracked by git:
     ```bash
     git check-ignore .env
     ```
   - Should output: `.env`

---

## Troubleshooting

### "Invalid Notion token" error
- Verify you copied the **entire** token (they're very long)
- Make sure there are no extra spaces or line breaks
- Check that the token starts with `secret_`
- Ensure you've granted the integration access to your pages/databases

### "Authentication failed" in ChatGPT
- Verify `MCP_API_KEY` matches exactly in both:
  - Your `.env` file
  - ChatGPT connector settings
- Check for extra spaces or quotes
- Regenerate the key if unsure and update both places

### Token not working after copying
- Some terminals add a newline - try copying again or remove trailing whitespace
- Make sure you're using the correct `.env` file in the project root
- Restart your Docker containers or server after changing `.env`

---

## Quick Reference

**Get NOTION_API_TOKEN:**
1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Copy the "Internal Integration Token"
4. Grant access to your pages/databases

**Generate MCP_API_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Verify setup:**
```bash
# Check Notion connection
curl http://localhost:8000/notion/me

# Check server health
curl http://localhost:8000/health
```

