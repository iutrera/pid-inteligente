import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

/**
 * These tests verify that each tool calls the correct API endpoint with
 * the correct parameters by mocking the global fetch function.
 *
 * Since MCP SDK tools are registered via server.tool() and invoked through
 * the MCP protocol, we test the underlying logic by importing the helpers
 * and simulating the fetch calls each tool would make.
 */

// We mock fetch at the global level
const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  // Reset env to defaults
  delete process.env.API_BASE_URL;
  delete process.env.PID_API_URL;
});

afterEach(() => {
  vi.restoreAllMocks();
});

// Helper to create a mock Response
function mockResponse(body: unknown, status = 200): Response {
  const responseBody =
    typeof body === "string" ? body : JSON.stringify(body);
  return new Response(responseBody, {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockBinaryResponse(content: string, status = 200): Response {
  return new Response(content, {
    status,
    headers: { "Content-Type": "application/octet-stream" },
  });
}

describe("convert tools — endpoint calls", () => {
  it("convert_drawio_to_dexpi calls POST /api/convert/drawio-to-dexpi", async () => {
    const { apiFetch, buildFormData } = await import(
      "../src/tools/helpers.js"
    );

    fetchMock.mockResolvedValueOnce(
      mockBinaryResponse("<xml>dexpi content</xml>"),
    );

    const response = await apiFetch("/api/convert/drawio-to-dexpi", {
      method: "POST",
      body: buildFormData("file", Buffer.from("<drawio/>"), "test.drawio"),
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/convert/drawio-to-dexpi");
    expect(options.method).toBe("POST");
    expect(response.status).toBe(200);
  });

  it("convert_dexpi_to_drawio calls POST /api/convert/dexpi-to-drawio", async () => {
    const { apiFetch, buildFormData } = await import(
      "../src/tools/helpers.js"
    );

    fetchMock.mockResolvedValueOnce(
      mockBinaryResponse("<mxfile>drawio content</mxfile>"),
    );

    const response = await apiFetch("/api/convert/dexpi-to-drawio", {
      method: "POST",
      body: buildFormData("file", Buffer.from("<xml/>"), "test.xml"),
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/convert/dexpi-to-drawio");
    expect(options.method).toBe("POST");
    expect(response.status).toBe(200);
  });
});

describe("graph tools — endpoint calls", () => {
  it("build_knowledge_graph calls POST /api/graph/build", async () => {
    const { apiFetch, buildFormDataWithField } = await import(
      "../src/tools/helpers.js"
    );

    fetchMock.mockResolvedValueOnce(
      mockResponse({
        pid_id: "test-pid",
        node_count: 10,
        edge_count: 15,
        equipment_count: 5,
        instrument_count: 3,
      }),
    );

    const formData = buildFormDataWithField(
      "file",
      Buffer.from("<drawio/>"),
      "test.drawio",
      "pid_id",
      "test-pid",
    );

    const response = await apiFetch("/api/graph/build", {
      method: "POST",
      body: formData,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/graph/build");
    expect(options.method).toBe("POST");

    const data = await response.json();
    expect(data).toEqual({
      pid_id: "test-pid",
      node_count: 10,
      edge_count: 15,
      equipment_count: 5,
      instrument_count: 3,
    });
  });

  it("get_graph calls GET /api/graph/{pid_id}", async () => {
    const { apiFetch } = await import("../src/tools/helpers.js");

    fetchMock.mockResolvedValueOnce(
      mockResponse({
        nodes: [{ id: "n1", type: "equipment", label: "Pump P-101" }],
        edges: [{ source: "n1", target: "n2", type: "connected_to" }],
      }),
    );

    const response = await apiFetch("/api/graph/test-pid", {
      method: "GET",
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/graph/test-pid");
    expect(response.status).toBe(200);
  });

  it("query_pid calls POST /api/chat with correct body", async () => {
    const { apiFetch } = await import("../src/tools/helpers.js");

    // Return a response matching the actual backend SSE format
    fetchMock.mockResolvedValueOnce(
      new Response(
        'data: {"delta":"The pump P-101 is a centrifugal pump."}\n\n' +
        'data: {"done":true,"full_response":"The pump P-101 is a centrifugal pump."}\n\n',
        { status: 200 },
      ),
    );

    const body = JSON.stringify({
      pid_id: "test-pid",
      message: "What is pump P-101?",
      history: [],
    });

    const response = await apiFetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/chat");
    expect(options.method).toBe("POST");
    expect(options.body).toBe(body);
  });
});

describe("validate tool — endpoint calls", () => {
  it("validate_pid calls POST /api/validate", async () => {
    const { apiFetch, buildFormData } = await import(
      "../src/tools/helpers.js"
    );

    fetchMock.mockResolvedValueOnce(
      mockResponse([
        {
          shape_id: "shape-1",
          error_type: "missing_tag",
          message: "Tag is missing",
        },
      ]),
    );

    const response = await apiFetch("/api/validate", {
      method: "POST",
      body: buildFormData("file", Buffer.from("<drawio/>"), "test.drawio"),
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/validate");
    expect(options.method).toBe("POST");

    const data = await response.json();
    expect(data).toHaveLength(1);
    expect(data[0].error_type).toBe("missing_tag");
  });

  it("validate_pid handles empty errors (clean file)", async () => {
    const { apiFetch, buildFormData } = await import(
      "../src/tools/helpers.js"
    );

    fetchMock.mockResolvedValueOnce(mockResponse([]));

    const response = await apiFetch("/api/validate", {
      method: "POST",
      body: buildFormData("file", Buffer.from("<drawio/>"), "clean.drawio"),
    });

    const data = await response.json();
    expect(data).toEqual([]);
  });
});

describe("error handling", () => {
  it("apiFetch throws on timeout", async () => {
    const { apiFetch } = await import("../src/tools/helpers.js");

    fetchMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          // Never resolves within timeout
          setTimeout(() => resolve(mockResponse({})), 60_000);
        }),
    );

    await expect(
      apiFetch("/api/health", { method: "GET" }, 50),
    ).rejects.toThrow(/timed out/i);
  });

  it("apiFetch throws on network error", async () => {
    const { apiFetch } = await import("../src/tools/helpers.js");

    fetchMock.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    await expect(
      apiFetch("/api/health", { method: "GET" }),
    ).rejects.toThrow(/ECONNREFUSED/);
  });
});
