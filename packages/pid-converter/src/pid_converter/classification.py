"""Classification of dexpi_class values into high-level DEXPI categories.

This mapping is used by the parser to assign a ``DexpiCategory`` to every
``<object>`` extracted from a Draw.io file.  It also drives the mapper when
deciding which DEXPI output model to instantiate.
"""

from __future__ import annotations

from pid_converter.models import DexpiCategory

# Equipment classes
EQUIPMENT_CLASSES: frozenset[str] = frozenset({
    "CentrifugalPump",
    "PositiveDisplacementPump",
    "HorizontalVessel",
    "VerticalVessel",
    "ShellTubeHeatExchanger",
    "PlateHeatExchanger",
    "AirCooledHeatExchanger",
    "Column",
    "TrayColumn",
    "PackedColumn",
    "Reactor",
    "StirredReactor",
    "Compressor",
    "CentrifugalCompressor",
    "ReciprocatingCompressor",
    "Filter",
    "BagFilter",
    "CartridgeFilter",
    "Tank",
    "StorageTank",
    "Agitator",
    "Blower",
    "Ejector",
    "Mixer",
    "Cyclone",
    "Centrifuge",
    "Dryer",
    "Evaporator",
    "Crystallizer",
    "Boiler",
    "Furnace",
    "Conveyor",
})

# Piping component classes (valves, fittings, etc.)
PIPING_COMPONENT_CLASSES: frozenset[str] = frozenset({
    "GateValve",
    "GlobeValve",
    "BallValve",
    "ButterflyValve",
    "CheckValve",
    "ControlValve",
    "SafetyValve",
    "ReliefValve",
    "Reducer",
    "Tee",
    "Elbow",
    "Flange",
    "BlindFlange",
    "SpectacleBlind",
    "Strainer",
    "SteamTrap",
    "PlugValve",
    "NeedleValve",
    "DiaphragmValve",
    "PinchValve",
    "ThreeWayValve",
    "FourWayValve",
    "BreatherValve",
    "SamplingValve",
    "Orifice",
    "RuptureDisc",
})

# Piping network segments / lines
PIPING_SEGMENT_CLASSES: frozenset[str] = frozenset({
    "ProcessLine",
    "UtilityLine",
    "PipingNetworkSegment",
})

# Nozzle
NOZZLE_CLASSES: frozenset[str] = frozenset({
    "Nozzle",
})

# Instrumentation classes
INSTRUMENT_CLASSES: frozenset[str] = frozenset({
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
    "AnalysisTransmitter",
    "AnalysisIndicator",
    "Transmitter",
    "Controller",
    "Indicator",
    "Alarm",
    "Recorder",
    "Switch",
})

# Signal line classes
SIGNAL_LINE_CLASSES: frozenset[str] = frozenset({
    "SignalLine",
})


def classify(dexpi_class: str) -> DexpiCategory:
    """Return the high-level DEXPI category for a given *dexpi_class* string."""
    if dexpi_class in EQUIPMENT_CLASSES:
        return DexpiCategory.EQUIPMENT
    if dexpi_class in PIPING_COMPONENT_CLASSES:
        return DexpiCategory.PIPING_COMPONENT
    if dexpi_class in PIPING_SEGMENT_CLASSES:
        return DexpiCategory.PIPING_NETWORK_SEGMENT
    if dexpi_class in NOZZLE_CLASSES:
        return DexpiCategory.NOZZLE
    if dexpi_class in INSTRUMENT_CLASSES:
        return DexpiCategory.INSTRUMENT
    if dexpi_class in SIGNAL_LINE_CLASSES:
        return DexpiCategory.SIGNAL_LINE
    return DexpiCategory.UNKNOWN
