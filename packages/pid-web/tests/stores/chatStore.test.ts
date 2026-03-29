import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore } from "@/stores/chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      streamingMessage: "",
      isStreaming: false,
    });
  });

  it("should start with empty state", () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.streamingMessage).toBe("");
    expect(state.isStreaming).toBe(false);
  });

  it("should add a user message", () => {
    useChatStore.getState().addUserMessage("Hola");

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual({ role: "user", content: "Hola" });
  });

  it("should handle streaming lifecycle", () => {
    // Start streaming
    useChatStore.getState().startStreaming();
    expect(useChatStore.getState().isStreaming).toBe(true);
    expect(useChatStore.getState().streamingMessage).toBe("");

    // Append deltas
    useChatStore.getState().appendDelta("Hola ");
    expect(useChatStore.getState().streamingMessage).toBe("Hola ");

    useChatStore.getState().appendDelta("mundo");
    expect(useChatStore.getState().streamingMessage).toBe("Hola mundo");

    // Finish streaming
    useChatStore.getState().finishStreaming("Hola mundo");

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.streamingMessage).toBe("");
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual({
      role: "assistant",
      content: "Hola mundo",
    });
  });

  it("should clear all messages", () => {
    useChatStore.getState().addUserMessage("Pregunta 1");
    useChatStore.getState().finishStreaming("Respuesta 1");
    useChatStore.getState().addUserMessage("Pregunta 2");

    useChatStore.getState().clearMessages();

    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.streamingMessage).toBe("");
    expect(state.isStreaming).toBe(false);
  });

  it("should accumulate multiple messages in order", () => {
    useChatStore.getState().addUserMessage("Q1");
    useChatStore.getState().finishStreaming("A1");
    useChatStore.getState().addUserMessage("Q2");
    useChatStore.getState().finishStreaming("A2");

    const messages = useChatStore.getState().messages;
    expect(messages).toHaveLength(4);
    expect(messages[0]).toEqual({ role: "user", content: "Q1" });
    expect(messages[1]).toEqual({ role: "assistant", content: "A1" });
    expect(messages[2]).toEqual({ role: "user", content: "Q2" });
    expect(messages[3]).toEqual({ role: "assistant", content: "A2" });
  });
});
