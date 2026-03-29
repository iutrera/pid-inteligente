import { z } from "zod";
import {
  readLocalFile,
  buildFormData,
  apiFetch,
  textResult,
  safeHandler,
  log,
} from "./helpers.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

/** Shape of a single validation error returned by the API. */
interface ValidationError {
  shape_id: string;
  error_type: string;
  message: string;
}

/**
 * Register validation tools on the MCP server.
 */
export function registerValidateTools(server: McpServer): void {
  server.tool(
    "validate_pid",
    "Validate a Draw.io P&ID file for common errors: missing tags, disconnected nozzles, missing line numbers, orphan instruments",
    {
      drawio_path: z
        .string()
        .describe("Absolute path to the .drawio file to validate"),
    },
    safeHandler(async ({ drawio_path }: { drawio_path: string }) => {
      log(`Tool invoked: validate_pid — file: ${drawio_path}`);

      const fileContent = await readLocalFile(drawio_path);
      const formData = buildFormData(
        "file",
        fileContent,
        drawio_path.split(/[/\\]/).pop() ?? "file.drawio",
      );

      const response = await apiFetch("/api/validate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API returned ${response.status}: ${errorText}`,
        );
      }

      const errors = (await response.json()) as ValidationError[];

      if (errors.length === 0) {
        return textResult(
          `Validation passed: No errors found in ${drawio_path}`,
        );
      }

      // Group errors by type for a clear summary
      const byType = new Map<string, ValidationError[]>();
      for (const err of errors) {
        const list = byType.get(err.error_type) ?? [];
        list.push(err);
        byType.set(err.error_type, list);
      }

      let report = `Validation found ${errors.length} error(s) in ${drawio_path}:\n\n`;

      for (const [errorType, items] of byType.entries()) {
        report += `## ${errorType} (${items.length})\n`;
        for (const item of items) {
          report += `  - Shape "${item.shape_id}": ${item.message}\n`;
        }
        report += "\n";
      }

      return textResult(report.trim());
    }),
  );
}
