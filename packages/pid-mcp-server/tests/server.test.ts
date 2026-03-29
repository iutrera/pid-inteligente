import { describe, it, expect } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerConvertTools } from "../src/tools/convert.js";
import { registerGraphTools } from "../src/tools/graph.js";
import { registerValidateTools } from "../src/tools/validate.js";

describe("MCP Server instantiation", () => {
  it("should create a server instance without errors", () => {
    const server = new McpServer({
      name: "pid-inteligente",
      version: "0.1.0",
    });
    expect(server).toBeDefined();
  });

  it("should register all tool groups without errors", () => {
    const server = new McpServer({
      name: "pid-inteligente",
      version: "0.1.0",
    });

    expect(() => registerConvertTools(server)).not.toThrow();
    expect(() => registerGraphTools(server)).not.toThrow();
    expect(() => registerValidateTools(server)).not.toThrow();
  });
});
