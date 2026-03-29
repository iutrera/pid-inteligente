"""Tests for pid_knowledge_graph.semantic -- semantic label enrichment."""

from __future__ import annotations

import networkx as nx
import pytest

from pid_knowledge_graph.condensation import condense_graph
from pid_knowledge_graph.models import NodeType
from pid_knowledge_graph.semantic import enrich_labels


# ---------------------------------------------------------------------------
# Detailed graph labels
# ---------------------------------------------------------------------------


class TestEnrichLabelsDetailed:
    @pytest.fixture()
    def enriched(self, detailed_graph: nx.DiGraph) -> nx.DiGraph:
        return enrich_labels(detailed_graph)

    def test_returns_same_graph(self, detailed_graph: nx.DiGraph):
        result = enrich_labels(detailed_graph)
        assert result is detailed_graph

    def test_all_nodes_have_labels(self, enriched: nx.DiGraph):
        for node_id, data in enriched.nodes(data=True):
            label = data.get("label", "")
            assert label, f"Node {node_id} has empty label"

    def test_equipment_label_format(self, enriched: nx.DiGraph):
        """Equipment labels should contain the human-readable class name and tag."""
        for _, data in enriched.nodes(data=True):
            if data.get("node_type") != NodeType.EQUIPMENT.value:
                continue
            label = data["label"]
            tag = data.get("tag_number", "")
            if tag:
                assert tag in label, f"Tag {tag} not in label '{label}'"

    def test_pump_label_has_power(self, enriched: nx.DiGraph):
        pump = next(
            d for _, d in enriched.nodes(data=True)
            if d.get("tag_number") == "P-101"
        )
        assert "15 kW" in pump["label"]

    def test_pump_label_has_design_conditions(self, enriched: nx.DiGraph):
        pump = next(
            d for _, d in enriched.nodes(data=True)
            if d.get("tag_number") == "P-101"
        )
        assert "10 barg" in pump["label"]
        assert "material" in pump["label"].lower()

    def test_instrument_label_format(self, enriched: nx.DiGraph):
        """Instrument labels should contain the tag and function description."""
        for _, data in enriched.nodes(data=True):
            if data.get("node_type") != NodeType.INSTRUMENT.value:
                continue
            label = data["label"]
            assert len(label) > 5, f"Instrument label too short: '{label}'"

    def test_nozzle_label_format(self, enriched: nx.DiGraph):
        """Nozzle labels should mention 'Nozzle'."""
        for _, data in enriched.nodes(data=True):
            if data.get("node_type") != NodeType.NOZZLE.value:
                continue
            label = data["label"]
            assert "Nozzle" in label, f"Nozzle label missing 'Nozzle': '{label}'"

    def test_piping_label_has_diameter(self, enriched: nx.DiGraph):
        for _, data in enriched.nodes(data=True):
            if data.get("node_type") != NodeType.PIPING_SEGMENT.value:
                continue
            label = data["label"]
            diameter = data.get("nominal_diameter", "")
            if diameter:
                assert diameter in label, f"Diameter '{diameter}' not in piping label '{label}'"

    def test_valve_label_format(self, enriched: nx.DiGraph):
        for _, data in enriched.nodes(data=True):
            if data.get("node_type") != NodeType.VALVE.value:
                continue
            label = data["label"]
            assert "Valve" in label or "valve" in label.lower()


# ---------------------------------------------------------------------------
# Edge labels
# ---------------------------------------------------------------------------


class TestEdgeLabels:
    @pytest.fixture()
    def enriched(self, detailed_graph: nx.DiGraph) -> nx.DiGraph:
        return enrich_labels(detailed_graph)

    def test_all_edges_have_labels(self, enriched: nx.DiGraph):
        for u, v, data in enriched.edges(data=True):
            label = data.get("label", "")
            assert label, f"Edge ({u} -> {v}) has empty label"


# ---------------------------------------------------------------------------
# Condensed graph labels
# ---------------------------------------------------------------------------


class TestEnrichLabelsCondensed:
    @pytest.fixture()
    def enriched_condensed(self, detailed_graph: nx.DiGraph) -> nx.DiGraph:
        cg = condense_graph(detailed_graph)
        return enrich_labels(cg)

    def test_condensed_labels_descriptive(self, enriched_condensed: nx.DiGraph):
        for node_id, data in enriched_condensed.nodes(data=True):
            label = data.get("label", "")
            assert len(label) > 3, f"Condensed node {node_id} label too short: '{label}'"
