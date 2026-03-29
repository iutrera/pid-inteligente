# Oleada 4 — Cierre

Crea un equipo para la Oleada 4: Cierre del proyecto P&ID Inteligente.
Activa delegate mode (Shift+Tab) — tu coordinas, no implementas.

Prerequisitos verificados: Oleada 3 completada. API funcional, web UI funcional, MCP operativo, tests de integracion pasando.

## 1. Testing (E2E + Rendimiento + Referencia DEXPI)

Eres el teammate de Testing en el proyecto P&ID Inteligente.
Tu scope exclusivo: e2e/.
NO toques codigo de produccion. Si encuentras bugs, reportalos al Lead.

Contexto: El stack completo de P&ID Inteligente esta funcional. Necesitas validar los 5 flujos principales con tests E2E, verificar el test de referencia DEXPI, y medir rendimiento.

Stack: Playwright, pytest.

Tarea concreta:
1. Configurar Playwright en e2e/playwright.config.ts: base URL http://localhost:3000, timeout 30s, screenshots on failure.
2. Test E2E — Flujo 1: Dibujar y exportar
   - Abrir web UI, subir P&ID de ejemplo (.drawio), verificar que se procesa
   - Verificar que aparece en la lista de P&IDs
3. Test E2E — Flujo 2: Importar P&ID existente (si la UI lo soporta, sino via API)
4. Test E2E — Flujo 3: Consultar P&ID con IA
   - Subir P&ID, esperar procesamiento
   - Escribir pregunta en el chat: "Cual es el flujo de proceso principal?"
   - Verificar que la respuesta llega (streaming), contiene referencias a equipos del P&ID
   - Escribir segunda pregunta: "Que instrumentos controlan la temperatura?"
   - Verificar respuesta relevante
5. Test E2E — Flujo 4: Validar P&ID
   - Subir P&ID con errores intencionales (tags faltantes)
   - Verificar que la validacion reporta los errores esperados
6. Test E2E — Flujo 5: Grafo interactivo
   - Subir P&ID, ir a la vista de grafo
   - Verificar que los nodos se renderizan
   - Click en un nodo, verificar que muestra detalles
7. Test de referencia DEXPI:
   - Tomar el P&ID de referencia DEXPI (C01V04-VER.EX01.xml si disponible, o el P&ID de ejemplo)
   - Convertir con pid-converter
   - Comparar estructura de la salida (no byte-a-byte, sino nodos y relaciones)
   - Documentar desviaciones si las hay
8. Tests de rendimiento:
   - Medir tiempo de generacion del Knowledge Graph con P&ID de ~50 equipos: debe ser <5 segundos
   - Medir tiempo de respuesta del LLM (retrieval + generacion): debe ser <15 segundos
9. Reporte de cobertura global: ejecutar todos los tests de todos los packages y generar reporte combinado.

Antes de completar, ejecuta:
- npx playwright test e2e/
- python -m pytest --cov --cov-report=term-missing (global)

Criterios de aceptacion:
- Los 5 flujos E2E pasan
- Test de referencia DEXPI pasa o desviaciones documentadas
- Rendimiento: KG <5s, LLM <15s
- Cobertura global >80%

## 2. Documentacion

Eres el teammate de Documentacion en el proyecto P&ID Inteligente.
Tu scope exclusivo: docs/ (excepto docs/adr/) y README.md raiz.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente es un puente Draw.io <-> DEXPI con Knowledge Graph e interfaz LLM. Tiene 6 packages en un monorepo. Los usuarios son ingenieros de procesos y desarrolladores.

Tarea concreta:
1. Crear docs/guides/getting-started.md:
   - Requisitos previos (Docker, Node.js 20+, Python 3.11+)
   - Instalacion rapida con Docker: docker-compose up
   - Instalacion con pip: pip install pid-converter pid-knowledge-graph
   - Primer uso: subir un P&ID de ejemplo, hacer una pregunta
   - Troubleshooting basico
2. Crear docs/guides/drawio-library.md:
   - Como cargar la biblioteca en Draw.io (URL del parametro clibs)
   - Como usar los simbolos: arrastrar, rellenar metadatos DEXPI
   - Explicacion de atributos DEXPI por tipo de simbolo
   - Como usar las capas (Process, Instrumentation, Annotations)
   - Ejemplo paso a paso: dibujar un lazo de control
3. Crear docs/guides/converter.md:
   - Uso del CLI: pid-converter convert, import, validate
   - Uso programatico: import desde Python
   - Limitaciones conocidas (topologias complejas, etc.)
4. Crear docs/guides/knowledge-graph.md:
   - Que es el Knowledge Graph y como se construye
   - Grafo detallado vs grafo condensado
   - Explorar en Neo4j Browser (http://localhost:7474)
   - Queries Cypher de ejemplo
5. Crear docs/guides/web-ui.md:
   - Como acceder (http://localhost:3000)
   - Subir un P&ID
   - Usar el chat: tipos de preguntas que funciona bien
   - Interpretar el grafo interactivo
   - Interpretar errores de validacion
6. Crear docs/guides/mcp-server.md:
   - Como configurar el MCP server para Claude Code
   - Tools disponibles y que hacen
   - Ejemplo de uso conversacional
7. Crear docs/api/: copiar/referenciar el schema OpenAPI auto-generado por FastAPI. Documentar endpoints con ejemplos de request/response.
8. Crear README.md raiz:
   - Descripcion del proyecto (2-3 parrafos)
   - Diagrama de arquitectura (ASCII o mermaid)
   - Quick start (3 pasos: clone, docker-compose up, abrir browser)
   - Links a cada guia
   - Estructura del monorepo
   - Contributing
   - Licencia

Antes de completar:
- Verificar que los comandos de ejemplo funcionan
- Verificar que los links internos apuntan a archivos existentes

Criterios de aceptacion:
- Un usuario nuevo puede ir de cero a consultar un P&ID siguiendo getting-started
- Cada guia tiene al menos un ejemplo ejecutable
- API documentada con endpoints y ejemplos
- README.md con quick start funcional en 3 pasos
- No hay links rotos

## 3. DevOps (Deploy Pipeline)

Eres el teammate de DevOps en el proyecto P&ID Inteligente.
Tu scope exclusivo: .github/workflows/, docker/, docker-compose.*.
NO toques archivos fuera de tu scope.

Contexto: El proyecto P&ID Inteligente esta completo y necesita un pipeline de publicacion para PyPI y Docker Hub, mas optimizacion de los Dockerfiles existentes.

Tarea concreta:
1. Crear .github/workflows/publish.yml:
   - Trigger: push de tags v*.*.*
   - Job 1: Publish Python packages a PyPI (pid-converter, pid-knowledge-graph)
   - Job 2: Build y push Docker images a Docker Hub (o GitHub Container Registry)
   - Usar GitHub Secrets para credenciales
2. Optimizar Dockerfiles existentes:
   - Verificar que son multi-stage
   - Minimizar tamano de imagen (imagen final < 500MB)
   - Usar .dockerignore para excluir archivos innecesarios
3. Crear .dockerignore:
   - Excluir: .git, node_modules, __pycache__, .venv, .env, docs/, specs/, e2e/, .github/
4. Validar que docker-compose up levanta todo limpio desde cero:
   - Neo4j con init.cypher
   - API conecta a Neo4j
   - Web sirve la app React
   - MCP server arranca
5. Actualizar docker-compose.dev.yml si es necesario para desarrollo local

Antes de completar, ejecuta:
- docker-compose config
- docker-compose build

Criterios de aceptacion:
- publish.yml valido con jobs para PyPI y Docker
- Dockerfiles optimizados (multi-stage, < 500MB)
- .dockerignore creado
- docker-compose up desde cero funciona sin errores
- No hay credenciales hardcodeadas

---

Este es el checkpoint final — el MVP debe estar completo.
Cuando todos terminen, presenta resumen de lo creado y estado del proyecto.
No marques como completo hasta que TODAS las verificaciones pasen.
