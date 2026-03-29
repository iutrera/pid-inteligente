"""Tests for Pydantic models in pid_knowledge_graph.models."""

from __future__ import annotations

import pytest

from pid_knowledge_graph.models import (
    ControlLoop,
    Equipment,
    Instrument,
    NodeType,
    Nozzle,
    PidNode,
    PipingSegment,
    RelType,
    Relationship,
    SignalLine,
    SteamTrap,
    UtilityLine,
    Valve,
    classify_dexpi_class,
)


# ---------------------------------------------------------------------------
# PidNode base
# ---------------------------------------------------------------------------

class TestPidNode:
    def test_create_minimal(self):
        node = PidNode(id="1")
        assert node.id == "1"
        assert node.pid_id == ""
        assert node.tag_number == ""
        assert node.dexpi_class == ""
        assert node.label == ""
        assert node.extra == {}

    def test_create_full(self):
        node = PidNode(
            id="10",
            pid_id="PID-001",
            tag_number="T-101",
            dexpi_class="VerticalVessel",
            dexpi_component_class="VTVS",
            label="Feed Tank T-101",
            node_type=NodeType.EQUIPMENT,
            extra={"design_pressure": "5 barg"},
        )
        assert node.tag_number == "T-101"
        assert node.node_type == NodeType.EQUIPMENT
        assert node.extra["design_pressure"] == "5 barg"

    def test_id_required(self):
        with pytest.raises((TypeError, ValueError)):
            PidNode()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------

class TestEquipment:
    def test_default_node_type(self):
        eq = Equipment(id="10", tag_number="P-101")
        assert eq.node_type == NodeType.EQUIPMENT

    def test_all_fields(self):
        eq = Equipment(
            id="30",
            pid_id="PID-001",
            tag_number="P-101",
            dexpi_class="CentrifugalPump",
            design_pressure="10 barg",
            design_temperature="80 degC",
            capacity="50 m3/h",
            power="15 kW",
            material="SS316L",
        )
        assert eq.design_pressure == "10 barg"
        assert eq.power == "15 kW"
        assert eq.material == "SS316L"


# ---------------------------------------------------------------------------
# Instrument
# ---------------------------------------------------------------------------

class TestInstrument:
    def test_default_node_type(self):
        inst = Instrument(id="200", tag_number="TT-101")
        assert inst.node_type == NodeType.INSTRUMENT

    def test_all_fields(self):
        inst = Instrument(
            id="200",
            tag_number="TT-101",
            measured_variable="Temperature",
            function="Transmitter",
            signal_type="4-20mA",
        )
        assert inst.measured_variable == "Temperature"
        assert inst.signal_type == "4-20mA"


# ---------------------------------------------------------------------------
# PipingSegment
# ---------------------------------------------------------------------------

class TestPipingSegment:
    def test_default_node_type(self):
        seg = PipingSegment(id="20")
        assert seg.node_type == NodeType.PIPING_SEGMENT

    def test_all_fields(self):
        seg = PipingSegment(
            id="20",
            line_number="PL-101",
            nominal_diameter="3 inch",
            fluid_code="PROCESS",
            material_spec="SS316L",
            insulation="None",
        )
        assert seg.line_number == "PL-101"
        assert seg.fluid_code == "PROCESS"


# ---------------------------------------------------------------------------
# Nozzle
# ---------------------------------------------------------------------------

class TestNozzle:
    def test_default_node_type(self):
        nz = Nozzle(id="11")
        assert nz.node_type == NodeType.NOZZLE

    def test_all_fields(self):
        nz = Nozzle(
            id="11",
            nozzle_id="N1",
            size="3 inch",
            rating="150#",
            service="Outlet to P-101",
        )
        assert nz.nozzle_id == "N1"
        assert nz.service == "Outlet to P-101"


# ---------------------------------------------------------------------------
# Valve
# ---------------------------------------------------------------------------

class TestValve:
    def test_default_node_type(self):
        v = Valve(id="50")
        assert v.node_type == NodeType.VALVE

    def test_all_fields(self):
        v = Valve(
            id="50",
            tag_number="TCV-101",
            size="3 inch",
            rating="150#",
            valve_type="Control",
        )
        assert v.valve_type == "Control"


# ---------------------------------------------------------------------------
# UtilityLine
# ---------------------------------------------------------------------------

class TestUtilityLine:
    def test_default_node_type(self):
        ul = UtilityLine(id="90")
        assert ul.node_type == NodeType.UTILITY_LINE

    def test_all_fields(self):
        ul = UtilityLine(
            id="90",
            line_number="UT-201",
            nominal_diameter="2 inch",
            fluid_code="STEAM-LP",
            material_spec="CS",
            insulation="Yes - 25mm",
        )
        assert ul.fluid_code == "STEAM-LP"


# ---------------------------------------------------------------------------
# SteamTrap
# ---------------------------------------------------------------------------

class TestSteamTrap:
    def test_default_node_type(self):
        st = SteamTrap(id="94")
        assert st.node_type == NodeType.STEAM_TRAP


# ---------------------------------------------------------------------------
# SignalLine
# ---------------------------------------------------------------------------

class TestSignalLine:
    def test_default_node_type(self):
        sl = SignalLine(id="210")
        assert sl.node_type == NodeType.SIGNAL_LINE

    def test_all_fields(self):
        sl = SignalLine(
            id="210",
            signal_type="4-20mA",
            instrument_tag="TT-101 to TIC-101",
        )
        assert sl.signal_type == "4-20mA"


# ---------------------------------------------------------------------------
# ControlLoop
# ---------------------------------------------------------------------------

class TestControlLoop:
    def test_default_node_type(self):
        cl = ControlLoop(id="CL1")
        assert cl.node_type == NodeType.CONTROL_LOOP

    def test_all_fields(self):
        cl = ControlLoop(
            id="CL1",
            sensor_tag="TT-101",
            controller_tag="TIC-101",
            final_element_tag="TCV-101",
            controlled_variable="Temperature",
        )
        assert cl.controller_tag == "TIC-101"


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------

class TestRelationship:
    def test_create_minimal(self):
        rel = Relationship(source_id="10", target_id="30", rel_type=RelType.SEND_TO)
        assert rel.source_id == "10"
        assert rel.target_id == "30"
        assert rel.rel_type == RelType.SEND_TO
        assert rel.properties == {}

    def test_with_properties(self):
        rel = Relationship(
            source_id="10",
            target_id="30",
            rel_type=RelType.FLOW,
            properties={"line_number": "PL-101", "diameter": "3 inch"},
        )
        assert rel.properties["line_number"] == "PL-101"


# ---------------------------------------------------------------------------
# classify_dexpi_class
# ---------------------------------------------------------------------------

class TestClassifyDexpiClass:
    @pytest.mark.parametrize(
        "dexpi_class,expected",
        [
            ("CentrifugalPump", NodeType.EQUIPMENT),
            ("VerticalVessel", NodeType.EQUIPMENT),
            ("ShellTubeHeatExchanger", NodeType.EQUIPMENT),
            ("TemperatureTransmitter", NodeType.INSTRUMENT),
            ("PressureIndicator", NodeType.INSTRUMENT),
            ("ProcessLine", NodeType.PIPING_SEGMENT),
            ("Nozzle", NodeType.NOZZLE),
            ("ControlValve", NodeType.VALVE),
            ("SteamTrap", NodeType.STEAM_TRAP),
            ("SignalLine", NodeType.SIGNAL_LINE),
            ("UtilityLine", NodeType.UTILITY_LINE),
        ],
    )
    def test_known_classes(self, dexpi_class: str, expected: NodeType):
        assert classify_dexpi_class(dexpi_class) == expected

    def test_instrument_by_component_code(self):
        assert classify_dexpi_class("SomeUnknown", "TIC") == NodeType.INSTRUMENT

    def test_unknown_class_defaults_to_equipment(self):
        assert classify_dexpi_class("CompletelyUnknown") == NodeType.EQUIPMENT
