"""Pipeline integration tests -- verify the Python packages work together
without requiring any running services (no API, no Neo4j).

These tests exercise:
  pid-converter  (parse, map, serialize, import, validate)
  pid-knowledge-graph  (build_graph, condense_graph, enrich_labels)
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from pid_converter.parser import parse_drawio
from pid_converter.mapper import map_to_dexpi
from pid_converter.serializer import serialize_to_proteus
from pid_converter.importer import import_dexpi
from pid_converter.validator import validate_pid
from pid_converter.models import DexpiCategory

from pid_knowledge_graph import (
    build_graph,
    build_graph_from_drawio,
    condense_graph,
    enrich_labels,
)
from pid_knowledge_graph.models import NodeType, RelType


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParser:
    """Verify the mxGraph parser extracts nodes and edges correctly."""

    def test_parser_extracts_nodes(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        assert len(model.nodes) >= 10, (
            f"Expected at least 10 nodes, got {len(model.nodes)}"
        )

    def test_parser_extracts_edges(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        assert len(model.edges) >= 3, (
            f"Expected at least 3 edges (process lines + signal lines), got {len(model.edges)}"
        )

    def test_parser_identifies_equipment(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        equipment = model.equipment()
        tags = {e.tag_number for e in equipment}
        assert "T-101" in tags
        assert "P-101" in tags
        assert "HE-101" in tags

    def test_parser_identifies_instruments(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        instruments = model.instruments()
        tags = {i.tag_number for i in instruments}
        assert "TT-101" in tags
        assert "TIC-101" in tags

    def test_parser_identifies_nozzles(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        nozzles = model.nozzles()
        assert len(nozzles) >= 2


# ---------------------------------------------------------------------------
# Converter roundtrip tests
# ---------------------------------------------------------------------------


class TestConverterRoundtrip:
    """Verify drawio -> dexpi -> drawio preserves principal equipment."""

    def test_roundtrip_preserves_equipment(self, drawio_file: Path) -> None:
        # Step 1: drawio -> PidModel -> DexpiModel -> Proteus XML
        pid_model = parse_drawio(drawio_file)
        dexpi_model = map_to_dexpi(pid_model)
        proteus_xml = serialize_to_proteus(dexpi_model)

        # Verify DEXPI XML is valid
        assert "PlantModel" in proteus_xml
        assert "Equipment" in proteus_xml

        # Step 2: Proteus XML -> drawio XML
        drawio_xml = import_dexpi(proteus_xml)
        assert "mxfile" in drawio_xml.lower()

        # Step 3: Re-parse the roundtripped drawio
        roundtrip_model = parse_drawio(drawio_xml)
        roundtrip_equipment = roundtrip_model.equipment()

        # The three major equipment items should survive the roundtrip
        roundtrip_tags = {e.tag_number for e in roundtrip_equipment}
        assert "T-101" in roundtrip_tags, (
            f"T-101 missing after roundtrip; got tags: {roundtrip_tags}"
        )
        assert "P-101" in roundtrip_tags, (
            f"P-101 missing after roundtrip; got tags: {roundtrip_tags}"
        )
        assert "HE-101" in roundtrip_tags, (
            f"HE-101 missing after roundtrip; got tags: {roundtrip_tags}"
        )

    def test_dexpi_xml_has_instrumentation(self, drawio_file: Path) -> None:
        """Verify that the DEXPI XML includes instrumentation elements."""
        pid_model = parse_drawio(drawio_file)
        dexpi_model = map_to_dexpi(pid_model)
        proteus_xml = serialize_to_proteus(dexpi_model)
        assert "InstrumentationLoopFunction" in proteus_xml
        assert "InstrumentComponent" in proteus_xml

    def test_dexpi_xml_has_piping(self, drawio_file: Path) -> None:
        """Verify that the DEXPI XML includes piping network elements."""
        pid_model = parse_drawio(drawio_file)
        dexpi_model = map_to_dexpi(pid_model)
        proteus_xml = serialize_to_proteus(dexpi_model)
        assert "PipingNetworkSystem" in proteus_xml
        assert "PipingNetworkSegment" in proteus_xml


# ---------------------------------------------------------------------------
# Knowledge graph builder tests
# ---------------------------------------------------------------------------


class TestGraphBuilder:
    """Verify graph construction from the drawio file."""

    def test_build_produces_graph(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() > 0
        assert graph.number_of_edges() > 0

    def test_graph_has_equipment(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        equipment_nodes = [
            n for n, d in graph.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        ]
        assert len(equipment_nodes) >= 3, (
            f"Expected at least 3 equipment nodes, got {len(equipment_nodes)}"
        )

    def test_graph_has_instruments(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        instrument_nodes = [
            n for n, d in graph.nodes(data=True)
            if d.get("node_type") == NodeType.INSTRUMENT.value
        ]
        assert len(instrument_nodes) >= 3, (
            f"Expected at least 3 instrument nodes, got {len(instrument_nodes)}"
        )

    def test_graph_has_flow_edges(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        flow_edges = [
            (u, v) for u, v, d in graph.edges(data=True)
            if d.get("rel_type") == RelType.SEND_TO.value
        ]
        assert len(flow_edges) >= 1, "Expected at least one SEND_TO edge"

    def test_graph_from_dexpi_model(self, drawio_file: Path) -> None:
        """Build graph via the DexpiModel path (preferred)."""
        pid_model = parse_drawio(drawio_file)
        dexpi_model = map_to_dexpi(pid_model)
        graph = build_graph(dexpi_model, pid_id="test-simple")
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() > 0


# ---------------------------------------------------------------------------
# Condensation tests
# ---------------------------------------------------------------------------


class TestCondensation:
    """Verify that condensation simplifies the graph."""

    def test_condensed_has_fewer_nodes(self, drawio_file: Path) -> None:
        detailed = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        condensed = condense_graph(detailed)

        assert condensed.number_of_nodes() < detailed.number_of_nodes(), (
            f"Condensed ({condensed.number_of_nodes()} nodes) should have "
            f"fewer nodes than detailed ({detailed.number_of_nodes()} nodes)"
        )

    def test_condensed_has_flow_edges(self, drawio_file: Path) -> None:
        detailed = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        condensed = condense_graph(detailed)

        flow_edges = [
            (u, v) for u, v, d in condensed.edges(data=True)
            if d.get("rel_type") == RelType.FLOW.value
        ]
        assert len(flow_edges) > 0, "Condensed graph should have FLOW edges"

    def test_condensed_nodes_are_equipment(self, drawio_file: Path) -> None:
        detailed = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        condensed = condense_graph(detailed)

        for _node_id, data in condensed.nodes(data=True):
            ntype = data.get("node_type", "")
            # Condensed graph should contain only equipment
            # (plus possibly instrument nodes for control annotations)
            assert ntype in (
                NodeType.EQUIPMENT.value,
                NodeType.INSTRUMENT.value,
            ), f"Unexpected node type in condensed graph: {ntype}"


# ---------------------------------------------------------------------------
# Semantic labels tests
# ---------------------------------------------------------------------------


class TestSemanticLabels:
    """Verify that semantic enrichment adds labels to all nodes."""

    def test_enriched_nodes_have_labels(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        enrich_labels(graph)

        for node_id, data in graph.nodes(data=True):
            label = data.get("label", "")
            assert label, (
                f"Node {node_id} (type={data.get('node_type')}) has no label after enrichment"
            )

    def test_enriched_edges_have_labels(self, drawio_file: Path) -> None:
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        enrich_labels(graph)

        for u, v, data in graph.edges(data=True):
            label = data.get("label", "")
            assert label, (
                f"Edge {u}->{v} (type={data.get('rel_type')}) has no label after enrichment"
            )

    def test_enriched_condensed_graph(self, drawio_file: Path) -> None:
        """Enrichment also works on condensed graphs."""
        detailed = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        condensed = condense_graph(detailed)
        enrich_labels(condensed)

        for node_id, data in condensed.nodes(data=True):
            assert data.get("label"), (
                f"Condensed node {node_id} has no label"
            )

    def test_equipment_labels_are_descriptive(self, drawio_file: Path) -> None:
        """Equipment labels should include the class name and tag."""
        graph = build_graph_from_drawio(drawio_file, pid_id="test-simple")
        enrich_labels(graph)

        equipment_nodes = [
            (n, d) for n, d in graph.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        ]
        for _node_id, data in equipment_nodes:
            label = data.get("label", "")
            tag = data.get("tag_number", "")
            if tag:
                assert tag in label, (
                    f"Equipment label '{label}' does not contain tag '{tag}'"
                )


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


class TestValidatorPipeline:
    """Verify validator catches known issues in test data."""

    def test_validate_returns_list(self, drawio_file: Path) -> None:
        model = parse_drawio(drawio_file)
        errors = validate_pid(model)
        assert isinstance(errors, list)

    def test_validate_detects_missing_tag(self) -> None:
        """A minimal model with equipment lacking tag_number should error."""
        from pid_converter.models import PidModel, PidNode, Position

        model = PidModel(
            nodes=[
                PidNode(
                    id="eq1",
                    dexpi_class="CentrifugalPump",
                    dexpi_component_class="CHBP",
                    category=DexpiCategory.EQUIPMENT,
                    tag_number="",
                    position=Position(x=0, y=0, width=60, height=60),
                ),
            ],
            edges=[],
        )
        errors = validate_pid(model)
        error_types = [e.error_type for e in errors]
        assert "missing_tag" in error_types
