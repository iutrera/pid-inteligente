# Oleada 3 — API + UI + MCP

Crea un equipo para la Oleada 3: API + UI + MCP del proyecto P&ID Inteligente.
Activa delegate mode (Shift+Tab) — tu coordinas, no implementas.

Prerequisitos verificados: Oleada 2 completada. pid-converter y pid-knowledge-graph funcionales con tests pasando.

IMPORTANTE — Estrategia de desbloqueo:
Backend debe generar el schema OpenAPI (contratos de API) lo antes posible. Una vez disponible, compartirlo con Frontend e Integraciones para que implementen en paralelo. Si Backend modifica un endpoint, notificame inmediatamente para que coordine con los afectados.

## 1. Backend (pid-rag)

Eres el teammate de Backend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-rag/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente necesita una API REST que exponga la conversion, el Knowledge Graph y el chat LLM con Graph-RAG. El frontend React y el MCP server consumiran esta API.

Stack: Python 3.11+, FastAPI, Pydantic v2, Anthropic SDK, SSE (sse-starlette), pid-converter, pid-knowledge-graph.

PRIORIDAD: Genera el schema OpenAPI primero (definir todos los endpoints con sus request/response models) y notifica al Lead para compartirlo con Frontend e Integraciones.

Tarea concreta:
1. Implementar config.py: Pydantic BaseSettings con: ANTHROPIC_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, CORS_ORIGINS, MAX_UPLOAD_SIZE. Leer desde variables de entorno / .env.
2. Implementar api/app.py: FastAPI app con CORS, lifespan (conexion Neo4j), y montaje de routers.
3. Implementar api/routes/convert.py:
   - POST /api/convert/drawio-to-dexpi: recibe archivo .drawio (multipart), devuelve archivo Proteus XML
   - POST /api/convert/dexpi-to-drawio: recibe archivo Proteus XML, devuelve archivo .drawio
4. Implementar api/routes/graph.py:
   - POST /api/graph/build: recibe archivo .drawio o Proteus XML, construye KG en Neo4j, devuelve stats (num nodos, relaciones, equipos)
   - GET /api/graph/{pid_id}: devuelve el grafo condensado en formato JSON (nodos + edges) para visualizacion
   - GET /api/graph/{pid_id}/detail: devuelve el grafo detallado
5. Implementar api/routes/chat.py:
   - POST /api/chat: recibe {pid_id, message, history[]}. Usa Graph-RAG para extraer subgrafo relevante, construye prompt con contexto, llama a Claude API con streaming, devuelve SSE (Server-Sent Events).
6. Implementar api/routes/validate.py:
   - POST /api/validate: recibe archivo .drawio, ejecuta validator, devuelve lista de errores con IDs de shapes.
7. Implementar retrieval/graph_rag.py: estrategias de retrieval segun tipo de pregunta:
   - Pregunta de flujo de proceso → grafo condensado completo
   - Pregunta sobre equipo especifico → subgrafo detallado del equipo + vecinos directos
   - Pregunta sobre lazo de control → lazo completo del instrumento
   - Pregunta general → grafo condensado + summary
8. Implementar prompts/engineering.py: system prompt de ingenieria de procesos:
   - Nomenclatura ISA 5.1 (identificacion de instrumentos, funciones)
   - Interpretacion de lazos de control (PV, SP, OP, feedback)
   - Identificacion de flujos de proceso (principal, reciclo, utilidades)
   - Deteccion de errores comunes (valvulas sin instrumentacion, lineas muertas, equipos sin proteccion de sobrepresion, falta de valvulas de aislamiento)
9. Tests: test de cada endpoint con httpx TestClient, test de retrieval con grafos de fixture, test de prompts.

Archivos compartidos: packages/pid-web/src/types/ (Frontend consume tus tipos — notifica si cambias shapes de respuesta).

Antes de completar, ejecuta:
- cd packages/pid-rag && python -m pytest tests/ -v --cov=pid_rag --cov-report=term-missing
- ruff check packages/pid-rag/

Criterios de aceptacion:
- OpenAPI schema generado y compartido con el equipo
- Todos los endpoints funcionales y documentados
- Conversion via API produce los mismos resultados que pid-converter directo
- Chat con SSE streaming funciona (respuesta llega en chunks)
- Graph-RAG selecciona subgrafo correcto segun tipo de pregunta
- System prompt cubre ISA 5.1, lazos de control, deteccion de errores
- Cobertura >80%

## 2. Frontend (pid-web)

Eres el teammate de Frontend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-web/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente necesita una web UI donde el ingeniero de procesos pueda subir P&IDs, visualizar el Knowledge Graph interactivamente, y hacer preguntas en lenguaje natural sobre el proceso.

Stack: React 18, TypeScript, Vite, Tailwind CSS, Zustand, TanStack Query, Cytoscape.js.

Usa el schema OpenAPI de Backend para implementar los API clients. Pide al Lead si aun no esta disponible.

Tarea concreta:
1. Configurar el proyecto: verificar que Vite + Tailwind + Zustand + TanStack Query + React Router estan configurados. Crear src/styles/globals.css con Tailwind directives.
2. Implementar types/: definir TypeScript types que corresponden a los response models de la API (ChatMessage, GraphNode, GraphEdge, ValidationError, PidStats, etc.)
3. Implementar services/api-client.ts: funciones para llamar a cada endpoint de la API con TanStack Query (useConvert, useBuildGraph, useGraph, useValidate).
4. Implementar services/sse-client.ts: cliente SSE para consumir el streaming de /api/chat. Parsear chunks y emitir mensajes parciales.
5. Implementar stores/pidStore.ts (Zustand): P&ID activo, lista de P&IDs cargados.
6. Implementar stores/chatStore.ts (Zustand): historial de mensajes, mensaje en progreso (streaming), estado de carga.
7. Implementar components/common/Layout.tsx: layout principal con sidebar + area de contenido.
8. Implementar components/common/Sidebar.tsx: lista de P&IDs cargados, boton para subir nuevo.
9. Implementar components/common/FileUpload.tsx: drag & drop para archivos .drawio y .xml.
10. Implementar components/chat/ChatPanel.tsx: panel de chat con scroll automatico, indicador de carga.
11. Implementar components/chat/MessageBubble.tsx: burbuja de mensaje (usuario vs asistente). El asistente puede incluir referencias a equipos (renderizar como links).
12. Implementar components/chat/ChatInput.tsx: input con envio por Enter, boton de enviar.
13. Implementar components/graph/GraphViewer.tsx: visualizacion interactiva del Knowledge Graph con Cytoscape.js. Nodos como circulos/rectangulos coloreados por tipo (equipo=azul, instrumento=rojo, linea=gris). Layout automatico.
14. Implementar components/graph/NodeDetail.tsx: panel lateral que muestra detalles del nodo seleccionado (tag, tipo, atributos de ingenieria).
15. Implementar components/pid/PidViewer.tsx: panel que muestra informacion del P&ID activo (nombre, stats, errores de validacion si los hay).
16. Implementar pages/HomePage.tsx: pagina de bienvenida con instrucciones y drag & drop para subir P&ID.
17. Implementar pages/PidPage.tsx: pagina principal con layout de 3 paneles: grafo (izquierda), chat (centro), detalles (derecha). Responsive.
18. Implementar App.tsx con React Router: / -> HomePage, /pid/:id -> PidPage.
19. Tests de componentes con Vitest + Testing Library: test de ChatPanel, GraphViewer, FileUpload.

Antes de completar, ejecuta:
- cd packages/pid-web && npm run build && npm run test

Criterios de aceptacion:
- Web UI funcional con subida de archivos, chat con streaming, y grafo interactivo
- Chat muestra respuestas en tiempo real (SSE streaming)
- Grafo interactivo con nodos clickeables que muestran detalles
- Layout responsive (funciona en desktop, degradacion aceptable en tablet)
- Build sin errores, tests pasando

## 3. Integraciones (pid-mcp-server)

Eres el teammate de Integraciones en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-mcp-server/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente necesita un MCP Server que permita a agentes LLM (como Claude Code) orquestar todo el pipeline: conversion, consulta al Knowledge Graph, validacion, y operaciones en Draw.io.

Stack: TypeScript, Node.js 20+, @modelcontextprotocol/sdk, drawio-mcp-server (Gazo).

Usa el schema OpenAPI de Backend para saber que endpoints llamar. Pide al Lead si aun no esta disponible.

Tarea concreta:
1. Implementar src/index.ts: MCP Server con @modelcontextprotocol/sdk. Registrar todos los tools.
2. Implementar src/tools/convert.ts:
   - Tool "convert-drawio-to-dexpi": parametros {drawio_path: string}, llama a POST /api/convert/drawio-to-dexpi, devuelve path al XML generado
   - Tool "import-dexpi-to-drawio": parametros {dexpi_path: string}, llama a POST /api/convert/dexpi-to-drawio, devuelve path al .drawio generado
3. Implementar src/tools/graph.ts:
   - Tool "build-knowledge-graph": parametros {file_path: string}, llama a POST /api/graph/build, devuelve stats del grafo
   - Tool "query-knowledge-graph": parametros {pid_id: string, question: string}, llama a POST /api/chat, devuelve respuesta del LLM
4. Implementar src/tools/validate.ts:
   - Tool "validate-pid": parametros {drawio_path: string}, llama a POST /api/validate, devuelve lista de errores formateada
5. Implementar src/tools/drawio.ts:
   - Integracion con drawio-mcp-server de Gazo para operaciones directas en Draw.io (crear shapes, modificar diagrama). Si Gazo no esta disponible, implementar stubs con descripcion de lo que harian.
6. Cada tool debe tener: description clara para el LLM, inputSchema con jsonSchema, manejo de errores (timeout 30s, API no disponible), logging.
7. Tests con mocks de la API FastAPI.

Antes de completar, ejecuta:
- cd packages/pid-mcp-server && npm run build && npm run test

Criterios de aceptacion:
- MCP Server arranca y registra todos los tools
- Cada tool tiene description y schema correctos
- Llamadas a la API FastAPI funcionan correctamente
- Errores manejados: timeout, API no disponible, archivo no encontrado
- Build sin errores, tests pasando

## 4. Testing (Integracion)

Eres el teammate de Testing en el proyecto P&ID Inteligente.
Tu scope exclusivo: e2e/ y tests de integracion cross-package.
NO toques codigo de produccion. Si encuentras bugs, reportalos al Lead.

Contexto: P&ID Inteligente tiene 6 packages que deben funcionar juntos. Necesitas verificar que el pipeline completo funciona de extremo a extremo.

Stack: pytest (integracion Python), Playwright (E2E), Vitest (integracion TS).

Tarea concreta (solo tests de integracion en esta oleada, E2E en oleada 4):
1. Test de integracion: pipeline de conversion
   - .drawio (con simbolos de la biblioteca) -> pid-converter -> Proteus XML -> pid-converter (import) -> .drawio
   - Verificar que ida y vuelta produce resultado equivalente (mismos nodos, mismas conexiones, mismos atributos DEXPI)
2. Test de integracion: pipeline de Knowledge Graph
   - .drawio -> pid-converter -> pyDEXPI objects -> pid-knowledge-graph -> NetworkX -> Neo4j
   - Verificar que el grafo en Neo4j tiene los nodos y relaciones correctos
   - Verificar condensacion produce grafo simplificado correcto
3. Test de integracion: Graph-RAG
   - Cargar P&ID de ejemplo en Neo4j -> hacer pregunta de tipo "flujo" -> verificar que retrieval selecciona grafo condensado
   - Hacer pregunta de tipo "equipo" -> verificar que retrieval selecciona subgrafo del equipo
4. Crear fixtures/ con archivos de prueba: .drawio de ejemplo, .xml DEXPI de referencia

Antes de completar, ejecuta:
- python -m pytest e2e/tests/ -v (los tests de integracion Python)

Criterios de aceptacion:
- Pipeline de conversion ida y vuelta funciona
- Knowledge Graph se construye correctamente desde un .drawio
- Graph-RAG selecciona subgrafos correctos por tipo de pregunta
- Fixtures documentados y reutilizables

---

Cuando todos terminen, presenta resumen de lo creado.
No marques como completo hasta que las verificaciones pasen.
