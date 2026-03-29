# MCP Server Guide

The P&ID Inteligente MCP (Model Context Protocol) server exposes P&ID tools to AI assistants like Claude. This allows an AI to convert diagrams, build Knowledge Graphs, query P&IDs in natural language, and validate designs -- all through conversational interaction.

## What Is MCP?

MCP (Model Context Protocol) is an open standard for connecting AI assistants to external tools and data sources. Instead of the AI calling REST APIs directly, it uses a structured tool-calling protocol over stdio or HTTP transport.

In P&ID Inteligente, the MCP server acts as a bridge between an AI client (like Claude Desktop or Claude Code) and the pid-rag backend API. The AI describes what it wants to do in natural language, and the MCP server translates that into the appropriate API calls.

## Setup

### Prerequisites

- Node.js 20+
- The pid-rag API backend running at http://localhost:8000 (or another URL)
- Neo4j running (the API needs it)

### Build the MCP Server

```bash
cd packages/pid-mcp-server
npm install
npm run build
```

### Configure in Claude Desktop

Add the following to your Claude Desktop MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pid-inteligente": {
      "command": "node",
      "args": ["<absolute-path-to>/packages/pid-mcp-server/dist/index.js"],
      "env": {
        "PID_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

Replace `<absolute-path-to>` with the full path to your project directory.

### Configure in Claude Code

Add to your `.claude/settings.local.json` or project settings:

```json
{
  "mcpServers": {
    "pid-inteligente": {
      "command": "node",
      "args": ["packages/pid-mcp-server/dist/index.js"],
      "env": {
        "PID_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Using Docker

If you started the stack with `docker-compose up`, the MCP server runs automatically inside the `mcp` container. It connects to the API via the Docker internal network (`http://api:8000`). To use it from a local MCP client, you still need the local configuration above pointing to the host-accessible API at `http://localhost:8000`.

## Available Tools

The MCP server exposes 6 tools:

### convert_drawio_to_dexpi

Convert a Draw.io P&ID file to DEXPI Proteus XML format.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `drawio_path` | string | Absolute path to the .drawio file |

**Returns**: Confirmation with input/output paths and file size. The converted XML file is written next to the input file with `.xml` extension.

### convert_dexpi_to_drawio

Convert a DEXPI Proteus XML file to Draw.io format for editing.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `dexpi_path` | string | Absolute path to the DEXPI .xml file |

**Returns**: Confirmation with input/output paths. The converted .drawio file is written next to the input file.

### build_knowledge_graph

Build a Knowledge Graph from a P&ID file and load it into Neo4j.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to the P&ID file (.drawio or .xml) |
| `pid_id` | string | No | Identifier for this P&ID. Auto-generated from filename if omitted |

**Returns**: Statistics about the built graph (node count, edge count, equipment count, instrument count).

### query_pid

Ask a question about a P&ID in natural language. Uses Graph-RAG to retrieve relevant context from the Knowledge Graph and answers using Claude.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `pid_id` | string | Identifier of the P&ID to query |
| `question` | string | Natural language question about the P&ID |

**Returns**: The LLM's answer based on the Knowledge Graph data.

### get_graph

Get the Knowledge Graph data for a P&ID as a structured summary of nodes and edges.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pid_id` | string | Yes | Identifier of the P&ID |
| `detailed` | boolean | No (default: false) | If true, returns the full detailed graph instead of the condensed view |

**Returns**: Summary with node types, edge types, counts, and (if detailed) full node/edge listing.

### validate_pid

Validate a Draw.io P&ID file for common design errors.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `drawio_path` | string | Absolute path to the .drawio file to validate |

**Returns**: Validation report grouped by error type, or confirmation that no errors were found.

## Example Conversation

Here is an example of how an AI assistant uses the MCP tools in a conversation:

---

**User**: I have a P&ID file at `/home/user/projects/plant-a/pid-100.drawio`. Can you analyze it?

**Assistant** *(uses `build_knowledge_graph`)*:

I've built the Knowledge Graph from your P&ID. Here are the statistics:
- P&ID ID: pid-100
- Nodes: 24
- Edges: 31
- Equipment: 6
- Instruments: 4

**User**: What's the main process flow?

**Assistant** *(uses `query_pid` with question "What is the main process flow?")*:

Based on the Knowledge Graph, the main process flow is:

T-101 (Feed Tank) --> P-101 (Feed Pump) --> HE-101 (Preheater) --> R-101 (Reactor) --> HE-102 (Product Cooler) --> T-102 (Product Tank)

The feed enters T-101, is pumped by P-101 through heat exchanger HE-101 where it is preheated, then enters reactor R-101. The product exits the reactor, passes through cooler HE-102, and is stored in T-102.

**User**: Are there any design issues?

**Assistant** *(uses `validate_pid`)*:

The validation found 2 issues:

1. **missing_line_number** (1): Piping segment between P-101 and HE-101 has no line number
2. **orphan_instrument** (1): Instrument PAH-101 (id=45) is not connected to any signal line

I recommend adding a line number to the piping segment and connecting the pressure alarm PAH-101 to the appropriate signal line.

**User**: Convert this to DEXPI format.

**Assistant** *(uses `convert_drawio_to_dexpi`)*:

Done. The DEXPI Proteus XML has been written to `/home/user/projects/plant-a/pid-100.xml` (12,340 bytes).

---

## Development

```bash
cd packages/pid-mcp-server

npm install          # Install dependencies
npm run dev          # Development with watch (tsx)
npm run build        # Compile TypeScript
npm start            # Run compiled server
npm test             # Run tests (Vitest)
npm run lint         # Run ESLint
npm run format       # Run Prettier
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PID_API_URL` | `http://localhost:8000` | Base URL of the pid-rag API backend |
