"""Tests for the topology resolver."""

from __future__ import annotations

from pid_converter.models import (
    DexpiCategory,
    PidEdge,
    PidModel,
    PidNode,
    Position,
)
from pid_converter.topology import assign_nozzles_to_equipment, resolve_topology


class TestResolveTopology:
    """Topology resolution on the example P&ID."""

    def test_connections_resolved(self, parsed_model: PidModel) -> None:
        connections = resolve_topology(parsed_model)
        assert len(connections) > 0

    def test_connections_stored_in_model(self, parsed_model: PidModel) -> None:
        resolve_topology(parsed_model)
        assert len(parsed_model.connections) > 0

    def test_process_lines_connect_equipment(self, parsed_model: PidModel) -> None:
        """Process lines should resolve to connections near equipment/nozzles."""
        resolve_topology(parsed_model)
        # At least some connections should reference known node IDs
        node_ids = {n.id for n in parsed_model.nodes}
        for conn in parsed_model.connections:
            if conn.from_node_id:
                assert conn.from_node_id in node_ids or conn.from_node_id == ""
            if conn.to_node_id:
                assert conn.to_node_id in node_ids or conn.to_node_id == ""


class TestLinearTopology:
    """Test linear A -> B -> C topology resolution."""

    def test_simple_chain(self) -> None:
        """Three nodes connected by two edges should yield two connections."""
        model = PidModel(
            nodes=[
                PidNode(
                    id="A", label="A", dexpi_class="VerticalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=0, y=0, width=40, height=40),
                ),
                PidNode(
                    id="B", label="B", dexpi_class="CentrifugalPump",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=200, y=0, width=40, height=40),
                ),
                PidNode(
                    id="C", label="C", dexpi_class="ShellTubeHeatExchanger",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=400, y=0, width=40, height=40),
                ),
            ],
            edges=[
                PidEdge(
                    id="e1",
                    dexpi_class="ProcessLine",
                    source_point=Position(x=40, y=20),
                    target_point=Position(x=200, y=20),
                ),
                PidEdge(
                    id="e2",
                    dexpi_class="ProcessLine",
                    source_point=Position(x=240, y=20),
                    target_point=Position(x=400, y=20),
                ),
            ],
        )
        connections = resolve_topology(model)
        assert len(connections) == 2
        assert connections[0].from_node_id == "A"
        assert connections[0].to_node_id == "B"
        assert connections[1].from_node_id == "B"
        assert connections[1].to_node_id == "C"

    def test_branching(self) -> None:
        """One node feeding two downstream nodes."""
        model = PidModel(
            nodes=[
                PidNode(
                    id="A", label="A", dexpi_class="VerticalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=0, y=100, width=40, height=40),
                ),
                PidNode(
                    id="B", label="B", dexpi_class="CentrifugalPump",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=200, y=0, width=40, height=40),
                ),
                PidNode(
                    id="C", label="C", dexpi_class="ShellTubeHeatExchanger",
                    category=DexpiCategory.EQUIPMENT,
                    position=Position(x=200, y=200, width=40, height=40),
                ),
            ],
            edges=[
                PidEdge(
                    id="e1",
                    dexpi_class="ProcessLine",
                    source_point=Position(x=40, y=110),
                    target_point=Position(x=200, y=20),
                ),
                PidEdge(
                    id="e2",
                    dexpi_class="ProcessLine",
                    source_point=Position(x=40, y=130),
                    target_point=Position(x=200, y=220),
                ),
            ],
        )
        connections = resolve_topology(model)
        assert len(connections) == 2
        from_ids = {c.from_node_id for c in connections}
        to_ids = {c.to_node_id for c in connections}
        assert from_ids == {"A"}
        assert to_ids == {"B", "C"}


class TestNozzleAssignment:
    """Test nozzle-to-equipment proximity assignment."""

    def test_nozzles_assigned(self, parsed_model: PidModel) -> None:
        mapping = assign_nozzles_to_equipment(parsed_model)
        assert len(mapping) > 0

    def test_nozzle_n1_belongs_to_tank(self, parsed_model: PidModel) -> None:
        """Nozzle N1 (id=11) is physically on T-101 (id=10)."""
        mapping = assign_nozzles_to_equipment(parsed_model)
        assert mapping.get("11") == "10"

    def test_nozzle_s1_belongs_to_he(self, parsed_model: PidModel) -> None:
        """Nozzle S1 (id=72) is physically on HE-101 (id=70)."""
        mapping = assign_nozzles_to_equipment(parsed_model)
        assert mapping.get("72") == "70"
