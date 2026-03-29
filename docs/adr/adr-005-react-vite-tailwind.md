# ADR-005: React con Vite + Tailwind para web UI

## Estado

Aceptada

## Contexto

El ingeniero de procesos necesita una interfaz visual para consultar P&IDs. No un CLI. La interfaz debe soportar chat con LLM, visualizacion interactiva del Knowledge Graph, y referencia visual del P&ID.

## Decision

React 18+ con Vite, Tailwind CSS, Zustand para estado, TanStack Query para data fetching. El package vive en `packages/pid-web/`.

Componentes principales:

- Chat con LLM (streaming via SSE)
- Visualizacion del Knowledge Graph (Cytoscape.js)
- Visor/referencia de P&ID
- Componentes compartidos (layout, formularios)

## Consecuencias

### Positivas

- Ecosistema maduro con amplia documentacion
- Claude Code genera React con alta calidad
- Vite acelera el desarrollo con HMR rapido

### Negativas

- Mas setup que Streamlit, pero mucho mas flexible para la UI de chat + grafo interactivo
