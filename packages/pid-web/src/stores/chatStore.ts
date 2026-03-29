import { create } from "zustand";
import type { ChatMessage } from "@/types/chat";

export interface ChatStoreState {
  messages: ChatMessage[];
  streamingMessage: string;
  isStreaming: boolean;
  addUserMessage: (content: string) => void;
  startStreaming: () => void;
  appendDelta: (delta: string) => void;
  finishStreaming: (fullResponse: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStoreState>((set) => ({
  messages: [],
  streamingMessage: "",
  isStreaming: false,

  addUserMessage: (content) =>
    set((state) => ({
      messages: [...state.messages, { role: "user" as const, content }],
    })),

  startStreaming: () =>
    set({ isStreaming: true, streamingMessage: "" }),

  appendDelta: (delta) =>
    set((state) => ({
      streamingMessage: state.streamingMessage + delta,
    })),

  finishStreaming: (fullResponse) =>
    set((state) => ({
      isStreaming: false,
      streamingMessage: "",
      messages: [
        ...state.messages,
        { role: "assistant" as const, content: fullResponse },
      ],
    })),

  clearMessages: () =>
    set({ messages: [], streamingMessage: "", isStreaming: false }),
}));
