import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { usePidStore } from "@/stores/pidStore";
import { useChatStore } from "@/stores/chatStore";
import { GraphViewer } from "@/components/graph/GraphViewer";
import { NodeDetail } from "@/components/graph/NodeDetail";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { PidViewer } from "@/components/pid/PidViewer";
import { DrawioViewer } from "@/components/pid/DrawioViewer";
import { updateDrawioAndRebuild } from "@/services/api-client";

type LeftTab = "pid" | "graph";

export function PidPage(): JSX.Element {
  const { pidId } = useParams<{ pidId: string }>();
  const queryClient = useQueryClient();
  const { pids, setActivePid, addPid } = usePidStore();
  const clearMessages = useChatStore((s) => s.clearMessages);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [leftTab, setLeftTab] = useState<LeftTab>("pid");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (pidId) {
      const exists = pids.some((p) => p.pid_id === pidId);
      if (exists) {
        setActivePid(pidId);
      }
    }
    return () => {
      clearMessages();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pidId]);

  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
  }, []);

  /** Called when the user saves changes in the Draw.io editor. */
  const handleDrawioSave = useCallback(
    async (xml: string) => {
      if (!pidId || saving) return;
      setSaving(true);
      try {
        const stats = await updateDrawioAndRebuild(pidId, xml);
        // Update the store with new stats
        addPid({ ...stats, file_name: pidId });
        // Invalidate graph queries so GraphViewer refreshes
        await queryClient.invalidateQueries({ queryKey: ["graph", pidId] });
      } catch (err) {
        console.error("Failed to rebuild KG after edit:", err);
      } finally {
        setSaving(false);
      }
    },
    [pidId, saving, addPid, queryClient],
  );

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
            P&amp;ID {saving && "(guardando...)"}
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
            <DrawioViewer
              pidId={pidId}
              className="h-full w-full"
              onSave={handleDrawioSave}
            />
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
