import type { ChatMessage } from "@/types/chat";

const BASE_URL = import.meta.env.VITE_API_URL || "";

/**
 * Send a chat message to the SSE endpoint and stream the response.
 *
 * Uses `fetch` with a `ReadableStream` reader so we can consume
 * server-sent events from a POST request (EventSource only supports GET).
 */
export async function sendChatMessage(
  pidId: string,
  message: string,
  history: ChatMessage[],
  onDelta: (text: string) => void,
  onDone: (fullResponse: string) => void,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pid_id: pidId, message, history }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Chat API ${res.status}: ${res.statusText}${text ? ` - ${text}` : ""}`,
    );
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder();
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
          const event = JSON.parse(jsonStr) as
            | { delta: string }
            | { done: true; full_response: string };

          if ("done" in event && event.done) {
            onDone(event.full_response);
            return;
          }

          if ("delta" in event) {
            onDelta(event.delta);
          }
        } catch {
          // Ignore malformed JSON lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
