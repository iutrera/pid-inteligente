import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

/**
 * Register MCP prompts for P&ID generation from PDFs/images.
 *
 * These prompts appear as slash commands in Claude Desktop and provide
 * structured instructions for generating .drawio files with DEXPI metadata.
 */
export function registerPrompts(server: McpServer): void {
  server.prompt(
    "generate-pid",
    "Interpreta un P&ID desde un PDF o imagen y genera un archivo .drawio con metadatos DEXPI completos, conexiones explícitas y lazos de control",
    {
      file_description: z
        .string()
        .optional()
        .describe("Descripción opcional del archivo o sistema del P&ID"),
    },
    async ({ file_description }) => {
      const context = file_description
        ? `\nEl usuario ha indicado que el P&ID contiene: ${file_description}\n`
        : "";

      return {
        messages: [
          {
            role: "user" as const,
            content: {
              type: "text" as const,
              text: `Interpreta el P&ID adjunto y genera un archivo .drawio completo con metadatos DEXPI.${context}

Sigue estas reglas ESTRICTAMENTE:

## ESTRUCTURA DEL ARCHIVO .drawio

Genera un archivo XML con esta estructura exacta:
- 3 capas: id="1" (Process), id="2" (Instrumentation), id="3" (Annotations)
- Cada equipo/válvula va en parent="1", cada instrumento en parent="2"
- Cada elemento es un <object> con atributos DEXPI + <mxCell> hijo

## ATRIBUTOS OBLIGATORIOS

En cada <object>:
- id: identificador numérico único (10, 20, 30...)
- label: tag visible (P-101, TIC-201)
- dexpi_class: tipo DEXPI (CentrifugalPump, ControlValve, TemperatureController...)
- tag_number: tag ISA del elemento

## CONEXIONES — ESTO ES LO MÁS IMPORTANTE

**CADA línea de proceso y señal DEBE tener source="ID" y target="ID" apuntando a IDs de nodos existentes.**

- Línea de proceso: <mxCell edge="1" source="ID_EQUIPO_A" target="ID_EQUIPO_B" parent="1">
- Línea de señal: <mxCell edge="1" source="ID_INSTRUMENTO" target="ID_EQUIPO" parent="2">
- NUNCA uses sourcePoint/targetPoint con coordenadas. SIEMPRE source/target con IDs.

## LAZOS DE CONTROL

Para cada lazo de control:
1. Crear signal line: Transmisor (TT-101) → Controlador (TIC-101)
2. Crear signal line: Controlador (TIC-101) → Válvula (TCV-101)

## ESTILOS

| Tipo | Style |
|------|-------|
| Bomba | shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1; |
| Tanque/Vessel | shape=rectangle;rounded=1;arcSize=50;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1; |
| Intercambiador | shape=rectangle;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1; |
| Válvula | shape=rhombus;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=11;fontStyle=1; |
| Instrumento | shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontStyle=1; |
| Línea proceso | endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;endSize=8; |
| Línea señal | strokeColor=#FF0000;strokeWidth=1.5;dashed=1;dashPattern=8 4;endArrow=block;endFill=1; |

## TAMAÑOS (width x height en pixels)

Tanque: 100x180, Intercambiador: 130x100, Bomba: 70x70, Compresor: 80x80,
Columna: 80x240, Válvula: 50x50, Instrumento: 45x45.
Espacio entre equipos: mínimo 250px. Canvas: 1654x1169.

## PROCESO

1. Identifica TODOS los equipos con tags del PDF
2. Identifica TODAS las válvulas con tags
3. Identifica TODOS los instrumentos con tags
4. Traza las líneas de proceso (equipo→válvula→equipo)
5. Traza los lazos de control (transmisor→controlador→válvula)
6. Genera el .drawio con TODAS las conexiones explícitas

## VERIFICACIÓN ANTES DE ENTREGAR

- Todo instrumento tiene al menos 1 signal line conectándolo
- Toda línea tiene source y target con IDs válidos
- No hay nodos huérfanos sin conexión
- Los lazos de control están completos
- No hay IDs duplicados

Después de generar el .drawio, usa la tool validate_pid para verificarlo y build_knowledge_graph para construir el Knowledge Graph.`,
            },
          },
        ],
      };
    },
  );
}
