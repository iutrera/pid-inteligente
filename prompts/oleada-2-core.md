# Oleada 2 — Core Data

Crea un equipo para la Oleada 2: Core Data del proyecto P&ID Inteligente.
Activa delegate mode (Shift+Tab) — tu coordinas, no implementas.

Prerequisitos verificados: Oleada 1 completada. Scaffolding listo, biblioteca Draw.io con ~60 simbolos, Docker y CI funcionando.

## 1. Backend (pid-converter)

Eres el teammate de Backend en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-converter/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente convierte P&IDs de Draw.io (.drawio XML) a DEXPI Proteus XML y viceversa, usando pyDEXPI como modelo canonico. Los simbolos Draw.io tienen atributos custom con prefijo dexpi_ que mapean directamente a clases pyDEXPI.

Stack: Python 3.11+, lxml, pyDEXPI, Pydantic v2, NetworkX, Typer.

Tarea concreta:
1. Implementar parser/mxgraph_parser.py: leer .drawio (mxGraphModel XML), extraer todos los `<object>` y `<mxCell>` con sus atributos custom (dexpi_class, tag_number, etc.) y la topologia de conexiones (source/target de las edges). Producir un modelo interno intermedio.
2. Implementar mapper/dexpi_mapper.py: para cada nodo del modelo interno, instanciar la clase Pydantic pyDEXPI correspondiente segun el atributo dexpi_class. Rellenar los atributos de ingenieria desde los custom properties del shape.
3. Implementar topology/topology_resolver.py: convertir edges Draw.io (con source/target) en PipingNetworkSegments conectados a los Nozzles de los equipos. Inferir direccion de flujo. ESTA ES LA PARTE MAS COMPLEJA — empezar con topologias lineales (A -> B -> C), luego ramificaciones simples (A -> B, A -> C). Documentar limitaciones.
4. Implementar serializer/proteus_serializer.py: usar el serializador de pyDEXPI para generar Proteus XML conforme al esquema DEXPI. Incluir posicionamiento grafico (coordenadas de los shapes) en el ShapeCatalogue.
5. Implementar importer/dexpi_importer.py: leer Proteus XML con pyDEXPI, generar archivo .drawio con shapes correctos (mapeando clases DEXPI a los simbolos de la biblioteca) y conexiones. Esta es la bidireccionalidad.
6. Implementar validator/pid_validator.py: comprobacion de completitud de tags, conexiones sin nozzle asignado, lineas sin numero, instrumentos sin lazos de control. Reporte con referencia al ID del shape en Draw.io.
7. Implementar cli.py: CLI con Typer. Comandos: `pid-converter convert <input.drawio> <output.xml>`, `pid-converter import <input.xml> <output.drawio>`, `pid-converter validate <input.drawio>`.
8. Tests unitarios en tests/: un test file por modulo. Usar fixtures/ para archivos .drawio y .xml de prueba. El P&ID de ejemplo de la Oleada 1 (packages/drawio-library/examples/) es el fixture principal.

Nota importante: Si topology/ se complica demasiado, implementar soporte basico (topologia lineal) y marcar ramificaciones complejas como TODO. No bloquear el resto del conversor por esto.

Antes de completar, ejecuta:
- cd packages/pid-converter && python -m pytest tests/ -v --cov=pid_converter --cov-report=term-missing
- ruff check packages/pid-converter/

Criterios de aceptacion:
- Conversion Draw.io -> DEXPI produce XML valido conforme al esquema
- Importacion DEXPI -> Draw.io produce .drawio con shapes y conexiones correctas
- Ida y vuelta (Draw.io -> DEXPI -> Draw.io) produce resultado equivalente
- Topologia nozzle-a-nozzle correcta para topologias lineales (minimo)
- Validador detecta: tags faltantes, conexiones sin nozzle, lineas sin numero
- CLI funcional con los 3 comandos
- Cobertura >80%

## 2. Base de Datos (pid-knowledge-graph)

Eres el teammate de Base de Datos en el proyecto P&ID Inteligente.
Tu scope exclusivo: packages/pid-knowledge-graph/ y docker/neo4j/.
NO toques archivos fuera de tu scope.

Contexto: P&ID Inteligente construye un Knowledge Graph de P&IDs a partir del modelo pyDEXPI. El grafo se persiste en Neo4j para queries Cypher que alimentan el sistema Graph-RAG. El grafo necesita tanto una vista detallada (todos los nodos) como una vista condensada (alto nivel para el LLM).

Stack: Python 3.11+, pyDEXPI, NetworkX, neo4j (driver oficial, async), Neo4j 5+.

Tarea concreta:
1. Implementar graph_builder.py: usar el parser de pyDEXPI a NetworkX para obtener el grafo completo del P&ID con todos los nodos (equipos, instrumentos, lineas, nozzles) y relaciones (has_nozzle, send_to, controls, is_located_in). Cada nodo tiene propiedades: id, type, tag_number, dexpi_class, y atributos de ingenieria.
2. Implementar condensation.py: generar grafo de alto nivel. Equipos principales como nodos, flujos de proceso como edges dirigidas, lazos de control como relaciones simplificadas. La condensacion colapsa nozzles y segmentos de piping en conexiones directas equipo-a-equipo. Seguir la tecnica de la TU Delft.
3. Implementar semantic.py: etiquetas descriptivas para nodos y edges que el LLM pueda interpretar. Formato: "Pump P-101 (centrifugal, 15 kW, design: 10 bar / 150 C)" con unidades, condiciones de diseno y codigos de servicio. Etiquetas de edges: "Process flow: 4\" CS, Cooling Water".
4. Implementar neo4j_store.py: carga y consulta del grafo en Neo4j. Funciones:
   - load_graph(pid_id, nx_graph): carga un grafo NetworkX completo en Neo4j
   - get_neighbors(node_id, depth=1): vecinos directos o a N saltos
   - get_flow_path(from_tag, to_tag): camino de flujo entre dos equipos
   - get_control_loop(instrument_tag): lazo de control completo de un instrumento
   - get_subgraph_by_area(area): subgrafo de un area/servicio
   - get_condensed_graph(pid_id): grafo condensado completo
   TODAS las queries con parametros (nunca string interpolation).
5. Crear migrations/001_initial_schema.cypher: constraints de unicidad (tag_number + pid_id), indices por tipo de nodo, indices por tag_number y dexpi_class.
6. Crear docker/neo4j/init.cypher: schema inicial para el contenedor (ejecuta migrations).
7. Tests unitarios: test por cada modulo. Para neo4j_store, usar testcontainer de Neo4j o mock. Fixtures con grafos NetworkX pre-construidos.

Archivos compartidos: docker/neo4j/init.cypher (DevOps lo monta en el contenedor — notifica si cambias schema).

Antes de completar, ejecuta:
- cd packages/pid-knowledge-graph && python -m pytest tests/ -v --cov=pid_knowledge_graph --cov-report=term-missing
- ruff check packages/pid-knowledge-graph/

Criterios de aceptacion:
- Grafo de un P&ID de ejemplo se genera correctamente con todos los nodos y relaciones
- Condensacion produce grafo de alto nivel correcto (equipos como nodos, flujos como edges)
- Etiquetas semanticas son legibles y completas (nombre, tipo, unidades, condiciones)
- Neo4j store: carga, query por vecinos, query por camino, query por lazo funcionan
- Migrations crean constraints e indices sin errores
- Queries con parametros (no string interpolation)
- Cobertura >80%

---

Nota para el Lead: Backend es la ruta critica. Si se bloquea en topology/ (nozzle-a-nozzle), permitir que avance con el resto y deje topology/ con soporte basico (lineal). Base de Datos puede usar el output de Backend (pyDEXPI objects) para construir el grafo aunque el conversor no este 100% completo.

Cuando todos terminen, presenta resumen de lo creado.
No marques como completo hasta que las verificaciones pasen.
