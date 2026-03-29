/** A single message in the chat conversation. */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** Shape of the chat store state. */
export interface ChatState {
  messages: ChatMessage[];
  streamingMessage: string;
  isStreaming: boolean;
  addUserMessage: (content: string) => void;
  startStreaming: () => void;
  appendDelta: (delta: string) => void;
  finishStreaming: (fullResponse: string) => void;
  clearMessages: () => void;
}
