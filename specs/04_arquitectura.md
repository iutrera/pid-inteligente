# Arquitectura Técnica: P&ID Inteligente

## Visión General

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUARIO / AGENTE IA                         │
│                                                                     │
│   Draw.io (desktop/web)          Web UI (React)         MCP Client │
│         │                            │                       │      │
└─────────┼────────────────────────────┼───────────────────────┼──────┘
          │                            │                       │
          │ .drawio XML                │ HTTP/WS               │ MCP
          │                            │                       │
┌─────────▼────────────────────────────▼───────────────────────▼──────┐
│                         CAPA DE SERVICIOS                           │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │  pid-converter│  │   pid-rag    │  │    pid-mcp-server (TS)    │ │
│  │   (Python)   │  │  (Python)    │  │                           │ │
│  │              │  │              │  │  Tools:                   │ │
│  │ • parser     │  │ • FastAPI    │  │  • convert-drawio-dexpi   │ │
│  │ • mapper     │  │ • retrieval  │  │  • import-dexpi-drawio    │ │
│  │ • topology   │  │ • prompts    │  │  • query-knowledge-graph  │ │
│  │ • serializer │  │ • graph-rag  │  │  • validate-pid           │ │
│  │ • importer   │  │              │  │  • draw-pid (via Gazo)    │ │
│  │ • validator  │  │              │  │                           │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────────┬─────────────┘ │
│         │                 │                         │               │
│  ┌──────▼─────────────────▼─────────────────────────▼─────────────┐ │
│  │              pid-knowledge-graph (Python)                      │ │
│  │                                                                │ │
│  │  • graph_builder (pyDEXPI → NetworkX)                         │ │
│  │  • condensation (grafo alto nivel)                            │ │
│  │  • semantic (etiquetas para LLM)                              │ │
│  │  • neo4j_store (persistencia)                                 │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
│                           │                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                   ┌────────▼────────┐       ┌──────────────┐
                   │     Neo4j       │       │  Claude API   │
                   │  (Knowledge     │       │  (LLM SaaS)   │
                   │   Graph DB)     │       │               │
                   └─────────────────┘       └──────────────┘
```

## Stack Tecnológico

### Frontend (Web UI)

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Framework | React 18+ con TypeScript | Ecosistema maduro, tipado fuerte, amplia documentación para Claude Code |
| Bundler | Vite | Rápido en dev, buen tree-shaking en producción |
| Estilos | Tailwind CSS | Utility-first, prototipado rápido, sin overhead de componentes UI pesados |
| Estado | Zustand | Ligero, sin boilerplate, suficiente para la complejidad del MVP |
| HTTP client | TanStack Query (React Query) | Cache, retry, invalidation automática para las llamadas a la API |
| Chat UI | Componentes custom | La interfaz de consulta LLM necesita control fino (streaming, grafos inline, referencias a equipos) |
| Visualización de grafos | Cytoscape.js o React Flow | Para mostrar el Knowledge Graph interactivamente |

### Backend (API + RAG)

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Framework API | FastAPI (Python) | Async nativo, OpenAPI auto-generado, tipado con Pydantic — alinea con pyDEXPI |
| Serialización | Pydantic v2 | Ya es la base de pyDEXPI; consistencia de modelos en todo el backend |
| LLM SDK | Anthropic Python SDK | Acceso a Claude API con streaming |
| Graph-RAG | Custom sobre Neo4j + Cypher | Queries específicas por tipo de pregunta (flujo, equipo, lazo de control) |
| Streaming | SSE (Server-Sent Events) | Para respuestas LLM en tiempo real hacia el frontend |
| Task runner | Celery o background tasks de FastAPI | Para conversiones largas (P&IDs grandes) |

### Conversor (Python Package)

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| XML parsing | lxml | Rendimiento y XPath para mxGraph XML y Proteus XML |
| Modelo DEXPI | pyDEXPI (Pydantic) | Modelo canónico del estándar |
| Grafos intermedios | NetworkX | Ya integrado en pyDEXPI para topología |
| CLI | Click o Typer | CLI ergonómico para el conversor standalone |
| Validación | Custom + esquema XSD DEXPI | Validación estructural + reglas de negocio |

### Knowledge Graph

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Base de datos | Neo4j 5+ | Grafo nativo, Cypher potente, visualización integrada en browser |
| Driver Python | neo4j (oficial) | Mantenido por Neo4j, async support, mejor documentado que py2neo |
| Grafo en memoria | NetworkX | Para operaciones intermedias y condensación antes de persistir |
| Migraciones | Custom (scripts Cypher) | Constraints, índices y esquema base |

### MCP Server (TypeScript)

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Runtime | Node.js 20+ | Estándar para MCP servers |
| MCP SDK | @modelcontextprotocol/sdk | SDK oficial TypeScript |
| Draw.io MCP | drawio-mcp-server (Gazo) | Integración con Draw.io ya resuelta |
| Comunicación con Python | HTTP (FastAPI) | El MCP server llama a la API FastAPI para conversión, KG y RAG |

### Infraestructura

| Componente | Servicio | Justificación |
|-----------|---------|---------------|
| Contenedores | Docker + docker-compose | Dev local unificado: Neo4j + FastAPI + React + MCP |
| Distribución Python | pip (PyPI) | Para instalar pid-converter y pid-knowledge-graph standalone |
| Distribución Docker | docker-compose.yml | Para levantar todo el stack con un comando |
| CI/CD | GitHub Actions | Estándar, gratuito para open-source |
| Linting Python | Ruff | Rápido, reemplaza flake8+isort+black |
| Linting TypeScript | ESLint + Prettier | Estándar del ecosistema |
| Testing Python | pytest + pytest-cov | Estándar, buena integración con FastAPI |
| Testing TypeScript | Vitest | Alineado con Vite, rápido |
| E2E | Playwright | Multi-browser, buena API, soporta React |

## ADRs (Architecture Decision Records)

### ADR-001: Monorepo con packages separados
- **Estado**: Aceptada
- **Contexto**: El proyecto tiene componentes en Python y TypeScript con ciclos de vida diferentes. Necesitamos que Agent Teams pueda asignar ownership claro por carpeta.
- **Decisión**: Monorepo con estructura `packages/` donde cada package es independiente (su propio `pyproject.toml` o `package.json`), pero comparten configuración raíz.
- **Consecuencias**: (+) Ownership claro por teammate, (+) CI unificado, (+) refactoring atómico entre packages, (-) Tooling de monorepo más complejo que multi-repo.

### ADR-002: TypeScript para MCP orquestador
- **Estado**: Aceptada
- **Contexto**: El MCP SDK es TypeScript-first. El drawio-mcp-server de Gazo es TypeScript. El frontend es React/TypeScript. El conversor y KG son Python.
- **Decisión**: MCP server en TypeScript. Se comunica con el backend Python vía HTTP (FastAPI).
- **Consecuencias**: (+) Alineado con ecosistema MCP, (+) integración natural con drawio-mcp-server, (+) separa capas de datos (Python) y orquestación (TS), (-) Dos lenguajes en el proyecto requieren dos stacks de tooling.

### ADR-003: Neo4j como store obligatorio del Knowledge Graph
- **Estado**: Aceptada
- **Contexto**: El usuario trabaja con P&IDs grandes. NetworkX en memoria no escala para persistencia ni queries complejas multi-sesión.
- **Decisión**: Neo4j como store principal. NetworkX se usa como formato intermedio para construcción y condensación antes de persistir.
- **Consecuencias**: (+) Queries Cypher potentes para Graph-RAG, (+) persistencia entre sesiones, (+) visualización nativa en Neo4j Browser, (-) Dependencia de infraestructura (mitigada con Docker).

### ADR-004: FastAPI como capa API unificada
- **Estado**: Aceptada
- **Contexto**: React frontend, MCP server (TS), y posibles clientes externos necesitan acceder al conversor, KG y RAG.
- **Decisión**: FastAPI expone una API REST unificada. Todos los consumidores pasan por ella.
- **Consecuencias**: (+) Un único punto de entrada, (+) OpenAPI auto-generado, (+) Pydantic compartido con pyDEXPI, (-) Latencia adicional para MCP → HTTP → Python.

### ADR-005: React con Vite + Tailwind para web UI
- **Estado**: Aceptada
- **Contexto**: El ingeniero de procesos necesita una interfaz visual para consultar P&IDs. No un CLI.
- **Decisión**: React 18+ con Vite, Tailwind CSS, Zustand, TanStack Query.
- **Consecuencias**: (+) Ecosistema maduro, (+) Claude Code genera React con alta calidad, (+) Vite acelera dev, (-) Más setup que Streamlit, pero mucho más flexible para la UI de chat + grafo.

### ADR-006: Distribución dual (pip + Docker)
- **Estado**: Aceptada
- **Contexto**: Diferentes usuarios tienen diferentes necesidades: un desarrollador quiere `pip install`, un ingeniero quiere `docker-compose up`.
- **Decisión**: Los packages Python se publican en PyPI. El stack completo se distribuye como docker-compose.
- **Consecuencias**: (+) Flexibilidad máxima, (+) pip para uso programático del conversor, (+) Docker para stack completo, (-) Doble pipeline de distribución.

## Estructura de Módulos y Ownership

```
pid-inteligente/
├── CLAUDE.md                           ← Lead (compartido)
├── .claude/                            ← Lead
│   ├── settings.local.json
│   └── hooks/
├── specs/                              ← Documentación (compartido, solo lectura)
├── docs/                               ← Documentación
│   ├── adr/                            ← Arquitecto
│   ├── api/                            ← Documentación
│   └── guides/                         ← Documentación
├── packages/
│   ├── drawio-library/                 ← Frontend (Fase 1)
│   │   ├── shapes/                     ← Stencils XML y SVGs
│   │   │   ├── equipment/              ← Bombas, tanques, intercambiadores...
│   │   │   ├── piping/                 ← Válvulas, reducciones, filtros...
│   │   │   ├── instrumentation/        ← Transmisores, controladores...
│   │   │   └── lines/                  ← Estilos de líneas de proceso y señal
│   │   ├── templates/                  ← Plantilla .drawio base con capas
│   │   ├── pid-library.xml             ← Biblioteca empaquetada
│   │   └── README.md
│   │
│   ├── pid-converter/                  ← Backend
│   │   ├── src/
│   │   │   └── pid_converter/
│   │   │       ├── parser/             ← mxGraph XML → modelo interno
│   │   │       ├── mapper/             ← modelo interno → pyDEXPI
│   │   │       ├── topology/           ← Reconstrucción nozzle-a-nozzle
│   │   │       ├── serializer/         ← pyDEXPI → Proteus XML
│   │   │       ├── importer/           ← Proteus XML → .drawio (bidireccional)
│   │   │       ├── validator/          ← Validación de P&ID
│   │   │       └── cli.py              ← CLI con Typer
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── pid-knowledge-graph/            ← Base de Datos
│   │   ├── src/
│   │   │   └── pid_knowledge_graph/
│   │   │       ├── graph_builder.py    ← pyDEXPI → NetworkX
│   │   │       ├── condensation.py     ← Grafo alto nivel
│   │   │       ├── semantic.py         ← Etiquetas para LLM
│   │   │       └── neo4j_store.py      ← Persistencia Neo4j
│   │   ├── migrations/                 ← Constraints e índices Cypher
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── pid-rag/                        ← Backend (Fase 4)
│   │   ├── src/
│   │   │   └── pid_rag/
│   │   │       ├── api/                ← FastAPI endpoints
│   │   │       │   ├── routes/
│   │   │       │   │   ├── convert.py  ← /api/convert/*
│   │   │       │   │   ├── graph.py    ← /api/graph/*
│   │   │       │   │   ├── chat.py     ← /api/chat/* (SSE streaming)
│   │   │       │   │   └── validate.py ← /api/validate/*
│   │   │       │   └── app.py          ← FastAPI app
│   │   │       ├── retrieval/          ← Graph-RAG retrieval strategies
│   │   │       ├── prompts/            ← System prompts de ingeniería
│   │   │       └── config.py           ← Settings (Pydantic BaseSettings)
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── pid-web/                        ← Frontend (Fase 4)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── chat/               ← Chat con LLM
│   │   │   │   ├── graph/              ← Visualización Knowledge Graph
│   │   │   │   ├── pid/                ← Visor/referencia de P&ID
│   │   │   │   └── common/             ← Componentes compartidos
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── stores/                 ← Zustand stores
│   │   │   ├── services/               ← API client (TanStack Query)
│   │   │   ├── types/                  ← TypeScript types
│   │   │   └── styles/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   └── tsconfig.json
│   │
│   └── pid-mcp-server/                 ← Integraciones (Fase 5)
│       ├── src/
│       │   ├── tools/
│       │   │   ├── convert.ts          ← Tools de conversión
│       │   │   ├── graph.ts            ← Tools de Knowledge Graph
│       │   │   ├── validate.ts         ← Tools de validación
│       │   │   └── drawio.ts           ← Tools de Draw.io (via Gazo)
│       │   ├── resources/
│       │   └── index.ts                ← MCP server entry point
│       ├── tests/
│       ├── package.json
│       └── tsconfig.json
│
├── docker/
│   ├── Dockerfile.api                  ← FastAPI + conversor + KG + RAG
│   ├── Dockerfile.web                  ← React build + nginx
│   ├── Dockerfile.mcp                  ← MCP server
│   └── neo4j/
│       └── init.cypher                 ← Schema inicial
├── docker-compose.yml                  ← Stack completo
├── docker-compose.dev.yml              ← Override para desarrollo
│
├── .github/
│   └── workflows/
│       ├── ci-python.yml               ← Lint + test Python packages
│       ├── ci-typescript.yml           ← Lint + test TS packages
│       ├── e2e.yml                     ← Tests E2E con Playwright
│       └── publish.yml                 ← Publicación a PyPI + Docker Hub
│
├── e2e/                                ← Tests E2E Playwright
├── .eslintrc.js
├── .prettierrc
├── ruff.toml
└── README.md
```

## Mapa de Ownership (Teammate → Carpetas)

| Carpeta | Propietario | Notas |
|---------|------------|-------|
| `docs/adr/` | Arquitecto | ADRs y decisiones técnicas |
| `packages/drawio-library/` | Frontend | Biblioteca de símbolos P&ID |
| `packages/pid-converter/` | Backend | Parser, mapper, topología, serializer, importer, validator |
| `packages/pid-knowledge-graph/` | Base de Datos | Grafo, condensación, Neo4j store |
| `packages/pid-rag/` | Backend | FastAPI, Graph-RAG, prompts |
| `packages/pid-web/` | Frontend | React UI |
| `packages/pid-mcp-server/` | Integraciones | MCP orquestador TypeScript |
| `docker/`, `docker-compose.*` | DevOps | Contenedores y orquestación |
| `.github/workflows/` | DevOps | CI/CD |
| `e2e/` | Testing | Tests end-to-end |
| `tests/` dentro de cada package | Testing | Tests unitarios e integración |
| `docs/` (excepto adr/) | Documentación | Guías, API docs |
| `specs/` | — | Solo lectura, referencia |

## Archivos Compartidos — Coordinar antes de editar

| Archivo | Teammates implicados | Regla |
|---------|---------------------|-------|
| `CLAUDE.md` | Todos | Solo el Lead modifica |
| `packages/pid-rag/src/pid_rag/api/` | Backend + Frontend | Backend define endpoints, Frontend consume. Cambios en contratos requieren coordinación |
| `packages/pid-web/src/types/` | Frontend + Backend | Backend define tipos de respuesta, Frontend los consume como TypeScript types |
| `docker-compose.yml` | DevOps + todos | DevOps posee, otros solicitan cambios |
| `README.md` raíz | Documentación + Arquitecto | Documentación posee, Arquitecto revisa |

## Siguiente Paso
Avanzar a **Fase 5: Composición del Equipo** para definir qué teammates se necesitan, sus spawn prompts específicos y puntos de intervención humana.
