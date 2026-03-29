# P&ID Inteligente — Puente Draw.io ↔ DEXPI con LLM

## Contexto

P&ID Inteligente es una arquitectura open-source que permite dibujar P&IDs (Piping & Instrumentation Diagrams) en Draw.io con metadatos semanticos DEXPI, convertirlos bidireccionalmente a formato DEXPI Proteus XML, construir un Knowledge Graph en Neo4j, y consultar/razonar sobre el proceso mediante un LLM con Graph-RAG.

El sistema tiene 5 capas: Biblioteca Draw.io (simbolos P&ID) → Conversor bidireccional (mxGraph XML ↔ Proteus XML) → Knowledge Graph (pyDEXPI → NetworkX → Neo4j) → Interfaz LLM (FastAPI + React + Graph-RAG) → Orquestacion MCP (TypeScript MCP Server).

El stack es open-source: Draw.io (Apache 2.0), pyDEXPI (MIT), Neo4j, React, FastAPI. El LLM usa Claude API.

## Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| Frontend: Biblioteca P&ID | Draw.io + XML custom shapes con metadatos DEXPI |
| Frontend: Web UI | React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query |
| Backend: Conversor | Python 3.11+ (lxml, pyDEXPI, Pydantic v2, Typer CLI) |
| Backend: API | FastAPI + Anthropic SDK + SSE streaming |
| Base de Datos | Neo4j 5+ (driver oficial async) + NetworkX (intermedio) |
| MCP Server | TypeScript + @modelcontextprotocol/sdk + drawio-mcp-server (Gazo) |
| Linting | Ruff (Python), ESLint + Prettier (TypeScript) |
| Testing | pytest + pytest-cov (Python), Vitest (TypeScript), Playwright (E2E) |
| Infra | Docker + docker-compose + GitHub Actions |

## Ownership de Archivos

| Carpeta | Propietario | Notas |
|---------|------------|-------|
| `packages/drawio-library/` | Frontend | Biblioteca de ~60 simbolos P&ID |
| `packages/pid-converter/` | Backend | Parser, mapper, topologia, serializer, importer, validator |
| `packages/pid-knowledge-graph/` | Base de Datos | Graph builder, condensacion, semantica, Neo4j store |
| `packages/pid-rag/` | Backend | FastAPI, Graph-RAG, system prompts |
| `packages/pid-web/` | Frontend | React web UI |
| `packages/pid-mcp-server/` | Integraciones | MCP Server TypeScript |
| `docker/`, `docker-compose.*` | DevOps | Contenedores y orquestacion |
| `.github/workflows/` | DevOps | CI/CD |
| `e2e/` | Testing | Tests end-to-end |
| `docs/adr/` | Arquitecto | Decisions records |
| `docs/` (resto) | Documentacion | Guias, API docs |

## Convenciones Clave

### Python
- snake_case para variables, funciones, archivos
- PascalCase para clases
- Type hints obligatorias en funciones publicas
- Linter: Ruff (line-length 100)

### TypeScript
- camelCase para variables/funciones
- PascalCase para componentes React, clases, interfaces
- ESLint + Prettier (semi, double quotes, trailing commas)

### Commits
```
tipo(alcance): descripcion en imperativo
Tipos: feat, fix, docs, style, refactor, test, chore, ci
Alcances: converter, kg, rag, web, mcp, library, docker, ci, docs, e2e
```

### XML/Draw.io
- Atributos DEXPI con prefijo `dexpi_` (ej: `dexpi_class="CentrifugalPump"`)
- Tag numbers formato ISA: `P-101`, `TIC-201`, `HE-301`

## Verificacion Obligatoria

Antes de completar cualquier tarea:

```bash
# Python
ruff check .
python -m pytest tests/ -v --cov --cov-report=term-missing

# TypeScript
npx eslint .
npm run build && npm run test

# Comando especifico de tu scope (ver specs/07_estandares.md)
```

Umbrales minimos:
- Cobertura: >80%
- Lint errors: 0
- Build errors: 0

## Archivos Compartidos — COORDINAR ANTES DE EDITAR

| Archivo | Regla |
|---------|-------|
| `CLAUDE.md` | Solo el Lead modifica |
| `packages/pid-rag/src/pid_rag/api/routes/` | Backend posee. Si cambia un endpoint, notifica a Frontend e Integraciones |
| `packages/pid-web/src/types/` | Frontend posee. Backend informa si cambia shape de respuesta |
| `docker-compose.yml` | DevOps posee. Otros solicitan cambios |
| `docker/neo4j/init.cypher` | Base de Datos define schema, DevOps integra |

## Estandares de Ingenieria P&ID

- Simbologia: ISA 5.1 (Instrumentation Symbols and Identification)
- Diagramas: ISO 10628 (Diagrams for chemical and petrochemical industry)
- Intercambio: DEXPI Proteus XML Schema
- Modelo de datos: ISO 15926 (via pyDEXPI)
- Subconjunto DEXPI: Equipment, PipingComponents, PipingNetworkSegment/System, InstrumentationLoop, Nozzle, SignalLine

## Specs

Documentacion completa de planificacion en `/specs/`:
- `01_discovery.md` — Vision y problema
- `02_producto.md` — Funcionalidades MVP y alcance
- `03_restricciones.md` — Recursos y normativa
- `04_arquitectura.md` — Stack, ADRs, estructura de modulos
- `05_equipo.md` — Teammates, scopes, spawn prompts
- `06_pipeline.md` — Oleadas de ejecucion con checkpoints
- `07_estandares.md` — Convenciones, testing, verificacion

## Pipeline de Oleadas

| Oleada | Teammates | Foco |
|--------|-----------|------|
| 1 — Setup & Biblioteca | Arquitecto + DevOps + Frontend | Scaffolding, CI/Docker, ~60 simbolos P&ID |
| 2 — Core Data | Backend + Base de Datos | Conversor bidireccional, Knowledge Graph + Neo4j |
| 3 — API + UI + MCP | Backend + Frontend + Integraciones + Testing | FastAPI, React UI, MCP Server, tests integracion |
| 4 — Cierre | Testing + Documentacion + DevOps | E2E, docs, deploy pipeline |

Prompts del Lead para cada oleada en `/prompts/`.
