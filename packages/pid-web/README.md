# pid-web

Interfaz web React para consultar Knowledge Graphs de P&ID con LLM via Graph-RAG.

Permite al ingeniero de procesos hacer preguntas en lenguaje natural sobre sus P&IDs, visualizar el Knowledge Graph interactivamente, y ver referencias al diagrama original.

## Componentes principales

- **Chat LLM** -- Interfaz de consulta con streaming (SSE) para preguntas sobre P&IDs
- **Visualizacion Knowledge Graph** -- Grafo interactivo con Cytoscape.js
- **Visor P&ID** -- Referencia visual del diagrama original
- **Componentes compartidos** -- Layout, formularios, navegacion

## Stack

| Capa | Tecnologia |
|------|-----------|
| Framework | React 18+ con TypeScript |
| Bundler | Vite |
| Estilos | Tailwind CSS |
| Estado | Zustand |
| Data fetching | TanStack Query (React Query) |
| Grafos | Cytoscape.js (react-cytoscapejs) |

## Instalacion

```bash
cd packages/pid-web

# Instalar dependencias
npm install
```

### Requisitos

- Node.js 20+
- Backend pid-rag corriendo en `http://localhost:8000` (o configurar URL)

## Uso basico

### Desarrollo

```bash
# Servidor de desarrollo con HMR
npm run dev
```

La aplicacion estara disponible en `http://localhost:5173`.

### Build de produccion

```bash
npm run build
```

Los archivos estaticos se generan en `dist/`.

### Preview del build

```bash
npm run preview
```

## Scripts disponibles

| Script | Descripcion |
|--------|-------------|
| `npm run dev` | Servidor de desarrollo con HMR |
| `npm run build` | Build de produccion (tsc + vite build) |
| `npm run preview` | Preview del build de produccion |
| `npm test` | Ejecutar tests (vitest) |
| `npm run test:watch` | Tests en modo watch |
| `npm run test:coverage` | Tests con reporte de cobertura |
| `npm run lint` | Linting con ESLint |
| `npm run lint:fix` | Linting con auto-fix |
| `npm run format` | Formatear con Prettier |

## Estructura

```
src/
  components/
    chat/       -- Chat con LLM
    graph/      -- Visualizacion Knowledge Graph
    pid/        -- Visor/referencia de P&ID
    common/     -- Componentes compartidos
  pages/        -- Paginas de la aplicacion
  hooks/        -- React hooks custom
  stores/       -- Zustand stores
  services/     -- API client (TanStack Query)
  types/        -- TypeScript types
  styles/       -- Estilos globales
```
