# Estandares y Convenciones: P&ID Inteligente

## Convenciones de Codigo

### Python (pid-converter, pid-knowledge-graph, pid-rag)

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Variables | snake_case | `tag_number`, `flow_direction` |
| Funciones | snake_case | `parse_drawio()`, `build_graph()` |
| Clases | PascalCase | `MxGraphParser`, `Neo4jStore` |
| Constantes | UPPER_SNAKE | `MAX_NOZZLE_DISTANCE`, `DEFAULT_TIMEOUT` |
| Archivos | snake_case | `graph_builder.py`, `neo4j_store.py` |
| Packages | snake_case | `pid_converter`, `pid_knowledge_graph` |
| Type hints | Obligatorias en funciones publicas | `def parse(path: Path) -> PidModel:` |
| Docstrings | Google style, solo en funciones publicas | `"""Parse a .drawio file into a PID model."""` |

**Linter/Formatter:** Ruff (reemplaza flake8 + isort + black)

```toml
# ruff.toml
target-version = "py311"
line-length = 100

[lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "SIM",   # flake8-simplify
    "TCH",   # flake8-type-checking
]

[format]
quote-style = "double"
```

### TypeScript (pid-web, pid-mcp-server)

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Variables | camelCase | `tagNumber`, `flowDirection` |
| Funciones | camelCase | `parseResponse()`, `buildQuery()` |
| Clases / Componentes React | PascalCase | `ChatPanel`, `GraphViewer` |
| Constantes | UPPER_SNAKE | `MAX_RETRIES`, `API_BASE_URL` |
| Archivos componentes | PascalCase.tsx | `ChatPanel.tsx`, `GraphViewer.tsx` |
| Archivos no-componentes | kebab-case.ts | `api-client.ts`, `graph-utils.ts` |
| Interfaces/Types | PascalCase con prefijo descriptivo | `ChatMessage`, `PidEquipment` |
| Enums | PascalCase | `NodeType.Equipment` |

**Linter/Formatter:** ESLint + Prettier

```js
// .eslintrc.js
module.exports = {
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "prettier",
  ],
  parser: "@typescript-eslint/parser",
  rules: {
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "react/react-in-jsx-scope": "off",
  },
};
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```

### XML (drawio-library)

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Atributos DEXPI | snake_case con prefijo `dexpi_` | `dexpi_class="CentrifugalPump"` |
| Tag numbers | UPPER con guion | `P-101`, `TIC-201`, `HE-301` |
| IDs de shapes | kebab-case descriptivo | `centrifugal-pump`, `gate-valve` |
| Nombres de archivos de shapes | kebab-case | `centrifugal-pump.xml`, `gate-valve.xml` |

## Formato de Commits

```
tipo(alcance): descripcion breve en imperativo

Cuerpo opcional con mas detalle.

Tipos:
  feat     - Nueva funcionalidad
  fix      - Correccion de bug
  docs     - Solo documentacion
  style    - Formato, sin cambio de logica
  refactor - Refactoring sin cambio funcional
  test     - Anadir o corregir tests
  chore    - Mantenimiento, dependencias, configs
  ci       - Cambios en CI/CD

Alcances validos:
  converter  - pid-converter
  kg         - pid-knowledge-graph
  rag        - pid-rag
  web        - pid-web
  mcp        - pid-mcp-server
  library    - drawio-library
  docker     - Docker/docker-compose
  ci         - GitHub Actions
  docs       - Documentacion
  e2e        - Tests E2E
```

Ejemplos:
```
feat(converter): add nozzle-to-nozzle topology reconstruction
fix(kg): resolve condensation losing signal lines
test(e2e): add Playwright test for chat streaming flow
chore(docker): optimize api Dockerfile with multi-stage build
docs(library): add usage guide for P&ID symbol library
```

## Formato de Branches

```
tipo/descripcion-breve

Tipos: feat/, fix/, docs/, test/, chore/, ci/

Ejemplos:
  feat/converter-bidirectional-import
  fix/neo4j-connection-retry
  test/e2e-chat-streaming
```

Branch principal: `main`
Cada oleada puede trabajar en `main` directamente (Agent Teams coordina) o en branches por teammate si se prefiere aislamiento.

## Estructura de Carpetas con Ownership

```
pid-inteligente/
├── CLAUDE.md                                    ← Lead (solo lectura para teammates)
├── .claude/                                     ← Lead
├── specs/                                       ← Solo lectura (referencia)
│
├── docs/                                        ← Documentacion
│   ��── adr/                                     ← Arquitecto
��   ├── api/                                     ← Documentacion
│   └── guides/                                  ← Documentacion
│
├── packages/
│   ├── drawio-library/                          ← Frontend
│   │   ├── shapes/
│   │   │   ├── equipment/                       ← ~15 simbolos
│   │   │   ├── piping/                          ← ~15 simbolos
│   │   │   ├── instrumentation/                 ← ~15 simbolos
│   │   │   └── lines/                           ← Estilos de linea
│   │   ├── templates/                           ← Plantilla .drawio
│   │   ├── examples/                            ← P&ID de ejemplo
│   │   └── pid-library.xml                      ← Biblioteca empaquetada
│   │
│   ��── pid-converter/                           ← Backend
│   │   ├── src/pid_converter/
│   │   │   ├── __init__.py
│   │   │   ├── parser/                          ← mxGraph XML parser
│   │   │   │   ├── __init__.py
│   │   │   │   └── mxgraph_parser.py
│   │   │   ├── mapper/                          ← Modelo interno -> pyDEXPI
│   ���   │   │   ├── __init__.py
│   │   │   │   └── dexpi_mapper.py
│   │   │   ├���─ topology/                        ← Nozzle-a-nozzle
│   │   │   │   ├── __init__.py
│   │   │   │   └── topology_resolver.py
│   │   │   ├── serializer/                      ← pyDEXPI -> Proteus XML
│   │   │   │   ├── __init__.py
│   │   │   │   └── proteus_serializer.py
│   │   ���   ├── importer/                        ← DEXPI -> Draw.io
│   │   │   │   ├── __init__.py
│   │   │   │   └── dexpi_importer.py
│   │   │   ├── validator/                       ← Validacion P&ID
│   │   │   │   ├── __init__.py
│   │   │   │   └── pid_validator.py
│   │   │   └── cli.py                           ← CLI Typer
│   │   ├── tests/
│   │   │   ├── test_parser.py
│   │   │   ├── test_mapper.py
│   │   │   ├── test_topology.py
│   │   │   ��── test_serializer.py
│   │   │   ├── test_importer.py
│   │   │   ├── test_validator.py
��   │   │   ├���─ test_cli.py
│   │   │   └── fixtures/                        ← .drawio y .xml de prueba
│   │   └── pyproject.toml
│   │
│   ├── pid-knowledge-graph/                     ← Base de Datos
│   │   ├── src/pid_knowledge_graph/
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py
│   │   │   ├── condensation.py
│   │   │   ├── semantic.py
│   │   ��   └── neo4j_store.py
│   │   ├── migrations/
│   │   │   └── 001_initial_schema.cypher
│   │   ├── tests/
│   │   │   ├── test_graph_builder.py
│   │   │   ├── test_condensation.py
│   │   │   ├── test_semantic.py
│   │   │   ├── test_neo4j_store.py
│   │   │   └── fixtures/
│   │   └── pyproject.toml
│   │
│   ├── pid-rag/                                 ← Backend
│   │   ├── src/pid_rag/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── app.py                       ← FastAPI app
│   │   │   │   └── routes/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── convert.py
│   │   │   │       ├── graph.py
│   │   │   │       ├── chat.py
│   │   │   │       └── validate.py
│   │   │   ├── retrieval/
│   │   │   │   ├── __init__.py
│   │   │   │   └── graph_rag.py
│   │   │   ├── prompts/
│   │   │   │   ├── __init__.py
│   │   │   │   └── engineering.py               ← System prompt ISA 5.1
│   │   ��   └── config.py
│   │   ├── tests/
│   │   │   ├── test_routes/
│   ��   │   ├── test_retrieval.py
���   │   │   └── test_prompts.py
│   │   └─��� pyproject.toml
│   │
│   ├── pid-web/                                 ← Frontend
│   │   ├── src/
│   ���   │   ├── components/
│   │   │   │   ├── chat/
│   │   │   │   │   ├── ChatPanel.tsx
│   │   │   │   │   ├── MessageBubble.tsx
│   │   ���   │   │   └── ChatInput.tsx
│   │   │   │   ├── graph/
│   │   │   │   │   ├── GraphViewer.tsx
│   │   │   │   │   └── NodeDetail.tsx
��   │   │   │   ├── pid/
│   │   │   │   │   └── PidViewer.tsx
│   │   │   │   └── common/
│   │   │   │       ├── Layout.tsx
│   │   │   │       ├── Sidebar.tsx
│   ��   │   │       └── FileUpload.tsx
│   │   │   ├── pages/
���   │   │   │   ├── HomePage.tsx
│   │   │   │   └── PidPage.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useChat.ts
│   │   │   │   └── useGraph.ts
│   │   │   ├── stores/
│   │   │   │   ├── chatStore.ts
│   │   │   │   └── pidStore.ts
│   │   │   ├── services/
��   │   │   │   ├── api-client.ts
│   │   │   │   └── sse-client.ts
��   │   │   ├── types/
│   ���   │   │   ├── api.ts
│   │   │   │   ├── chat.ts
│   │   │   │   └── graph.ts
│   │   │   ├── styles/
│   │   │   │   └── globals.css
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── public/
│   │   ├── tests/
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   └���─ tsconfig.json
│   │
│   └── pid-mcp-server/                          ← Integraciones
│       ├── src/
│       │   ├── tools/
│       │   │   ├── convert.ts
│       │   │   ├── graph.ts
│       │   ���   ├── validate.ts
│       │   │   └── drawio.ts
│       │   ├── resources/
│       │   └── index.ts
│       ���── tests/
│       ├── package.json
│       └── tsconfig.json
│
├── docker/                                      ← DevOps
│   ├── Dockerfile.api
│   ├─�� Dockerfile.web
│   ├── Dockerfile.mcp
│   └── neo4j/
│       └── init.cypher                          ← Base de Datos define, DevOps integra
│
├── .github/workflows/                           ← DevOps
│   ├── ci-python.yml
│   ├─��� ci-typescript.yml
│   ├── e2e.yml
│   └── publish.yml
│
├── e2e/                                         ← Testing
│   ├── tests/
│   │   ├── pipeline.spec.ts
│   │   ├── chat-streaming.spec.ts
│   │   ├── graph-viewer.spec.ts
│   │   ├── converter-roundtrip.spec.ts
│   │   └── dexpi-reference.spec.ts
│   ├── fixtures/
│   └── playwright.config.ts
│
├── docker-compose.yml                           ← DevOps
├── docker-compose.dev.yml                       ← DevOps
├── ruff.toml                                    ← Arquitecto
├── .eslintrc.js                                 ← Arquitecto
├── .prettierrc                                  ← Arquitecto
├���─ .gitignore
└── README.md                                    ← Documentacion
```

## Reglas Globales (todos los teammates)

1. **Trabajar SOLO dentro de tu scope exclusivo.** Si necesitas tocar un archivo compartido, coordina con el Lead primero.
2. **Ejecutar verificacion antes de completar tarea.** El hook `verify-task.sh` lo fuerza, pero hazlo proactivamente.
3. **No hardcodear credenciales, API keys ni secretos.** Usar variables de entorno via `.env` (no committed) o `config.py` con Pydantic BaseSettings.
4. **Commits siguen el formato convencional** (`tipo(alcance): descripcion`).
5. **Documentar decisiones no obvias** con comentarios concisos en el codigo o en un ADR si es arquitectural.
6. **No instalar dependencias sin justificacion.** Preferir lo que ya esta en el stack definido.

## Reglas por Teammate

### Arquitecto
- Documentar toda decision en `docs/adr/` con formato ADR estandar (Estado, Contexto, Decision, Consecuencias)
- No implementar logica de negocio — solo estructura, configs y ADRs
- README.md en cada package con: descripcion, instalacion, uso basico

### Backend
- Test unitario por cada modulo publico del conversor
- Test por cada endpoint de la API
- Documentar la API con docstrings en las rutas FastAPI (genera OpenAPI automaticamente)
- Validar inputs en el router (Pydantic models como request body)
- Manejar errores con HTTPException y codigos de estado correctos
- El system prompt de ingenieria debe ser revisable/editable sin cambiar codigo (archivo separado o constante documentada)

### Base de Datos
- Cada migracion Cypher debe ser idempotente (usar `CREATE CONSTRAINT IF NOT EXISTS`)
- Documentar el modelo de datos: tipos de nodos, tipos de relaciones, propiedades
- Queries Cypher con parametros (nunca string interpolation — riesgo de inyeccion)
- Indices en propiedades usadas frecuentemente en queries (tag_number, dexpi_class, pid_id)

### Frontend (drawio-library)
- Cada simbolo debe tener TODOS los atributos DEXPI obligatorios como custom properties
- Atributos opcionales incluidos con valor vacio (el ingeniero los rellena)
- Stencils XML probados en Draw.io desktop Y web
- Nomenclatura de simbolos alineada con ISA 5.1

### Frontend (pid-web)
- Componentes pequenos y reutilizables (<150 lineas)
- No llamadas API directas desde componentes — usar hooks + TanStack Query
- Estado global solo en Zustand stores, estado local con useState
- Accesibilidad basica: labels en formularios, contraste suficiente, navegacion por teclado en el chat

### Integraciones
- Cada MCP tool debe tener description clara y schema de parametros con jsonSchema
- Manejar timeouts: si la API no responde en 30s, devolver error descriptivo
- Logging de cada llamada a la API (tool invocado, endpoint, status code, duracion)

### Testing
- Nombres de tests descriptivos: `test_converter_roundtrip_preserves_nozzle_connections`
- Fixtures reutilizables en `fixtures/` (no duplicar .drawio/.xml de prueba)
- Tests E2E cubren los 5 flujos principales de `specs/02_producto.md`
- No testear implementacion interna — testear comportamiento publico

### Documentacion
- Todas las guias deben tener un ejemplo ejecutable (no solo texto)
- Comandos de ejemplo deben ser copy-pasteable y funcionar
- Screenshots/diagramas donde ayuden a la comprension
- Mantener tabla de contenidos en guias largas

### DevOps
- Dockerfiles optimizados con multi-stage builds
- Secretos nunca hardcodeados — usar GitHub Secrets en CI, `.env` en local
- Workflows validados con actionlint antes de commit
- docker-compose.yml debe levantar todo con un solo `docker-compose up`

## Comandos de Verificacion por Teammate

| Teammate | Comando | Cuando |
|----------|---------|--------|
| Arquitecto | `tree -L 4 packages/` | Tras crear scaffolding |
| Arquitecto | `ruff check --config ruff.toml .` | Tras crear config |
| Backend | `cd packages/pid-converter && python -m pytest tests/ -v --cov=pid_converter --cov-report=term-missing` | Antes de completar |
| Backend | `cd packages/pid-rag && python -m pytest tests/ -v --cov=pid_rag --cov-report=term-missing` | Antes de completar |
| Backend | `ruff check packages/pid-converter/ packages/pid-rag/` | Antes de completar |
| Base de Datos | `cd packages/pid-knowledge-graph && python -m pytest tests/ -v --cov=pid_knowledge_graph --cov-report=term-missing` | Antes de completar |
| Base de Datos | `ruff check packages/pid-knowledge-graph/` | Antes de completar |
| Frontend | `cd packages/pid-web && npm run build && npm run test` | Antes de completar (pid-web) |
| Frontend | Abrir `pid-library.xml` en Draw.io, colocar 5 simbolos, verificar metadatos | Antes de completar (drawio-library) |
| Integraciones | `cd packages/pid-mcp-server && npm run build && npm run test` | Antes de completar |
| Testing | `npx playwright test e2e/` | Al finalizar E2E |
| Testing | `python -m pytest --cov --cov-report=term-missing` (global) | Al finalizar suite |
| DevOps | `docker-compose config` | Tras cambios en compose |
| DevOps | `docker-compose build` | Antes de completar |
| Documentacion | Verificar links internos y comandos de ejemplo | Antes de completar |
| **Todos** | `ruff check .` (Python) o `npx eslint .` (TS) | **Siempre** |

## Configuraciones

### pyproject.toml base (Python packages)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
extend = "../../ruff.toml"
```

### tsconfig base (TypeScript packages)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env

# TypeScript/Node
node_modules/
dist/
.next/

# IDE
.vscode/
.idea/
*.swp

# Testing
.coverage
htmlcov/
coverage/
test-results/
playwright-report/

# Docker
*.log

# OS
.DS_Store
Thumbs.db

# Neo4j local data
neo4j-data/
```

## Umbrales de Calidad

| Metrica | Umbral | Donde aplica |
|---------|--------|-------------|
| Cobertura de tests | >80% | Cada package Python y TypeScript |
| Lint errors | 0 | Todo el repositorio |
| Build errors | 0 | `npm run build` (TS) + `ruff check` (Python) |
| Tests E2E | 100% pass | Los 5 flujos principales |
| Rendimiento KG | <5 segundos | P&ID de ~50 equipos |
| Rendimiento LLM | <15 segundos | Incluye retrieval + generacion |
| Docker build | Sin errores | Los 3 Dockerfiles |
| Docker compose up | Sin errores | Stack completo limpio |

## Siguiente Paso
Avanzar a **Fase 8: Generacion** para crear el proyecto completo listo para Agent Teams.
