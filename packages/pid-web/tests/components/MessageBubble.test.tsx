import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageBubble } from "@/components/chat/MessageBubble";

describe("MessageBubble", () => {
  it("renders user message", () => {
    render(
      <MessageBubble message={{ role: "user", content: "Hello" }} />,
    );
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders assistant message", () => {
    render(
      <MessageBubble
        message={{ role: "assistant", content: "I can help with that." }}
      />,
    );
    expect(
      screen.getByText(/I can help with that/),
    ).toBeInTheDocument();
  });

  it("highlights equipment tags in assistant messages", () => {
    render(
      <MessageBubble
        message={{ role: "assistant", content: "La bomba P-101 esta conectada a TIC-201" }}
      />,
    );
    expect(screen.getByText("P-101")).toBeInTheDocument();
    expect(screen.getByText("TIC-201")).toBeInTheDocument();
  });
});
