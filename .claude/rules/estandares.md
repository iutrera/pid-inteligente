# Estándares y Convenciones

## Convenciones de Código

### Nombrado
| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Variables | camelCase | `userName` |
| Funciones | camelCase | `calculateTotal()` |
| Clases | PascalCase | `UserService` |
| Constantes | UPPER_SNAKE | `MAX_RETRIES` |
| Archivos | kebab-case | `user-service.ts` |

### Formato de Commits
```
tipo(alcance): descripción breve

Tipos: feat, fix, docs, style, refactor, test, chore
```

## Estructura de Carpetas con Ownership

```
src/
├── api/          ← Backend
├── services/     ← Backend
├── models/       ← Backend
├── middleware/    ← Backend
├── components/   ← Frontend
├── pages/        ← Frontend
├── styles/       ← Frontend
├── hooks/        ← Frontend
├── types/        ← ⚠️ COMPARTIDO (Backend define, Frontend consume)
├── integrations/ ← Integraciones
├── db/           ← Base de Datos
tests/            ← Testing
e2e/              ← Testing
docs/             ← Documentación
docs/adr/         ← Arquitecto
.github/          ← DevOps
infra/            ← DevOps
migrations/       ← Base de Datos
```

## Reglas Globales (todos los teammates)

- Trabajar SOLO dentro de tu scope exclusivo
- Coordinar con el lead antes de editar archivos compartidos
- Ejecutar comandos de verificación antes de marcar tarea como completa
- Documentar decisiones relevantes
- `npm run lint` antes de completar cualquier tarea

## Reglas por Teammate

**Arquitecto**: README.md en cada carpeta. Documentar toda decisión en /docs/adr/. No implementar lógica de negocio.

**Backend**: Test por cada endpoint. Documentar APIs con OpenAPI. Validar inputs en el controlador.

**Frontend**: Componentes pequeños y reutilizables. No llamadas API directas desde componentes. Usar sistema de estado definido.

**Testing**: Mínimo 80% cobertura en código crítico. Tests E2E para cada flujo principal. Nombres descriptivos.

**DevOps**: Workflows validados con linter. Dockerfiles optimizados (multi-stage si aplica). Secretos nunca hardcodeados.

## Comandos de Verificación por Teammate

| Teammate | Comando | Cuándo |
|----------|---------|--------|
| Backend | `npm test -- --coverage src/api/` | Antes de completar |
| Frontend | `npm run build && npm test src/components/` | Antes de completar |
| DevOps | `actionlint .github/workflows/` | Antes de completar |
| Testing | `npm test -- --coverage` | Al finalizar suite |
| Base de Datos | Migraciones up/down sin errores | Antes de completar |
| Todos | `npm run lint` | Siempre |
