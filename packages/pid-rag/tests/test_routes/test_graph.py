"""Tests for the /api/graph endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_build_graph(client: AsyncClient) -> None:
    """POST /api/graph/build creates a knowledge graph and returns stats."""
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/graph/build",
        files={"file": ("test.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
        data={"pid_id": "test-pid"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pid_id"] == "test-pid"
    assert body["node_count"] >= 0
    assert body["edge_count"] >= 0
    assert "equipment_count" in body
    assert "instrument_count" in body


@pytest.mark.asyncio
async def test_build_graph_default_pid_id(client: AsyncClient) -> None:
    """POST /api/graph/build uses filename as pid_id when not provided."""
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/graph/build",
        files={"file": ("my-diagram.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pid_id"] == "my-diagram"


@pytest.mark.asyncio
async def test_build_graph_empty_file(client: AsyncClient) -> None:
    """POST /api/graph/build rejects empty files."""
    resp = await client.post(
        "/api/graph/build",
        files={"file": ("empty.drawio", b"", "application/xml")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_condensed_graph(client: AsyncClient) -> None:
    """GET /api/graph/{pid_id} returns the condensed graph."""
    resp = await client.get("/api/graph/test-pid")
    assert resp.status_code == 200
    body = resp.json()
    assert "nodes" in body
    assert "edges" in body
    assert len(body["nodes"]) >= 1
    # Check node structure
    node = body["nodes"][0]
    assert "id" in node
    assert "tag" in node
    assert "type" in node
    assert "label" in node


@pytest.mark.asyncio
async def test_get_detailed_graph(client: AsyncClient) -> None:
    """GET /api/graph/{pid_id}/detail returns the detailed graph."""
    resp = await client.get("/api/graph/test-pid/detail")
    assert resp.status_code == 200
    body = resp.json()
    assert "nodes" in body
    assert "edges" in body
    assert len(body["nodes"]) >= 1


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """GET /api/health returns ok status."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
