import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "@/components/chat/ChatInput";

describe("ChatInput", () => {
  it("renders with placeholder", () => {
    render(<ChatInput onSend={() => {}} />);
    expect(
      screen.getByPlaceholderText("Pregunta sobre tu P&ID..."),
    ).toBeInTheDocument();
  });

  it("calls onSend when Enter is pressed with text", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Pregunta sobre tu P&ID...");
    fireEvent.change(textarea, { target: { value: "test message" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(onSend).toHaveBeenCalledWith("test message");
  });

  it("does not call onSend on Shift+Enter", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Pregunta sobre tu P&ID...");
    fireEvent.change(textarea, { target: { value: "test" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input when disabled prop is true", () => {
    render(<ChatInput onSend={() => {}} disabled />);
    expect(
      screen.getByPlaceholderText("Pregunta sobre tu P&ID..."),
    ).toBeDisabled();
  });

  it("does not call onSend with empty text", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText("Pregunta sobre tu P&ID...");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(onSend).not.toHaveBeenCalled();
  });
});
