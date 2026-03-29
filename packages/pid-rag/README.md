# pid-rag

Backend FastAPI con Graph-RAG para consultar Knowledge Graphs de P&ID usando Claude LLM.

Expone una API REST unificada que integra el conversor Draw.io/DEXPI, el Knowledge Graph, y el motor de consultas Graph-RAG con streaming via SSE.

## Endpoints principales

| Ruta | Descripcion |
|------|-------------|
| `POST /api/convert/drawio-to-dexpi` | Convierte archivo .drawio a Proteus XML |
| `POST /api/convert/dexpi-to-drawio` | Convierte Proteus XML a .drawio |
| `POST /api/graph/build` | Construye Knowledge Graph desde P&ID |
| `GET /api/graph/query` | Ejecuta queries sobre el Knowledge Graph |
| `POST /api/chat/` | Consulta LLM con Graph-RAG (SSE streaming) |
| `POST /api/validate/` | Valida un P&ID y retorna reporte de errores |

## Arquitectura interna

```
pid-rag/
  src/pid_rag/
    api/
      app.py          -- FastAPI application
      routes/
        convert.py    -- Endpoints de conversion
        graph.py      -- Endpoints de Knowledge Graph
        chat.py       -- Endpoints de chat LLM (SSE streaming)
        validate.py   -- Endpoints de validacion
    retrieval/        -- Graph-RAG retrieval strategies
    prompts/          -- System prompts de ingenieria (ISA 5.1, lazos de control)
    config.py         -- Settings (Pydantic BaseSettings)
```

## Instalacion

```bash
# Desde el monorepo (modo desarrollo)
cd packages/pid-rag
pip install -e ".[dev]"
```

### Requisitos

- Python >= 3.11
- Neo4j 5+ corriendo (via docker-compose del proyecto)
- API key de Anthropic (Claude) configurada
- Dependencias: FastAPI, Uvicorn, Anthropic SDK, Pydantic v2, neo4j, sse-starlette, pid-converter, pid-knowledge-graph

## Uso basico

### Levantar el servidor

```bash
# Desarrollo
uvicorn pid_rag.api.app:app --reload --port 8000

# Via docker-compose (recomendado)
docker-compose up api
```

### Configuracion

Variables de entorno (o archivo `.env`):

```env
ANTHROPIC_API_KEY=sk-ant-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Documentacion API

Con el servidor corriendo, la documentacion OpenAPI auto-generada esta disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=pid_rag
```
