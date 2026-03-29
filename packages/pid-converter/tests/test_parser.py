"""Tests for the mxGraph parser."""

from __future__ import annotations

from pathlib import Path

from pid_converter.models import DexpiCategory, PidModel
from pid_converter.parser import parse_drawio


class TestParseDrawio:
    """Parsing the example P&ID fixture."""

    def test_returns_pid_model(self, parsed_model: PidModel) -> None:
        assert isinstance(parsed_model, PidModel)

    def test_extracts_nodes(self, parsed_model: PidModel) -> None:
        """The example has multiple objects with dexpi_class attributes."""
        assert len(parsed_model.nodes) > 0

    def test_extracts_edges(self, parsed_model: PidModel) -> None:
        """The example has process lines and signal lines (edges)."""
        assert len(parsed_model.edges) > 0

    def test_equipment_detected(self, parsed_model: PidModel) -> None:
        equip = parsed_model.equipment()
        # T-101 (VerticalVessel), P-101 (CentrifugalPump), HE-101 (ShellTubeHeatExchanger)
        assert len(equip) >= 3
        tags = {n.tag_number for n in equip}
        assert "T-101" in tags
        assert "P-101" in tags
        assert "HE-101" in tags

    def test_nozzles_detected(self, parsed_model: PidModel) -> None:
        nozzles = parsed_model.nozzles()
        # N1, N2 on T-101; S1, S2 on HE-101
        assert len(nozzles) >= 4

    def test_instruments_detected(self, parsed_model: PidModel) -> None:
        instruments = parsed_model.instruments()
        # TT-101, TIC-101, LI-101, PI-101
        assert len(instruments) >= 4

    def test_piping_component_detected(self, parsed_model: PidModel) -> None:
        """Control valve TCV-101 and steam trap ST-101 should be piping components."""
        comps = parsed_model.nodes_by_category(DexpiCategory.PIPING_COMPONENT)
        assert len(comps) >= 2
        classes = {c.dexpi_class for c in comps}
        assert "ControlValve" in classes
        assert "SteamTrap" in classes

    def test_process_line_edges(self, parsed_model: PidModel) -> None:
        """PL-101 through PL-104 should be parsed as edges."""
        process_edges = [
            e for e in parsed_model.edges
            if e.dexpi_class == "ProcessLine"
        ]
        assert len(process_edges) >= 4

    def test_signal_line_edges(self, parsed_model: PidModel) -> None:
        signal_edges = [
            e for e in parsed_model.edges
            if e.dexpi_class == "SignalLine"
        ]
        assert len(signal_edges) >= 3

    def test_custom_attributes_extracted(self, parsed_model: PidModel) -> None:
        """T-101 should carry design_pressure, design_temperature, etc."""
        tank = next(
            (n for n in parsed_model.nodes if n.tag_number == "T-101"),
            None,
        )
        assert tank is not None
        assert tank.attributes.get("design_pressure") == "5 barg"
        assert tank.attributes.get("design_temperature") == "80 degC"

    def test_position_extracted(self, parsed_model: PidModel) -> None:
        """Nodes should have position data from mxGeometry."""
        tank = next(
            (n for n in parsed_model.nodes if n.tag_number == "T-101"),
            None,
        )
        assert tank is not None
        assert tank.position.x == 100
        assert tank.position.y == 200
        assert tank.position.width == 80
        assert tank.position.height == 150

    def test_metadata_extracted(self, parsed_model: PidModel) -> None:
        assert parsed_model.metadata.get("diagram_name") == "P&ID Example - Heat Exchange Loop"


class TestParseFromString:
    """Parsing from raw XML string."""

    def test_minimal_xml(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mxfile>
          <diagram id="d1" name="Test">
            <mxGraphModel>
              <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>
                <object label="V-100" dexpi_class="VerticalVessel"
                        dexpi_component_class="VTVS" tag_number="V-100" id="10">
                  <mxCell style="shape=rectangle;" vertex="1" parent="1">
                    <mxGeometry x="50" y="50" width="40" height="80" as="geometry"/>
                  </mxCell>
                </object>
              </root>
            </mxGraphModel>
          </diagram>
        </mxfile>
        """
        model = parse_drawio(xml)
        assert len(model.nodes) == 1
        assert model.nodes[0].tag_number == "V-100"
        assert model.nodes[0].dexpi_class == "VerticalVessel"
        assert model.nodes[0].category == DexpiCategory.EQUIPMENT
