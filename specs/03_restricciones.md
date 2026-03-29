# Restricciones y Recursos: P&ID Inteligente

## Presupuesto

**Ilimitado.** No hay restricción de presupuesto. Esto permite:

| Concepto | Implicación |
|----------|-------------|
| Tokens Claude API | Usar claude-opus-4-6 sin restricción para Graph-RAG y system prompts largos |
| Neo4j | Instancia dedicada (Aura o self-hosted) sin preocuparse por tier gratuito |
| Hosting web UI | Servicio de hosting sin límite de tier |
| Herramientas de desarrollo | Licencias si se necesitan (aunque el stack es open-source) |
| Agent Teams (Claude Code) | Uso intensivo de teammates en paralelo sin restricción de tokens |

**Nota sobre licencias propias**: La licencia del conversor y MCP orquestador queda pendiente de decisión. No bloquea el desarrollo pero debe definirse antes de publicar.

## Timeline

**Ilimitado. Prioridad: calidad sobre velocidad.**

Estimación orientativa del plan original (con equipo de 2-3 personas):

| Fase | Duración estimada | Acumulado |
|------|-------------------|-----------|
| 1 — Biblioteca P&ID | 3-4 semanas | Semana 4 |
| 2 — Conversor bidireccional | 4-5 semanas | Semana 9 |
| 3 — Knowledge Graph | 3-4 semanas | Semana 12 |
| 4 — Interfaz LLM + Web UI | 3-4 semanas | Semana 15 |
| 5 — Orquestación MCP | 3-4 semanas | Semana 18 |
| **Total estimado** | **16-21 semanas** | **~4-5 meses** |

Con Agent Teams la paralelización puede comprimir tiempos, pero sin presión de deadline se priorizará:
- Hacer bien la topología del conversor (la parte más compleja)
- Validar exhaustivamente contra el P&ID de referencia DEXPI
- Iterar en la calidad del Graph-RAG y system prompt

**Hitos sugeridos (no obligatorios)**:
1. PoC funcional (5 símbolos + script de grafo + consulta Claude) — primer checkpoint
2. Biblioteca completa (~60 símbolos) cargable en Draw.io — Fase 1 cerrada
3. Conversión ida y vuelta Draw.io ↔ DEXPI con P&ID de referencia — Fase 2 cerrada
4. Knowledge Graph en Neo4j consultable — Fase 3 cerrada
5. Web UI funcional con Graph-RAG — Fase 4 cerrada
6. MCP Server operativo — MVP completo

## Supervisión

| Aspecto | Detalle |
|---------|---------|
| Responsable | El propio usuario (rol dual: ingeniero de procesos + desarrollador) |
| Nivel técnico | Alto — maneja tanto ingeniería de procesos como desarrollo Python/TypeScript |
| Disponibilidad | Revisa checkpoints entre oleadas de Agent Teams |
| Rol en checkpoints | Valida tanto la corrección técnica del código como la corrección de ingeniería de procesos (símbolos, topología, semántica DEXPI) |
| Decisiones delegables | Implementación, estructura de código, patrones de diseño |
| Decisiones no delegables | Subconjunto DEXPI, convenciones de P&ID, semántica de los símbolos, criterios de validación de ingeniería |

**Implicación para Agent Teams**: Los spawn prompts deben ser lo suficientemente detallados para que los teammates trabajen sin supervisión continua, pero los checkpoints de ingeniería (¿el símbolo mapea correctamente a DEXPI? ¿la topología es correcta?) requieren revisión humana.

## Preferencias Tecnológicas

### Confirmadas (del plan de desarrollo)

| Componente | Tecnología | Estado |
|-----------|------------|--------|
| Editor | Draw.io (Apache 2.0) | Confirmado |
| Modelo de datos | pyDEXPI (MIT) — Pydantic + NetworkX | Confirmado |
| Lenguaje conversor | Python (lxml, pydantic) | Confirmado |
| Knowledge Graph | Neo4j (obligatorio, P&IDs grandes) | Confirmado |
| LLM | Claude API | Confirmado |
| MCP Draw.io | drawio-mcp-server de Gazo (npm, MIT) | Confirmado |
| MCP orquestador | Custom (TypeScript o Python) | Por decidir lenguaje |

### Por decidir

| Decisión | Opciones | Cuándo decidir |
|----------|----------|---------------|
| Lenguaje del MCP orquestador | TypeScript vs Python | Fase 4 (Arquitectura) |
| Framework web UI | FastAPI + React / Streamlit / Gradio / otro | Fase 4 (Arquitectura) |
| Licencia código propio | MIT / Apache 2.0 / GPL / propietaria | Antes de publicar |
| Driver Neo4j para Python | neo4j (oficial) vs py2neo | Fase 4 (Arquitectura) |
| Formato de distribución | pip package / Docker / ambos | Fase 4 (Arquitectura) |

### Prohibiciones

- No usar software propietario en el flujo base (el stack debe ser 100% open-source excepto Claude API como SaaS).
- No hardcodear credenciales ni API keys en el repositorio.

## Normativa

| Regulación | Aplica | Implicaciones |
|------------|--------|---------------|
| ISA 5.1 (Instrumentation Symbols) | Sí | Los símbolos de la biblioteca deben seguir la simbología estándar ISA 5.1 |
| ISO 10628 (Diagrams for the chemical and petrochemical industry) | Sí | Convenciones de representación gráfica de P&IDs |
| DEXPI / Proteus XML Schema | Sí | El conversor debe generar XML conforme al esquema DEXPI publicado |
| ISO 15926 (Industrial data) | Indirecta | DEXPI se basa parcialmente en ISO 15926; el mapeo de clases debe ser coherente |
| GDPR | No | No se procesan datos personales |
| HIPAA | No | No aplica (no es industria de salud) |
| PCI-DSS | No | No aplica (no hay datos de pago) |
| IEC 62443 (Cybersecurity industrial) | No para MVP | Podría aplicar si el sistema se despliega en entornos OT en el futuro |

**Nota sobre confidencialidad**: Los P&IDs de planta pueden ser información confidencial industrial. El sistema debe poder operar localmente excepto la llamada al LLM. Se contempla soporte futuro para LLM local (post-MVP).

## Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| pyDEXPI es proyecto académico joven | Medio | Media | Código MIT y auditable. Forkar si se abandona. Evaluar contribuir upstream |
| Complejidad del mapeo topológico nozzle-a-nozzle | Alto | Alta | Empezar con topologías simples (lineal), iterar añadiendo complejidad. P&ID de referencia DEXPI como benchmark |
| Alucinaciones del LLM en análisis de proceso | Alto | Media | Graph-RAG ancla respuestas en datos reales. Human-in-the-loop para decisiones críticas |
| MCP Draw.io no accede a toda la shape library | Medio | Media | MCP de Gazo permite shapes custom. Library propia se precarga vía XML directo |
| Draw.io no cubre toda la simbología ISA 5.1 | Medio | Baja | Biblioteca custom extensible. Añadir símbolos progresivamente |
| Neo4j complejidad operacional | Bajo | Baja | Docker-compose para desarrollo local. Presupuesto ilimitado para Aura si se prefiere managed |
| Supervisor es una sola persona (cuello de botella en checkpoints) | Medio | Media | Spawn prompts detallados para minimizar intervención. Checkpoints bien definidos para maximizar eficiencia de la revisión |

## Siguiente Paso
Avanzar a **Fase 4: Arquitectura y Stack Tecnológico** para cerrar las decisiones técnicas pendientes (framework web UI, lenguaje MCP, driver Neo4j, distribución) y definir la estructura de módulos con ownership.
