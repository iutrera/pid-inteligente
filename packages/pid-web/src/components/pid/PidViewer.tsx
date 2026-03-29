import { useCallback, useRef, useState } from "react";
import { usePidStore } from "@/stores/pidStore";
import { validatePid, convertDrawioToDexpi, convertDexpiToDrawio } from "@/services/api-client";
import type { ValidationError } from "@/types/api";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function PidViewer() {
  const { pids, activePidId } = usePidStore();
  const activePid = pids.find((p) => p.pid_id === activePidId);

  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [validating, setValidating] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [actionTarget, setActionTarget] = useState<"validate" | "dexpi" | "drawio" | null>(null);

  const handleFileSelected = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file || !actionTarget) return;
      e.target.value = "";

      try {
        if (actionTarget === "validate") {
          setValidating(true);
          const errors = await validatePid(file);
          setValidationErrors(errors);
        } else if (actionTarget === "dexpi") {
          setExporting("dexpi");
          const blob = await convertDrawioToDexpi(file);
          downloadBlob(blob, file.name.replace(/\.\w+$/, ".dexpi.xml"));
        } else if (actionTarget === "drawio") {
          setExporting("drawio");
          const blob = await convertDexpiToDrawio(file);
          downloadBlob(blob, file.name.replace(/\.\w+$/, ".drawio"));
        }
      } catch (err) {
        console.error(err);
      } finally {
        setValidating(false);
        setExporting(null);
        setActionTarget(null);
      }
    },
    [actionTarget],
  );

  function triggerFileAction(target: "validate" | "dexpi" | "drawio") {
    setActionTarget(target);
    fileInputRef.current?.click();
  }

  if (!activePid) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="text-sm text-gray-400">Selecciona un P&amp;ID</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Informacion del P&amp;ID
        </h3>
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto p-4">
        <h4 className="text-base font-bold text-gray-900">
          {activePid.file_name ?? activePid.pid_id}
        </h4>

        {/* Stats grid */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <StatCard label="Equipos" value={activePid.equipment_count} />
          <StatCard label="Instrumentos" value={activePid.instrument_count} />
          <StatCard label="Nodos" value={activePid.node_count} />
          <StatCard label="Conexiones" value={activePid.edge_count} />
        </div>

        {/* Actions */}
        <div className="mt-6 space-y-2">
          <button
            type="button"
            className="btn-secondary w-full text-sm"
            disabled={validating}
            onClick={() => triggerFileAction("validate")}
          >
            {validating ? "Validando..." : "Validar P&ID"}
          </button>
          <button
            type="button"
            className="btn-secondary w-full text-sm"
            disabled={exporting !== null}
            onClick={() => triggerFileAction("dexpi")}
          >
            {exporting === "dexpi" ? "Exportando..." : "Exportar DEXPI"}
          </button>
          <button
            type="button"
            className="btn-secondary w-full text-sm"
            disabled={exporting !== null}
            onClick={() => triggerFileAction("drawio")}
          >
            {exporting === "drawio" ? "Exportando..." : "Exportar Draw.io"}
          </button>
        </div>

        {/* Validation errors */}
        {validationErrors.length > 0 && (
          <div className="mt-4">
            <h5 className="mb-2 text-xs font-semibold uppercase tracking-wide text-red-600">
              Errores de Validacion ({validationErrors.length})
            </h5>
            <ul className="space-y-2">
              {validationErrors.map((err, i) => (
                <li
                  key={`${err.shape_id}-${i}`}
                  className="rounded-lg border border-red-200 bg-red-50 p-2 text-xs"
                >
                  <span className="font-medium text-red-800">
                    [{err.error_type}]
                  </span>{" "}
                  <span className="text-red-700">{err.message}</span>
                  <p className="mt-0.5 text-red-500">
                    Shape: {err.shape_id}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".drawio,.xml"
        className="hidden"
        onChange={handleFileSelected}
      />
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
