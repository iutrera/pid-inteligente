# Detalle de Fases del Proyecto

## FASE 1: Discovery
**Preguntas clave**:
- ¿Qué problema específico resuelve este software?
- ¿Quiénes son los usuarios objetivo? ¿Cómo trabajan actualmente?
- ¿Existe competencia? ¿Qué diferenciará tu solución?
- ¿Por qué ahora? ¿Qué ha cambiado que hace viable este proyecto?
- ¿Hay restricciones conocidas (regulación, seguridad, compatibilidad)?

## FASE 2: Definición de Producto
**Preguntas clave**:
- ¿Qué funcionalidades son imprescindibles para el MVP?
- ¿Qué funcionalidades son deseables pero no críticas?
- ¿Qué NO hará el producto (alcance negativo)?
- ¿Web, móvil, escritorio, o combinación?
- ¿Qué integraciones con otros sistemas son necesarias?
- ¿Requisitos de rendimiento, disponibilidad, seguridad?

## FASE 3: Restricciones y Recursos
**Preguntas clave**:
- ¿Cuál es el presupuesto disponible (o rango)?
- ¿Hay fecha límite o hitos obligatorios?
- ¿Hay preferencias tecnológicas por razones de negocio?
- ¿Normativa aplicable (GDPR, HIPAA, PCI-DSS, etc.)?
- ¿Quién supervisará el desarrollo? ¿Nivel técnico del supervisor?

## FASE 4: Arquitectura y Stack Tecnológico
**Decisiones a tomar**:
- Arquitectura general (monolito, microservicios, serverless, híbrida)
- Stack de frontend (framework, lenguaje, librerías clave)
- Stack de backend (lenguaje, framework, base de datos)
- Infraestructura (cloud provider, servicios gestionados)
- Herramientas de desarrollo (control de versiones, CI/CD)

**Criterios de decisión**: Requisitos técnicos, capacidad de Claude Code con el stack, madurez/documentación, coste de operación.

## FASE 5: Composición del Equipo
**Elementos a definir**:
- Qué teammates se necesitan
- Scope exclusivo de cada uno (qué carpetas/archivos posee)
- Archivos compartidos que requieren coordinación
- Spawn prompts específicos por teammate
- Puntos de intervención humana

**Regla crítica**: Cada archivo tiene un único propietario. Si dos lo necesitan, se marca como "coordinar antes de editar".

## FASE 6: Pipeline por Oleadas
**Elementos a definir**:
- Oleadas de ejecución (qué teammates en paralelo en cada una)
- Dependencias entre oleadas
- Checkpoints de validación humana
- Criterios de completitud por teammate y por oleada
- Gestión de errores (qué pasa si un teammate falla)

## FASE 7: Estándares y Convenciones
**Elementos a definir**:
- Convenciones de código (naming, estructura, formato)
- Estrategia de testing por teammate
- Estructura de carpetas con ownership
- Formato de commits y branches
- Documentación requerida
- Comandos de verificación por teammate

## FASE 8: Generación del Proyecto
Al ejecutar `/generar`:
1. Verificar fases 1-7 completas
2. Crear estructura de carpetas
3. Generar CLAUDE.md del proyecto (contexto compartido)
4. Generar `.claude/settings.local.json` con Agent Teams + hooks
5. Generar scripts de hooks
6. Copiar specs
7. Generar un prompt por oleada en `/prompts/`
8. Generar configuraciones según stack
9. Crear scaffolding básico
10. Generar README.md con instrucciones de activación
