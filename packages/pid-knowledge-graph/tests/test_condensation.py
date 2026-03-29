"""Tests for pid_knowledge_graph.condensation."""

from __future__ import annotations

import networkx as nx
import pytest

from pid_knowledge_graph.condensation import condense_graph
from pid_knowledge_graph.models import NodeType, RelType


# ---------------------------------------------------------------------------
# Condensation produces equipment-only graph
# ---------------------------------------------------------------------------


class TestCondenseGraph:
    @pytest.fixture()
    def condensed(self, detailed_graph: nx.DiGraph) -> nx.DiGraph:
        return condense_graph(detailed_graph)

    def test_returns_digraph(self, condensed: nx.DiGraph):
        assert isinstance(condensed, nx.DiGraph)

    def test_condensed_flag(self, condensed: nx.DiGraph):
        assert condensed.graph.get("condensed") is True

    def test_only_equipment_and_controller_nodes(self, condensed: nx.DiGraph):
        """Condensed graph should have mostly equipment nodes."""
        for node_id, data in condensed.nodes(data=True):
            ntype = data.get("node_type", "")
            role = data.get("condensed_role", "")
            assert (
                ntype == NodeType.EQUIPMENT.value or role == "control_loop"
            ), f"Unexpected node {node_id} with type={ntype} in condensed graph"

    def test_equipment_nodes_present(self, condensed: nx.DiGraph):
        eq_tags = {
            d["tag_number"]
            for _, d in condensed.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        }
        # At least T-101, P-101, HE-101
        assert "T-101" in eq_tags or "P-101" in eq_tags or "HE-101" in eq_tags, (
            f"Expected major equipment in condensed graph, got tags: {eq_tags}"
        )

    def test_fewer_nodes_than_detailed(self, detailed_graph: nx.DiGraph, condensed: nx.DiGraph):
        """Condensed graph should have significantly fewer nodes."""
        assert len(condensed.nodes) < len(detailed_graph.nodes)

    def test_no_nozzles_or_piping(self, condensed: nx.DiGraph):
        """No nozzle or piping segment nodes should survive condensation."""
        for _, data in condensed.nodes(data=True):
            assert data.get("node_type") != NodeType.NOZZLE.value
            assert data.get("node_type") != NodeType.PIPING_SEGMENT.value

    def test_flow_edges_present(self, condensed: nx.DiGraph):
        """Condensed graph should have FLOW or CONTROLS edges."""
        edge_types = {d.get("rel_type", "") for _, _, d in condensed.edges(data=True)}
        assert edge_types, "No edges in condensed graph"

    def test_preserves_pid_id(self, condensed: nx.DiGraph):
        assert condensed.graph.get("pid_id") == "PID-101-001"


# ---------------------------------------------------------------------------
# Condensation of an empty graph
# ---------------------------------------------------------------------------


class TestCondenseEmpty:
    def test_empty_graph(self):
        empty = nx.DiGraph()
        empty.graph["pid_id"] = "EMPTY"
        result = condense_graph(empty)
        assert len(result.nodes) == 0
        assert result.graph.get("condensed") is True
