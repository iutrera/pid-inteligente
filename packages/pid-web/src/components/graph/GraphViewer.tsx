import { useCallback, useRef } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import type cytoscape from "cytoscape";
import { useQuery } from "@tanstack/react-query";
import { getGraph } from "@/services/api-client";
import { toCytoscapeElements, cytoscapeStylesheet } from "@/types/graph";

interface GraphViewerProps {
  pidId: string;
  onNodeSelect: (nodeId: string | null) => void;
}

export function GraphViewer({ pidId, onNodeSelect }: GraphViewerProps) {
  const cyRef = useRef<cytoscape.Core | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["graph", pidId],
    queryFn: () => getGraph(pidId),
    enabled: !!pidId,
  });

  const elements = data ? toCytoscapeElements(data.nodes, data.edges) : [];

  const handleCyInit = useCallback(
    (cy: cytoscape.Core) => {
      cyRef.current = cy;

      cy.on("tap", "node", (evt) => {
        const nodeId = evt.target.id();
        onNodeSelect(nodeId);
      });

      cy.on("tap", (evt) => {
        if (evt.target === cy) {
          onNodeSelect(null);
        }
      });

      // Apply layout after mounting
      cy.layout({
        name: "cose",
        animate: true,
        animationDuration: 500,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 80,
        padding: 30,
      } as cytoscape.LayoutOptions).run();
    },
    [onNodeSelect],
  );

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <svg
            className="mx-auto h-8 w-8 animate-spin text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-500">Cargando grafo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="text-sm text-red-600">
          Error al cargar el grafo:{" "}
          {error instanceof Error ? error.message : "Error desconocido"}
        </p>
      </div>
    );
  }

  if (elements.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="text-sm text-gray-400">Grafo vacio</p>
      </div>
    );
  }

  return (
    <CytoscapeComponent
      elements={elements}
      stylesheet={cytoscapeStylesheet}
      className="h-full w-full"
      cy={handleCyInit}
      wheelSensitivity={0.3}
    />
  );
}
