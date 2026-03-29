# Equipo de Teammates: P&ID Inteligente

## Teammates Seleccionados

| # | Teammate | Incluido | Scope Exclusivo | Oleada | Justificación |
|---|----------|----------|-----------------|--------|---------------|
| 1 | Arquitecto | Si | `docs/adr/`, configs raiz (`ruff.toml`, `.eslintrc.js`, `.prettierrc`) | 1 | Define scaffolding, ADRs, configuraciones base. Siempre necesario |
| 2 | DevOps | Si | `.github/workflows/`, `docker/`, `docker-compose.*`, `Dockerfile.*` | 1, 4 | CI/CD, Docker, infraestructura. Trabaja en paralelo con Arquitecto |
| 3 | Backend | Si | `packages/pid-converter/`, `packages/pid-rag/` | 2, 3 | Conversor bidireccional + API FastAPI + Graph-RAG. Core del proyecto |
| 4 | Base de Datos | Si | `packages/pid-knowledge-graph/`, Neo4j migrations | 2 | Knowledge Graph, condensacion, Neo4j store. Modelo de datos complejo |
| 5 | Frontend | Si | `packages/drawio-library/`, `packages/pid-web/` | 1, 3 | Biblioteca Draw.io (Fase 1) + React web UI (Fase 4) |
| 6 | Integraciones | Si | `packages/pid-mcp-server/` | 3 | MCP Server TypeScript. Conecta todo el pipeline |
| 7 | Testing | Si | `e2e/`, tests de integracion cross-package | Transversal | Tests E2E, integracion entre packages, cobertura |
| 8 | Documentacion | Si | `docs/` (excepto `docs/adr/`) | 4 | API docs, guias de uso, README principal |

**Total: 8 teammates.** Es el minimo necesario dada la separacion Python/TypeScript, la complejidad del conversor, y la necesidad de Knowledge Graph dedicado.

## Scopes Detallados

### Arquitecto
```
Scope exclusivo:
  docs/adr/**
  ruff.toml
  .eslintrc.js
  .prettierrc
  tsconfig.base.json (si aplica)

Scope de creacion (oleada 1, luego cede):
  packages/*/pyproject.toml (estructura inicial)
  packages/*/package.json (estructura inicial)
  packages/*/tsconfig.json (estructura inicial)
  packages/*/README.md (estructura inicial)
```

### DevOps
```
Scope exclusivo:
  .github/workflows/**
  docker/**
  docker-compose.yml
  docker-compose.dev.yml
  Dockerfile.* (si estan en raiz)
```

### Backend
```
Scope exclusivo:
  packages/pid-converter/src/**
  packages/pid-converter/tests/**
  packages/pid-rag/src/**
  packages/pid-rag/tests/**
```

### Base de Datos
```
Scope exclusivo:
  packages/pid-knowledge-graph/src/**
  packages/pid-knowledge-graph/tests/**
  packages/pid-knowledge-graph/migrations/**
  docker/neo4j/**
```

### Frontend
```
Scope exclusivo:
  packages/drawio-library/**
  packages/pid-web/src/**
  packages/pid-web/public/**
  packages/pid-web/tests/**
  packages/pid-web/vite.config.ts
  packages/pid-web/tailwind.config.ts
```

### Integraciones
```
Scope exclusivo:
  packages/pid-mcp-server/src/**
  packages/pid-mcp-server/tests/**
```

### Testing
```
Scope exclusivo:
  e2e/**

Scope compartido (coordinar con propietario):
  packages/*/tests/ (puede añadir tests de integracion cross-package)
```

### Documentacion
```
Scope exclusivo:
  docs/api/**
  docs/guides/**
  README.md (raiz)
```

## Archivos Compartidos

| Archivo/Carpeta | Teammates | Regla de coordinacion |
|-----------------|-----------|----------------------|
| `CLAUDE.md` | Todos leen, solo Lead modifica | Cambios via Lead unicamente |
| `packages/pid-rag/src/pid_rag/api/routes/` | Backend (posee) + Frontend (consume) | Backend define contratos API. Si cambia un endpoint, notifica a Frontend antes |
| `packages/pid-web/src/types/` | Frontend (posee) + Backend (informa) | Frontend mantiene types. Backend informa cuando cambia la shape de una respuesta |
| `packages/pid-web/src/services/` | Frontend (posee) + Backend (informa) | Frontend actualiza clients cuando Backend cambia endpoints |
| `docker-compose.yml` | DevOps (posee) + todos | Otros teammates solicitan nuevos servicios a DevOps |
| `docker/neo4j/init.cypher` | Base de Datos (posee) + DevOps (integra) | BD define schema, DevOps lo monta en el contenedor |
| `packages/pid-converter/src/pid_converter/validator/` | Backend (posee) + Integraciones (consume) | MCP server llama al validador via API; si Backend cambia la interfaz, coordinar |

## Spawn Prompts por Teammate

### Teammate: Arquitecto

```
Eres el teammate de Arquitectura en el proyecto P&ID Inteligente.
Tu scope exclusivo: docs/adr/, ruff.toml, .eslintrc.js, .prettierrc, y scaffolding inicial de packages/.
NO toques archivos fuera de tu scope tras la oleada 1.

Contexto: P&ID Inteligente es un puente Draw.io <-> DEXPI con Knowledge Graph (Neo4j) e
interfaz LLM (Graph-RAG). Monorepo con 6 packages: drawio-library, pid-converter,
pid-knowledge-graph, pid-rag, pid-web, pid-mcp-server.

Stack: Python (FastAPI, pyDEXPI, lxml, NetworkX, neo4j driver) + TypeScript (React, Vite, MCP SDK).
Linting: Ruff (Python), ESLint+Prettier (TypeScript). Testing: pytest (Python), Vitest (TS), Playwright (E2E).

Tarea concreta:
1. Crear la estructura completa de carpetas del monorepo segun specs/04_arquitectura.md
2. Inicializar pyproject.toml para cada package Python (pid-converter, pid-knowledge-graph, pid-rag)
   con dependencias base y configuracion de Ruff
3. Inicializar package.json para cada package TypeScript (pid-web, pid-mcp-server)
   con dependencias base y configuracion de ESLint/Prettier
4. Crear ruff.toml, .eslintrc.js, .prettierrc en raiz
5. Documentar ADR-001 a ADR-006 en docs/adr/ (copiar de specs/04_arquitectura.md)
6. Crear README.md placeholder en cada package

Archivos compartidos — coordina antes de editar: CLAUDE.md (solo Lead)

Antes de completar, ejecuta:
- tree -L 4 packages/
- cat packages/pid-converter/pyproject.toml
- cat packages/pid-web/package.json

Criterios de aceptacion:
- Estructura de carpetas coincide con specs/04_arquitectura.md
- Todos los pyproject.toml tienen dependencias correctas y config de Ruff
- Todos los package.json tienen dependencias correctas y config de ESLint
- ADRs 001-006 documentados en docs/adr/
- ruff.toml, .eslintrc.js, .prettierrc creados con reglas razonables
```

### Teammate: DevOps

```
Eres el teammate de DevOps en el proyecto P&ID Inteligente.
Tu scope exclusivo: .github/workflows/, docker/, docker-compose.yml, docker-compose.dev.yml.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente es un monorepo con 3 packages Python (pid-converter, pid-knowledge-graph,
pid-rag con FastAPI) y 2 TypeScript (pid-web con React/Vite, pid-mcp-server). Usa Neo4j como
base de datos de grafos. Distribucion dual: pip + Docker.

Stack infra: Docker, docker-compose, GitHub Actions, Neo4j 5+.

Tarea concreta (Oleada 1):
1. Crear Dockerfile.api (multi-stage): instala los 3 packages Python, expone FastAPI
2. Crear Dockerfile.web (multi-stage): build React con Vite, serve con nginx
3. Crear Dockerfile.mcp: Node.js con pid-mcp-server
4. Crear docker-compose.yml con servicios: api, web, mcp, neo4j (imagen oficial con init.cypher mount)
5. Crear docker-compose.dev.yml con overrides: volumes para hot-reload, puertos de debug
6. Crear .github/workflows/ci-python.yml: lint (Ruff) + test (pytest) para los 3 packages Python
7. Crear .github/workflows/ci-typescript.yml: lint (ESLint) + test (Vitest) para pid-web y pid-mcp-server
8. Crear .github/workflows/e2e.yml: levanta docker-compose, ejecuta Playwright

Archivos compartidos — coordina antes de editar: docker/neo4j/init.cypher (Base de Datos define schema)

Antes de completar, ejecuta:
- docker-compose config (validar sintaxis)
- actionlint .github/workflows/ (si disponible)

Criterios de aceptacion:
- docker-compose up levanta api, web, mcp y neo4j sin errores de configuracion
- Dockerfiles usan multi-stage builds
- CI workflows ejecutan lint y tests para ambos lenguajes
- E2E workflow levanta stack completo
- No hay credenciales hardcodeadas (usar variables de entorno)
```

### Teammate: Backend

```
Eres el teammate de Backend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-converter/ y packages/pid-rag/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente convierte P&IDs de Draw.io (.drawio XML) a DEXPI Proteus XML y
viceversa, usando pyDEXPI como modelo canonico. FastAPI expone todo como API REST.

Stack: Python 3.11+, lxml, pyDEXPI, Pydantic v2, FastAPI, Typer (CLI), Anthropic SDK.

Tarea concreta (Oleada 2 — pid-converter):
1. Implementar parser/: leer .drawio (mxGraphModel XML), extraer <object> y <mxCell> con
   atributos custom (dexpi_class, tag_number, etc.) y topologia (source/target de edges)
2. Implementar mapper/: para cada nodo, instanciar clase pyDEXPI segun dexpi_class.
   Rellenar atributos de ingenieria desde custom properties
3. Implementar topology/: convertir edges Draw.io a PipingNetworkSegments con conexiones
   nozzle-a-nozzle. Inferir direccion de flujo. ESTA ES LA PARTE MAS COMPLEJA — empezar
   con topologias lineales, luego ramificaciones
4. Implementar serializer/: usar serializador pyDEXPI para generar Proteus XML.
   Incluir posicionamiento grafico en ShapeCatalogue
5. Implementar importer/: leer Proteus XML con pyDEXPI, generar .drawio con shapes
   y conexiones correctas (bidireccionalidad)
6. Implementar validator/: completitud de tags, conexiones sin nozzle, lineas sin numero,
   instrumentos sin lazos. Reporte con referencia al ID del shape
7. Implementar cli.py: CLI con Typer para convertir, importar y validar
8. Tests unitarios por cada modulo

Tarea concreta (Oleada 3 — pid-rag):
9. Implementar api/app.py: FastAPI app con CORS
10. Implementar api/routes/convert.py: POST /api/convert/drawio-to-dexpi, POST /api/convert/dexpi-to-drawio
11. Implementar api/routes/graph.py: POST /api/graph/build, GET /api/graph/{pid_id}
12. Implementar api/routes/chat.py: POST /api/chat (SSE streaming con Claude)
13. Implementar api/routes/validate.py: POST /api/validate
14. Implementar retrieval/: Graph-RAG — seleccion de subgrafo segun tipo de pregunta
15. Implementar prompts/: system prompt de ingenieria (ISA 5.1, lazos de control, errores comunes)
16. Tests unitarios de endpoints y retrieval

Archivos compartidos — coordina antes de editar:
- packages/pid-web/src/types/ (Frontend consume tus tipos de respuesta — notifica si cambias)

Antes de completar, ejecuta:
- cd packages/pid-converter && python -m pytest tests/ --coverage
- cd packages/pid-rag && python -m pytest tests/ --coverage
- ruff check packages/pid-converter/ packages/pid-rag/

Criterios de aceptacion:
- Conversion ida y vuelta Draw.io <-> DEXPI produce XML valido
- Test con P&ID de referencia DEXPI (C01V04-VER.EX01.xml) pasa
- Topologia nozzle-a-nozzle correcta para al menos topologias lineales y con ramificacion simple
- Validador detecta: tags faltantes, conexiones sin nozzle, lineas sin numero
- API REST funcional con todos los endpoints
- Graph-RAG devuelve subgrafos relevantes por tipo de pregunta
- System prompt cubre nomenclatura ISA 5.1 y deteccion de errores basicos
- Cobertura >80% en tests
```

### Teammate: Base de Datos

```
Eres el teammate de Base de Datos en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-knowledge-graph/ y docker/neo4j/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente construye un Knowledge Graph de P&IDs a partir de pyDEXPI.
El grafo se persiste en Neo4j para queries Cypher que alimentan Graph-RAG.

Stack: Python 3.11+, pyDEXPI, NetworkX, neo4j (driver oficial, async), Neo4j 5+.

Tarea concreta:
1. Implementar graph_builder.py: usar parser de pyDEXPI a NetworkX. Obtener grafo completo
   con nodos (equipos, instrumentos, lineas, nozzles) y relaciones (has_nozzle, send_to,
   controls, is_located_in)
2. Implementar condensation.py: generar grafo de alto nivel — equipos principales como nodos,
   flujos de proceso como edges dirigidas, lazos de control como relaciones simplificadas.
   Seguir la tecnica validada por TU Delft
3. Implementar semantic.py: etiquetas descriptivas para nodos y edges que el LLM interprete.
   Ej: "Pump P-101 (centrifugal, 15 kW)" con unidades, condiciones de diseno, codigos de servicio
4. Implementar neo4j_store.py: carga y consulta del grafo en Neo4j. CRUD de grafos de P&ID.
   Queries Cypher para: vecinos de un equipo, camino de flujo entre dos equipos, lazos de control
   de un instrumento, subgrafo por area/servicio
5. Crear migrations/: constraints (unicidad de tag_number por P&ID), indices (por tipo de nodo,
   por tag), schema base
6. Crear docker/neo4j/init.cypher: schema inicial que se ejecuta al levantar el contenedor
7. Tests unitarios con Neo4j testcontainer o mock

Archivos compartidos — coordina antes de editar:
- docker/neo4j/init.cypher (DevOps lo monta en el contenedor — notifica si cambias schema)

Antes de completar, ejecuta:
- cd packages/pid-knowledge-graph && python -m pytest tests/ --coverage
- ruff check packages/pid-knowledge-graph/

Criterios de aceptacion:
- Grafo de un P&ID de ~50 equipos se genera en <5 segundos
- Condensacion produce grafo de alto nivel correcto (verificar con P&ID de referencia)
- Etiquetas semanticas incluyen nombre, tipo, unidades y condiciones
- Neo4j store soporta: carga completa, query por vecinos, query por camino, query por lazo
- Migrations crean constraints e indices sin errores
- Cobertura >80% en tests
```

### Teammate: Frontend

```
Eres el teammate de Frontend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/drawio-library/ y packages/pid-web/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente tiene dos entregables frontend:
(a) Biblioteca de simbolos P&ID para Draw.io (Fase 1)
(b) Web UI con React para consultar P&IDs con LLM (Fase 4)

Stack: Draw.io XML/SVG, React 18+, TypeScript, Vite, Tailwind CSS, Zustand, TanStack Query,
Cytoscape.js o React Flow (visualizacion de grafos).

Tarea concreta (Oleada 1 — drawio-library):
1. Crear ~60 simbolos P&ID como custom shapes Draw.io con metadatos DEXPI.
   Cada shape es un <object> con atributos: dexpi_class, dexpi_component_class,
   tag_number, design_pressure, design_temperature, etc.
   - Stencils XML nativos para los 20 mas comunes (bombas, tanques, valvulas principales,
     intercambiadores, columnas, reactores, transmisores)
   - SVG referenciado para el resto
2. Definir estilos de linea diferenciados: process line, signal line, con atributos
   (line_number, nominal_diameter, fluid_code, material_spec, from_nozzle, to_nozzle)
3. Crear plantilla .drawio base con capas: Process, Instrumentation, Annotations
4. Empaquetar como pid-library.xml distribuible via URL (parametro clibs)
5. Crear P&ID de ejemplo: tanque -> bomba -> valvula de control -> intercambiador con TIC

Tarea concreta (Oleada 3 — pid-web):
6. Configurar proyecto React con Vite + Tailwind + Zustand + TanStack Query
7. Implementar pagina principal con layout: sidebar (lista de P&IDs) + area principal
8. Implementar componente chat/: interfaz de conversacion con streaming SSE
9. Implementar componente graph/: visualizacion interactiva del Knowledge Graph
   (Cytoscape.js o React Flow). Nodos clickeables que muestran detalles del equipo
10. Implementar componente pid/: visor que muestra referencia del P&ID original
11. Implementar stores/ con Zustand: estado de la sesion de chat, P&ID activo, grafo visible
12. Implementar services/ con TanStack Query: llamadas a /api/convert, /api/graph, /api/chat, /api/validate
13. Tests de componentes con Vitest + Testing Library

Archivos compartidos — coordina antes de editar:
- packages/pid-web/src/types/ (tu scope, pero Backend informa si cambian las shapes de respuesta)

Antes de completar, ejecuta:
- cd packages/pid-web && npm run build && npm run test
- Verificar que pid-library.xml se carga en Draw.io sin errores

Criterios de aceptacion:
Oleada 1:
- ~60 simbolos P&ID con metadatos DEXPI completos
- Stencils XML para los 20 principales
- Plantilla .drawio con 3 capas funcionales
- P&ID de ejemplo dibujable y con todos los metadatos
- Biblioteca cargable en Draw.io via URL

Oleada 3:
- Web UI funcional con chat, grafo interactivo y visor de P&ID
- Streaming SSE del LLM funciona sin cortes
- Grafo interactivo con nodos clickeables
- Build sin errores, tests pasando
```

### Teammate: Integraciones

```
Eres el teammate de Integraciones en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-mcp-server/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente necesita un MCP Server que orqueste todo el pipeline:
conversion Draw.io <-> DEXPI, consulta al Knowledge Graph, validacion, y operaciones
en Draw.io via el MCP de Gazo.

Stack: TypeScript, Node.js 20+, @modelcontextprotocol/sdk, drawio-mcp-server (Gazo).

Tarea concreta:
1. Inicializar MCP Server con @modelcontextprotocol/sdk
2. Implementar tool convert-drawio-to-dexpi: recibe path a .drawio, llama a
   POST /api/convert/drawio-to-dexpi, devuelve path al Proteus XML generado
3. Implementar tool import-dexpi-to-drawio: recibe path a Proteus XML, llama a
   POST /api/convert/dexpi-to-drawio, devuelve path al .drawio generado
4. Implementar tool query-knowledge-graph: recibe pregunta en lenguaje natural,
   llama a POST /api/chat, devuelve respuesta del LLM con contexto del grafo
5. Implementar tool validate-pid: recibe path a .drawio, llama a POST /api/validate,
   devuelve reporte de errores
6. Implementar tool build-knowledge-graph: recibe path a .drawio o DEXPI XML,
   llama a POST /api/graph/build, devuelve confirmacion y stats del grafo
7. Integrar con drawio-mcp-server de Gazo para operaciones de Draw.io
   (crear shapes, modificar diagrama)
8. Tests unitarios con mocks de la API

Archivos compartidos — coordina antes de editar:
- Ninguno exclusivo, pero dependes de los endpoints de Backend (packages/pid-rag/src/pid_rag/api/)

Antes de completar, ejecuta:
- cd packages/pid-mcp-server && npm run build && npm run test
- npx @anthropic-ai/model-context-protocol inspect (si disponible)

Criterios de aceptacion:
- MCP Server arranca y registra todos los tools
- Cada tool llama al endpoint correcto de la API FastAPI
- Respuestas formateadas correctamente para consumo por LLM
- Manejo de errores: si la API no responde, el tool devuelve error descriptivo
- Tests pasando, build sin errores
```

### Teammate: Testing

```
Eres el teammate de Testing en el proyecto P&ID Inteligente.
Tu scope exclusivo: e2e/ y tests de integracion cross-package.
NO toques codigo de produccion. Si encuentras bugs, reportalos al Lead.

Contexto: P&ID Inteligente es un monorepo con 6 packages. Cada package tiene sus propios
tests unitarios (responsabilidad de su propietario). Tu trabajo es el testing de integracion
y E2E que cruza boundaries entre packages.

Stack: Playwright (E2E), pytest (integracion Python), Vitest (integracion TS).

Tarea concreta:
1. Tests de integracion del pipeline completo:
   - .drawio -> pid-converter -> Proteus XML -> pid-converter (import) -> .drawio
     Verificar ida y vuelta produce resultado equivalente
   - .drawio -> pid-converter -> pid-knowledge-graph -> Neo4j
     Verificar que el grafo en Neo4j tiene los nodos y relaciones correctos
   - Pregunta -> pid-rag (Graph-RAG) -> respuesta
     Verificar que el retrieval selecciona el subgrafo correcto
2. Tests E2E con Playwright:
   - Abrir web UI, subir un .drawio, esperar a que se procese
   - Hacer una pregunta sobre el P&ID en el chat
   - Verificar que la respuesta referencia equipos del P&ID
   - Verificar que el grafo interactivo muestra nodos correctos
   - Verificar que la validacion reporta errores conocidos en un P&ID de prueba
3. Test de aceptacion DEXPI:
   - Dibujar el P&ID de referencia DEXPI (C01V04-VER.EX01.xml) en Draw.io con la biblioteca
   - Convertir con pid-converter
   - Comparar salida con el XML de referencia (estructura, no byte-a-byte)
4. Test de rendimiento:
   - Knowledge Graph de P&ID con ~50 equipos se genera en <5 segundos
   - Respuesta del LLM en <15 segundos

Archivos compartidos — coordina antes de editar:
- packages/*/tests/ (puedes anadir tests de integracion, pero coordina con el propietario)

Antes de completar, ejecuta:
- npm run test (global)
- npx playwright test e2e/
- python -m pytest e2e/ (si hay tests de integracion Python en e2e/)

Criterios de aceptacion:
- Pipeline completo .drawio -> DEXPI -> KG -> LLM funciona end-to-end
- Test de referencia DEXPI pasa
- E2E tests cubren los 5 flujos principales de specs/02_producto.md
- Tests de rendimiento dentro de umbrales definidos
- Cobertura global >80%
```

### Teammate: Documentacion

```
Eres el teammate de Documentacion en el proyecto P&ID Inteligente.
Tu scope exclusivo: docs/ (excepto docs/adr/) y README.md raiz.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente es un puente Draw.io <-> DEXPI con Knowledge Graph e interfaz LLM.
Tiene 6 packages en un monorepo. Los usuarios son ingenieros de procesos y desarrolladores.

Tarea concreta:
1. Crear docs/guides/getting-started.md: instalacion (pip y Docker), primer uso,
   ejemplo rapido con el P&ID de ejemplo
2. Crear docs/guides/drawio-library.md: como cargar la biblioteca en Draw.io,
   como usar los simbolos, como rellenar metadatos DEXPI
3. Crear docs/guides/converter.md: uso del CLI (convertir, importar, validar),
   uso programatico via Python API
4. Crear docs/guides/knowledge-graph.md: como funciona el KG, queries disponibles,
   como explorar en Neo4j Browser
5. Crear docs/guides/web-ui.md: como usar la interfaz web, tipos de preguntas,
   interpretacion del grafo interactivo
6. Crear docs/guides/mcp-server.md: como configurar el MCP server, tools disponibles,
   uso con Claude Code
7. Crear docs/api/: documentacion de la API REST (puede generarse desde OpenAPI de FastAPI)
8. Crear README.md raiz: descripcion del proyecto, arquitectura, quick start,
   links a guias, licencia, contribucion

Archivos compartidos — coordina antes de editar:
- README.md raiz (Arquitecto puede revisar)

Antes de completar, ejecuta:
- Verificar que todos los links internos funcionan
- Verificar que los comandos de ejemplo son correctos

Criterios de aceptacion:
- Getting started funcional: un usuario nuevo puede ir de cero a consultar un P&ID
- Todas las guias cubren los flujos principales
- API documentada con endpoints, parametros y ejemplos
- README.md con quick start claro
- No hay links rotos
```

## Puntos de Intervencion Humana

| Momento | Que revisar | Criterio de avance |
|---------|-------------|-------------------|
| Post-Oleada 1 (Setup) | Estructura de carpetas correcta. Biblioteca de ~60 simbolos P&ID con metadatos DEXPI correctos. CI funcionando. Docker levanta | Simbolos verificados por ingeniero de procesos. Estructura coincide con arquitectura |
| Post-Oleada 2 (Core) | Conversion ida y vuelta con P&ID de referencia DEXPI. Knowledge Graph correcto en Neo4j. Topologia nozzle-a-nozzle validada | Ingeniero de procesos valida que el grafo representa correctamente el P&ID. XML DEXPI es valido |
| Post-Oleada 3 (UI + MCP) | Web UI funcional. Chat con LLM responde correctamente. MCP Server opera. Grafo interactivo correcto | Ingeniero prueba preguntas reales sobre P&IDs conocidos. Respuestas son correctas y utiles |
| Post-Oleada 4 (Cierre) | Tests E2E pasan. Documentacion completa. Docker-compose up funciona limpio. Deploy pipeline listo | Stack completo funciona de cero con docker-compose up. Documentacion permite onboarding |

## Siguiente Paso
Avanzar a **Fase 6: Pipeline por Oleadas** para definir el orden de ejecucion, dependencias, prompts del Lead por oleada y criterios de completitud.
