# Getting Started

This guide takes you from zero to querying a P&ID with the LLM assistant in under 10 minutes.

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker + Docker Compose | 20+ / v2+ | Run all services with one command |
| Node.js | 20+ | Web UI and MCP server (only for local dev without Docker) |
| Python | 3.11+ | Converter and API (only for local dev without Docker) |
| Anthropic API key | - | Required for the LLM chat feature |

## Quick Start with Docker (Recommended)

### 1. Clone and configure

```bash
git clone <repo-url> pid-inteligente
cd pid-inteligente
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

The other defaults match docker-compose.yml and work out of the box:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pidinteligente
CORS_ORIGINS=http://localhost:3000
API_BASE_URL=http://localhost:8000
```

### 2. Start all services

```bash
docker-compose up
```

This starts four containers:

| Service | Port | URL |
|---------|------|-----|
| Neo4j (graph database) | 7474, 7687 | http://localhost:7474 |
| API (FastAPI backend) | 8000 | http://localhost:8000/docs |
| Web UI (React frontend) | 3000 | http://localhost:3000 |
| MCP Server | - | stdio transport (no HTTP port) |

Wait until you see log messages from all services indicating readiness. The API waits for Neo4j's healthcheck before starting.

### 3. Open the Web UI

Navigate to **http://localhost:3000** in your browser.

## Quick Start without Docker

If you prefer running services individually (for development or debugging):

### 1. Start Neo4j

Install and run Neo4j 5+ locally, or use the Docker image alone:

```bash
docker run -d \
  --name pid-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/pidinteligente \
  -e 'NEO4J_PLUGINS=["apoc"]' \
  neo4j:5
```

Wait for it to be ready at http://localhost:7474.

### 2. Start the API

```bash
cd packages/pid-rag
pip install -e ".[dev]"

# Set environment variables (or use .env file in project root)
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=pidinteligente

uvicorn pid_rag.api.app:app --reload --port 8000
```

Verify at http://localhost:8000/docs (Swagger UI).

### 3. Start the Web UI

```bash
cd packages/pid-web
npm install
npm run dev
```

The development server runs at http://localhost:5173 (note: different port than Docker's 3000). If the API runs on port 8000, it connects automatically.

## First Use: Upload, Explore, and Ask

### Step 1: Upload a P&ID

The repository includes a test file at `packages/drawio-library/examples/test-simple.drawio`. This is a simple P&ID with a tank (T-101), pump (P-101), control valve (TCV-101), and heat exchanger (HE-101).

1. Open the Web UI at http://localhost:3000
2. Drag and drop the file `test-simple.drawio` onto the upload area (or click to browse)
3. The system will:
   - Parse the Draw.io file
   - Build the Knowledge Graph (detailed and condensed)
   - Load it into Neo4j

You should see a confirmation with statistics: number of nodes, edges, equipment, and instruments.

### Step 2: Explore the Knowledge Graph

Switch to the **Knowledge Graph** tab to see the interactive graph visualization (powered by Cytoscape.js). Equipment nodes appear as the main elements with flow edges between them.

Click on any node to see its details: tag number, DEXPI class, design conditions, and connections.

### Step 3: Ask Questions

Switch to the **Chat** tab and try these questions:

- "What is the main process flow?"
- "What equipment is connected to P-101?"
- "Describe the control loop for TCV-101"
- "Are there any potential design issues?"

The LLM uses Graph-RAG to retrieve the relevant portion of the Knowledge Graph before answering, so responses are grounded in your actual P&ID data.

### Step 4: Explore in Neo4j Browser (Optional)

Open http://localhost:7474 and log in with:
- Username: `neo4j`
- Password: `pidinteligente`

Try a Cypher query:

```cypher
MATCH (n:PidNode) RETURN n LIMIT 25
```

## Troubleshooting

### Neo4j does not start

**Symptom**: `docker-compose up` hangs or the API fails with connection errors.

**Fixes**:
- Ensure ports 7474 and 7687 are free: `lsof -i :7474` (Linux/Mac) or `netstat -an | findstr 7474` (Windows)
- Check Docker has enough memory (Neo4j needs at least 512 MB)
- Check logs: `docker-compose logs neo4j`
- If the volume is corrupted, remove it: `docker-compose down -v && docker-compose up`

### API does not connect to Neo4j

**Symptom**: API returns 500 errors mentioning Neo4j connection.

**Fixes**:
- Ensure Neo4j is fully started (healthcheck takes ~30 seconds)
- Verify `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in `.env` match docker-compose.yml
- When running without Docker, use `bolt://localhost:7687`; with Docker, the API uses `bolt://neo4j:7687` (Docker internal network)

### CORS errors in the browser

**Symptom**: Browser console shows "CORS policy" errors when the Web UI calls the API.

**Fixes**:
- Ensure `CORS_ORIGINS` in `.env` includes the exact origin of the Web UI (including port)
- For Docker: `CORS_ORIGINS=http://localhost:3000`
- For local dev: `CORS_ORIGINS=http://localhost:5173` (Vite dev server port)
- Multiple origins: `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`

### API key errors in chat

**Symptom**: Chat returns an error about `ANTHROPIC_API_KEY`.

**Fixes**:
- Verify the key is set in `.env` and starts with `sk-ant-`
- When using Docker, restart after changing `.env`: `docker-compose down && docker-compose up`
- The key is required only for the chat feature; conversion, graph building, and validation work without it

### Upload fails with 422 error

**Symptom**: Uploading a .drawio file returns a 422 Unprocessable Entity error.

**Fixes**:
- Ensure the file uses symbols from the P&ID library with `dexpi_class` attributes
- Validate the file first using the CLI: `pid-converter validate your-file.drawio`
- Check the API logs for the specific parsing error

## Next Steps

- [Draw.io Library Guide](drawio-library.md) -- Learn to create P&IDs with semantic symbols
- [Converter Guide](converter.md) -- Convert between Draw.io and DEXPI formats
- [Knowledge Graph Guide](knowledge-graph.md) -- Understand and query the graph
- [Web UI Guide](web-ui.md) -- Full guide to the web interface
- [MCP Server Guide](mcp-server.md) -- Automate with the MCP protocol
- [API Reference](../api/endpoints.md) -- All REST endpoints documented
