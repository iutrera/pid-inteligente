# ADR-001: Monorepo con packages separados

## Estado

Aceptada

## Contexto

El proyecto tiene componentes en Python y TypeScript con ciclos de vida diferentes. Necesitamos que Agent Teams pueda asignar ownership claro por carpeta.

## Decision

Monorepo con estructura `packages/` donde cada package es independiente (su propio `pyproject.toml` o `package.json`), pero comparten configuracion raiz.

Los packages son:

- `packages/drawio-library/` -- Biblioteca de simbolos P&ID para Draw.io
- `packages/pid-converter/` -- Conversor bidireccional Draw.io <-> DEXPI (Python)
- `packages/pid-knowledge-graph/` -- Knowledge Graph builder (Python)
- `packages/pid-rag/` -- FastAPI backend con Graph-RAG (Python)
- `packages/pid-web/` -- Interfaz web React (TypeScript)
- `packages/pid-mcp-server/` -- MCP server orquestador (TypeScript)

## Consecuencias

### Positivas

- Ownership claro por teammate: cada package tiene un unico propietario
- CI unificado: un solo repositorio con workflows compartidos
- Refactoring atomico entre packages: cambios cross-cutting en un solo commit

### Negativas

- Tooling de monorepo mas complejo que multi-repo (dos ecosistemas: Python + TypeScript)
