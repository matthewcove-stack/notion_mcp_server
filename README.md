# MCP Server – Notion Second Brain Integration

Local MCP-style server enabling ChatGPT voice commands to create, query and manage a Notion Second Brain workspace.

## Quick Start

### Option 1: Docker (Recommended)

1. **Start Docker Desktop** (if not already running)

2. **Configure Notion API Token**
   - Edit `.env` file
   - Add your Notion Integration token: `NOTION_API_TOKEN=your_token_here`
   - Get your token from: https://www.notion.so/my-integrations

3. **Start the Service**
   ```bash
   docker-compose up --build
   ```

### Option 2: Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Notion API Token**
   - Edit `.env` file
   - Add your Notion Integration token: `NOTION_API_TOKEN=your_token_here`

3. **Run the Server**
   ```bash
   python run_local.py
   ```
   Or:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Verify it's Running

- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Verify Notion connection: http://localhost:8000/notion/me

## Development

### Phase 0 (Implemented)
- `GET /health` - Health check
- `GET /version` - Service version
- `GET /notion/me` - Notion token verification

### Phase 1 (Implemented)
- `GET /databases` - List configured databases
- `POST /databases/discover` - Find databases by name
- `GET /databases/{db_id}` - Get database schema
- `PATCH /databases/{db_id}` - Update database schema
- `POST /second-brain/bootstrap` - Create Second Brain structure
- `GET /second-brain/status` - Validate structure
- `POST /second-brain/migrate` - Schema migrations

## Stack

- FastAPI
- Docker / Docker Compose
- Python 3.12
- Notion API

See `SPEC.md` for the complete specification and roadmap.

