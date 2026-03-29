# Oleada 1 — Setup & Biblioteca

Crea un equipo para la Oleada 1: Setup & Biblioteca del proyecto P&ID Inteligente.
Activa delegate mode (Shift+Tab) — tu coordinas, no implementas.

Lanza los siguientes teammates en paralelo:

## 1. Arquitecto

Eres el teammate de Arquitectura en el proyecto P&ID Inteligente.
Tu scope exclusivo: docs/adr/, ruff.toml, .eslintrc.js, .prettierrc, y scaffolding inicial de packages/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente es un puente Draw.io <-> DEXPI con Knowledge Graph (Neo4j) e interfaz LLM (Graph-RAG). Monorepo con 6 packages: drawio-library, pid-converter, pid-knowledge-graph, pid-rag, pid-web, pid-mcp-server.

Stack: Python (FastAPI, pyDEXPI, lxml, NetworkX, neo4j driver) + TypeScript (React, Vite, MCP SDK). Linting: Ruff (Python), ESLint+Prettier (TypeScript). Testing: pytest (Python), Vitest (TS), Playwright (E2E).

Tarea concreta:
1. Verificar que la estructura de carpetas del monorepo esta completa segun specs/04_arquitectura.md. Crear lo que falte.
2. Verificar que los pyproject.toml (Python) y package.json (TS) tienen las dependencias correctas. Ajustar si es necesario.
3. Verificar las configs de linting raiz (ruff.toml, .eslintrc.js, .prettierrc). Ajustar si es necesario.
4. Documentar ADR-001 a ADR-006 en docs/adr/ (ver specs/04_arquitectura.md para el contenido).
5. Crear README.md placeholder en cada package con: descripcion, instalacion basica, uso basico.

Antes de completar, ejecuta:
- tree -L 4 packages/
- cat packages/pid-converter/pyproject.toml
- cat packages/pid-web/package.json

Criterios de aceptacion:
- Estructura de carpetas coincide con specs/04_arquitectura.md
- ADRs 001-006 documentados en docs/adr/
- README.md en cada package

## 2. DevOps

Eres el teammate de DevOps en el proyecto P&ID Inteligente.
Tu scope exclusivo: .github/workflows/, docker/, docker-compose.yml, docker-compose.dev.yml.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente es un monorepo con 3 packages Python (pid-converter, pid-knowledge-graph, pid-rag con FastAPI) y 2 TypeScript (pid-web con React/Vite, pid-mcp-server). Usa Neo4j como base de datos de grafos. Distribucion dual: pip + Docker.

Stack infra: Docker, docker-compose, GitHub Actions, Neo4j 5+.

Tarea concreta:
1. Crear docker/Dockerfile.api (multi-stage): instala los 3 packages Python, expone FastAPI en puerto 8000
2. Crear docker/Dockerfile.web (multi-stage): build React con Vite, serve con nginx en puerto 3000
3. Crear docker/Dockerfile.mcp: Node.js con pid-mcp-server
4. Crear docker-compose.yml con servicios: api (puerto 8000), web (puerto 3000), mcp, neo4j (puertos 7474/7687 con init.cypher mount)
5. Crear docker-compose.dev.yml con overrides: volumes para hot-reload, puertos de debug
6. Crear .github/workflows/ci-python.yml: checkout, setup Python 3.11, install deps, ruff check, pytest para los 3 packages
7. Crear .github/workflows/ci-typescript.yml: checkout, setup Node 20, npm install, eslint, vitest para pid-web y pid-mcp-server
8. Crear .github/workflows/e2e.yml: levanta docker-compose, ejecuta Playwright

Antes de completar, ejecuta:
- docker-compose config (validar sintaxis)

Criterios de aceptacion:
- docker-compose.yml define 4 servicios (api, web, mcp, neo4j)
- Dockerfiles usan multi-stage builds
- CI workflows cubren lint + tests para ambos lenguajes
- No hay credenciales hardcodeadas

## 3. Frontend (Biblioteca Draw.io)

Eres el teammate de Frontend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/drawio-library/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente necesita una biblioteca de ~60 simbolos P&ID para Draw.io con metadatos semanticos DEXPI. Los ingenieros de procesos usaran estos simbolos para dibujar P&IDs en Draw.io.

Estandares: ISA 5.1 (simbologia de instrumentacion), ISO 10628 (diagramas de proceso), DEXPI Proteus XML Schema.

Tarea concreta:
1. Crear ~60 simbolos P&ID como custom shapes Draw.io con metadatos DEXPI. Cada shape es un `<object>` con atributos: dexpi_class, dexpi_component_class, tag_number (vacio para que el usuario rellene), design_pressure, design_temperature, y otros atributos de ingenieria relevantes.
   - Stencils XML nativos para los 20 mas comunes: CentrifugalPump, Tank, HeatExchanger, Column, Reactor, Compressor, Vessel, GateValve, GlobeValve, BallValve, ButterflyValve, CheckValve, ControlValve, SafetyValve, Reducer, Transmitter, Controller, Indicator, PressureGauge, LevelGlass
   - SVG referenciado o stencils simplificados para el resto: Filter, Agitator, Tee, Elbow, Flange, BlindFlange, SpectacleBlind, Strainer, SteamTrap, Alarm, y variantes especificas
2. Definir estilos de linea diferenciados para:
   - Process line (linea continua gruesa) con atributos: line_number, nominal_diameter, fluid_code, material_spec, from_nozzle, to_nozzle
   - Signal line (linea discontinua) con atributos: signal_type, instrument_tag
   - Utility line (linea continua delgada)
3. Crear plantilla .drawio base en templates/ con capas preconfiguradas: Process, Instrumentation, Annotations
4. Empaquetar todo como pid-library.xml distribuible via URL (parametro clibs de Draw.io)
5. Crear P&ID de ejemplo en examples/: tanque T-101 -> bomba P-101 -> valvula de control TCV-101 -> intercambiador HE-101 con lazo de control TIC-101

Antes de completar:
- Verificar que pid-library.xml es XML valido
- Verificar que el P&ID de ejemplo tiene todos los metadatos DEXPI completos

Criterios de aceptacion:
- ~60 simbolos con metadatos DEXPI (dexpi_class obligatorio en todos)
- Stencils XML para los 20 principales
- Plantilla con 3 capas funcionales
- P&ID de ejemplo completo con todos los metadatos
- Biblioteca empaquetada como pid-library.xml

---

Cuando todos terminen, presenta resumen de lo creado.
No marques como completo hasta que las verificaciones pasen.
