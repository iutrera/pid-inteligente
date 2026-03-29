import { useNavigate } from "react-router-dom";
import { usePidStore } from "@/stores/pidStore";
import { FileUpload } from "@/components/common/FileUpload";
import type { PidStats } from "@/types/api";

export function HomePage() {
  const navigate = useNavigate();
  const addPid = usePidStore((s) => s.addPid);

  function handleUploadSuccess(stats: PidStats, file: File) {
    addPid({ ...stats, file_name: file.name });
    navigate(`/pid/${stats.pid_id}`);
  }

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <div className="w-full max-w-lg text-center">
        <h2 className="text-3xl font-bold text-gray-900">
          P&amp;ID Inteligente
        </h2>
        <p className="mt-3 text-gray-600">
          Sube un diagrama P&amp;ID para generar su Knowledge Graph,
          visualizarlo interactivamente y hacer preguntas en lenguaje natural.
        </p>

        <div className="mt-8">
          <FileUpload onSuccess={handleUploadSuccess} />
        </div>

        <p className="mt-4 text-xs text-gray-400">
          Formatos soportados: .drawio, .xml
        </p>
      </div>
    </div>
  );
}
