import { z } from "zod";
import {
  readLocalFile,
  buildFormDataWithField,
  apiFetch,
  consumeSseStream,
  textResult,
  safeHandler,
  log,
} from "./helpers.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

/** Shape of the /api/graph/build response. */
interface BuildGraphResponse {
  pid_id: string;
  node_count: number;
  edge_count: number;
  equipment_count: number;
  instrument_count: number;
}

/** Shape of a node in the graph response. */
interface GraphNode {
  id: string;
  tag?: string;
  type?: string;
  label?: string;
  [key: string]: unknown;
}

/** Shape of an edge in the graph response. */
interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  label?: string;
  [key: string]: unknown;
}

/** Shape of the /api/graph/{pid_id} response. */
interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Register Knowledge Graph tools on the MCP server.
 */
export function registerGraphTools(server: McpServer): void {
  // ---------- build_knowledge_graph ----------
  server.tool(
    "build_knowledge_graph",
    "Build a Knowledge Graph from a P&ID file and load it into Neo4j for querying",
    {
      file_path: z
        .string()
        .describe("Absolute path to the P&ID file (Draw.io or DEXPI XML)"),
      pid_id: z
        .string()
        .optional()
        .describe(
          "Optional identifier for this P&ID. If omitted, the backend will generate one.",
        ),
    },
    safeHandler(async ({ file_path, pid_id }: { file_path: string; pid_id?: string }) => {
      log(`Tool invoked: build_knowledge_graph — file: ${file_path}, pid_id: ${pid_id ?? "(auto)"}`);

      const fileContent = await readLocalFile(file_path);
      const fileName = file_path.split(/[/\\]/).pop() ?? "file";

      let formData: FormData;
      if (pid_id) {
        formData = buildFormDataWithField(
          "file",
          fileContent,
          fileName,
          "pid_id",
          pid_id,
        );
      } else {
        const fd = new FormData();
        fd.append("file", new Blob([new Uint8Array(fileContent)]), fileName);
        formData = fd;
      }

      const response = await apiFetch("/api/graph/build", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      const data = (await response.json()) as BuildGraphResponse;

      return textResult(
        `Knowledge Graph built successfully.\n` +
          `P&ID ID:     ${data.pid_id}\n` +
          `Nodes:       ${data.node_count}\n` +
          `Edges:       ${data.edge_count}\n` +
          `Equipment:   ${data.equipment_count}\n` +
          `Instruments: ${data.instrument_count}`,
      );
    }),
  );

  // ---------- query_pid ----------
  server.tool(
    "query_pid",
    "Ask a question about a P&ID in natural language. The system uses Graph-RAG to retrieve relevant context from the Knowledge Graph and answers using Claude.",
    {
      pid_id: z.string().describe("Identifier of the P&ID to query"),
      question: z.string().describe("Natural language question about the P&ID"),
    },
    safeHandler(async ({ pid_id, question }: { pid_id: string; question: string }) => {
      log(`Tool invoked: query_pid — pid_id: ${pid_id}, question: "${question}"`);

      const response = await apiFetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pid_id,
          message: question,
          history: [],
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      // The /api/chat endpoint returns an SSE stream
      const answer = await consumeSseStream(response);

      if (!answer.trim()) {
        return textResult(
          "The system did not return an answer. The Knowledge Graph may not have been built yet for this P&ID. " +
            "Try running build_knowledge_graph first.",
        );
      }

      return textResult(answer.trim());
    }),
  );

  // ---------- get_graph ----------
  server.tool(
    "get_graph",
    "Get the Knowledge Graph data for a P&ID as a list of nodes and edges",
    {
      pid_id: z.string().describe("Identifier of the P&ID whose graph to retrieve"),
      detailed: z
        .boolean()
        .optional()
        .default(false)
        .describe("If true, fetch the detailed graph endpoint with full node/edge properties"),
    },
    safeHandler(async ({ pid_id, detailed }: { pid_id: string; detailed?: boolean }) => {
      log(`Tool invoked: get_graph — pid_id: ${pid_id}, detailed: ${detailed ?? false}`);

      const endpoint = detailed
        ? `/api/graph/${encodeURIComponent(pid_id)}/detail`
        : `/api/graph/${encodeURIComponent(pid_id)}`;

      const response = await apiFetch(endpoint, { method: "GET" });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      const data = (await response.json()) as GraphResponse;

      // Format into a human-readable summary
      const nodeTypes = new Map<string, number>();
      for (const node of data.nodes) {
        const nodeType = node.type ?? "unknown";
        nodeTypes.set(nodeType, (nodeTypes.get(nodeType) ?? 0) + 1);
      }

      const edgeTypes = new Map<string, number>();
      for (const edge of data.edges) {
        const edgeType = edge.type ?? "unknown";
        edgeTypes.set(edgeType, (edgeTypes.get(edgeType) ?? 0) + 1);
      }

      let summary = `Knowledge Graph for P&ID: ${pid_id}\n`;
      summary += `Total nodes: ${data.nodes.length}\n`;
      summary += `Total edges: ${data.edges.length}\n`;

      if (nodeTypes.size > 0) {
        summary += `\nNode types:\n`;
        for (const [type, count] of nodeTypes.entries()) {
          summary += `  - ${type}: ${count}\n`;
        }
      }

      if (edgeTypes.size > 0) {
        summary += `\nEdge types:\n`;
        for (const [type, count] of edgeTypes.entries()) {
          summary += `  - ${type}: ${count}\n`;
        }
      }

      if (detailed && data.nodes.length > 0) {
        summary += `\nNodes:\n`;
        for (const node of data.nodes) {
          const label = node.label ?? node.tag ?? node.id;
          const type = node.type ?? "unknown";
          const tag = node.tag ? ` tag=${node.tag}` : "";
          summary += `  [${type}] ${label} (id: ${node.id}${tag})\n`;
        }

        summary += `\nEdges:\n`;
        for (const edge of data.edges) {
          const type = edge.type ?? "->";
          const label = edge.label ? ` "${edge.label}"` : "";
          summary += `  ${edge.source} --[${type}${label}]--> ${edge.target}\n`;
        }
      }

      return textResult(summary.trim());
    }),
  );
}
