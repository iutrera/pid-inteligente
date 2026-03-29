# API Reference

The P&ID Inteligente API is a FastAPI application that provides REST endpoints for P&ID conversion, Knowledge Graph construction and querying, LLM-powered chat, and validation.

## Base URL

| Environment | Base URL |
|-------------|----------|
| Docker | `http://localhost:8000` |
| Local development | `http://localhost:8000` |

## Interactive Documentation

With the API running, auto-generated documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints Summary

| Method | Path | Tags | Description |
|--------|------|------|-------------|
| `GET` | `/api/health` | health | Health check |
| `POST` | `/api/convert/drawio-to-dexpi` | convert | Convert Draw.io to DEXPI Proteus XML |
| `POST` | `/api/convert/dexpi-to-drawio` | convert | Convert DEXPI Proteus XML to Draw.io |
| `POST` | `/api/graph/build` | graph | Build Knowledge Graph from a P&ID file |
| `GET` | `/api/graph/{pid_id}` | graph | Get condensed graph for a P&ID |
| `GET` | `/api/graph/{pid_id}/detail` | graph | Get detailed graph for a P&ID |
| `GET` | `/api/graph/{pid_id}/drawio` | graph | Get raw .drawio XML for viewer |
| `POST` | `/api/chat` | chat | Chat with the P&ID assistant (SSE streaming) |
| `POST` | `/api/validate` | validate | Validate a P&ID file for design errors |

---

## Health

### GET /api/health

Returns API status and version.

**Response** `200 OK`:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## Conversion

### POST /api/convert/drawio-to-dexpi

Upload a `.drawio` file and receive DEXPI Proteus XML.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The .drawio file to convert |

**Response** `200 OK`: `application/xml`

The response is an XML file download with `Content-Disposition: attachment; filename="<name>.xml"`.

**Errors**:

| Status | Condition |
|--------|-----------|
| `400` | No filename provided or empty file |
| `422` | Conversion failed (parsing or mapping error) |

**Example** (curl):

```bash
curl -X POST http://localhost:8000/api/convert/drawio-to-dexpi \
  -F "file=@my-pid.drawio" \
  -o output.xml
```

### POST /api/convert/dexpi-to-drawio

Upload a DEXPI Proteus XML file and receive a `.drawio` file.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The DEXPI .xml file to convert |

**Response** `200 OK`: `application/xml`

The response is an XML file download with `Content-Disposition: attachment; filename="<name>.drawio"`.

**Errors**:

| Status | Condition |
|--------|-----------|
| `400` | No filename provided or empty file |
| `422` | Import failed (parsing error) |

**Example** (curl):

```bash
curl -X POST http://localhost:8000/api/convert/dexpi-to-drawio \
  -F "file=@dexpi-input.xml" \
  -o output.drawio
```

---

## Knowledge Graph

### POST /api/graph/build

Upload a `.drawio` file to build its Knowledge Graph and store it in Neo4j.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The .drawio file |
| `pid_id` | string | No | Custom identifier for this P&ID. Defaults to the filename without extension |

**Response** `200 OK`:

```json
{
  "pid_id": "test-simple",
  "node_count": 14,
  "edge_count": 18,
  "equipment_count": 4,
  "instrument_count": 2
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| `400` | No filename provided or empty file |
| `422` | Graph build failed (parsing or graph construction error) |

**Example** (curl):

```bash
curl -X POST http://localhost:8000/api/graph/build \
  -F "file=@test-simple.drawio" \
  -F "pid_id=my-test-pid"
```

### GET /api/graph/{pid_id}

Get the condensed (equipment-level) graph for a P&ID. This graph has equipment as nodes and flow relationships as edges.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `pid_id` | string | The P&ID identifier (set during build) |

**Response** `200 OK`:

```json
{
  "nodes": [
    {
      "id": "node_10",
      "tag": "T-101",
      "type": "Equipment",
      "label": "Tank T-101 (vertical vessel, 10 m3)",
      "extra": {
        "dexpi_class": "VerticalVessel",
        "design_pressure": "5 barg"
      }
    }
  ],
  "edges": [
    {
      "source": "node_10",
      "target": "node_30",
      "type": "FLOW",
      "label": "Process flow"
    }
  ]
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| `404` | No graph found for the given pid_id |
| `500` | Internal error during graph retrieval |

**Example** (curl):

```bash
curl http://localhost:8000/api/graph/test-simple
```

### GET /api/graph/{pid_id}/detail

Get the full detailed graph for a P&ID (all nodes and edges, including nozzles, piping components, and instruments).

**Path Parameters**: same as above.

**Response** `200 OK`: same schema as `/api/graph/{pid_id}` but with more nodes and edges.

**Example** (curl):

```bash
curl http://localhost:8000/api/graph/test-simple/detail
```

### GET /api/graph/{pid_id}/drawio

Get the raw `.drawio` XML for rendering in the embedded viewer. This returns the XML that was uploaded during the build step.

**Path Parameters**: same as above.

**Response** `200 OK`:

```json
{
  "pid_id": "test-simple",
  "xml": "<?xml version=\"1.0\" ...>..."
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| `404` | No .drawio XML cached for this pid_id (the P&ID may have been built from a previous server session) |

**Example** (curl):

```bash
curl http://localhost:8000/api/graph/test-simple/drawio
```

---

## Chat

### POST /api/chat

Send a question about a P&ID and receive a streaming response via Server-Sent Events (SSE). The system uses Graph-RAG to retrieve relevant context from the Knowledge Graph before calling the LLM.

**Request**: `application/json`

```json
{
  "pid_id": "test-simple",
  "message": "What is the main process flow?",
  "history": [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous answer"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pid_id` | string | Yes | Identifier of the P&ID to query |
| `message` | string | Yes | The user's question |
| `history` | array | No | Previous conversation turns for context (default: empty) |

Each item in `history` has:

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | `"user"` or `"assistant"` |
| `content` | string | The message text |

**Response** `200 OK`: `text/event-stream` (SSE)

The stream emits events in this format:

```
data: {"delta": "The main"}

data: {"delta": " process flow"}

data: {"delta": " goes from T-101..."}

data: {"done": true, "full_response": "The main process flow goes from T-101..."}
```

- **Delta events**: partial text chunks as the LLM generates them
- **Done event**: signals completion with the full concatenated response
- **Error event**: `{"error": "error message"}` if the LLM call fails

**Errors**:

| Status | Condition |
|--------|-----------|
| `500` | ANTHROPIC_API_KEY not configured, or graph retrieval failed |

**Example** (curl):

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"pid_id": "test-simple", "message": "What is the main process flow?"}'
```

### Graph-RAG Strategy Selection

The system automatically selects which portion of the Knowledge Graph to retrieve based on the question:

| Question Pattern | Strategy | Graph Used |
|-----------------|----------|------------|
| Contains a tag number (e.g., P-101) | Tag neighbourhood | 2-hop neighbourhood of the tag in detailed graph |
| Contains flow/process keywords | Condensed view | Full condensed (equipment-level) graph |
| Contains control/loop keywords | Condensed view | Condensed graph with instrument context |
| Default (no match) | Condensed view | Full condensed graph |

---

## Validation

### POST /api/validate

Upload a `.drawio` file and receive a list of validation findings.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The .drawio file to validate |

**Response** `200 OK`:

```json
{
  "errors": [
    {
      "shape_id": "42",
      "error_type": "missing_tag",
      "message": "CentrifugalPump (id=42) has no tag_number"
    },
    {
      "shape_id": "55",
      "error_type": "missing_line_number",
      "message": "Piping segment (id=55, label='') has no line_number"
    }
  ],
  "total": 2
}
```

An empty `errors` array and `total: 0` means the P&ID passed all checks.

**Validation checks performed**:

| Error Type | Description |
|-----------|-------------|
| `missing_tag` | Equipment or instrument without a `tag_number` |
| `missing_line_number` | Piping segment (ProcessLine, UtilityLine, PipingNetworkSegment) without `line_number` |
| `unconnected_nozzle` | Nozzle not referenced by any piping segment connection |
| `orphan_instrument` | Instrument not connected by any signal line or control loop |
| `duplicate_tag` | Multiple elements sharing the same `tag_number` |

**Errors**:

| Status | Condition |
|--------|-----------|
| `400` | No filename provided or empty file |
| `422` | Validation failed (parsing error in the file itself) |

**Example** (curl):

```bash
curl -X POST http://localhost:8000/api/validate \
  -F "file=@my-pid.drawio"
```

---

## Configuration

The API reads configuration from environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (empty) | Claude API key. Required for `/api/chat` |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | (empty) | Neo4j password |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum upload file size in MB |

## CORS

The API includes CORS middleware. The `CORS_ORIGINS` variable accepts a comma-separated list of allowed origins:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

All HTTP methods and headers are allowed for the configured origins.
