import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePidStore } from "@/stores/pidStore";
import { useChatStore } from "@/stores/chatStore";
import { GraphViewer } from "@/components/graph/GraphViewer";
import { NodeDetail } from "@/components/graph/NodeDetail";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { PidViewer } from "@/components/pid/PidViewer";
import { DrawioViewer } from "@/components/pid/DrawioViewer";

type LeftTab = "pid" | "graph";

export function PidPage(): JSX.Element {
  const { pidId } = useParams<{ pidId: string }>();
  const navigate = useNavigate();
  const { pids, setActivePid } = usePidStore();
  const clearMessages = useChatStore((s) => s.clearMessages);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [leftTab, setLeftTab] = useState<LeftTab>("pid");

  // Sync the active PID when navigating directly to this URL
  useEffect(() => {
    if (pidId) {
      const exists = pids.some((p) => p.pid_id === pidId);
      if (exists) {
        setActivePid(pidId);
      }
      // Don't redirect if PID not in store — it may have been loaded via API
      // The graph/drawio viewer will fetch directly from the API
    }
    return () => {
      clearMessages();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pidId]);

  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
  }, []);

  if (!pidId) return <></>;

  return (
    <div className="flex h-full">
      {/* Left column: P&ID / Graph with tabs (45%) */}
      <div className="flex h-full w-[45%] min-w-0 flex-col border-r border-gray-200">
        {/* Tab bar */}
        <div className="flex border-b border-gray-200">
          <button
            type="button"
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              leftTab === "pid"
                ? "border-b-2 border-blue-500 text-blue-600 bg-blue-50/50"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setLeftTab("pid")}
          >
            P&amp;ID
          </button>
          <button
            type="button"
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              leftTab === "graph"
                ? "border-b-2 border-blue-500 text-blue-600 bg-blue-50/50"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setLeftTab("graph")}
          >
            Knowledge Graph
          </button>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-hidden">
          {leftTab === "pid" ? (
            <DrawioViewer pidId={pidId} className="h-full w-full" />
          ) : (
            <GraphViewer pidId={pidId} onNodeSelect={handleNodeSelect} />
          )}
        </div>
      </div>

      {/* Center column: Chat (30%) */}
      <div className="flex h-full w-[30%] min-w-0 flex-col border-r border-gray-200">
        <ChatPanel />
      </div>

      {/* Right column: Detail or PidViewer (25%) */}
      <div className="flex h-full w-[25%] min-w-0 flex-col bg-white">
        {selectedNodeId && leftTab === "graph" ? (
          <NodeDetail
            pidId={pidId}
            nodeId={selectedNodeId}
            onClose={() => setSelectedNodeId(null)}
          />
        ) : (
          <PidViewer />
        )}
      </div>
    </div>
  );
}
