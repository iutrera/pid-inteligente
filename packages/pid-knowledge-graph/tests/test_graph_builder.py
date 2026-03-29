"""Tests for pid_knowledge_graph.graph_builder -- both drawio and dexpi paths."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from pid_knowledge_graph.graph_builder import (
    build_graph,
    build_graph_from_dexpi,
    build_graph_from_drawio,
)
from pid_knowledge_graph.models import NodeType, RelType


# ===========================================================================
# PATH B: build_graph_from_drawio (original .drawio parser)
# ===========================================================================


class TestBuildGraphFromDrawio:
    """Verify that build_graph_from_drawio produces the expected graph."""

    def test_returns_digraph(self, detailed_graph: nx.DiGraph):
        assert isinstance(detailed_graph, nx.DiGraph)

    def test_pid_id_stored(self, detailed_graph: nx.DiGraph):
        assert detailed_graph.graph["pid_id"] == "PID-101-001"

    def test_source_tag(self, detailed_graph: nx.DiGraph):
        assert detailed_graph.graph["source"] == "drawio"

    def test_has_nodes(self, detailed_graph: nx.DiGraph):
        # The example has: 3 equipment, 4 nozzles, 5 process lines, 1 control valve,
        # 2 utility lines, 1 steam trap, 4 instruments, 4 signal lines = ~24 objects
        assert len(detailed_graph.nodes) > 10

    def test_has_edges(self, detailed_graph: nx.DiGraph):
        assert len(detailed_graph.edges) > 0


# ---------------------------------------------------------------------------
# Equipment nodes (drawio)
# ---------------------------------------------------------------------------


class TestEquipmentNodes:
    """Verify that major equipment items are parsed correctly."""

    def _equipment_nodes(self, g: nx.DiGraph) -> dict[str, dict]:
        return {
            n: d for n, d in g.nodes(data=True) if d.get("node_type") == NodeType.EQUIPMENT.value
        }

    def test_three_equipment_items(self, detailed_graph: nx.DiGraph):
        eq = self._equipment_nodes(detailed_graph)
        tags = {d["tag_number"] for d in eq.values()}
        assert "T-101" in tags, "Tank T-101 missing"
        assert "P-101" in tags, "Pump P-101 missing"
        assert "HE-101" in tags, "Heat Exchanger HE-101 missing"

    def test_tank_attributes(self, detailed_graph: nx.DiGraph):
        eq = self._equipment_nodes(detailed_graph)
        tank = next(d for d in eq.values() if d["tag_number"] == "T-101")
        assert tank["dexpi_class"] == "VerticalVessel"
        assert tank["design_pressure"] == "5 barg"
        assert tank["material"] == "SS316L"

    def test_pump_attributes(self, detailed_graph: nx.DiGraph):
        eq = self._equipment_nodes(detailed_graph)
        pump = next(d for d in eq.values() if d["tag_number"] == "P-101")
        assert pump["dexpi_class"] == "CentrifugalPump"
        assert pump["power"] == "15 kW"

    def test_he_attributes(self, detailed_graph: nx.DiGraph):
        eq = self._equipment_nodes(detailed_graph)
        he = next(d for d in eq.values() if d["tag_number"] == "HE-101")
        assert he["dexpi_class"] == "ShellTubeHeatExchanger"
        assert he["capacity"] == "2000 kW"


# ---------------------------------------------------------------------------
# Instrument nodes (drawio)
# ---------------------------------------------------------------------------


class TestInstrumentNodes:
    def _instrument_nodes(self, g: nx.DiGraph) -> dict[str, dict]:
        return {
            n: d for n, d in g.nodes(data=True) if d.get("node_type") == NodeType.INSTRUMENT.value
        }

    def test_instruments_present(self, detailed_graph: nx.DiGraph):
        inst = self._instrument_nodes(detailed_graph)
        tags = {d["tag_number"] for d in inst.values()}
        # We expect TT-101, TIC-101, LI-101, PI-101
        assert len(tags) >= 3, f"Expected at least 3 instruments, got {tags}"

    def test_transmitter_attributes(self, detailed_graph: nx.DiGraph):
        inst = self._instrument_nodes(detailed_graph)
        tt = [d for d in inst.values() if d.get("dexpi_class") == "TemperatureTransmitter"]
        assert len(tt) >= 1
        assert tt[0]["measured_variable"] == "Temperature"
        assert tt[0]["signal_type"] == "4-20mA"


# ---------------------------------------------------------------------------
# Nozzle nodes (drawio)
# ---------------------------------------------------------------------------


class TestNozzleNodes:
    def test_nozzles_present(self, detailed_graph: nx.DiGraph):
        nozzles = [
            d for _, d in detailed_graph.nodes(data=True)
            if d.get("node_type") == NodeType.NOZZLE.value
        ]
        assert len(nozzles) >= 4, f"Expected at least 4 nozzles, got {len(nozzles)}"

    def test_nozzle_belongs_to_equipment(self, detailed_graph: nx.DiGraph):
        """At least some nozzles should have BELONGS_TO edges to equipment."""
        belongs_to_edges = [
            (u, v) for u, v, d in detailed_graph.edges(data=True)
            if d.get("rel_type") == RelType.BELONGS_TO.value
        ]
        assert len(belongs_to_edges) >= 1, "No BELONGS_TO edges found for nozzles"


# ---------------------------------------------------------------------------
# Piping / edge connections (drawio)
# ---------------------------------------------------------------------------


class TestPipingAndEdges:
    def test_process_lines_exist(self, detailed_graph: nx.DiGraph):
        piping_nodes = [
            d for _, d in detailed_graph.nodes(data=True)
            if d.get("node_type") == NodeType.PIPING_SEGMENT.value
        ]
        # 5 process lines in the example
        assert len(piping_nodes) >= 4

    def test_send_to_edges_created(self, detailed_graph: nx.DiGraph):
        send_to = [
            (u, v) for u, v, d in detailed_graph.edges(data=True)
            if d.get("rel_type") == RelType.SEND_TO.value
        ]
        assert len(send_to) >= 1, "No SEND_TO edges found"

    def test_valve_node_present(self, detailed_graph: nx.DiGraph):
        valves = [
            d for _, d in detailed_graph.nodes(data=True)
            if d.get("node_type") == NodeType.VALVE.value
        ]
        assert len(valves) >= 1
        tags = {d["tag_number"] for d in valves}
        assert "TCV-101" in tags


# ---------------------------------------------------------------------------
# Signal lines (drawio)
# ---------------------------------------------------------------------------


class TestSignalLines:
    def test_signal_edges_created(self, detailed_graph: nx.DiGraph):
        signal_edges = [
            (u, v, d) for u, v, d in detailed_graph.edges(data=True)
            if d.get("rel_type") == RelType.SIGNAL.value
        ]
        assert len(signal_edges) >= 1, "No SIGNAL edges found"


# ---------------------------------------------------------------------------
# Edge case: non-existent file
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_nonexistent_file_raises(self):
        with pytest.raises(OSError):
            build_graph_from_drawio(Path("/nonexistent/file.drawio"))

    def test_nonexistent_file_via_build_graph(self):
        with pytest.raises(OSError):
            build_graph(Path("/nonexistent/file.drawio"))


# ===========================================================================
# PATH A: build_graph_from_dexpi (pyDEXPI model)
# ===========================================================================


class TestBuildGraphFromDexpi:
    """Verify that build_graph_from_dexpi produces a valid graph."""

    @pytest.fixture()
    def dexpi_graph(self, sample_dexpi_model) -> nx.DiGraph:
        return build_graph_from_dexpi(sample_dexpi_model, pid_id="TEST-DEXPI")

    def test_returns_digraph(self, dexpi_graph: nx.DiGraph):
        assert isinstance(dexpi_graph, nx.DiGraph)

    def test_pid_id_stored(self, dexpi_graph: nx.DiGraph):
        assert dexpi_graph.graph["pid_id"] == "TEST-DEXPI"

    def test_source_tag(self, dexpi_graph: nx.DiGraph):
        assert dexpi_graph.graph["source"] == "pydexpi"

    def test_has_nodes(self, dexpi_graph: nx.DiGraph):
        assert len(dexpi_graph.nodes) >= 2, (
            f"Expected at least 2 nodes (vessel + pump), got {len(dexpi_graph.nodes)}"
        )

    def test_equipment_node_types(self, dexpi_graph: nx.DiGraph):
        """Equipment nodes should have node_type == Equipment."""
        eq_nodes = [
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        ]
        assert len(eq_nodes) >= 2, f"Expected at least 2 equipment, got {len(eq_nodes)}"

    def test_vessel_tag(self, dexpi_graph: nx.DiGraph):
        tags = {
            d.get("tag_number", "")
            for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        }
        assert "V-100" in tags, f"V-100 not found in tags: {tags}"

    def test_pump_tag(self, dexpi_graph: nx.DiGraph):
        tags = {
            d.get("tag_number", "")
            for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.EQUIPMENT.value
        }
        assert "P-100" in tags, f"P-100 not found in tags: {tags}"

    def test_vessel_dexpi_class(self, dexpi_graph: nx.DiGraph):
        vessel = next(
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("tag_number") == "V-100"
        )
        assert vessel["dexpi_class"] == "Vessel"

    def test_pump_dexpi_class(self, dexpi_graph: nx.DiGraph):
        pump = next(
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("tag_number") == "P-100"
        )
        assert pump["dexpi_class"] == "CentrifugalPump"

    def test_has_edges(self, dexpi_graph: nx.DiGraph):
        """The piping connection should produce at least one edge."""
        assert len(dexpi_graph.edges) >= 1, "No edges found in dexpi graph"

    def test_piping_edge_rel_type(self, dexpi_graph: nx.DiGraph):
        """Piping connections should map to SEND_TO."""
        send_to = [
            (u, v) for u, v, d in dexpi_graph.edges(data=True)
            if d.get("rel_type") == RelType.SEND_TO.value
        ]
        assert len(send_to) >= 1, "No SEND_TO edges from piping connection"

    def test_all_nodes_have_node_type(self, dexpi_graph: nx.DiGraph):
        """Every node must have a node_type attribute."""
        for node_id, data in dexpi_graph.nodes(data=True):
            assert "node_type" in data, f"Node {node_id} missing node_type"

    def test_all_nodes_have_pid_id(self, dexpi_graph: nx.DiGraph):
        for node_id, data in dexpi_graph.nodes(data=True):
            assert data.get("pid_id") == "TEST-DEXPI"


class TestBuildGraphFromDexpiInstruments:
    """Test that instruments from DexpiModel are properly handled."""

    @pytest.fixture()
    def dexpi_graph(self, sample_dexpi_model) -> nx.DiGraph:
        return build_graph_from_dexpi(sample_dexpi_model, pid_id="TEST-INST")

    def test_instrument_present(self, dexpi_graph: nx.DiGraph):
        inst_nodes = [
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.INSTRUMENT.value
        ]
        assert len(inst_nodes) >= 1, "No instrument nodes found"

    def test_instrument_tag(self, dexpi_graph: nx.DiGraph):
        inst = next(
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.INSTRUMENT.value
        )
        assert inst["tag_number"] == "TIC-101"

    def test_instrument_measured_variable(self, dexpi_graph: nx.DiGraph):
        inst = next(
            d for _, d in dexpi_graph.nodes(data=True)
            if d.get("node_type") == NodeType.INSTRUMENT.value
        )
        assert inst["measured_variable"] == "Temperature"


# ===========================================================================
# Unified build_graph dispatcher
# ===========================================================================


class TestBuildGraphDispatcher:
    """Verify that build_graph correctly dispatches to the right builder."""

    def test_dispatches_path_to_drawio(self, example_drawio_path: Path):
        g = build_graph(example_drawio_path, pid_id="DISPATCH-DRAWIO")
        assert g.graph["pid_id"] == "DISPATCH-DRAWIO"
        assert g.graph["source"] == "drawio"
        assert len(g.nodes) > 10

    def test_dispatches_str_to_drawio(self, example_drawio_path: Path):
        g = build_graph(str(example_drawio_path), pid_id="DISPATCH-STR")
        assert g.graph["source"] == "drawio"
        assert len(g.nodes) > 10

    def test_dispatches_dexpi_model(self, sample_dexpi_model):
        g = build_graph(sample_dexpi_model, pid_id="DISPATCH-DEXPI")
        assert g.graph["pid_id"] == "DISPATCH-DEXPI"
        assert g.graph["source"] == "pydexpi"
        assert len(g.nodes) >= 2
