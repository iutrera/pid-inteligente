# pid-mcp-server

Servidor MCP (Model Context Protocol) para P&ID Inteligente. Orquesta herramientas de Draw.io, conversion DEXPI, consultas al Knowledge Graph y validacion de P&IDs.

Escrito en TypeScript con el SDK oficial de MCP. Se comunica con el backend Python (pid-rag) via HTTP.

## Tools expuestas

| Tool | Descripcion |
|------|-------------|
| `convert-drawio-dexpi` | Convierte archivo .drawio a Proteus XML DEXPI |
| `import-dexpi-drawio` | Importa Proteus XML y genera archivo .drawio |
| `query-knowledge-graph` | Ejecuta consultas sobre el Knowledge Graph en lenguaje natural |
| `validate-pid` | Valida un P&ID y retorna reporte de errores |
| `draw-pid` | Crea/modifica P&IDs en Draw.io via drawio-mcp-server (Gazo) |

## Arquitectura interna

```
pid-mcp-server/
  src/
    tools/
      convert.ts    -- Tools de conversion (Draw.io <-> DEXPI)
      graph.ts      -- Tools de Knowledge Graph
      validate.ts   -- Tools de validacion
      drawio.ts     -- Tools de Draw.io (via Gazo drawio-mcp-server)
    resources/      -- MCP resources expuestos
    index.ts        -- Entry point del MCP server
```

## Instalacion

```bash
cd packages/pid-mcp-server

# Instalar dependencias
npm install

# Build
npm run build
```

### Requisitos

- Node.js 20+
- Backend pid-rag corriendo en `http://localhost:8000`
- (Opcional) drawio-mcp-server de Gazo para tools de Draw.io

## Uso basico

### Ejecutar el servidor

```bash
# Produccion
npm start

# Desarrollo (con watch)
npm run dev
```

### Configurar en un cliente MCP

Agregar al archivo de configuracion del cliente MCP (ej. Claude Desktop):

```json
{
  "mcpServers": {
    "pid-inteligente": {
      "command": "node",
      "args": ["packages/pid-mcp-server/dist/index.js"],
      "env": {
        "PID_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Scripts disponibles

| Script | Descripcion |
|--------|-------------|
| `npm run build` | Compilar TypeScript |
| `npm start` | Ejecutar servidor compilado |
| `npm run dev` | Desarrollo con watch (tsx) |
| `npm test` | Ejecutar tests (vitest) |
| `npm run lint` | Linting con ESLint |
| `npm run lint:fix` | Linting con auto-fix |
| `npm run format` | Formatear con Prettier |
