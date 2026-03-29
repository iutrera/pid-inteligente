import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { usePidStore } from "@/stores/pidStore";
import { sendChatMessage } from "@/services/sse-client";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

export function ChatPanel() {
  const {
    messages,
    streamingMessage,
    isStreaming,
    addUserMessage,
    startStreaming,
    appendDelta,
    finishStreaming,
  } = useChatStore();
  const activePidId = usePidStore((s) => s.activePidId);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, streamingMessage]);

  async function handleSend(text: string) {
    if (!activePidId || isStreaming) return;

    addUserMessage(text);
    startStreaming();

    try {
      await sendChatMessage(
        activePidId,
        text,
        // Send entire conversation history (without the user msg we just added,
        // since the store update may not have flushed yet). We include all
        // previous messages plus the new user message.
        [...messages, { role: "user" as const, content: text }],
        (delta) => appendDelta(delta),
        (fullResponse) => finishStreaming(fullResponse),
      );
    } catch (err) {
      finishStreaming(
        `Error: ${err instanceof Error ? err.message : "No se pudo conectar con el chat."}`,
      );
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 px-4 py-2">
        <h3 className="text-sm font-semibold text-gray-700">Chat</h3>
      </div>

      {/* Messages area */}
      <div
        ref={scrollRef}
        className="scrollbar-thin flex-1 space-y-3 overflow-y-auto p-4"
      >
        {messages.length === 0 && !isStreaming && (
          <p className="py-8 text-center text-sm text-gray-400">
            Pregunta lo que quieras sobre tu P&amp;ID
          </p>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {/* Streaming in-progress message */}
        {isStreaming && streamingMessage && (
          <MessageBubble
            message={{ role: "assistant", content: streamingMessage }}
          />
        )}

        {/* Typing indicator */}
        {isStreaming && !streamingMessage && (
          <div className="flex items-center gap-1 px-2 py-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
          </div>
        )}
      </div>

      <ChatInput onSend={handleSend} disabled={isStreaming || !activePidId} />
    </div>
  );
}
