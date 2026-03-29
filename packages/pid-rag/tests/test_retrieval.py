"""Tests for the Graph-RAG retrieval module."""

from __future__ import annotations

import pytest

from pid_rag.retrieval.graph_rag import GraphRAG, _serialize_graph

from tests.conftest import MockNeo4jStore, _make_sample_graph


@pytest.mark.asyncio
async def test_retrieve_default_returns_condensed() -> None:
    """A generic question should return the condensed graph."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("test-pid", "What is this diagram about?")
    assert "NODES:" in result
    assert "CONNECTIONS:" in result
    assert "P-101" in result
    assert "E-101" in result


@pytest.mark.asyncio
async def test_retrieve_flow_keyword() -> None:
    """Questions with flow keywords should return the condensed graph."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("test-pid", "Show me the main process flow")
    assert "NODES:" in result
    assert "P-101" in result


@pytest.mark.asyncio
async def test_retrieve_specific_tag() -> None:
    """Questions mentioning a specific tag should retrieve its neighbourhood."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("test-pid", "Tell me about P-101")
    assert "P-101" in result


@pytest.mark.asyncio
async def test_retrieve_multiple_tags() -> None:
    """Questions with multiple tags should retrieve merged neighbourhoods."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("test-pid", "Compare P-101 and E-101")
    assert "P-101" in result
    assert "E-101" in result


@pytest.mark.asyncio
async def test_retrieve_loop_keyword() -> None:
    """Questions about control loops should use appropriate retrieval."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("test-pid", "Explain the control loop")
    assert "NODES:" in result


@pytest.mark.asyncio
async def test_retrieve_nonexistent_pid() -> None:
    """Querying a non-existent pid should still return graph data (mock returns default)."""
    store = MockNeo4jStore()
    rag = GraphRAG(store)
    result = await rag.retrieve("nonexistent", "What is here?")
    assert "NODES:" in result


def test_serialize_graph_format() -> None:
    """_serialize_graph produces the expected text format."""
    graph = _make_sample_graph()
    text = _serialize_graph(graph)
    assert text.startswith("NODES:")
    assert "CONNECTIONS:" in text
    assert "[Equipment]" in text
    assert "P-101" in text
    assert "FLOW" in text
