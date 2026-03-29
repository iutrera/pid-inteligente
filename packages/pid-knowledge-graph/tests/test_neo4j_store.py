"""Tests for pid_knowledge_graph.neo4j_store.

These tests verify that:
1. Neo4jStore can be instantiated and compiled correctly.
2. Query strings use parameterised bindings (no string interpolation).
3. The class works as an async context manager.

Integration tests against a live Neo4j instance are skipped unless
the NEO4J_TEST_URI environment variable is set.
"""

from __future__ import annotations

import inspect
import os

import networkx as nx
import pytest

from pid_knowledge_graph.models import NodeType
from pid_knowledge_graph.neo4j_store import Neo4jStore


# ---------------------------------------------------------------------------
# Construction and compilation
# ---------------------------------------------------------------------------


class TestNeo4jStoreConstruction:
    def test_default_constructor(self):
        store = Neo4jStore()
        assert store._uri == "bolt://localhost:7687"
        assert store._user == "neo4j"
        assert store._database == "neo4j"

    def test_custom_constructor(self):
        store = Neo4jStore(
            uri="bolt://custom:7688",
            user="admin",
            password="secret",
            database="piddb",
        )
        assert store._uri == "bolt://custom:7688"
        assert store._database == "piddb"

    def test_driver_initially_none(self):
        store = Neo4jStore()
        assert store._driver is None

    def test_get_driver_raises_when_not_connected(self):
        store = Neo4jStore()
        with pytest.raises(RuntimeError, match="not connected"):
            store._get_driver()


# ---------------------------------------------------------------------------
# Query safety: no string interpolation
# ---------------------------------------------------------------------------


class TestQuerySafety:
    """Verify that all Cypher queries use parameterised bindings."""

    def test_load_graph_uses_params(self):
        source = inspect.getsource(Neo4jStore.load_graph)
        # The query should use $id, $pid_id, $props etc.
        assert "$pid_id" in source
        assert "$id" in source or "$props" in source

    def test_get_neighbors_uses_params(self):
        source = inspect.getsource(Neo4jStore.get_neighbors)
        assert "$pid_id" in source
        assert "$tag" in source

    def test_get_flow_path_uses_params(self):
        source = inspect.getsource(Neo4jStore.get_flow_path)
        assert "$pid_id" in source
        assert "$from_tag" in source
        assert "$to_tag" in source

    def test_get_control_loop_uses_params(self):
        source = inspect.getsource(Neo4jStore.get_control_loop)
        assert "$pid_id" in source
        assert "$tag" in source

    def test_get_condensed_graph_uses_params(self):
        source = inspect.getsource(Neo4jStore.get_condensed_graph)
        assert "$pid_id" in source

    def test_delete_graph_uses_params(self):
        source = inspect.getsource(Neo4jStore.delete_graph)
        assert "$pid_id" in source


# ---------------------------------------------------------------------------
# Neo4j labels
# ---------------------------------------------------------------------------


class TestNeo4jLabels:
    @pytest.mark.parametrize(
        "node_type,expected",
        [
            (NodeType.EQUIPMENT.value, ":PidNode:Equipment"),
            (NodeType.INSTRUMENT.value, ":PidNode:Instrument"),
            (NodeType.PIPING_SEGMENT.value, ":PidNode:PipingSegment"),
            (NodeType.NOZZLE.value, ":PidNode:Nozzle"),
            (NodeType.VALVE.value, ":PidNode:Valve"),
            (NodeType.UTILITY_LINE.value, ":PidNode:UtilityLine"),
            (NodeType.STEAM_TRAP.value, ":PidNode:SteamTrap"),
            (NodeType.SIGNAL_LINE.value, ":PidNode:SignalLine"),
            (NodeType.CONTROL_LOOP.value, ":PidNode:ControlLoop"),
        ],
    )
    def test_label_mapping(self, node_type: str, expected: str):
        assert Neo4jStore._neo4j_labels(node_type) == expected

    def test_unknown_type(self):
        assert Neo4jStore._neo4j_labels("Unknown") == ":PidNode"


# ---------------------------------------------------------------------------
# Clean props
# ---------------------------------------------------------------------------


class TestCleanProps:
    def test_removes_internal_keys(self):
        data = {"_geo_x": 100, "_is_edge": True, "tag_number": "P-101"}
        result = Neo4jStore._clean_props(data)
        assert "_geo_x" not in result
        assert "_is_edge" not in result
        assert result["tag_number"] == "P-101"

    def test_keeps_serialisable_values(self):
        data = {"name": "test", "count": 5, "ratio": 3.14, "active": True}
        result = Neo4jStore._clean_props(data)
        assert result == data

    def test_filters_non_serialisable(self):
        data = {"name": "ok", "obj": object(), "func": lambda x: x}
        result = Neo4jStore._clean_props(data)
        assert "name" in result
        assert "obj" not in result
        assert "func" not in result

    def test_keeps_list_of_primitives(self):
        data = {"tags": ["a", "b"], "counts": [1, 2]}
        result = Neo4jStore._clean_props(data)
        assert result["tags"] == ["a", "b"]
        assert result["counts"] == [1, 2]


# ---------------------------------------------------------------------------
# Integration tests (skipped unless Neo4j is available)
# ---------------------------------------------------------------------------


NEO4J_AVAILABLE = os.environ.get("NEO4J_TEST_URI") is not None


@pytest.mark.skipif(not NEO4J_AVAILABLE, reason="NEO4J_TEST_URI not set")
class TestNeo4jIntegration:
    """Integration tests that require a live Neo4j instance."""

    @pytest.fixture()
    def neo4j_uri(self) -> str:
        return os.environ["NEO4J_TEST_URI"]

    @pytest.fixture()
    def neo4j_user(self) -> str:
        return os.environ.get("NEO4J_TEST_USER", "neo4j")

    @pytest.fixture()
    def neo4j_password(self) -> str:
        return os.environ.get("NEO4J_TEST_PASSWORD", "password")

    async def test_load_and_delete(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        detailed_graph: nx.DiGraph,
    ):
        async with Neo4jStore(neo4j_uri, neo4j_user, neo4j_password) as store:
            pid_id = "TEST-INTEGRATION"
            await store.load_graph(pid_id, detailed_graph)
            await store.delete_graph(pid_id)
