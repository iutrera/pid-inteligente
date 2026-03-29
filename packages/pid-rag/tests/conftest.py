"""Shared fixtures for pid-rag tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import networkx as nx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from pid_rag.config import Settings


# ---------------------------------------------------------------------------
# Sample Draw.io XML for testing
# ---------------------------------------------------------------------------

SAMPLE_DRAWIO_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="test">
  <diagram id="test-diagram" name="Test P&amp;ID">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" value="Process" parent="0"/>
        <mxCell id="2" value="Instrumentation" parent="0"/>
        <object label="P-101" dexpi_class="CentrifugalPump" dexpi_component_class="PUMP" tag_number="P-101" id="node-1">
          <mxCell style="shape=ellipse;" vertex="1" parent="1">
            <mxGeometry x="100" y="100" width="60" height="60" as="geometry"/>
          </mxCell>
        </object>
        <object label="E-101" dexpi_class="ShellTubeHeatExchanger" dexpi_component_class="HX" tag_number="E-101" id="node-2">
          <mxCell style="shape=rectangle;" vertex="1" parent="1">
            <mxGeometry x="300" y="100" width="80" height="80" as="geometry"/>
          </mxCell>
        </object>
        <object label="" dexpi_class="ProcessLine" dexpi_component_class="PRCL" line_number="PL-001" id="edge-1">
          <mxCell style="endArrow=block;" edge="1" source="node-1" target="node-2" parent="1">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>
        <object label="TIC-101" dexpi_class="TemperatureController" dexpi_component_class="TIC" tag_number="TIC-101" measured_variable="Temperature" function="Controller" id="inst-1">
          <mxCell style="shape=ellipse;" vertex="1" parent="2">
            <mxGeometry x="200" y="50" width="40" height="40" as="geometry"/>
          </mxCell>
        </object>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


# ---------------------------------------------------------------------------
# Mock Neo4jStore
# ---------------------------------------------------------------------------

def _make_sample_graph() -> nx.DiGraph:
    """Create a small sample graph for testing."""
    g = nx.DiGraph()
    g.graph["pid_id"] = "test-pid"
    g.graph["condensed"] = True
    g.add_node("node-1", pid_id="test-pid", tag_number="P-101",
               dexpi_class="CentrifugalPump", node_type="Equipment",
               label="Centrifugal Pump P-101")
    g.add_node("node-2", pid_id="test-pid", tag_number="E-101",
               dexpi_class="ShellTubeHeatExchanger", node_type="Equipment",
               label="Shell & Tube Heat Exchanger E-101")
    g.add_edge("node-1", "node-2", rel_type="FLOW",
               label="Process flow: P-101 -> E-101")
    return g


class MockNeo4jStore:
    """In-memory mock of Neo4jStore for testing."""

    def __init__(self) -> None:
        self._graphs: dict[str, nx.DiGraph] = {}
        self._database = "neo4j"

    async def __aenter__(self) -> "MockNeo4jStore":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def close(self) -> None:
        pass

    def _get_driver(self) -> Any:
        raise RuntimeError("MockNeo4jStore does not have a real driver")

    async def load_graph(self, pid_id: str, graph: nx.DiGraph) -> None:
        self._graphs[pid_id] = graph

    async def get_condensed_graph(self, pid_id: str) -> nx.DiGraph:
        if pid_id in self._graphs:
            return self._graphs[pid_id]
        return _make_sample_graph()

    async def get_neighbors(
        self, pid_id: str, node_tag: str, depth: int = 1,
    ) -> nx.DiGraph:
        g = _make_sample_graph()
        # Filter to just the requested tag if it exists
        for nid, data in list(g.nodes(data=True)):
            if data.get("tag_number") == node_tag:
                return g
        return g

    async def get_detailed_graph(self, pid_id: str) -> nx.DiGraph:
        if pid_id in self._graphs:
            return self._graphs[pid_id]
        return _make_sample_graph()

    async def get_control_loop(
        self, pid_id: str, instrument_tag: str,
    ) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_node("inst-1", pid_id=pid_id, tag_number="TIC-101",
                    dexpi_class="TemperatureController", node_type="Instrument",
                    label="TIC-101 (Temperature Indicating Controller)")
        return g


@pytest.fixture()
def mock_neo4j_store() -> MockNeo4jStore:
    return MockNeo4jStore()


# ---------------------------------------------------------------------------
# Test app and client
# ---------------------------------------------------------------------------

@pytest.fixture()
def settings() -> Settings:
    return Settings(
        ANTHROPIC_API_KEY="test-key-for-testing",
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="test",
        CORS_ORIGINS="http://localhost:3000",
    )


@pytest.fixture()
def test_app(settings: Settings, mock_neo4j_store: MockNeo4jStore) -> FastAPI:
    """Create a FastAPI app with mocked dependencies."""
    from pid_rag.api.routes import chat, convert, graph, validate

    app = FastAPI()
    # Inject state directly (ASGITransport does not trigger lifespan)
    app.state.settings = settings
    app.state.neo4j_store = mock_neo4j_store

    app.include_router(convert.router)
    app.include_router(graph.router)
    app.include_router(chat.router)
    app.include_router(validate.router)

    from pydantic import BaseModel

    class HealthResponse(BaseModel):
        status: str
        version: str

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", version="0.1.0")

    return app


@pytest.fixture()
async def client(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async HTTP client for the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
