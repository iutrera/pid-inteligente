# ADR-003: Neo4j como store obligatorio del Knowledge Graph

## Estado

Aceptada

## Contexto

El usuario trabaja con P&IDs grandes. NetworkX en memoria no escala para persistencia ni queries complejas multi-sesion. Se necesita una base de datos de grafos que soporte queries Cypher complejas y persistencia entre sesiones.

## Decision

Neo4j como store principal del Knowledge Graph. NetworkX se usa como formato intermedio para construccion y condensacion antes de persistir.

El flujo es: pyDEXPI -> NetworkX (construccion + condensacion) -> Neo4j (persistencia + queries).

## Consecuencias

### Positivas

- Queries Cypher potentes para Graph-RAG (subgrafos por tipo de pregunta)
- Persistencia entre sesiones (el grafo sobrevive al proceso Python)
- Visualizacion nativa en Neo4j Browser para debugging y exploracion

### Negativas

- Dependencia de infraestructura (mitigada con Docker: `docker-compose` levanta Neo4j automaticamente)
