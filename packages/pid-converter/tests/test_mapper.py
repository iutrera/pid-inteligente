"""Tests for the DEXPI mapper (produces pyDEXPI DexpiModel)."""

from __future__ import annotations

from pydexpi.dexpi_classes.dexpiModel import DexpiModel
from pydexpi.dexpi_classes.equipment import Equipment

from pid_converter.mapper import map_to_dexpi
from pid_converter.mapper.dexpi_mapper import (
    get_equipment,
    get_instruments,
    get_nozzles,
    get_piping_segments,
)
from pid_converter.models import PidModel


class TestMapToDexpi:
    """Mapping the parsed example P&ID to a pyDEXPI DexpiModel."""

    def test_returns_dexpi_model(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        assert isinstance(dexpi, DexpiModel)

    def test_has_conceptual_model(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        assert dexpi.conceptualModel is not None

    def test_equipment_mapped(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        equipment = get_equipment(dexpi)
        assert len(equipment) >= 3
        tags = {eq.tagName for eq in equipment}
        assert "T-101" in tags
        assert "P-101" in tags
        assert "HE-101" in tags

    def test_equipment_attributes(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        equipment = get_equipment(dexpi)
        tank = next(
            (eq for eq in equipment if eq.tagName == "T-101"), None
        )
        assert tank is not None
        # pyDEXPI stores custom attributes as CustomAttribute objects
        attr_dict = {ca.attributeName: ca.value for ca in tank.customAttributes}
        assert "design_pressure" in attr_dict
        assert attr_dict["design_pressure"] == "5 barg"

    def test_equipment_is_pydexpi_type(self, parsed_model: PidModel) -> None:
        """Equipment instances should be pyDEXPI Equipment subclasses."""
        dexpi = map_to_dexpi(parsed_model)
        equipment = get_equipment(dexpi)
        for eq in equipment:
            assert isinstance(eq, Equipment)

    def test_nozzles_mapped(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        nozzles = get_nozzles(dexpi)
        assert len(nozzles) >= 4

    def test_nozzle_ownership(self, parsed_model: PidModel) -> None:
        """Nozzles should be assigned to their nearest equipment (via eq.nozzles)."""
        dexpi = map_to_dexpi(parsed_model)
        equipment = get_equipment(dexpi)
        # T-101 (id=10) should have at least 2 nozzles
        tank = next((eq for eq in equipment if eq.id == "10"), None)
        assert tank is not None
        assert len(tank.nozzles) >= 2

    def test_piping_segments_mapped(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        segments = get_piping_segments(dexpi)
        assert len(segments) >= 4
        line_numbers = {s.segmentNumber for s in segments}
        assert "PL-101" in line_numbers

    def test_instruments_mapped(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        instruments = get_instruments(dexpi)
        assert len(instruments) >= 4

    def test_instrument_attributes(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        instruments = get_instruments(dexpi)
        # Find the TemperatureTransmitter by checking measured_variable
        tt = next(
            (
                i
                for i in instruments
                if i.processInstrumentationFunctionCategory == "Temperature"
                and i.processInstrumentationFunctions == "Transmitter"
            ),
            None,
        )
        assert tt is not None

    def test_piping_network_systems(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        cm = dexpi.conceptualModel
        assert cm is not None
        assert len(cm.pipingNetworkSystems) >= 1

    def test_instrumentation_loops(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        cm = dexpi.conceptualModel
        assert cm is not None
        assert len(cm.instrumentationLoopFunctions) >= 1
