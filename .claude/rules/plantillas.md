# Plantillas de Entregables

## 01_discovery.md
```markdown
# Visión del Proyecto: [Nombre]

## Resumen Ejecutivo
[2-3 párrafos describiendo el proyecto]

## Problema
### Situación Actual
[Cómo trabajan los usuarios hoy]
### Pain Points
[Problemas específicos]
### Coste del Problema
[Impacto en tiempo, dinero, satisfacción]

## Solución Propuesta
### Visión
[Qué será el producto completo]
### Propuesta de Valor
[Por qué elegirían esta solución]

## Usuarios Objetivo
### Perfil Principal
[Descripción del usuario principal]
### Perfiles Secundarios
[Otros usuarios relevantes]

## Contexto de Mercado
### Competencia
[Soluciones existentes y limitaciones]
### Diferenciación
[Qué hace única esta solución]

## Restricciones Identificadas
[Regulación, compatibilidad, seguridad]

## Criterios de Éxito
[Cómo sabremos que ha tenido éxito]
```

## 02_producto.md
```markdown
# Especificación de Producto: [Nombre]

## Alcance del MVP
### Funcionalidades Core
| ID | Funcionalidad | Descripción | Prioridad |
|----|---------------|-------------|-----------|
| F1 | ... | ... | Must Have |

### Funcionalidades Diferidas
[Para versiones posteriores]

### Alcance Negativo
[Qué NO hará el producto]

## Plataformas
[Web / Móvil / Escritorio + justificación]

## Requisitos No Funcionales
- Rendimiento: [tiempos, concurrencia]
- Disponibilidad: [SLA]
- Seguridad: [auth, cifrado]
- Escalabilidad: [crecimiento]

## Integraciones
| Sistema | Tipo | Prioridad | Complejidad |

## Flujos Principales
[Diagramas de flujos críticos]
```

## 03_restricciones.md
```markdown
# Restricciones y Recursos: [Nombre]

## Presupuesto
[Rango + consideraciones: hosting, APIs, licencias, tokens Claude Code]

## Timeline
[Fecha objetivo + hitos obligatorios]

## Supervisión
- Responsable: [quién revisa]
- Nivel técnico: [para ajustar comunicación]
- Disponibilidad: [horas/semana para checkpoints]

## Preferencias Tecnológicas
[Tecnologías preferidas o prohibidas]

## Normativa
| Regulación | Aplica | Implicaciones |
```

## 04_arquitectura.md
```markdown
# Arquitectura Técnica: [Nombre]

## Visión General
[Diagrama]

## Stack Tecnológico
### Frontend
| Capa | Tecnología | Justificación |
### Backend
| Capa | Tecnología | Justificación |
### Infraestructura
| Componente | Servicio | Justificación |

## ADRs
### ADR-001: [Título]
- Estado: Aceptada
- Contexto: [por qué]
- Decisión: [qué]
- Consecuencias: [pros/contras]

## Estructura de Módulos y Ownership
[Mapa carpeta → teammate propietario]
```

## 05_equipo.md
```markdown
# Equipo de Teammates: [Nombre]

## Teammates Seleccionados
| Teammate | Incluido | Scope Exclusivo | Justificación |

## Archivos Compartidos
| Archivo/Carpeta | Teammates | Regla de coordinación |

## Spawn Prompts por Teammate
### Teammate: [Nombre]
[Spawn prompt completo con scope, contexto, tarea, verificación, criterios]

## Puntos de Intervención Humana
| Momento | Qué revisar | Criterio de avance |
```

## 06_pipeline.md
```markdown
# Pipeline por Oleadas: [Nombre]

## Visión General
[Diagrama mermaid]

## Oleada N: [Nombre]
- Teammates en paralelo: [lista]
- Duración estimada: [tiempo]
- Tabla de tareas: [teammate, tarea, output, verificación]
- Checkpoint humano: [qué revisar]
- Prompt para el lead: [instrucción exacta]

## Dependencias Críticas
| Teammate | Bloqueado por | Bloquea a |

## Gestión de Errores
[Qué hacer si falla]

## Criterios de Completitud
| Oleada | Criterio |
```

## 07_estandares.md
```markdown
# Estándares: [Nombre]

## Convenciones de Código
[Naming, estructura, formato]

## Estructura con Ownership
[Carpeta → propietario]

## Reglas por Teammate
[Reglas específicas]

## Comandos de Verificación
| Teammate | Comando | Cuándo |

## Configuraciones
[ESLint, Prettier, TypeScript]
```

## CLAUDE.md del Proyecto Generado
```markdown
# [Nombre del Proyecto]

## Contexto
[Resumen de discovery y producto — 2-3 párrafos]

## Stack Tecnológico
[Resumen de arquitectura]

## Ownership de Archivos
| Carpeta | Propietario | Notas |

## Convenciones Clave
[Resumen de estándares]

## Verificación Obligatoria
Antes de completar cualquier tarea:
- `npm run lint`
- `npm test`
- Comando específico de tu scope (ver specs/07_estandares.md)

## Archivos Compartidos — COORDINAR ANTES DE EDITAR
[Lista con regla de coordinación]

## Specs
Documentación completa en /specs/
```
