# Web UI Guide

The P&ID Inteligente web interface lets process engineers upload P&ID diagrams, explore the Knowledge Graph visually, and ask questions in natural language through the LLM assistant powered by Graph-RAG.

## Accessing the Web UI

| Setup | URL |
|-------|-----|
| Docker (production) | http://localhost:3000 |
| Local development (Vite) | http://localhost:5173 |

The Web UI requires the API backend running at http://localhost:8000. In Docker this is handled automatically; for local development, start the API first (see [Getting Started](getting-started.md)).

## Uploading a P&ID

### Drag and Drop

1. Open the Web UI in your browser
2. Drag a `.drawio` or `.xml` (DEXPI Proteus) file onto the upload area
3. The system processes the file:
   - Parses the Draw.io/DEXPI structure
   - Builds the Knowledge Graph (detailed and condensed)
   - Loads it into Neo4j
4. A summary appears showing the number of nodes, edges, equipment, and instruments

### Click to Browse

Click the upload area to open a file browser and select your `.drawio` or `.xml` file.

### Test File

For a quick test, use the included example:

```
packages/drawio-library/examples/test-simple.drawio
```

This file contains a tank (T-101), pump (P-101), control valve (TCV-101), and heat exchanger (HE-101) with a temperature control loop.

## Tabs

The interface has two main views, accessible via tabs:

### P&ID Tab (Draw.io Viewer)

Displays the uploaded P&ID diagram in an embedded Draw.io viewer. This gives you a visual reference of the original diagram while you interact with the graph and chat.

Features:
- Zoom and pan to navigate the diagram
- The diagram renders using the same Draw.io engine, preserving all symbols and layout
- Useful as a reference when the LLM mentions specific equipment or instruments by tag number

### Knowledge Graph Tab (Cytoscape.js)

Displays the condensed Knowledge Graph as an interactive node-link diagram powered by Cytoscape.js.

Features:
- **Nodes** represent equipment (tanks, pumps, exchangers, etc.)
- **Edges** represent process flow (directed arrows) and control relationships
- **Zoom**: mouse wheel or pinch
- **Pan**: click and drag on empty space
- **Select**: click on a node or edge to see its details
- **Layout**: the graph is laid out automatically; nodes can be dragged to new positions

## Chat

The Chat panel provides a conversational interface to the LLM assistant. It uses Server-Sent Events (SSE) for streaming responses, so you see the answer being generated in real time.

### How It Works

1. You type a question about the uploaded P&ID
2. The system selects the relevant portion of the Knowledge Graph (Graph-RAG):
   - Mentions of a specific tag (e.g., "P-101") fetch that tag's neighborhood
   - Questions about flow or process use the condensed graph
   - Questions about control loops use relevant instrument subgraphs
3. The retrieved graph context is sent to Claude along with your question
4. Claude responds based on the actual P&ID data

### Types of Questions That Work Well

#### Process flow questions

- "What is the main process flow?"
- "Trace the path from T-101 to HE-101"
- "What equipment does fluid pass through after leaving the pump?"

#### Equipment-specific questions

- "What are the design conditions for P-101?"
- "What nozzles does T-101 have?"
- "What is the material of construction of HE-101?"

#### Control loop questions

- "What controls the temperature at HE-101?"
- "Describe the TIC-101 control loop"
- "What is the final control element for the temperature loop?"

#### Design review questions

- "Are there any equipment without safety valves?"
- "Are there orphan instruments?"
- "Are there any lines without line numbers?"

#### Overview questions

- "Give me a summary of this P&ID"
- "How many equipment items are in this diagram?"
- "List all the control loops"

### Tips for Better Answers

- **Use tag numbers**: "What is connected to P-101?" gives more precise results than "What is connected to the pump?"
- **Be specific**: "What is the design pressure of T-101?" works better than "Tell me about the tank"
- **Ask about what is in the P&ID**: The LLM only answers based on the Knowledge Graph data. It will explicitly say when data is insufficient.
- **Conversation history**: Previous messages are sent as context, so follow-up questions work (e.g., "What about its outlet nozzle?" after asking about an equipment)

## Detail Panel

Clicking on a node in the Knowledge Graph tab opens a detail panel showing:

- **Tag number**: The ISA tag identifier
- **DEXPI class**: The element type (e.g., CentrifugalPump)
- **Label**: Human-readable description
- **Design conditions**: Pressure, temperature, capacity, material
- **Connections**: List of directly connected nodes with relationship types

## Stack

| Technology | Role |
|-----------|------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool and dev server |
| Tailwind CSS | Styling |
| Zustand | State management |
| TanStack Query | Data fetching and caching |
| Cytoscape.js | Graph visualization |
| SSE | Streaming chat responses |

## Development

```bash
cd packages/pid-web

npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:5173)
npm run build        # Production build
npm test             # Run tests (Vitest)
npm run lint         # Run ESLint
npm run format       # Run Prettier
```
