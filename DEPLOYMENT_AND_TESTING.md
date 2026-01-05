# Notion MCP Server - Deployment and Testing Guide

## 🎉 Implementation Complete!

All functionality has been implemented. This MCP server now enables ChatGPT to **fully administer your Notion workspace** including:

✅ Create/update/delete databases
✅ Create/update/archive pages  
✅ Manage blocks and content
✅ Query databases with filters and sorts
✅ Search across workspace
✅ Upsert operations (create or update)
✅ Link pages via relations
✅ Bulk operations
✅ All property types (title, select, multi-select, date, number, checkbox, url, email, phone, people, files, relations, rollups, formulas)
✅ Audit logging
✅ Idempotency keys
✅ Error handling
✅ Both REST API and MCP protocol support

---

## 📦 Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependencies added:**
- `notion-client` - Official Notion SDK
- `sqlalchemy` - Database ORM
- `cryptography` - Token encryption
- `celery` & `redis` - Job queue (optional)
- `sse-starlette` - SSE support

---

## 🔧 Step 2: Configure Environment

Update your `.env` file with required values:

```env
# Notion API Token (Required)
NOTION_API_TOKEN=your_notion_integration_token_here

# Base URL (Required for OAuth)
BASE_URL=https://notionmcp.nowhere-else.co.uk

# OAuth Configuration (Optional - for ChatGPT OAuth)
OAUTH_CLIENT_SECRET=your_secure_random_secret

# Token Encryption (Optional - auto-generates if not set)
TOKEN_ENCRYPTION_KEY=your_encryption_key

# MCP API Key (Optional - for additional security)
MCP_API_KEY=your_mcp_api_key

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///./notion_mcp.db
```

### Getting Your Notion Token

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "ChatGPT MCP Server"
4. Select capabilities:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
5. Copy the "Internal Integration Token"
6. **Important:** Share your Notion pages/databases with this integration!

---

## 🚀 Step 3: Start the Server

### Option A: Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d
```

### Option B: Local Development

```bash
# Run the server
python run_local.py

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ Step 4: Verify Installation

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"ok": true, "status": "healthy"}
```

### 2. Verify Notion Connection

```bash
curl http://localhost:8000/notion/me
```

Expected response:
```json
{
  "ok": true,
  "message": "Notion token is valid",
  "user": {
    "object": "user",
    "id": "...",
    "type": "bot",
    "name": "ChatGPT MCP Server"
  }
}
```

### 3. Test API Documentation

Visit http://localhost:8000/docs to see the interactive API documentation.

---

## 🧪 Step 5: Test Core Functionality

### Test 1: List Databases

```bash
curl http://localhost:8000/databases
```

### Test 2: Search Workspace

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "tasks"}'
```

### Test 3: Create a Page

```bash
curl -X POST http://localhost:8000/pages \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {
      "type": "database_id",
      "database_id": "YOUR_DATABASE_ID"
    },
    "properties": {
      "Name": {
        "type": "title",
        "value": "Test Task from MCP"
      },
      "Status": {
        "type": "select",
        "value": "To Do"
      }
    }
  }'
```

### Test 4: Upsert Operation

```bash
curl -X POST http://localhost:8000/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "database_id": "YOUR_DATABASE_ID",
    "unique_property": "Name",
    "unique_value": "My Project",
    "properties": {
      "Status": {"type": "select", "value": "In Progress"},
      "Due": {"type": "date", "value": "2026-01-15"}
    }
  }'
```

---

## 🔌 Step 6: Connect ChatGPT via MCP

### 1. Verify MCP Endpoint

```bash
curl http://localhost:8000/mcp
```

Expected response:
```json
{
  "protocol": "mcp",
  "version": "1.0",
  "transport": "sse",
  "endpoint": "/mcp/sse",
  "status": "active",
  "tools_available": 5
}
```

### 2. Configure ChatGPT Developer Mode

1. Open ChatGPT (web or app)
2. Go to **Settings** → **Apps & Connectors**
3. Enable **Developer Mode**
4. Click **Create** or **Add Connector**
5. Fill in:
   - **Name:** Notion MCP Server
   - **Description:** Full Notion administration via MCP
   - **MCP Server URL:** `https://notionmcp.nowhere-else.co.uk/mcp/sse`
   - **Authentication:** OAuth (if configured) or None

### 3. Test MCP Tools in ChatGPT

Try these prompts:

```
"List all my Notion databases"

"Create a new database called Tasks with properties: Name (title), Status (select), Due Date (date)"

"Add a task called 'Review project proposal' to my Tasks database"

"Find all pages in my workspace that mention 'project'"

"Show me tasks that are due today"

"Create a new customer record with name 'Acme Corp' and status 'Active'"
```

---

## 🎯 Available MCP Tools

ChatGPT can now use these tools:

### Database Operations
- `notion.list_databases` - List all databases
- `notion.get_database` - Get database schema
- `notion.create_database` - Create new database
- `notion.query_database` - Query with filters/sorts

### Page Operations
- `notion.create_page` - Create page in database
- `notion.get_page` - Retrieve page details
- `notion.update_page` - Update page properties

### Search & Query
- `notion.search` - Search across workspace

### High-Level Operations
- `notion.upsert` - Create or update page
- `notion.link` - Link pages via relations
- `notion.bulk` - Execute multiple operations

### Block Operations
- `notion.append_blocks` - Add content to pages

### Second Brain
- `second_brain.status` - Check workspace status
- `second_brain.bootstrap` - Setup guidance

---

## 📊 Available REST Endpoints

All endpoints return standard response format:

```json
{
  "ok": true,
  "result": { ... },
  "error": null,
  "meta": {
    "request_id": "..."
  }
}
```

### Core Endpoints
- `GET /health` - Health check
- `GET /version` - Service version
- `GET /notion/me` - Verify Notion token

### Database Endpoints
- `GET /databases` - List databases
- `POST /databases` - Create database
- `GET /databases/{id}` - Get database
- `PATCH /databases/{id}` - Update database
- `POST /databases/{id}/query` - Query database

### Page Endpoints
- `POST /pages` - Create page
- `GET /pages/{id}` - Get page
- `PATCH /pages/{id}` - Update page
- `DELETE /pages/{id}` - Archive page

### Block Endpoints
- `GET /blocks/{id}` - Get block
- `GET /blocks/{id}/children` - List children
- `POST /blocks/{id}/children` - Append blocks
- `DELETE /blocks/{id}` - Delete block

### Operations Endpoints
- `POST /search` - Search workspace
- `POST /upsert` - Upsert page
- `POST /link` - Link pages
- `POST /bulk` - Bulk operations

### Job Endpoints
- `POST /jobs` - Create job
- `GET /jobs/{id}` - Get job status

---

## 🎨 Usage Examples

### Example 1: Create a Complete Task Database

```bash
curl -X POST http://localhost:8000/databases \
  -H "Content-Type: application/json" \
  -d '{
    "parent_page_id": "YOUR_PARENT_PAGE_ID",
    "title": "Tasks",
    "properties": {
      "Name": {"title": {}},
      "Status": {
        "select": {
          "options": [
            {"name": "To Do", "color": "gray"},
            {"name": "In Progress", "color": "blue"},
            {"name": "Done", "color": "green"}
          ]
        }
      },
      "Priority": {
        "select": {
          "options": [
            {"name": "Low", "color": "gray"},
            {"name": "Medium", "color": "yellow"},
            {"name": "High", "color": "red"}
          ]
        }
      },
      "Due Date": {"date": {}},
      "Assignee": {"people": {}},
      "Tags": {"multi_select": {}}
    }
  }'
```

### Example 2: Bulk Create Multiple Tasks

```bash
curl -X POST http://localhost:8000/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "continue_on_error",
    "operations": [
      {
        "op": "upsert",
        "args": {
          "database_id": "YOUR_DATABASE_ID",
          "unique_property": "Name",
          "unique_value": "Task 1",
          "properties": {
            "Status": {"type": "select", "value": "To Do"},
            "Priority": {"type": "select", "value": "High"}
          }
        }
      },
      {
        "op": "upsert",
        "args": {
          "database_id": "YOUR_DATABASE_ID",
          "unique_property": "Name",
          "unique_value": "Task 2",
          "properties": {
            "Status": {"type": "select", "value": "In Progress"}
          }
        }
      }
    ]
  }'
```

### Example 3: Query with Filters

```bash
curl -X POST http://localhost:8000/databases/YOUR_DATABASE_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "and": [
        {
          "property": "Status",
          "select": {"equals": "In Progress"}
        },
        {
          "property": "Priority",
          "select": {"equals": "High"}
        }
      ]
    },
    "sorts": [
      {
        "property": "Due Date",
        "direction": "ascending"
      }
    ]
  }'
```

---

## 🔒 Security Features

- ✅ Token encryption at rest
- ✅ Audit logging for all write operations
- ✅ Idempotency keys to prevent duplicates
- ✅ Request ID tracking
- ✅ Error handling without leaking sensitive data
- ✅ Retry logic with exponential backoff
- ✅ Rate limit handling

---

## 📝 Audit Logs

All write operations are logged to the database:

```sql
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

Columns include:
- `request_id` - Unique request identifier
- `actor` - 'chatgpt_action' or 'chatgpt_mcp'
- `endpoint` - Operation performed
- `notion_ids` - Object IDs affected
- `summary` - Human-readable description
- `success` - Whether operation succeeded
- `created_at` - Timestamp

---

## 🐛 Troubleshooting

### Issue: "NOTION_API_TOKEN not configured"

**Solution:** Ensure `.env` file exists and contains valid `NOTION_API_TOKEN`

### Issue: "Notion API error: object not found"

**Solution:** Share your Notion pages/databases with the integration:
1. Open page in Notion
2. Click "..." menu → "Connections"
3. Add your integration

### Issue: "Internal error"

**Solution:** Check logs:
```bash
docker-compose logs mcp
# or
tail -f logs/app.log
```

### Issue: MCP tools not working in ChatGPT

**Solution:** 
1. Verify MCP endpoint is accessible: `curl https://notionmcp.nowhere-else.co.uk/mcp`
2. Check Cloudflare tunnel is running: `docker-compose ps cloudflared`
3. Reconnect in ChatGPT settings

---

## 📚 Property Type Examples

### Title
```json
{"Name": {"type": "title", "value": "My Page"}}
```

### Rich Text
```json
{"Description": {"type": "rich_text", "value": "Some text"}}
```

### Select
```json
{"Status": {"type": "select", "value": "In Progress"}}
```

### Multi-Select
```json
{"Tags": {"type": "multi_select", "value": ["tag1", "tag2"]}}
```

### Date
```json
{"Due": {"type": "date", "value": "2026-01-15"}}
```

### Number
```json
{"Count": {"type": "number", "value": 42}}
```

### Checkbox
```json
{"Done": {"type": "checkbox", "value": true}}
```

### URL
```json
{"Website": {"type": "url", "value": "https://example.com"}}
```

### Email
```json
{"Email": {"type": "email", "value": "user@example.com"}}
```

### Phone
```json
{"Phone": {"type": "phone_number", "value": "+1234567890"}}
```

### Relation (link to another page)
```json
{"Project": {"type": "relation", "value": ["page-id-1", "page-id-2"]}}
```

---

## 🎓 Next Steps

### 1. Set Up Your Notion Workspace
Share relevant pages/databases with the integration.

### 2. Test Basic Operations
Try creating, updating, and querying pages.

### 3. Connect ChatGPT
Configure MCP connector in ChatGPT settings.

### 4. Start Administering!
Ask ChatGPT to manage your Notion workspace naturally:
- "Create a customer database"
- "Add a task for tomorrow"
- "Show me all high-priority items"
- "Link this project to that client"

---

## 🚀 You're Ready!

Your Notion MCP server is now **fully functional** and ready to be administered by ChatGPT!

**Try saying to ChatGPT:**
```
"List all my Notion databases and create a new one called 'Projects' with properties for Name, Status, Owner, and Due Date"
```

Enjoy your AI-powered Notion administration! 🎉

