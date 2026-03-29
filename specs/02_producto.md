# Especificación de Producto: P&ID Inteligente

## Alcance del MVP

### Funcionalidades Core (Must Have)

| ID | Funcionalidad | Descripción | Fase |
|----|---------------|-------------|------|
| F1 | Biblioteca P&ID semántica completa | ~60 símbolos P&ID como custom shapes Draw.io con metadatos DEXPI (dexpi_class, tag_number, condiciones de diseño, etc.). Stencils XML nativos para los 20 más comunes, SVG referenciado para el resto | 1 |
| F2 | Plantilla base Draw.io | Archivo .drawio con capas preconfiguradas: Process, Instrumentation, Annotations | 1 |
| F3 | Convenciones de conexión | Líneas = PipingNetworkSegments con atributos (line_number, nominal_diameter, fluid_code, etc.). Signal lines diferenciadas con atributos propios | 1 |
| F4 | Distribución como biblioteca | Publicación como .xml cargable vía URL (parámetro clibs de Draw.io) | 1 |
| F5 | Guía de uso con ejemplo | P&ID de referencia: tanque → bomba → válvula de control → intercambiador con TIC | 1 |
| F6 | Parser mxGraph XML | Lectura de .drawio: extracción de `<object>` y `<mxCell>` con atributos custom y topología de conexiones | 2 |
| F7 | Mapper a pyDEXPI | Instanciación de clases Pydantic pyDEXPI desde atributos dexpi_class de los shapes | 2 |
| F8 | Reconstrucción topológica | Conversión de edges Draw.io a PipingNetworkSegments con conexiones nozzle-a-nozzle e inferencia de dirección de flujo | 2 |
| F9 | Serialización a Proteus XML | Generación de archivo .xml conforme al esquema DEXPI con posicionamiento gráfico en ShapeCatalogue | 2 |
| F10 | Importación DEXPI → Draw.io | Lectura de Proteus XML y generación de archivo .drawio con shapes y conexiones correctas (bidireccionalidad) | 2 |
| F11 | Validador de P&ID | Comprobación de: completitud de tags, conexiones sin nozzle, líneas sin número, instrumentos sin lazos. Reporte con referencia al ID del shape | 2 |
| F12 | Test contra P&ID de referencia DEXPI | Conversión del C01V04-VER.EX01.xml de referencia DEXPI como test de aceptación | 2 |
| F13 | Grafo detallado desde pyDEXPI | Parser a NetworkX con nodos (equipos, instrumentos, líneas, nozzles) y relaciones (has_nozzle, send_to, controls, is_located_in) | 3 |
| F14 | Condensación a grafo de alto nivel | Grafo simplificado: equipos como nodos, flujos como edges dirigidas, lazos de control simplificados | 3 |
| F15 | Etiquetas semánticas | Labels descriptivos para el LLM: "Pump P-101 (centrifugal, 15 kW)" con unidades, condiciones de diseño y códigos de servicio | 3 |
| F16 | Persistencia en Neo4j | Carga del grafo en Neo4j para queries Cypher en P&IDs grandes | 3 |
| F17 | Graph-RAG retrieval | Ante una pregunta, extracción del subgrafo relevante como contexto para el LLM. Grafo condensado para preguntas de flujo; subgrafo detallado para preguntas de equipo específico | 4 |
| F18 | System prompt de ingeniería | Prompt especializado en nomenclatura ISA 5.1, lazos de control, flujos de proceso, detección de errores comunes | 4 |
| F19 | Consultas tipo validadas | "¿Cuál es el flujo principal?", "¿Qué controla la temperatura de R-101?", "¿Hay líneas sin válvula de aislamiento?", etc. | 4 |
| F20 | Interfaz visual de consulta | UI web para que el ingeniero de procesos interactúe con el LLM sobre sus P&IDs sin usar CLI | 4 |
| F21 | MCP Server pid-bridge | Servidor MCP con tools: crear/modificar P&IDs en Draw.io, ejecutar conversión DEXPI, consultar Knowledge Graph, ejecutar validaciones | 5 |

### Funcionalidades Diferidas (Nice to Have / Post-MVP)

| ID | Funcionalidad | Descripción | Razón de diferimiento |
|----|---------------|-------------|----------------------|
| D1 | Pre-HAZOP asistido | LLM recorre P&ID con palabras guía HAZOP (más, menos, inverso, nada) y genera preguntas para el equipo | Requiere validación extensiva con ingenieros de proceso reales |
| D2 | Flujo conversacional completo | Usuario describe sistema en lenguaje natural → LLM dibuja P&ID completo en Draw.io | Funcionalidad muy ambiciosa, requiere MVP estable primero |
| D3 | Feedback loop automático | LLM detecta problemas y propone/aplica correcciones en Draw.io tras confirmación | Depende de D2 y madurez del MCP |
| D4 | Integración directa en Draw.io | Botón/plugin nativo en Draw.io para exportar/importar DEXPI sin salir del editor | El conversor programático es suficiente para MVP |
| D5 | Soporte multi-hoja | P&IDs que abarcan múltiples hojas con referencias cruzadas | Complejidad añadida que no bloquea el flujo base |

### Alcance Negativo (NO hará el MVP)

- **No es un reemplazo completo de AVEVA/COMOS**: No implementa gestión de proyectos, control de cambios multi-usuario ni workflows de aprobación.
- **No genera documentación normativa**: No produce data sheets, instrument index ni line lists automáticamente.
- **No hace simulación de proceso**: No calcula balances de masa/energía ni dimensionamiento de equipos.
- **No implementa el modelo DEXPI completo**: Solo el subconjunto definido (Equipment, PipingComponents, PipingNetworkSegment/System, InstrumentationLoop, Nozzle, SignalLine).
- **No valida contra normativa específica**: No verifica cumplimiento de ASME, API, o códigos locales. Solo errores estructurales del P&ID.
- **No soporta 3D**: Solo diagramas 2D (P&IDs son inherentemente 2D).

## Plataformas

| Componente | Plataforma | Justificación |
|-----------|-----------|---------------|
| Biblioteca P&ID | Draw.io desktop + web | El ingeniero dibuja donde prefiera |
| Conversor drawio2dexpi | Python CLI + API programática | Integrable en pipelines y scripts |
| Knowledge Graph | Servicio Python + Neo4j | Backend procesable |
| Interfaz LLM | Aplicación web | El ingeniero necesita algo visual, no CLI |
| MCP Server | Servicio local/remoto | Orquestación programática |

## Requisitos No Funcionales

### Rendimiento
- Conversión Draw.io → DEXPI de un P&ID de ~50 equipos: < 10 segundos
- Conversión DEXPI → Draw.io de un P&ID de ~50 equipos: < 10 segundos
- Generación del Knowledge Graph de ~50 equipos: < 5 segundos
- Respuesta del LLM a consultas sobre el P&ID: < 15 segundos (incluye retrieval + generación)
- Carga de la interfaz web: < 3 segundos

### Disponibilidad
- Herramienta de uso local/individual primariamente. No requiere SLA de alta disponibilidad.
- Neo4j y la web UI deben poder correr en local (docker-compose) o en un servidor.

### Seguridad
- Los P&IDs pueden contener información confidencial de planta. El procesamiento debe poder ser 100% local excepto la llamada al LLM.
- Opción de usar LLM local (Ollama/similar) para entornos air-gapped en el futuro (no MVP).
- No se almacenan credenciales en el repositorio.

### Escalabilidad
- MVP diseñado para uso individual o equipo pequeño (1-5 usuarios concurrentes).
- Arquitectura preparada para escalar (Neo4j, API REST, MCP), pero no se optimiza para alta concurrencia en MVP.

## Integraciones

| Sistema | Tipo | Prioridad | Complejidad | Notas |
|---------|------|-----------|-------------|-------|
| Draw.io (desktop/web) | Biblioteca de símbolos + MCP | Must Have | Media | Biblioteca vía clibs, MCP vía drawio-mcp-server |
| pyDEXPI | Librería Python | Must Have | Media | Modelo Pydantic + parser NetworkX |
| DEXPI Proteus XML | Formato de intercambio | Must Have | Alta | Lectura y escritura conforme al esquema |
| Neo4j | Base de datos de grafos | Must Have | Media | Persistencia del Knowledge Graph |
| Claude API | LLM | Must Have | Baja | Graph-RAG + system prompt |
| AVEVA/COMOS/SmartPlant | Importación de DEXPI generado | Validación | Alta | Test de aceptación: que el XML generado se importe sin errores |
| Draw.io MCP Server (Gazo) | Orquestación | Must Have (F5) | Media | Crear/modificar shapes programáticamente |

## Flujos Principales

### Flujo 1: Dibujar y exportar P&ID
```
Ingeniero abre Draw.io → Carga biblioteca P&ID semántica → Dibuja P&ID con
metadatos → Guarda .drawio → Ejecuta conversor → Obtiene Proteus XML DEXPI
```

### Flujo 2: Importar P&ID existente
```
Ingeniero tiene Proteus XML de otro sistema → Ejecuta conversor inverso →
Obtiene .drawio con shapes y conexiones → Edita en Draw.io → Re-exporta
```

### Flujo 3: Consultar P&ID con IA
```
Ingeniero sube .drawio o DEXPI XML → Sistema genera Knowledge Graph → Carga
en Neo4j → Ingeniero abre interfaz web → Hace preguntas en lenguaje natural →
LLM responde con contexto del grafo (Graph-RAG)
```

### Flujo 4: Validar P&ID
```
Ingeniero ejecuta validador sobre .drawio → Sistema reporta: tags faltantes,
conexiones sin nozzle, líneas sin número, instrumentos huérfanos → Ingeniero
corrige en Draw.io
```

### Flujo 5: Orquestación MCP
```
Agente IA recibe instrucción → Usa MCP para consultar KG → Identifica problema →
Usa MCP para ejecutar validación → Reporta hallazgos → (Post-MVP: propone y
aplica correcciones)
```

## Subconjunto DEXPI Objetivo

Clases priorizadas para el MVP:

| Categoría | Clases DEXPI |
|-----------|-------------|
| Equipment | CentrifugalPump, Tank, HeatExchanger, Column, Reactor, Compressor, Filter, Vessel, Agitator |
| PipingComponents | GateValve, GlobeValve, BallValve, ButterflyValve, CheckValve, ControlValve, SafetyValve, Reducer, Tee, Elbow, Flange, BlindFlange, SpectacleBlind, Strainer, SteamTrap |
| Piping | PipingNetworkSegment, PipingNetworkSystem, Nozzle |
| Instrumentation | InstrumentationLoop, Transmitter, Controller, Indicator, Alarm, ControlValve (actuada), SignalLine |
| Structural | Equipment supports (simplificado) |

## Siguiente Paso
Avanzar a **Fase 3: Restricciones y Recursos** para definir presupuesto, timeline, supervisión y preferencias tecnológicas.
