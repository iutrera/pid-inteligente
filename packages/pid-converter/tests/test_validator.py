"""Tests for the P&ID validator."""

from __future__ import annotations

from pid_converter.models import (
    DexpiCategory,
    PidEdge,
    PidModel,
    PidNode,
    Position,
)
from pid_converter.topology import resolve_topology
from pid_converter.validator import validate_pid
from pid_converter.validator.pid_validator import ErrorType


class TestValidateExamplePid:
    """Run validation on the example P&ID fixture."""

    def test_returns_list(self, parsed_model: PidModel) -> None:
        resolve_topology(parsed_model)
        errors = validate_pid(parsed_model)
        assert isinstance(errors, list)


class TestMissingTags:
    """Detect equipment/instruments without tag_number."""

    def test_missing_equipment_tag(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="1", label="", dexpi_class="VerticalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    tag_number="",
                    position=Position(),
                ),
            ]
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.MISSING_TAG for e in errors)
        assert errors[0].shape_id == "1"

    def test_missing_instrument_tag(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="2", label="", dexpi_class="TemperatureTransmitter",
                    category=DexpiCategory.INSTRUMENT,
                    tag_number="",
                    position=Position(),
                ),
            ]
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.MISSING_TAG for e in errors)

    def test_valid_tag_no_error(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="1", label="T-100", dexpi_class="VerticalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    tag_number="T-100",
                    position=Position(),
                ),
            ]
        )
        errors = validate_pid(model)
        assert not any(e.error_type == ErrorType.MISSING_TAG for e in errors)


class TestMissingLineNumber:
    """Detect piping edges without line_number."""

    def test_missing_line_number(self) -> None:
        model = PidModel(
            edges=[
                PidEdge(
                    id="e1", dexpi_class="ProcessLine",
                    attributes={"line_number": ""},
                ),
            ]
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.MISSING_LINE_NUMBER for e in errors)

    def test_valid_line_number(self) -> None:
        model = PidModel(
            edges=[
                PidEdge(
                    id="e1", dexpi_class="ProcessLine",
                    attributes={"line_number": "PL-100"},
                ),
            ]
        )
        errors = validate_pid(model)
        assert not any(e.error_type == ErrorType.MISSING_LINE_NUMBER for e in errors)


class TestUnconnectedNozzles:
    """Detect nozzles not referenced by topology connections."""

    def test_orphan_nozzle(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="n1", dexpi_class="Nozzle",
                    category=DexpiCategory.NOZZLE,
                    attributes={"nozzle_id": "N1"},
                    position=Position(),
                ),
            ],
            connections=[],  # No connections reference n1
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.UNCONNECTED_NOZZLE for e in errors)


class TestOrphanInstruments:
    """Detect instruments not connected by signal lines."""

    def test_orphan_instrument(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="i1", dexpi_class="TemperatureTransmitter",
                    category=DexpiCategory.INSTRUMENT,
                    tag_number="TT-100",
                    position=Position(),
                ),
            ],
            edges=[],  # No signal lines
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.ORPHAN_INSTRUMENT for e in errors)


class TestDuplicateTags:
    """Detect duplicate tag_number across elements."""

    def test_duplicate_tag(self) -> None:
        model = PidModel(
            nodes=[
                PidNode(
                    id="1", dexpi_class="VerticalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    tag_number="T-100",
                    position=Position(),
                ),
                PidNode(
                    id="2", dexpi_class="HorizontalVessel",
                    category=DexpiCategory.EQUIPMENT,
                    tag_number="T-100",
                    position=Position(),
                ),
            ]
        )
        errors = validate_pid(model)
        assert any(e.error_type == ErrorType.DUPLICATE_TAG for e in errors)
