"""Chat route: LLM-powered Q&A over P&ID Knowledge Graphs with SSE streaming."""

from __future__ import annotations

import json
from typing import AsyncIterator

import anthropic
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from pid_rag.prompts.engineering import SYSTEM_PROMPT
from pid_rag.retrieval.graph_rag import GraphRAG

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    """Body for the chat endpoint."""

    pid_id: str = Field(..., description="P&ID identifier to query")
    message: str = Field(..., description="User's question")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns",
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post(
    "",
    summary="Chat with the P&ID assistant (SSE streaming)",
    response_class=EventSourceResponse,
)
async def chat(request: Request, body: ChatRequest) -> EventSourceResponse:
    """Send a question about a P&ID and receive a streaming response via SSE.

    The response is a stream of Server-Sent Events:
    - ``data: {"delta": "partial text"}`` for each chunk
    - ``data: {"done": true, "full_response": "complete text"}`` at the end
    """
    settings = request.app.state.settings
    neo4j_store = request.app.state.neo4j_store

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured.",
        )

    # Retrieve relevant graph context
    rag = GraphRAG(neo4j_store)
    try:
        graph_context = await rag.retrieve(body.pid_id, body.message)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Graph retrieval failed: {exc}",
        ) from exc

    # Build messages for Claude
    system_message = (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Knowledge Graph Data for P&ID '{body.pid_id}'\n\n"
        f"{graph_context}"
    )

    messages: list[dict[str, str]] = []
    for msg in body.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def _event_generator() -> AsyncIterator[str]:
        full_response = ""
        try:
            async with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_message,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield json.dumps({"delta": text})
        except anthropic.APIError as exc:
            yield json.dumps({"error": str(exc)})
            return

        yield json.dumps({"done": True, "full_response": full_response})

    return EventSourceResponse(_event_generator())
