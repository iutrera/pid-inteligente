# Catálogo de Teammates

## Tabla Resumen

| Teammate | Cuándo incluirlo | Scope típico exclusivo | Oleada típica |
|----------|------------------|------------------------|---------------|
| Arquitecto | Siempre | `/docs/adr/`, configs raíz | 1 |
| Backend | APIs, lógica de negocio, BD | `/src/api/`, `/src/services/`, `/src/models/` | 2 |
| Frontend | Interfaz de usuario | `/src/components/`, `/src/pages/`, `/src/styles/` | 3 |
| Mobile | App nativa iOS/Android | `/mobile/` | 3 |
| Testing | Siempre | `/tests/`, `/e2e/` | Transversal |
| DevOps | CI/CD, IaC | `/.github/`, `/infra/`, `/deploy/` | 1 y 4 |
| Integraciones | APIs externas | `/src/integrations/` | 2-3 |
| Documentación | Recomendado | `/docs/` (excepto adr/) | 4 |
| Seguridad | Datos sensibles | Auditor (sin scope exclusivo, solo lectura) | 4 |
| Base de Datos | Modelo de datos complejo | `/src/db/`, `/migrations/`, `/seeds/` | 2 |
| Extensión | Gap funcional detectado | Según necesidad | Bajo demanda |

## Detalle por Teammate

### Arquitecto
- **Rol**: Define estructura técnica del proyecto
- **Scope exclusivo**: `/docs/adr/`, configuraciones raíz (package.json, tsconfig, etc.)
- **Scope compartido**: CLAUDE.md (coordinar con lead)
- **Responsabilidades**: Crear estructura de carpetas, definir patrones, configurar proyecto base, documentar ADRs, establecer interfaces entre capas
- **Produce**: Scaffolding, documento de arquitectura, configuraciones base
- **Requiere**: specs/04_arquitectura.md, specs/07_estandares.md
- **Verificación**: `tree -L 3 src/` y `cat package.json`

### Backend
- **Rol**: Implementa lógica de negocio y APIs
- **Scope exclusivo**: `/src/api/`, `/src/services/`, `/src/models/`, `/src/middleware/`
- **Scope compartido**: `/src/types/` (coordinar con Frontend — Backend define, Frontend consume)
- **Responsabilidades**: Modelos de datos, endpoints REST/GraphQL, lógica de negocio, autenticación/autorización
- **Produce**: APIs, modelos, migraciones, tests unitarios
- **Requiere**: Estructura del Arquitecto (oleada 1), specs/02_producto.md
- **Verificación**: `npm test -- --coverage src/api/` y `npm run lint src/api/ src/services/`

### Frontend
- **Rol**: Implementa interfaz de usuario
- **Scope exclusivo**: `/src/components/`, `/src/pages/`, `/src/styles/`, `/src/hooks/`
- **Scope compartido**: `/src/types/` (consume lo que Backend define)
- **Responsabilidades**: Componentes UI, gestión de estado, consumir APIs, navegación, responsive design
- **Produce**: Componentes, estado, integración con APIs, tests de componentes
- **Requiere**: APIs funcionando o contratos de API definidos
- **Verificación**: `npm test -- --coverage src/components/` y `npm run build`

### Mobile
- **Rol**: Aplicaciones móviles nativas o híbridas
- **Scope exclusivo**: `/mobile/`, `/src/native/`
- **Responsabilidades**: UI nativa o React Native/Flutter, estado offline, notificaciones push, builds iOS/Android
- **Produce**: App móvil funcional, configuración de stores
- **Requiere**: APIs funcionando
- **Verificación**: Tests unitarios del framework móvil, build sin errores

### Testing
- **Rol**: Garantiza calidad del código
- **Scope exclusivo**: `/tests/`, `/e2e/`, `/cypress/` o `/playwright/`
- **Responsabilidades**: Tests unitarios, integración, E2E, casos edge, cobertura
- **Produce**: Suite de tests completa, reporte de cobertura
- **Requiere**: Código de Backend y/o Frontend, criterios de aceptación
- **Verificación**: `npm test -- --coverage` (mínimo 80%) y `npm run e2e`

### DevOps
- **Rol**: Automatiza infraestructura y despliegue
- **Scope exclusivo**: `/.github/`, `/infra/`, `/deploy/`, `/docker/`, Dockerfile, docker-compose.yml
- **Responsabilidades**: Repo, CI/CD, IaC (Terraform/Pulumi), entornos, monitorización
- **Produce**: Pipeline CI/CD, IaC, scripts de despliegue, monitorización
- **Requiere**: specs/04_arquitectura.md
- **Verificación**: `actionlint .github/workflows/` y `docker build .`

### Integraciones
- **Rol**: Conecta con sistemas externos
- **Scope exclusivo**: `/src/integrations/`, `/src/connectors/`
- **Responsabilidades**: Clientes de APIs externas, OAuth, mapeo de datos, webhooks, reintentos
- **Produce**: Conectores, mappers, gestión de webhooks
- **Requiere**: Documentación de APIs externas, credenciales de prueba
- **Verificación**: Tests de integración con mocks, verificar reintentos

### Documentación
- **Rol**: Genera y mantiene documentación técnica
- **Scope exclusivo**: `/docs/` (excepto `/docs/adr/` que es del Arquitecto)
- **Responsabilidades**: Documentación de API (OpenAPI), componentes, guías, README, changelog
- **Produce**: Docs de API, guías de desarrollo, README, changelog
- **Requiere**: Código existente, convenciones definidas
- **Verificación**: Todos los endpoints documentados, README con instrucciones funcionales

### Seguridad
- **Rol**: Audita código e infraestructura (NO posee archivos, solo revisa)
- **Scope exclusivo**: Ninguno — es auditor
- **Scope lectura**: Todo el proyecto
- **Responsabilidades**: Auditar dependencias, revisar fallos de seguridad, verificar auth, headers, cumplimiento normativo
- **Produce**: Reporte de vulnerabilidades en `/docs/security/`, recomendaciones (que otros implementan)
- **Requiere**: Código completo, requisitos de seguridad
- **Verificación**: `npm audit`, revisión de secrets expuestos

### Base de Datos
- **Rol**: Diseña y optimiza modelo de datos
- **Scope exclusivo**: `/src/db/`, `/migrations/`, `/seeds/`
- **Responsabilidades**: Esquema de BD, migraciones, queries, índices, seeds
- **Produce**: Esquema, migraciones, seeds, documentación del modelo
- **Requiere**: specs/02_producto.md, requisitos de rendimiento
- **Verificación**: Migraciones up/down sin errores, seeds ejecutables

### Extensión
- **Rol**: Detecta carencias y propone nuevos teammates
- **Scope**: Según necesidad
- **Responsabilidades**: Evaluar gaps, diseñar nuevo teammate, actualizar pipeline, verificar no solapamiento
- **Produce**: Especificación del nuevo teammate, spawn prompt, actualización de pipeline
- **Requiere**: Descripción del gap, contexto del proyecto, catálogo actual

## Plantilla de Spawn Prompt

```
Eres el teammate de [Rol] en el proyecto [Nombre].
Tu scope exclusivo: [carpetas]. NO toques archivos fuera de tu scope.

Contexto: [Resumen relevante para este teammate]
Stack: [Tecnologías que usa]
Tarea concreta: [Qué debe hacer]

Archivos compartidos — coordina antes de editar: [lista]

Antes de completar, ejecuta: [comandos de verificación]

Criterios de aceptación: [lista concreta]
```
