"""Tests for the /api/chat endpoint."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_returns_sse_stream(client: AsyncClient) -> None:
    """POST /api/chat returns an SSE stream with delta events and a done event."""
    # Mock the Anthropic streaming client
    mock_stream_ctx = AsyncMock()

    async def mock_text_stream():
        yield "Hello, "
        yield "this is a test."

    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream_ctx.text_stream = mock_text_stream()

    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages = MagicMock()
    mock_anthropic_client.messages.stream = MagicMock(return_value=mock_stream_ctx)

    with patch("pid_rag.api.routes.chat.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
        resp = await client.post(
            "/api/chat",
            json={
                "pid_id": "test-pid",
                "message": "What equipment is in this P&ID?",
                "history": [],
            },
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    # Parse SSE events from the response body
    events = _parse_sse_events(resp.text)
    assert len(events) >= 2  # At least one delta + done

    # Check that we got delta events
    deltas = [e for e in events if "delta" in e]
    assert len(deltas) >= 1

    # Check that we got a done event
    done_events = [e for e in events if e.get("done") is True]
    assert len(done_events) == 1
    assert done_events[0]["full_response"] == "Hello, this is a test."


@pytest.mark.asyncio
async def test_chat_with_history(client: AsyncClient) -> None:
    """POST /api/chat accepts conversation history."""
    mock_stream_ctx = AsyncMock()

    async def mock_text_stream():
        yield "Response with context."

    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream_ctx.text_stream = mock_text_stream()

    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages = MagicMock()
    mock_anthropic_client.messages.stream = MagicMock(return_value=mock_stream_ctx)

    with patch("pid_rag.api.routes.chat.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
        resp = await client.post(
            "/api/chat",
            json={
                "pid_id": "test-pid",
                "message": "Tell me more about P-101",
                "history": [
                    {"role": "user", "content": "What pumps are there?"},
                    {"role": "assistant", "content": "There is P-101."},
                ],
            },
        )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_chat_missing_api_key(client: AsyncClient) -> None:
    """POST /api/chat returns 500 when ANTHROPIC_API_KEY is empty."""
    # Override the settings to have no API key
    client._transport.app.state.settings.ANTHROPIC_API_KEY = ""  # type: ignore[union-attr]

    resp = await client.post(
        "/api/chat",
        json={
            "pid_id": "test-pid",
            "message": "Hello",
        },
    )
    assert resp.status_code == 500

    # Restore for other tests
    client._transport.app.state.settings.ANTHROPIC_API_KEY = "test-key-for-testing"  # type: ignore[union-attr]


def _parse_sse_events(text: str) -> list[dict]:
    """Parse SSE event data lines from raw response text."""
    events: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            if data_str:
                try:
                    events.append(json.loads(data_str))
                except json.JSONDecodeError:
                    pass
    return events
