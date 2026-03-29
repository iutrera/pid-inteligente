"""Map a parsed PidModel to a pyDEXPI ``DexpiModel``.

For every node in the :class:`~pid_converter.models.PidModel` the mapper
creates the corresponding pyDEXPI object based on the node's
:attr:`~pid_converter.models.PidNode.category`.

The mapper also resolves nozzle ownership (via proximity) and wires piping
segments to their source/target nozzles when the topology has been resolved.

The output is a canonical ``pydexpi.dexpi_classes.dexpiModel.DexpiModel``
instance.
"""

from __future__ import annotations

import math
from typing import Any

from pydexpi.dexpi_classes.dexpiModel import DexpiModel
from pydexpi.dexpi_classes.equipment import (
    CentrifugalPump,
    Compressor,
    Equipment,
    Fan,
    Filter,
    Furnace,
    HeatExchanger,
    Nozzle,
    PlateHeatExchanger,
    PressureVessel,
    ProcessColumn,
    Pump,
    Tank,
    TubularHeatExchanger,
    Vessel,
)
from pydexpi.dexpi_classes.instrumentation import (
    InstrumentationLoopFunction,
    ProcessInstrumentationFunction,
    SignalLineFunction,
)
from pydexpi.dexpi_classes.piping import (
    BallValve,
    ButterflyValve,
    CheckValve,
    GateValve,
    GlobeValve,
    OperatedValve,
    PipingComponent,
    PipingNetworkSegment,
    PipingNetworkSystem,
    SteamTrap,
    Strainer,
)
from pydexpi.dexpi_classes.pydantic_classes import (
    ConceptualModel,
    CustomAttribute,
)

from pid_converter.models import (
    DexpiCategory,
    PidModel,
    PidNode,
    Position,
)
from pid_converter.topology import assign_nozzles_to_equipment, resolve_topology


# ---------------------------------------------------------------------------
# dexpi_class name -> pyDEXPI Equipment class mapping
# ---------------------------------------------------------------------------

_EQUIPMENT_CLASS_MAP: dict[str, type] = {
    "CentrifugalPump": CentrifugalPump,
    "PositiveDisplacementPump": Pump,
    "VerticalVessel": Vessel,
    "HorizontalVessel": Vessel,
    "ShellTubeHeatExchanger": TubularHeatExchanger,
    "TubularHeatExchanger": TubularHeatExchanger,
    "PlateHeatExchanger": PlateHeatExchanger,
    "HeatExchanger": HeatExchanger,
    "ProcessColumn": ProcessColumn,
    "Compressor": Compressor,
    "Filter": Filter,
    "Fan": Fan,
    "Furnace": Furnace,
    "PressureVessel": PressureVessel,
    "Tank": Tank,
    "Vessel": Vessel,
    "Pump": Pump,
}

# ---------------------------------------------------------------------------
# dexpi_class name -> pyDEXPI PipingComponent class mapping
# ---------------------------------------------------------------------------

_PIPING_COMPONENT_CLASS_MAP: dict[str, type] = {
    "ControlValve": OperatedValve,
    "GateValve": GateValve,
    "GlobeValve": GlobeValve,
    "BallValve": BallValve,
    "ButterflyValve": ButterflyValve,
    "CheckValve": CheckValve,
    "OperatedValve": OperatedValve,
    "SteamTrap": SteamTrap,
    "Strainer": Strainer,
}


# ---------------------------------------------------------------------------
# Attribute extraction helpers
# ---------------------------------------------------------------------------

def _get(node: PidNode, key: str, default: str = "") -> str:
    """Read an attribute from *node.attributes*, falling back to *default*."""
    return node.attributes.get(key, default)


def _make_custom_attrs(
    attrs: dict[str, str],
    exclude: set[str] | None = None,
) -> list[CustomAttribute]:
    """Convert a dict of string attributes to a list of pyDEXPI CustomAttribute."""
    exclude = exclude or set()
    result: list[CustomAttribute] = []
    for key, value in sorted(attrs.items()):
        if key not in exclude:
            result.append(CustomAttribute(attributeName=key, value=value))
    return result


# ---------------------------------------------------------------------------
# Individual mappers
# ---------------------------------------------------------------------------

def _map_equipment(node: PidNode) -> Equipment:
    """Create a pyDEXPI Equipment subclass instance from a PidNode."""
    cls = _EQUIPMENT_CLASS_MAP.get(node.dexpi_class, Equipment)
    tag = node.tag_number or _get(node, "tag_number")
    custom_attrs = _make_custom_attrs(
        node.attributes,
        exclude={"tag_number", "dexpi_class", "dexpi_component_class"},
    )
    # Preserve original dexpi_class and component_class for roundtrip fidelity
    if node.dexpi_class:
        custom_attrs.append(
            CustomAttribute(
                attributeName="_dexpi_class", value=node.dexpi_class,
            )
        )
    if node.dexpi_component_class:
        custom_attrs.append(
            CustomAttribute(
                attributeName="_dexpi_component_class",
                value=node.dexpi_component_class,
            )
        )
    return cls(
        id=node.id,
        tagName=tag,
        customAttributes=custom_attrs,
    )


def _map_nozzle(node: PidNode) -> Nozzle:
    """Create a pyDEXPI Nozzle from a PidNode."""
    custom_attrs = _make_custom_attrs(
        node.attributes,
        exclude={"nozzle_id", "dexpi_class", "dexpi_component_class"},
    )
    return Nozzle(
        id=node.id,
        subTagName=_get(node, "nozzle_id"),
        customAttributes=custom_attrs,
    )


def _map_piping_component(node: PidNode) -> PipingComponent:
    """Create a pyDEXPI PipingComponent subclass instance from a PidNode."""
    cls = _PIPING_COMPONENT_CLASS_MAP.get(node.dexpi_class, PipingComponent)
    custom_attrs = _make_custom_attrs(
        node.attributes,
        exclude={"tag_number", "dexpi_class", "dexpi_component_class"},
    )
    kwargs: dict[str, Any] = {
        "id": node.id,
        "customAttributes": custom_attrs,
    }
    # OperatedValve, CheckValve and PipeFitting subclasses have pipingComponentName
    if "pipingComponentName" in cls.model_fields:
        kwargs["pipingComponentName"] = node.tag_number or _get(node, "tag_number")
    return cls(**kwargs)


def _map_instrument(node: PidNode) -> ProcessInstrumentationFunction:
    """Create a pyDEXPI ProcessInstrumentationFunction from a PidNode."""
    tag = node.tag_number or _get(node, "tag_number")
    custom_attrs = _make_custom_attrs(
        node.attributes,
        exclude={
            "tag_number", "dexpi_class", "dexpi_component_class",
            "measured_variable", "function", "signal_type",
        },
    )
    # Preserve original dexpi_class and component_class for roundtrip fidelity
    if node.dexpi_class:
        custom_attrs.append(
            CustomAttribute(
                attributeName="_dexpi_class", value=node.dexpi_class,
            )
        )
    if node.dexpi_component_class:
        custom_attrs.append(
            CustomAttribute(
                attributeName="_dexpi_component_class",
                value=node.dexpi_component_class,
            )
        )
    return ProcessInstrumentationFunction(
        id=node.id,
        processInstrumentationFunctionNumber=tag,
        processInstrumentationFunctionCategory=_get(node, "measured_variable"),
        processInstrumentationFunctions=_get(node, "function"),
        typicalInformation=_get(node, "signal_type"),
        customAttributes=custom_attrs,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def map_to_dexpi(model: PidModel) -> DexpiModel:
    """Convert a :class:`PidModel` into a pyDEXPI :class:`DexpiModel`.

    This function **also** resolves topology (if not already done) and assigns
    nozzles to their parent equipment.
    """
    # Ensure topology is resolved
    if not model.connections:
        resolve_topology(model)

    nozzle_owners = assign_nozzles_to_equipment(model)

    # Collect pyDEXPI objects
    equipment_list: list[Equipment] = []
    nozzle_map: dict[str, Nozzle] = {}  # node_id -> Nozzle
    piping_components: list[PipingComponent] = []
    instrument_list: list[ProcessInstrumentationFunction] = []

    # --- Map nodes ---
    for node in model.nodes:
        cat = node.category
        if cat == DexpiCategory.EQUIPMENT:
            eq = _map_equipment(node)
            equipment_list.append(eq)
        elif cat == DexpiCategory.NOZZLE:
            noz = _map_nozzle(node)
            nozzle_map[node.id] = noz
        elif cat == DexpiCategory.PIPING_COMPONENT:
            piping_components.append(_map_piping_component(node))
        elif cat == DexpiCategory.INSTRUMENT:
            instrument_list.append(_map_instrument(node))

    # --- Assign nozzles to equipment ---
    for noz_node_id, eq_node_id in nozzle_owners.items():
        noz = nozzle_map.get(noz_node_id)
        if noz is None:
            continue
        for eq in equipment_list:
            if eq.id == eq_node_id:
                eq.nozzles.append(noz)
                break

    # --- Map edges that represent piping segments ---
    piping_segments: list[PipingNetworkSegment] = []

    # Index instruments by their original PidNode id for signal line wiring
    instrument_by_id: dict[str, ProcessInstrumentationFunction] = {
        inst.id: inst for inst in instrument_list
    }

    for edge in model.edges:
        if edge.dexpi_class in {"ProcessLine", "UtilityLine", "PipingNetworkSegment"}:
            seg = PipingNetworkSegment(
                id=edge.id,
                fluidCode=edge.attributes.get("fluid_code"),
                insulationType=edge.attributes.get("insulation"),
                nominalDiameterRepresentation=edge.attributes.get(
                    "nominal_diameter"
                ),
                segmentNumber=edge.attributes.get("line_number"),
                pipingClassCode=edge.attributes.get("material_spec"),
                customAttributes=_make_custom_attrs(
                    edge.attributes,
                    exclude={
                        "line_number", "nominal_diameter", "fluid_code",
                        "material_spec", "insulation",
                        "dexpi_class", "dexpi_component_class",
                    },
                ),
            )
            piping_segments.append(seg)
        elif edge.dexpi_class == "SignalLine":
            sl = SignalLineFunction(
                id=edge.id,
                customAttributes=_make_custom_attrs(
                    edge.attributes,
                    exclude={"signal_type", "dexpi_class", "dexpi_component_class"},
                ),
            )
            # Attach signal line to source instrument if known
            source_inst = instrument_by_id.get(edge.source_id)
            if source_inst is not None:
                source_inst.signalConveyingFunctions.append(sl)
            else:
                # Fallback: attach to target instrument
                target_inst = instrument_by_id.get(edge.target_id)
                if target_inst is not None:
                    target_inst.signalConveyingFunctions.append(sl)

    # --- Build PipingNetworkSystem ---
    piping_systems: list[PipingNetworkSystem] = []
    if piping_segments or piping_components:
        # Place all piping components as items within segments (simplified)
        pns = PipingNetworkSystem(
            id="PipingSystem-1",
            segments=piping_segments,
        )
        piping_systems.append(pns)

    # --- Build InstrumentationLoopFunctions ---
    # Group instruments by measured_variable (heuristic for control loops)
    loops: dict[str, list[ProcessInstrumentationFunction]] = {}
    for inst in instrument_list:
        key = inst.processInstrumentationFunctionCategory or "General"
        loops.setdefault(key, []).append(inst)

    instrumentation_loops: list[InstrumentationLoopFunction] = []
    for loop_name, instruments in loops.items():
        ilf = InstrumentationLoopFunction(
            id=f"Loop-{loop_name}",
            instrumentationLoopFunctionNumber=loop_name,
            processInstrumentationFunctions=instruments,
        )
        instrumentation_loops.append(ilf)

    # --- Assemble the ConceptualModel ---
    conceptual = ConceptualModel(
        taggedPlantItems=equipment_list,
        pipingNetworkSystems=piping_systems,
        instrumentationLoopFunctions=instrumentation_loops,
    )

    return DexpiModel(
        conceptualModel=conceptual,
        originatingSystemName="pid-converter",
    )


# ---------------------------------------------------------------------------
# Convenience accessors for backward compatibility
# ---------------------------------------------------------------------------
# The CLI and serializer need quick access to equipment, nozzles, etc. from a
# DexpiModel.  These helpers extract flat lists from the pyDEXPI hierarchy.

def get_equipment(dexpi: DexpiModel) -> list[Equipment]:
    """Return all Equipment instances (taggedPlantItems) from the model."""
    cm = dexpi.conceptualModel
    if cm is None:
        return []
    return [
        item for item in cm.taggedPlantItems
        if isinstance(item, Equipment)
    ]


def get_nozzles(dexpi: DexpiModel) -> list[Nozzle]:
    """Return all Nozzle instances across all Equipment."""
    result: list[Nozzle] = []
    for eq in get_equipment(dexpi):
        result.extend(eq.nozzles)
    return result


def get_piping_segments(dexpi: DexpiModel) -> list[PipingNetworkSegment]:
    """Return all PipingNetworkSegment instances from the model."""
    cm = dexpi.conceptualModel
    if cm is None:
        return []
    result: list[PipingNetworkSegment] = []
    for pns in cm.pipingNetworkSystems:
        result.extend(pns.segments)
    return result


def get_piping_components(dexpi: DexpiModel) -> list[PipingComponent]:
    """Return all PipingComponent instances (from segment items)."""
    result: list[PipingComponent] = []
    for seg in get_piping_segments(dexpi):
        for item in seg.items:
            if isinstance(item, PipingComponent):
                result.append(item)
    return result


def get_instruments(
    dexpi: DexpiModel,
) -> list[ProcessInstrumentationFunction]:
    """Return all ProcessInstrumentationFunction instances from the model."""
    cm = dexpi.conceptualModel
    if cm is None:
        return []
    result: list[ProcessInstrumentationFunction] = []
    for ilf in cm.instrumentationLoopFunctions:
        result.extend(ilf.processInstrumentationFunctions)
    return result


def get_signal_lines(dexpi: DexpiModel) -> list[SignalLineFunction]:
    """Return all SignalLineFunction instances from the model."""
    result: list[SignalLineFunction] = []
    for inst in get_instruments(dexpi):
        for scf in inst.signalConveyingFunctions:
            if isinstance(scf, SignalLineFunction):
                result.append(scf)
    return result


def _find_nozzle_for_point(
    point: Position | None,
    nozzles: list[Nozzle],
    nozzle_positions: dict[str, Position],
    max_dist: float = 40.0,
) -> str:
    """Return the ID of the nozzle closest to *point*, or ``""``."""
    if point is None:
        return ""
    best_id = ""
    best_d = max_dist
    for noz in nozzles:
        pos = nozzle_positions.get(noz.id)
        if pos is None:
            continue
        cx = pos.x + pos.width / 2
        cy = pos.y + pos.height / 2
        d = math.hypot(point.x - cx, point.y - cy)
        if d < best_d:
            best_d = d
            best_id = noz.id
    return best_id
