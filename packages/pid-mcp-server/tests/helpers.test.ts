import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getApiBaseUrl,
  replaceExtension,
  textResult,
  consumeSseStream,
} from "../src/tools/helpers.js";

describe("getApiBaseUrl", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("should return default URL when no env vars set", () => {
    delete process.env.API_BASE_URL;
    delete process.env.PID_API_URL;
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("should prefer API_BASE_URL over PID_API_URL", () => {
    process.env.API_BASE_URL = "http://api-base:9000";
    process.env.PID_API_URL = "http://pid-api:9001";
    expect(getApiBaseUrl()).toBe("http://api-base:9000");
  });

  it("should fall back to PID_API_URL when API_BASE_URL is not set", () => {
    delete process.env.API_BASE_URL;
    process.env.PID_API_URL = "http://pid-api:9001";
    expect(getApiBaseUrl()).toBe("http://pid-api:9001");
  });
});

describe("replaceExtension", () => {
  it("should replace .drawio with .xml", () => {
    expect(replaceExtension("/path/to/file.drawio", ".xml")).toBe(
      "/path/to/file.xml",
    );
  });

  it("should replace .xml with .drawio", () => {
    expect(replaceExtension("/path/to/file.xml", ".drawio")).toBe(
      "/path/to/file.drawio",
    );
  });

  it("should handle files without extension", () => {
    expect(replaceExtension("/path/to/file", ".xml")).toBe(
      "/path/to/file.xml",
    );
  });
});

describe("textResult", () => {
  it("should return a text content block", () => {
    const result = textResult("hello");
    expect(result).toEqual({
      content: [{ type: "text", text: "hello" }],
      isError: false,
    });
  });

  it("should set isError flag", () => {
    const result = textResult("bad", true);
    expect(result.isError).toBe(true);
  });
});

describe("consumeSseStream", () => {
  function makeResponse(chunks: string[]): Response {
    const encoder = new TextEncoder();
    let index = 0;
    const stream = new ReadableStream<Uint8Array>({
      pull(controller) {
        if (index < chunks.length) {
          controller.enqueue(encoder.encode(chunks[index]));
          index++;
        } else {
          controller.close();
        }
      },
    });
    return new Response(stream);
  }

  it("should accumulate delta events and return full_response when done", async () => {
    const response = makeResponse([
      'data: {"delta":"Hello "}\n\n',
      'data: {"delta":"World"}\n\n',
      'data: {"done":true,"full_response":"Hello World"}\n\n',
    ]);
    const result = await consumeSseStream(response);
    expect(result).toBe("Hello World");
  });

  it("should accumulate deltas if no done event arrives", async () => {
    const response = makeResponse([
      'data: {"delta":"chunk1"}\n\n',
      'data: {"delta":"chunk2"}\n\n',
    ]);
    const result = await consumeSseStream(response);
    expect(result).toBe("chunk1chunk2");
  });

  it("should handle empty stream", async () => {
    const response = makeResponse([]);
    const result = await consumeSseStream(response);
    expect(result).toBe("");
  });

  it("should handle plain text fallback for non-JSON data lines", async () => {
    const response = makeResponse(["data: some plain text\n\n"]);
    const result = await consumeSseStream(response);
    expect(result).toBe("some plain text");
  });
});
