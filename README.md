# P&ID Inteligente

Arquitectura open-source para dibujar P&IDs en Draw.io con metadatos DEXPI, convertirlos bidireccionalmente al estandar DEXPI Proteus XML, y consultar el proceso mediante un LLM con Graph-RAG sobre un Knowledge Graph en Neo4j.

## Arquitectura

```
         Draw.io                    Web UI (React)              MCP Client
            |                            |                          |
            | .drawio XML                | HTTP/SSE                 | MCP
            |                            |                          |
    --------v----------------------------v--------------------------v--------
    |                        FastAPI (pid-rag)                             |
    |   pid-converter            Graph-RAG              pid-mcp-server    |
    |   (Python)                 + Claude API            (TypeScript)     |
    |       |                        |                        |           |
    |   ----v------------------------v------------------------v------     |
    |   |           pid-knowledge-graph (Python)                   |     |
    |   |   pyDEXPI → NetworkX → Neo4j                             |     |
    |   -------------------------------------------------------    |     |
    ----------------------------------------------------------------     |
                            |                                            |
                       Neo4j 5+                                Claude API
```

## Quick Start

### 1. Clonar y configurar

```bash
git clone <repo-url> pid-inteligente
cd pid-inteligente
cp .env.example .env
# Editar .env y añadir tu ANTHROPIC_API_KEY
```

### 2. Levantar con Docker

```bash
docker-compose up
```

Esto inicia Neo4j, la API (FastAPI), la Web UI (React) y el MCP Server. Espera a que todos los servicios reporten estar listos.

### 3. Usar

- **Web UI**: http://localhost:3000 — sube un P&ID y haz preguntas
- **Neo4j Browser**: http://localhost:7474 — explora el Knowledge Graph (user: `neo4j`, password: `pidinteligente`)
- **API Swagger**: http://localhost:8000/docs — documentacion OpenAPI interactiva

### 4. Primer uso rapido

1. Abre http://localhost:3000
2. Arrastra el archivo `packages/drawio-library/examples/test-simple.drawio` sobre la zona de upload
3. Cambia a la tab **Knowledge Graph** para ver el grafo interactivo
4. Cambia a la tab **Chat** y pregunta: "What is the main process flow?"

Ver la [guia completa de Getting Started](docs/guides/getting-started.md) para mas detalles y troubleshooting.

## Estructura del Monorepo

```
pid-inteligente/
├── packages/
│   ├── drawio-library/          ← Biblioteca ~60 simbolos P&ID para Draw.io
│   ├── pid-converter/           ← Conversor bidireccional Draw.io ↔ DEXPI
│   ├── pid-knowledge-graph/     ← Knowledge Graph: pyDEXPI → Neo4j
│   ├── pid-rag/                 ← FastAPI + Graph-RAG + Claude API
│   ├── pid-web/                 ← React web UI
│   └── pid-mcp-server/         ← MCP Server (TypeScript)
├── docker/                      ← Dockerfiles
├── e2e/                         ← Tests end-to-end (Playwright)
├── docs/                        ← Documentacion
├── specs/                       ← Especificaciones de planificacion
├── prompts/                     ← Prompts por oleada (Agent Teams)
├── docker-compose.yml           ← Stack completo
└── CLAUDE.md                    ← Contexto compartido para Agent Teams
```

## Uso sin Docker

### Conversor (CLI)

```bash
cd packages/pid-converter
pip install -e ".[dev]"

# Convertir Draw.io a DEXPI
pid-converter convert input.drawio -o output.xml

# Importar DEXPI a Draw.io
pid-converter import input.xml -o output.drawio

# Validar P&ID
pid-converter validate input.drawio
```

### API

```bash
cd packages/pid-rag
pip install -e ".[dev]"
uvicorn pid_rag.api.app:app --reload
```

### Web UI

```bash
cd packages/pid-web
npm install
npm run dev
```

## Biblioteca Draw.io

Cargar la biblioteca P&ID en Draw.io:

1. Abrir Draw.io (desktop o web)
2. File → Open Library from → URL (o Device para archivo local)
3. Pegar la URL del archivo `packages/drawio-library/pid-library.xml`

Los 62 simbolos incluyen metadatos DEXPI embebidos: arrastrar al canvas, rellenar `tag_number` y condiciones de diseno. Ver la [guia de la biblioteca](docs/guides/drawio-library.md) para la lista completa de simbolos y ejemplos.

## Visor Draw.io Integrado

La Web UI incluye un visor Draw.io embebido en la tab **P&ID** que renderiza el diagrama original. Al subir un archivo `.drawio`, el diagrama se muestra junto al Knowledge Graph y el chat, permitiendo navegar visualmente mientras se hacen preguntas al LLM. El visor soporta zoom y pan, y se actualiza automaticamente al subir un nuevo archivo.

## Documentacion

- [Getting Started](docs/guides/getting-started.md) — De cero a consultar un P&ID
- [Biblioteca Draw.io](docs/guides/drawio-library.md) — 62 simbolos, capas, convenciones ISA
- [Conversor](docs/guides/converter.md) — CLI y API programatica para Draw.io ↔ DEXPI
- [Knowledge Graph](docs/guides/knowledge-graph.md) — Grafos, Neo4j, queries Cypher
- [Web UI](docs/guides/web-ui.md) — Chat, grafo interactivo, visor Draw.io
- [MCP Server](docs/guides/mcp-server.md) — 6 tools para AI assistants
- [API Reference](docs/api/endpoints.md) — Todos los endpoints REST documentados

## Desarrollo con Agent Teams

Este proyecto esta configurado para desarrollo con Claude Code Agent Teams. Los prompts para cada oleada estan en `/prompts/`.

### Lanzar Oleada 1 (Setup & Biblioteca)

1. Abrir Claude Code en el directorio del proyecto
2. Copiar el contenido de `prompts/oleada-1-setup.md`
3. Pegar como prompt — el Lead coordinara los teammates

Ver `specs/06_pipeline.md` para el pipeline completo y `specs/05_equipo.md` para los spawn prompts detallados.

## Stack Tecnologico

| Componente | Tecnologia |
|-----------|-----------|
| Editor P&ID | Draw.io (Apache 2.0) |
| Modelo DEXPI | pyDEXPI (MIT) |
| Conversor | Python + lxml |
| Knowledge Graph | Neo4j 5+ |
| API | FastAPI |
| LLM | Claude API |
| Web UI | React + Vite + Tailwind |
| MCP | TypeScript + MCP SDK |
| CI/CD | GitHub Actions |
| Contenedores | Docker |

## Licencia

Por definir.
