import type {
  GraphData,
  HealthResponse,
  PidStats,
  ValidationError,
} from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_URL || "";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function jsonRequest<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `API ${res.status}: ${res.statusText}${text ? ` - ${text}` : ""}`,
    );
  }
  return res.json() as Promise<T>;
}

async function fileDownloadRequest(
  url: string,
  file: File,
): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}${url}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `API ${res.status}: ${res.statusText}${text ? ` - ${text}` : ""}`,
    );
  }
  return res.blob();
}

// ---------------------------------------------------------------------------
// Graph endpoints
// ---------------------------------------------------------------------------

/** Update the .drawio XML after editing and rebuild the Knowledge Graph. */
export async function updateDrawioAndRebuild(
  pidId: string,
  xml: string,
): Promise<PidStats> {
  return jsonRequest<PidStats>(`/api/graph/${encodeURIComponent(pidId)}/drawio`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ xml }),
  });
}

/** Upload a file and build the Knowledge Graph. */
export async function uploadAndBuildGraph(file: File): Promise<PidStats> {
  const formData = new FormData();
  formData.append("file", file);
  return jsonRequest<PidStats>("/api/graph/build", {
    method: "POST",
    body: formData,
  });
}

/** Fetch the graph for a given P&ID. */
export async function getGraph(pidId: string): Promise<GraphData> {
  return jsonRequest<GraphData>(`/api/graph/${encodeURIComponent(pidId)}`);
}

/** Fetch the detailed graph for a given P&ID. */
export async function getDetailedGraph(pidId: string): Promise<GraphData> {
  return jsonRequest<GraphData>(
    `/api/graph/${encodeURIComponent(pidId)}/detail`,
  );
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/** Validate a P&ID file and return any errors found. */
export async function validatePid(file: File): Promise<ValidationError[]> {
  const formData = new FormData();
  formData.append("file", file);
  return jsonRequest<ValidationError[]>("/api/validate", {
    method: "POST",
    body: formData,
  });
}

// ---------------------------------------------------------------------------
// Conversions
// ---------------------------------------------------------------------------

/** Convert a Draw.io file to DEXPI format (returns downloadable blob). */
export async function convertDrawioToDexpi(file: File): Promise<Blob> {
  return fileDownloadRequest("/api/convert/drawio-to-dexpi", file);
}

/** Convert a DEXPI file to Draw.io format (returns downloadable blob). */
export async function convertDexpiToDrawio(file: File): Promise<Blob> {
  return fileDownloadRequest("/api/convert/dexpi-to-drawio", file);
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

/** Health-check endpoint. */
export async function checkHealth(): Promise<HealthResponse> {
  return jsonRequest<HealthResponse>("/api/health");
}
