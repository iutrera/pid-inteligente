# ADR-004: FastAPI como capa API unificada

## Estado

Aceptada

## Contexto

React frontend, MCP server (TypeScript), y posibles clientes externos necesitan acceder al conversor, Knowledge Graph y RAG. Se necesita un punto de entrada unico para todas las operaciones del backend Python.

## Decision

FastAPI expone una API REST unificada en `packages/pid-rag/`. Todos los consumidores pasan por ella.

Los endpoints principales son:

- `/api/convert/*` -- Conversion Draw.io <-> DEXPI
- `/api/graph/*` -- Operaciones sobre el Knowledge Graph
- `/api/chat/*` -- Consultas LLM con Graph-RAG (SSE streaming)
- `/api/validate/*` -- Validacion de P&IDs

## Consecuencias

### Positivas

- Un unico punto de entrada para todos los consumidores
- OpenAPI auto-generado (documentacion automatica de la API)
- Pydantic compartido con pyDEXPI (consistencia de modelos)

### Negativas

- Latencia adicional para MCP -> HTTP -> Python (aceptable para el caso de uso)
