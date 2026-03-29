/** A node in the P&ID Knowledge Graph. */
export interface GraphNode {
  id: string;
  tag: string;
  type: string;
  label: string;
  /** Additional engineering attributes returned by the detail endpoint. */
  [key: string]: unknown;
}

/** An edge in the P&ID Knowledge Graph. */
export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  label: string;
}

/** Full graph payload returned by GET /api/graph/{pid_id}. */
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** Statistics returned after building a graph from an uploaded file. */
export interface PidStats {
  pid_id: string;
  node_count: number;
  edge_count: number;
  equipment_count: number;
  instrument_count: number;
  /** The original file name — added client-side after upload. */
  file_name?: string;
}

/** A single validation error reported by POST /api/validate. */
export interface ValidationError {
  shape_id: string;
  error_type: string;
  message: string;
}

/** Health-check response from GET /api/health. */
export interface HealthResponse {
  status: "ok" | string;
}

/** SSE delta event from the chat endpoint. */
export interface ChatStreamDelta {
  delta: string;
}

/** SSE done event from the chat endpoint. */
export interface ChatStreamDone {
  done: true;
  full_response: string;
}

export type ChatStreamEvent = ChatStreamDelta | ChatStreamDone;
