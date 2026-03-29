import { describe, it, expect } from "vitest";
import {
  toCytoscapeElements,
  NODE_TYPE_COLORS,
  DEFAULT_NODE_COLOR,
} from "@/types/graph";

describe("graph utilities", () => {
  it("converts nodes and edges to Cytoscape elements", () => {
    const nodes = [
      { id: "n1", tag: "P-101", type: "Equipment", label: "Pump P-101" },
      { id: "n2", tag: "TIC-201", type: "Instrument", label: "TIC-201" },
    ];
    const edges = [
      { source: "n1", target: "n2", type: "connects", label: "connection" },
    ];

    const elements = toCytoscapeElements(nodes, edges);

    // 2 nodes + 1 edge = 3 elements
    expect(elements).toHaveLength(3);

    // Verify node data
    const nodeEl = elements.find((e) => e.data.id === "n1");
    expect(nodeEl?.data.label).toBe("P-101");
    expect(nodeEl?.data.type).toBe("Equipment");

    // Verify edge data
    const edgeEl = elements.find(
      (e) => e.data.source === "n1" && e.data.target === "n2",
    );
    expect(edgeEl).toBeDefined();
    expect(edgeEl?.data.label).toBe("connection");
  });

  it("uses tag as label when available", () => {
    const nodes = [
      { id: "n1", tag: "FV-301", type: "Valve", label: "Flow Valve 301" },
    ];
    const elements = toCytoscapeElements(nodes, []);

    expect(elements[0].data.label).toBe("FV-301");
  });

  it("has expected color mappings", () => {
    expect(NODE_TYPE_COLORS.Equipment).toBe("#2563eb");
    expect(NODE_TYPE_COLORS.Instrument).toBe("#dc2626");
    expect(NODE_TYPE_COLORS.Valve).toBe("#f97316");
    expect(NODE_TYPE_COLORS.PipingSegment).toBe("#6b7280");
    expect(NODE_TYPE_COLORS.Nozzle).toBe("#16a34a");
    expect(DEFAULT_NODE_COLOR).toBe("#8b5cf6");
  });
});
