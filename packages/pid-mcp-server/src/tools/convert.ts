import { z } from "zod";
import {
  readLocalFile,
  writeLocalFile,
  buildFormData,
  apiFetch,
  replaceExtension,
  textResult,
  safeHandler,
  log,
} from "./helpers.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

/**
 * Register conversion tools on the MCP server.
 */
export function registerConvertTools(server: McpServer): void {
  // ---------- convert_drawio_to_dexpi ----------
  server.tool(
    "convert_drawio_to_dexpi",
    "Convert a Draw.io P&ID file (.drawio) to DEXPI Proteus XML format",
    {
      drawio_path: z
        .string()
        .describe("Absolute path to the .drawio file to convert"),
    },
    safeHandler(async ({ drawio_path }: { drawio_path: string }) => {
      log(`Tool invoked: convert_drawio_to_dexpi — file: ${drawio_path}`);

      const fileContent = await readLocalFile(drawio_path);
      const formData = buildFormData(
        "file",
        fileContent,
        drawio_path.split(/[/\\]/).pop() ?? "file.drawio",
      );

      const response = await apiFetch("/api/convert/drawio-to-dexpi", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API returned ${response.status}: ${errorText}`,
        );
      }

      const xmlBuffer = Buffer.from(await response.arrayBuffer());
      const outputPath = replaceExtension(drawio_path, ".xml");
      await writeLocalFile(outputPath, xmlBuffer);

      return textResult(
        `Successfully converted Draw.io to DEXPI.\n` +
          `Input:  ${drawio_path}\n` +
          `Output: ${outputPath}\n` +
          `Size:   ${xmlBuffer.byteLength} bytes`,
      );
    }),
  );

  // ---------- convert_dexpi_to_drawio ----------
  server.tool(
    "convert_dexpi_to_drawio",
    "Convert a DEXPI Proteus XML file to Draw.io format for editing",
    {
      dexpi_path: z
        .string()
        .describe("Absolute path to the DEXPI .xml file to convert"),
    },
    safeHandler(async ({ dexpi_path }: { dexpi_path: string }) => {
      log(`Tool invoked: convert_dexpi_to_drawio — file: ${dexpi_path}`);

      const fileContent = await readLocalFile(dexpi_path);
      const formData = buildFormData(
        "file",
        fileContent,
        dexpi_path.split(/[/\\]/).pop() ?? "file.xml",
      );

      const response = await apiFetch("/api/convert/dexpi-to-drawio", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API returned ${response.status}: ${errorText}`,
        );
      }

      const drawioBuffer = Buffer.from(await response.arrayBuffer());
      const outputPath = replaceExtension(dexpi_path, ".drawio");
      await writeLocalFile(outputPath, drawioBuffer);

      return textResult(
        `Successfully converted DEXPI to Draw.io.\n` +
          `Input:  ${dexpi_path}\n` +
          `Output: ${outputPath}\n` +
          `Size:   ${drawioBuffer.byteLength} bytes`,
      );
    }),
  );
}
