# Visión del Proyecto: P&ID Inteligente — Puente Draw.io ↔ DEXPI

## Resumen Ejecutivo

P&ID Inteligente es una arquitectura open-source que permite dibujar Piping & Instrumentation Diagrams (P&IDs) en Draw.io usando una biblioteca de símbolos con metadatos semánticos alineados al estándar DEXPI (ISA 5.1 / ISO 10628), exportarlos/importarlos en formato DEXPI Proteus XML, y habilitar un LLM para interpretar, razonar y asistir sobre el proceso de planta.

El sistema cierra el ciclo completo: dibujo → traducción → grafo de conocimiento → razonamiento LLM → orquestación MCP, creando un flujo donde un ingeniero de procesos puede trabajar con P&IDs inteligentes sin depender de software propietario, y donde un agente IA con skills avanzados de ingeniería de procesos puede operar sobre estos diagramas de forma autónoma.

El stack completo es open-source (Draw.io Apache 2.0, pyDEXPI MIT, código propio bajo licencia a definir). No se depende de ningún software propietario para el flujo base.

## Problema

### Situación Actual
Los ingenieros de procesos dibujan P&IDs en AutoCAD P&ID u otras herramientas propietarias (AVEVA, COMOS, SmartPlant P&ID). Estos diagramas son fundamentalmente "dibujos tontos": contienen información visual pero no semántica. La información de proceso (tags, condiciones de diseño, lazos de control) vive separada del diagrama o se pierde entre formatos.

### Pain Points
- **Lock-in propietario**: Las herramientas industriales (AVEVA, COMOS) tienen costes de licencia elevados y formatos cerrados. Migrar entre ellas es costoso y propenso a errores.
- **P&IDs no interpretables por máquina**: Los diagramas en AutoCAD son geometría, no conocimiento. No se pueden consultar programáticamente ("¿qué instrumentos controlan la temperatura del reactor R-101?").
- **Revisiones HAZOP manuales e intensivas**: Preparar y ejecutar un HAZOP requiere que un equipo recorra manualmente cada nodo del proceso. No hay asistencia automatizada para detectar errores comunes o generar preguntas guía.
- **Interoperabilidad limitada**: Aunque existe el estándar DEXPI, la adopción es baja porque las herramientas no facilitan generar/consumir DEXPI de forma nativa.
- **Sin puente IA ↔ P&ID**: No existe un flujo establecido para que un LLM pueda leer, interpretar y operar sobre un P&ID de forma estructurada.

### Coste del Problema
- Horas de ingeniería perdidas en transcripción manual entre sistemas.
- Errores en P&IDs que solo se detectan en fases avanzadas (construcción, comisionamiento).
- HAZOPs incompletos por fatiga del equipo revisor.
- Imposibilidad de escalar revisiones de seguridad con IA.
- Dependencia de proveedores que limita la innovación y aumenta costes operativos.

## Solución Propuesta

### Visión
Un ecosistema de 5 capas que transforma Draw.io en una herramienta de P&ID de grado industrial con inteligencia artificial integrada:

| Capa | Componente | Tecnología |
|------|-----------|------------|
| 1. Dibujo | Biblioteca P&ID semántica para Draw.io | Draw.io + XML custom shapes con `<object>` tags DEXPI |
| 2. Traducción | Conversor bidireccional mxGraph XML ↔ DEXPI Proteus XML | Python (lxml + pyDEXPI) |
| 3. Grafo | P&ID Knowledge Graph | pyDEXPI → NetworkX / Neo4j |
| 4. LLM | Interfaz de consulta natural con Graph-RAG | Claude API + graph-RAG |
| 5. MCP | Orquestación bidireccional completa | Draw.io MCP Server + MCP custom |

### Propuesta de Valor
- **Open-source end-to-end**: Sin dependencia de software propietario.
- **P&IDs semánticos**: Cada símbolo lleva metadatos DEXPI desde el momento de colocarlo.
- **Interoperabilidad real**: Export/import DEXPI Proteus XML compatible con software industrial.
- **IA nativa**: Un LLM puede consultar, validar y hasta generar P&IDs.
- **Accesible**: Draw.io es gratuito, multiplataforma y ampliamente conocido.

## Usuarios Objetivo

### Perfil Principal
**Ingeniero de procesos** que diseña, revisa y mantiene P&IDs de planta. Actualmente usa AutoCAD u otras herramientas propietarias. Busca una alternativa open-source que no sacrifique la semántica del diagrama y que le permita trabajar más eficientemente con asistencia de IA.

### Perfiles Secundarios
- **Agente IA especializado**: Un agente LLM con skills avanzados de ingeniería de procesos que opera sobre P&IDs programáticamente — consulta, valida, genera y modifica diagramas de forma autónoma o semi-autónoma.
- **Equipo HAZOP**: Usa el sistema para preparar revisiones de seguridad con asistencia de IA (pre-HAZOP automatizado).
- **Ingeniero de instrumentación**: Consulta lazos de control y relaciones entre instrumentos.
- **Gerente de planta / ingeniería**: Consulta estado del diseño y obtiene respuestas en lenguaje natural sobre el proceso.

## Contexto de Mercado

### Competencia
| Solución | Tipo | Limitación principal |
|----------|------|---------------------|
| AVEVA P&ID | Propietario | Coste elevado, formato cerrado |
| COMOS (Siemens) | Propietario | Lock-in, complejidad |
| SmartPlant P&ID | Propietario | Coste, integración limitada |
| AutoCAD P&ID | Propietario | Diagramas sin semántica, sin IA |
| Draw.io (vanilla) | Open-source | Sin símbolos P&ID ni metadatos DEXPI |
| pyDEXPI (TU Delft) | Open-source (MIT) | Solo modelo de datos, sin editor visual |

### Diferenciación
- **Único stack open-source completo**: De dibujo a razonamiento IA, sin software propietario.
- **Bidireccional**: No solo exporta a DEXPI, también importa — permite editar P&IDs de otros sistemas.
- **IA integrada desde el diseño**: No es un add-on posterior; el Knowledge Graph y el LLM son capas nativas.
- **Basado en estándares**: DEXPI (ISO 15926 / Proteus XML), ISA 5.1, ISO 10628.
- **Extensible**: Arquitectura MCP permite añadir capacidades sin modificar el core.

## Restricciones Identificadas

- **pyDEXPI es un proyecto académico joven** (TU Delft, licencia MIT). Riesgo de abandono mitigable con fork.
- **El MCP de Draw.io** aún no accede a toda la shape library programáticamente. El MCP comunitario de Gazo permite crear shapes custom; para la library propia, se precargan vía XML directo.
- **Alucinaciones del LLM**: Graph-RAG mitiga al anclar respuestas en datos reales del grafo. Human-in-the-loop obligatorio para decisiones críticas. No usar para validación normativa sin revisión humana.
- **Complejidad del mapeo topológico**: Las conexiones nozzle-a-nozzle y la inferencia de dirección de flujo son la parte más compleja del conversor. Empezar con topologías simples e iterar.
- **Sin normativa regulatoria específica** que aplique al software en sí (no es un sistema de seguridad funcional), pero los P&IDs que produce deben cumplir ISA 5.1 / ISO 10628.

## Criterios de Éxito

| Fase | Criterio |
|------|----------|
| 1 — Biblioteca | Un ingeniero de procesos puede dibujar un P&ID completo en Draw.io con todos los metadatos DEXPI sin editar XML a mano |
| 2 — Conversor | El P&ID de referencia DEXPI, dibujado en Draw.io, se convierte a Proteus XML y puede importarse en AVEVA/COMOS sin errores de esquema. Importación DEXPI → Draw.io funcional |
| 3 — Knowledge Graph | El KG de un P&ID de ~50 equipos se genera en <5 segundos con todas las relaciones topológicas correctas |
| 4 — LLM | El LLM responde correctamente al 80%+ de preguntas sobre flujo de proceso, instrumentación y detección de errores básicos |
| 5 — MCP | Un usuario puede describir un sistema en lenguaje natural y obtener un P&ID dibujado en Draw.io con metadatos DEXPI completos |

## Stack Tecnológico Previsto

| Componente | Tecnología | Licencia |
|-----------|------------|----------|
| Editor de diagramas | Draw.io (desktop o web) | Apache 2.0 |
| Modelo de datos P&ID | pyDEXPI (Pydantic + NetworkX) | MIT |
| Conversor | Python (lxml, pydantic) | Por definir |
| Knowledge Graph | NetworkX (pequeño) / Neo4j (grande) | BSD / GPL |
| LLM | Claude API | SaaS |
| MCP Draw.io | drawio-mcp-server (npm) | MIT |
| MCP orquestador | MCP Server custom (TypeScript/Python) | Por definir |

## Siguiente Paso
Avanzar a **Fase 2: Definición de Producto** para delimitar el MVP funcionalidad por funcionalidad, definir alcance negativo, y especificar requisitos no funcionales.
