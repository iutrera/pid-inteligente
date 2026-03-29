"""Pydantic v2 models for the P&ID Knowledge Graph nodes and relationships."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NodeType(str, Enum):
    """High-level node classification."""

    EQUIPMENT = "Equipment"
    INSTRUMENT = "Instrument"
    PIPING_SEGMENT = "PipingSegment"
    NOZZLE = "Nozzle"
    CONTROL_LOOP = "ControlLoop"
    VALVE = "Valve"
    UTILITY_LINE = "UtilityLine"
    STEAM_TRAP = "SteamTrap"
    SIGNAL_LINE = "SignalLine"


class RelType(str, Enum):
    """Relationship types used in the Knowledge Graph."""

    SEND_TO = "SEND_TO"
    HAS_NOZZLE = "HAS_NOZZLE"
    CONTROLS = "CONTROLS"
    BELONGS_TO = "BELONGS_TO"
    MEASURED_BY = "MEASURED_BY"
    SIGNAL = "SIGNAL"
    FEEDS = "FEEDS"
    FLOW = "FLOW"


# ---------------------------------------------------------------------------
# Node models
# ---------------------------------------------------------------------------

class PidNode(BaseModel):
    """Base model for every node in the P&ID Knowledge Graph."""

    id: str = Field(..., description="Unique node ID (from the drawio <object> id)")
    pid_id: str = Field(
        default="", description="Identifier of the P&ID drawing this node belongs to"
    )
    tag_number: str = Field(default="", description="ISA/plant tag (e.g. P-101, TIC-101)")
    dexpi_class: str = Field(default="", description="DEXPI class name (e.g. CentrifugalPump)")
    dexpi_component_class: str = Field(default="", description="DEXPI component class code")
    label: str = Field(default="", description="Human-readable semantic label for the LLM")
    node_type: NodeType = Field(default=NodeType.EQUIPMENT, description="High-level classification")
    extra: dict[str, Any] = Field(
        default_factory=dict, description="All other DEXPI/drawio attributes"
    )


class Equipment(PidNode):
    """Major process equipment (vessels, pumps, exchangers, etc.)."""

    node_type: NodeType = NodeType.EQUIPMENT
    design_pressure: str = Field(default="")
    design_temperature: str = Field(default="")
    capacity: str = Field(default="")
    power: str = Field(default="")
    material: str = Field(default="")


class Instrument(PidNode):
    """Instrumentation device (transmitter, controller, indicator, etc.)."""

    node_type: NodeType = NodeType.INSTRUMENT
    measured_variable: str = Field(default="")
    function: str = Field(default="")
    signal_type: str = Field(default="")


class PipingSegment(PidNode):
    """A section of piping between two connection points."""

    node_type: NodeType = NodeType.PIPING_SEGMENT
    line_number: str = Field(default="")
    nominal_diameter: str = Field(default="")
    fluid_code: str = Field(default="")
    material_spec: str = Field(default="")
    insulation: str = Field(default="")


class Nozzle(PidNode):
    """A nozzle on a piece of equipment."""

    node_type: NodeType = NodeType.NOZZLE
    nozzle_id: str = Field(default="")
    size: str = Field(default="")
    rating: str = Field(default="")
    service: str = Field(default="")


class Valve(PidNode):
    """A valve (control valve, gate valve, etc.)."""

    node_type: NodeType = NodeType.VALVE
    size: str = Field(default="")
    rating: str = Field(default="")
    valve_type: str = Field(default="")


class UtilityLine(PidNode):
    """A utility piping line (steam, condensate, cooling water, etc.)."""

    node_type: NodeType = NodeType.UTILITY_LINE
    line_number: str = Field(default="")
    nominal_diameter: str = Field(default="")
    fluid_code: str = Field(default="")
    material_spec: str = Field(default="")
    insulation: str = Field(default="")


class SteamTrap(PidNode):
    """A steam trap on a condensate line."""

    node_type: NodeType = NodeType.STEAM_TRAP
    size: str = Field(default="")
    rating: str = Field(default="")


class SignalLine(PidNode):
    """A signal/instrument line connecting instruments."""

    node_type: NodeType = NodeType.SIGNAL_LINE
    signal_type: str = Field(default="")
    instrument_tag: str = Field(default="")


class ControlLoop(PidNode):
    """A control loop grouping sensor, controller, and final element."""

    node_type: NodeType = NodeType.CONTROL_LOOP
    sensor_tag: str = Field(default="")
    controller_tag: str = Field(default="")
    final_element_tag: str = Field(default="")
    controlled_variable: str = Field(default="")


# ---------------------------------------------------------------------------
# Relationship model
# ---------------------------------------------------------------------------

class Relationship(BaseModel):
    """A directed relationship between two nodes in the Knowledge Graph."""

    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    rel_type: RelType = Field(..., description="Relationship type")
    properties: dict[str, Any] = Field(default_factory=dict, description="Extra relationship data")


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

# DEXPI classes that map to Equipment
EQUIPMENT_CLASSES: set[str] = {
    # pyDEXPI native class names
    "Vessel",
    "Pump",
    "HeatExchanger",
    "Equipment",
    # Specific drawio / DEXPI sub-classes
    "VerticalVessel",
    "HorizontalVessel",
    "CentrifugalPump",
    "PositiveDisplacementPump",
    "EjectorPump",
    "ShellTubeHeatExchanger",
    "PlateHeatExchanger",
    "AirCooledHeatExchanger",
    "Column",
    "Reactor",
    "Compressor",
    "CentrifugalCompressor",
    "AxialCompressor",
    "Filter",
    "Tank",
    "Agitator",
    "Drum",
    "Ejector",
    "Cyclone",
    "Mixer",
    "Boiler",
    "CoolingTower",
    "Centrifuge",
    "Dryer",
    "Conveyor",
}

# DEXPI classes that map to Instrument
INSTRUMENT_CLASSES: set[str] = {
    # pyDEXPI native class names
    "ProcessInstrumentationFunction",
    "ControlledActuator",
    "Positioner",
    "SignalOffPageConnector",
    # Specific drawio / DEXPI sub-classes
    "TemperatureTransmitter",
    "PressureTransmitter",
    "FlowTransmitter",
    "LevelTransmitter",
    "TemperatureController",
    "PressureController",
    "FlowController",
    "LevelController",
    "TemperatureIndicator",
    "PressureIndicator",
    "FlowIndicator",
    "LevelIndicator",
    "TemperatureAlarm",
    "PressureAlarm",
    "FlowAlarm",
    "LevelAlarm",
}

# DEXPI component class codes for instruments
INSTRUMENT_COMPONENT_CODES: set[str] = {
    "TT", "PT", "FT", "LT",  # Transmitters
    "TIC", "PIC", "FIC", "LIC",  # Controllers
    "TI", "PI", "FI", "LI",  # Indicators
    "TAH", "PAH", "FAH", "LAH",  # Alarms
    "TAL", "PAL", "FAL", "LAL",
}

# DEXPI classes that map to PipingSegment
PIPING_CLASSES: set[str] = {
    "ProcessLine",
    "PipingNetworkSegment",
    "PipingNetworkSystem",
}

# DEXPI classes that map to Valve
VALVE_CLASSES: set[str] = {
    "ControlValve",
    "GateValve",
    "GlobeValve",
    "BallValve",
    "ButterflyValve",
    "CheckValve",
    "SafetyValve",
    "OperatedControlValve",
    "OperatedGateValve",
    "OperatedGlobeValve",
    "OperatedBallValve",
    "OperatedButterflyValve",
    "Reducer",
    "Tee",
    "Elbow",
    "Flange",
    "BlindFlange",
    "SpectacleBlind",
    "Strainer",
}


def classify_dexpi_class(dexpi_class: str, component_class: str = "") -> NodeType:
    """Return the high-level NodeType for a given DEXPI class name."""
    if dexpi_class == "Nozzle":
        return NodeType.NOZZLE
    if dexpi_class == "SteamTrap":
        return NodeType.STEAM_TRAP
    if dexpi_class == "SignalLine":
        return NodeType.SIGNAL_LINE
    if dexpi_class == "UtilityLine":
        return NodeType.UTILITY_LINE
    if dexpi_class in EQUIPMENT_CLASSES:
        return NodeType.EQUIPMENT
    if dexpi_class in INSTRUMENT_CLASSES or component_class in INSTRUMENT_COMPONENT_CODES:
        return NodeType.INSTRUMENT
    if dexpi_class in PIPING_CLASSES:
        return NodeType.PIPING_SEGMENT
    if dexpi_class in VALVE_CLASSES:
        return NodeType.VALVE
    # Fallback: treat unknown classes as equipment
    return NodeType.EQUIPMENT
