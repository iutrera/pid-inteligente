import type { ElementDefinition } from "cytoscape";

/** Node type categories used for colouring in Cytoscape. */
export type NodeType =
  | "Equipment"
  | "Instrument"
  | "Valve"
  | "PipingSegment"
  | "Nozzle"
  | string;

/** Colour map for each node type. */
export const NODE_TYPE_COLORS: Record<string, string> = {
  Equipment: "#2563eb", // blue
  Instrument: "#dc2626", // red
  Valve: "#f97316", // orange
  PipingSegment: "#6b7280", // gray
  Nozzle: "#16a34a", // green
};

/** Fallback colour for unknown node types. */
export const DEFAULT_NODE_COLOR = "#8b5cf6"; // purple

/** Build Cytoscape element definitions from raw API data. */
export function toCytoscapeElements(
  nodes: { id: string; tag: string; type: string; label: string }[],
  edges: { source: string; target: string; type: string; label: string }[],
): ElementDefinition[] {
  const nodeElements: ElementDefinition[] = nodes.map((n) => ({
    data: {
      id: n.id,
      label: n.tag || n.label || n.id,
      type: n.type,
      tag: n.tag,
    },
  }));

  const edgeElements: ElementDefinition[] = edges.map((e, idx) => ({
    data: {
      id: `e-${idx}-${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.label,
      type: e.type,
    },
  }));

  return [...nodeElements, ...edgeElements];
}

/** Cytoscape stylesheet entry (avoids importing cytoscape internal types). */
interface CyStyle {
  selector: string;
  style: Record<string, unknown>;
}

/** Default Cytoscape stylesheet. */
export const cytoscapeStylesheet: CyStyle[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "text-valign": "bottom",
      "text-halign": "center",
      "font-size": "10px",
      width: 30,
      height: 30,
      "background-color": DEFAULT_NODE_COLOR,
      "border-width": 2,
      "border-color": "#e5e7eb",
    },
  },
  ...Object.entries(NODE_TYPE_COLORS).map(
    ([type, color]) =>
      ({
        selector: `node[type = "${type}"]`,
        style: {
          "background-color": color,
        },
      }) as CyStyle,
  ),
  {
    selector: "node:selected",
    style: {
      "border-width": 3,
      "border-color": "#1e293b",
      "overlay-opacity": 0.1,
    },
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": "#94a3b8",
      "target-arrow-color": "#94a3b8",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(label)",
      "font-size": "8px",
      "text-rotation": "autorotate",
      color: "#64748b",
    },
  },
];
