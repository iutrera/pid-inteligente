# ADR-002: TypeScript para MCP orquestador

## Estado

Aceptada

## Contexto

El MCP SDK es TypeScript-first. El drawio-mcp-server de Gazo es TypeScript. El frontend es React/TypeScript. El conversor y Knowledge Graph son Python.

Se necesita decidir el lenguaje del MCP server que orquesta las herramientas de P&ID Inteligente.

## Decision

MCP server en TypeScript (`packages/pid-mcp-server/`). Se comunica con el backend Python via HTTP (FastAPI).

Las tools expuestas por el MCP server son:

- `convert-drawio-dexpi` -- Conversion Draw.io a DEXPI
- `import-dexpi-drawio` -- Importacion DEXPI a Draw.io
- `query-knowledge-graph` -- Consultas al Knowledge Graph
- `validate-pid` -- Validacion de P&ID
- `draw-pid` -- Dibujo de P&ID via Gazo (drawio-mcp-server)

## Consecuencias

### Positivas

- Alineado con ecosistema MCP (SDK oficial TypeScript)
- Integracion natural con drawio-mcp-server de Gazo
- Separacion clara de capas: datos (Python) y orquestacion (TypeScript)

### Negativas

- Dos lenguajes en el proyecto requieren dos stacks de tooling (Ruff + ESLint/Prettier)
