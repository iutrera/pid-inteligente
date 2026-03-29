# ADR-006: Distribucion dual (pip + Docker)

## Estado

Aceptada

## Contexto

Diferentes usuarios tienen diferentes necesidades: un desarrollador quiere `pip install`, un ingeniero quiere `docker-compose up`. El proyecto tiene componentes Python (conversor, KG, RAG), TypeScript (MCP, web), y Neo4j como dependencia de infraestructura.

## Decision

Los packages Python se publican en PyPI para uso programatico. El stack completo se distribuye como docker-compose para levantar todo con un solo comando.

- `pip install pid-converter` -- Para uso standalone del conversor
- `pip install pid-knowledge-graph` -- Para uso standalone del Knowledge Graph builder
- `docker-compose up` -- Para levantar el stack completo (Neo4j + FastAPI + React + MCP)

## Consecuencias

### Positivas

- Flexibilidad maxima para diferentes perfiles de usuario
- pip para uso programatico del conversor (integracion en scripts/pipelines)
- Docker para stack completo sin configurar dependencias manualmente

### Negativas

- Doble pipeline de distribucion (PyPI + Docker Hub / GitHub Container Registry)
