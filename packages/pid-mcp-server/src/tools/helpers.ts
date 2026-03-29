import { readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { basename, dirname, join } from "node:path";

/**
 * Base URL for the P&ID backend API.
 * Reads from API_BASE_URL or PID_API_URL env vars, defaults to localhost:8000.
 */
export function getApiBaseUrl(): string {
  return (
    process.env.API_BASE_URL ||
    process.env.PID_API_URL ||
    "http://localhost:8000"
  );
}

/**
 * Default timeout for API requests (30 seconds).
 */
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Log a message to stderr (MCP servers use stdout for protocol, stderr for logs).
 */
export function log(message: string): void {
  process.stderr.write(`[pid-mcp-server] ${message}\n`);
}

/**
 * Read a file from disk and return its content as a Buffer.
 * Throws a descriptive error if the file does not exist.
 */
export async function readLocalFile(filePath: string): Promise<Buffer> {
  if (!existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
  return readFile(filePath);
}

/**
 * Write content to a file on disk.
 */
export async function writeLocalFile(
  filePath: string,
  content: Buffer | string,
): Promise<void> {
  await writeFile(filePath, content);
}

/**
 * Build a multipart/form-data body manually using the built-in FormData
 * available in Node.js 20+ (via undici).
 */
export function buildFormData(
  fieldName: string,
  fileContent: Buffer,
  fileName: string,
): FormData {
  const formData = new FormData();
  const blob = new Blob([fileContent]);
  formData.append(fieldName, blob, fileName);
  return formData;
}

/**
 * Build a multipart/form-data body with an extra text field.
 */
export function buildFormDataWithField(
  fileFieldName: string,
  fileContent: Buffer,
  fileName: string,
  textFieldName: string,
  textFieldValue: string,
): FormData {
  const formData = new FormData();
  const blob = new Blob([fileContent]);
  formData.append(fileFieldName, blob, fileName);
  formData.append(textFieldName, textFieldValue);
  return formData;
}

/**
 * Perform a fetch request to the backend API with timeout handling.
 * Returns the Response object. Throws on network errors or timeout.
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const url = `${getApiBaseUrl()}${path}`;
  log(`Calling ${options.method ?? "GET"} ${url}`);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    log(`Response status: ${response.status}`);
    return response;
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `API request timed out after ${timeoutMs}ms: ${options.method ?? "GET"} ${url}`,
      );
    }
    throw new Error(
      `API request failed: ${options.method ?? "GET"} ${url} - ${error instanceof Error ? error.message : String(error)}`,
    );
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * SSE event shape: either a delta chunk or the final done event.
 * Matches the backend contract used by pid-rag FastAPI.
 */
interface SseDelta {
  delta: string;
}
interface SseDone {
  done: true;
  full_response: string;
}
type SseEvent = SseDelta | SseDone;

/**
 * Consume an SSE (Server-Sent Events) stream from the /api/chat endpoint.
 *
 * The backend sends lines in the format `data: <json>` where the JSON is
 * either `{delta: "..."}` for incremental chunks or
 * `{done: true, full_response: "..."}` for the final message.
 *
 * Returns the complete accumulated response.
 */
export async function consumeSseStream(response: Response): Promise<string> {
  const body = response.body;
  if (!body) {
    throw new Error("Response body is null — cannot consume SSE stream");
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let accumulated = "";
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split("\n");
      // Keep the last (possibly incomplete) line in the buffer
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        const jsonStr = trimmed.slice("data:".length).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr) as SseEvent;

          // Final event — use the authoritative full_response
          if ("done" in event && event.done) {
            return event.full_response;
          }

          // Delta chunk — accumulate
          if ("delta" in event) {
            accumulated += event.delta;
          }
        } catch {
          // Not valid JSON — treat as plain text delta
          accumulated += jsonStr;
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      const remaining = buffer.trim();
      if (remaining.startsWith("data:")) {
        const jsonStr = remaining.slice("data:".length).trim();
        if (jsonStr) {
          try {
            const event = JSON.parse(jsonStr) as SseEvent;
            if ("done" in event && event.done) {
              return event.full_response;
            }
            if ("delta" in event) {
              accumulated += event.delta;
            }
          } catch {
            accumulated += jsonStr;
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return accumulated;
}

/**
 * Derive an output file path by replacing the extension of the input file.
 */
export function replaceExtension(
  filePath: string,
  newExtension: string,
): string {
  const dir = dirname(filePath);
  const base = basename(filePath);
  const dotIndex = base.lastIndexOf(".");
  const stem = dotIndex >= 0 ? base.slice(0, dotIndex) : base;
  return join(dir, `${stem}${newExtension}`);
}

/**
 * Format an MCP tool result as a text content block.
 */
export function textResult(text: string, isError = false) {
  return {
    content: [{ type: "text" as const, text }],
    isError,
  };
}

/**
 * Wrap a tool handler so that any thrown error is returned as a user-friendly
 * error result instead of crashing the server.
 */
export function safeHandler<T>(
  fn: (args: T) => Promise<{ content: { type: "text"; text: string }[]; isError?: boolean }>,
): (args: T) => Promise<{ content: { type: "text"; text: string }[]; isError?: boolean }> {
  return async (args: T) => {
    try {
      return await fn(args);
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : String(error);
      log(`Error: ${message}`);
      return textResult(`Error: ${message}`, true);
    }
  };
}
