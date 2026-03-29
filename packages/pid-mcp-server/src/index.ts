#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerConvertTools } from "./tools/convert.js";
import { registerGraphTools } from "./tools/graph.js";
import { registerValidateTools } from "./tools/validate.js";
import { registerPrompts } from "./prompts/pid-from-pdf.js";
import { getApiBaseUrl, log } from "./tools/helpers.js";

/**
 * P&ID Inteligente MCP Server
 *
 * Exposes tools for:
 * - Converting between Draw.io and DEXPI formats
 * - Building and querying Knowledge Graphs from P&IDs
 * - Validating P&ID files for common errors
 *
 * Communicates with the pid-rag FastAPI backend over HTTP.
 */
async function main(): Promise<void> {
  const server = new McpServer({
    name: "pid-inteligente",
    version: "0.1.0",
  });

  // Register all tool groups
  registerConvertTools(server);
  registerGraphTools(server);
  registerValidateTools(server);
  registerPrompts(server);

  // Connect via stdio transport (standard MCP communication channel)
  const transport = new StdioServerTransport();
  log(`Starting pid-inteligente MCP server (API: ${getApiBaseUrl()})`);

  await server.connect(transport);
  log("MCP server connected and ready");
}

main().catch((error: unknown) => {
  log(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
});
