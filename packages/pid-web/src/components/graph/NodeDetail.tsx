import { useQuery } from "@tanstack/react-query";
import { getDetailedGraph } from "@/services/api-client";
import { NODE_TYPE_COLORS, DEFAULT_NODE_COLOR } from "@/types/graph";

interface NodeDetailProps {
  pidId: string;
  nodeId: string;
  onClose: () => void;
}

export function NodeDetail({ pidId, nodeId, onClose }: NodeDetailProps) {
  const { data } = useQuery({
    queryKey: ["graph-detail", pidId],
    queryFn: () => getDetailedGraph(pidId),
    enabled: !!pidId,
  });

  const node = data?.nodes.find((n) => n.id === nodeId);

  if (!node) {
    return (
      <div className="p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">
            Detalle del Nodo
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Cerrar detalle"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p className="mt-4 text-sm text-gray-400">Cargando...</p>
      </div>
    );
  }

  const color = NODE_TYPE_COLORS[node.type] ?? DEFAULT_NODE_COLOR;

  // Extract engineering attributes (everything besides the known fields)
  const knownKeys = new Set(["id", "tag", "type", "label"]);
  const extraAttrs = Object.entries(node).filter(
    ([k]) => !knownKeys.has(k),
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Detalle del Nodo
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          aria-label="Cerrar detalle"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto p-4">
        {/* Type badge */}
        <div className="mb-3 flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
            {node.type}
          </span>
        </div>

        {/* Tag */}
        <h4 className="text-lg font-bold text-gray-900">{node.tag}</h4>

        {/* Label */}
        {node.label && node.label !== node.tag && (
          <p className="mt-1 text-sm text-gray-600">{node.label}</p>
        )}

        {/* Engineering attributes */}
        {extraAttrs.length > 0 && (
          <div className="mt-4">
            <h5 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
              Atributos
            </h5>
            <dl className="space-y-1.5">
              {extraAttrs.map(([key, value]) => (
                <div key={key} className="flex text-sm">
                  <dt className="w-1/3 shrink-0 font-medium text-gray-500">
                    {key}
                  </dt>
                  <dd className="text-gray-800">{String(value)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
