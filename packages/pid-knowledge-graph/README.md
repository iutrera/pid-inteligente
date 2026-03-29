# pid-knowledge-graph

Knowledge Graph builder para diagramas P&ID: construye grafos desde modelos pyDEXPI, aplica condensacion multi-nivel, anade etiquetas semanticas para LLM, y persiste en Neo4j.

## Arquitectura interna

```
pyDEXPI model
    |
    v
  graph_builder.py    -- pyDEXPI -> NetworkX (nodos: equipos, instrumentos,
    |                     lineas, nozzles; relaciones: has_nozzle, send_to,
    |                     controls, is_located_in)
    v
  condensation.py     -- Grafo de alto nivel: equipos como nodos, flujos
    |                     como edges dirigidas, lazos de control simplificados
    v
  semantic.py         -- Etiquetas descriptivas para LLM:
    |                     "Pump P-101 (centrifugal, 15 kW)"
    v
  neo4j_store.py      -- Persistencia en Neo4j para queries Cypher
```

## Instalacion

```bash
# Desde el monorepo (modo desarrollo)
cd packages/pid-knowledge-graph
pip install -e ".[dev]"

# Desde PyPI (cuando se publique)
pip install pid-knowledge-graph
```

### Requisitos

- Python >= 3.11
- Neo4j 5+ (para persistencia; disponible via docker-compose del proyecto)
- Dependencias: pyDEXPI, NetworkX, neo4j (driver oficial), Pydantic v2

## Uso basico

### Construir grafo desde pyDEXPI

```python
from pid_knowledge_graph.graph_builder import build_graph
from pid_knowledge_graph.condensation import condense
from pid_knowledge_graph.semantic import add_semantic_labels
from pid_knowledge_graph.neo4j_store import Neo4jStore

# Construir grafo detallado desde modelo pyDEXPI
graph = build_graph(dexpi_model)

# Condensar a grafo de alto nivel
condensed = condense(graph)

# Anadir etiquetas semanticas para LLM
add_semantic_labels(graph)
add_semantic_labels(condensed)

# Persistir en Neo4j
store = Neo4jStore(uri="bolt://localhost:7687", user="neo4j", password="password")
await store.save(graph)
await store.save(condensed)
```

### Queries Cypher (via Neo4j)

```cypher
-- Flujo principal entre dos equipos
MATCH path = (a:Equipment)-[:SEND_TO*]->(b:Equipment)
WHERE a.tag = 'T-101' AND b.tag = 'E-201'
RETURN path

-- Lazos de control sobre un equipo
MATCH (loop:InstrumentationLoop)-[:CONTROLS]->(eq:Equipment {tag: 'R-101'})
RETURN loop, eq
```

## Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=pid_knowledge_graph
```

## Migraciones Neo4j

Los scripts de migracion (constraints, indices, esquema base) estan en `migrations/`. Se ejecutan automaticamente al inicializar el store o pueden aplicarse manualmente:

```bash
cypher-shell -f migrations/001_schema.cypher
```
