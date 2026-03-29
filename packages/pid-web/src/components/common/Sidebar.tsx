import { useNavigate } from "react-router-dom";
import { usePidStore } from "@/stores/pidStore";

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const { pids, activePidId, setActivePid } = usePidStore();
  const navigate = useNavigate();

  function handleSelectPid(pidId: string) {
    setActivePid(pidId);
    navigate(`/pid/${pidId}`);
    onNavigate?.();
  }

  function handleUploadClick() {
    navigate("/");
    onNavigate?.();
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          P&amp;IDs Cargados
        </h2>
      </div>

      <nav className="scrollbar-thin flex-1 overflow-y-auto p-2">
        {pids.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-gray-400">
            No hay P&amp;IDs cargados
          </p>
        ) : (
          <ul className="space-y-1">
            {pids.map((pid) => (
              <li key={pid.pid_id}>
                <button
                  type="button"
                  className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
                    activePidId === pid.pid_id
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                  onClick={() => handleSelectPid(pid.pid_id)}
                >
                  <p className="truncate text-sm font-medium">
                    {pid.file_name ?? pid.pid_id}
                  </p>
                  <div className="mt-0.5 flex gap-3 text-xs text-gray-500">
                    <span title="Equipos">{pid.equipment_count} equip.</span>
                    <span title="Nodos">{pid.node_count} nodos</span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="border-t border-gray-200 p-3">
        <button
          type="button"
          className="btn-primary w-full text-sm"
          onClick={handleUploadClick}
        >
          + Subir P&amp;ID
        </button>
      </div>
    </div>
  );
}
