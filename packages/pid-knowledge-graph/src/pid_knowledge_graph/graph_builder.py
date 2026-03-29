"""Build a NetworkX DiGraph from a pyDEXPI model or a .drawio XML file.

Supports two entry points:

* **Preferred**: ``build_graph_from_dexpi(dexpi_model, pid_id)`` -- walks the
  ``DexpiModel`` object tree (equipment, piping, instrumentation) and builds
  a knowledge-graph ``DiGraph`` directly.

* **Fallback**: ``build_graph_from_drawio(drawio_path, pid_id)`` -- parses
  the mxGraph XML directly with lxml (original implementation).

The unified ``build_graph(source, pid_id)`` detects the input type and
dispatches to the appropriate builder.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

import networkx as nx
from lxml import etree

from pid_knowledge_graph.models import (
    PIPING_CLASSES,
    NodeType,
    RelType,
    classify_dexpi_class,
)

if TYPE_CHECKING:
    from typing import Any

    from pydexpi.dexpi_classes.dexpiModel import DexpiModel


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_graph(
    source: Union[Path, str, "DexpiModel"],
    pid_id: str = "",
) -> nx.DiGraph:
    """Build a typed directed graph from *source*.

    Parameters
    ----------
    source:
        Either a ``DexpiModel`` instance (preferred) or a path to a
        ``.drawio`` file (fallback).
    pid_id:
        Optional P&ID identifier.  When empty, a sensible default is
        derived from the source.

    Returns
    -------
    nx.DiGraph
        Directed graph with typed nodes and edges.
    """
    # Import here to avoid hard import at module level if pydexpi is absent
    try:
        from pydexpi.dexpi_classes.dexpiModel import DexpiModel as _DexpiModel
    except ImportError:  # pragma: no cover
        _DexpiModel = None  # type: ignore[assignment,misc]

    if _DexpiModel is not None and isinstance(source, _DexpiModel):
        return build_graph_from_dexpi(source, pid_id=pid_id)

    # Treat as path
    return build_graph_from_drawio(Path(source), pid_id=pid_id)


# ===================================================================
# PATH A -- from pyDEXPI DexpiModel  (preferred)
# ===================================================================


def build_graph_from_dexpi(
    dexpi_model: "DexpiModel",
    pid_id: str = "",
) -> nx.DiGraph:
    """Convert a pyDEXPI ``DexpiModel`` into a knowledge-graph ``DiGraph``.

    Walks the DexpiModel composition tree directly (equipment, piping,
    instrumentation) and produces a graph whose nodes and edges match the
    knowledge-graph schema used by the rest of this package
    (``node_type``, ``tag_number``, ``rel_type``, etc.).

    Parameters
    ----------
    dexpi_model:
        A populated ``DexpiModel`` (e.g. from ``ProteusSerializer.load()``
        or from ``pid-converter``).
    pid_id:
        P&ID identifier stored in ``graph.graph["pid_id"]``.

    Returns
    -------
    nx.DiGraph
        Directed graph with typed nodes and edges compatible with
        ``condensation``, ``semantic``, and ``neo4j_store``.
    """
    from pydexpi.dexpi_classes import equipment as eq_mod
    from pydexpi.dexpi_classes import instrumentation as inst_mod
    from pydexpi.dexpi_classes import piping as pip_mod
    from pydexpi.dexpi_classes.dexpiBaseModels import DexpiBaseModel
    from pydexpi.toolkits.base_model_utils import get_data_attributes

    graph = nx.DiGraph()
    graph.graph["pid_id"] = pid_id
    graph.graph["source"] = "pydexpi"

    conceptual = dexpi_model.conceptualModel
    if conceptual is None:
        return graph

    # -----------------------------------------------------------------
    # Phase 1: Equipment (TaggedPlantItems that are NozzleOwners)
    # -----------------------------------------------------------------
    # Map nozzle object -> parent equipment for piping resolution
    nozzle_to_equipment: dict[DexpiBaseModel, DexpiBaseModel] = {}

    for item in conceptual.taggedPlantItems:
        if not isinstance(item, eq_mod.NozzleOwner):
            continue
        if not item.nozzles:
            continue

        _add_dexpi_equipment_node(graph, item, pid_id, get_data_attributes)
        for nozzle in item.nozzles:
            nozzle_to_equipment[nozzle] = item

    # -----------------------------------------------------------------
    # Phase 2: Piping (PipingNetworkSystems -> Segments -> Items + Connections)
    # -----------------------------------------------------------------
    for piping_system in conceptual.pipingNetworkSystems:
        for segment in piping_system.segments:
            # Add piping component items as nodes
            for piping_item in segment.items:
                _add_dexpi_piping_item_node(
                    graph, piping_item, pid_id, piping_system, segment, get_data_attributes,
                )

            # Add piping connections as edges
            for conn in segment.connections:
                source_item = conn.sourceItem
                target_item = conn.targetItem
                if source_item is None or target_item is None:
                    continue

                # Resolve nozzles to their parent equipment
                if isinstance(source_item, eq_mod.Nozzle):
                    resolved_source = nozzle_to_equipment.get(source_item)
                    if resolved_source is None:
                        continue
                    source_item = resolved_source
                if isinstance(target_item, eq_mod.Nozzle):
                    resolved_target = nozzle_to_equipment.get(target_item)
                    if resolved_target is None:
                        continue
                    target_item = resolved_target

                # Ensure both endpoints are in the graph
                if source_item.id not in graph:
                    _add_dexpi_equipment_node(graph, source_item, pid_id, get_data_attributes)
                if target_item.id not in graph:
                    _add_dexpi_equipment_node(graph, target_item, pid_id, get_data_attributes)

                # Build edge attributes from segment data
                seg_attrs = get_data_attributes(segment)
                sys_attrs = get_data_attributes(piping_system)

                edge_data: dict[str, Any] = {
                    "rel_type": RelType.SEND_TO.value,
                    "dexpi_class": "PipingConnection",
                    "pid_id": pid_id,
                }
                # Copy piping info from segment
                if seg_attrs.get("nominalDiameter"):
                    edge_data["nominal_diameter"] = str(seg_attrs["nominalDiameter"])
                if seg_attrs.get("materialOfConstructionCode"):
                    edge_data["material_spec"] = str(seg_attrs["materialOfConstructionCode"])
                if seg_attrs.get("insulationCode"):
                    edge_data["insulation"] = str(seg_attrs["insulationCode"])
                # Copy system-level info
                if sys_attrs.get("fluidCode"):
                    edge_data["fluid_code"] = str(sys_attrs["fluidCode"])

                graph.add_edge(source_item.id, target_item.id, **edge_data)

    # -----------------------------------------------------------------
    # Phase 3: Instrumentation
    # -----------------------------------------------------------------

    # 3a: Actuating systems (ControlledActuator -> OperatedValve)
    for actuating_system in conceptual.actuatingSystems:
        valve_ref = actuating_system.operatedValveReference
        if valve_ref is None:
            continue
        valve = valve_ref.valve
        actuator = actuating_system.controlledActuator
        if actuator and valve:
            _add_dexpi_instrument_node(graph, actuator, pid_id, get_data_attributes)
            if valve.id not in graph:
                _add_dexpi_piping_item_node(
                    graph, valve, pid_id, None, None, get_data_attributes,
                )
            graph.add_edge(
                actuator.id, valve.id,
                rel_type=RelType.CONTROLS.value,
                dexpi_class="OperatedValveReference",
                pid_id=pid_id,
            )
        positioner = actuating_system.positioner
        if positioner and valve:
            _add_dexpi_instrument_node(graph, positioner, pid_id, get_data_attributes)
            if valve.id not in graph:
                _add_dexpi_piping_item_node(
                    graph, valve, pid_id, None, None, get_data_attributes,
                )
            graph.add_edge(
                positioner.id, valve.id,
                rel_type=RelType.CONTROLS.value,
                dexpi_class="OperatedValveReference",
                pid_id=pid_id,
            )

    # 3b: ProcessInstrumentationFunctions (instruments + signal connections)
    for instr_fn in conceptual.processInstrumentationFunctions:
        _add_dexpi_instrument_node(graph, instr_fn, pid_id, get_data_attributes)

        # Signal connections
        for scf in instr_fn.signalConveyingFunctions:
            target_obj = _resolve_signal_reference(
                scf.target, conceptual, nozzle_to_equipment, pip_mod, eq_mod, inst_mod,
            )
            source_obj = _resolve_signal_reference(
                scf.source, conceptual, nozzle_to_equipment, pip_mod, eq_mod, inst_mod,
            )
            if source_obj is not None and target_obj is not None:
                # Ensure endpoints exist
                for obj in (source_obj, target_obj):
                    if obj.id not in graph:
                        _add_dexpi_generic_node(graph, obj, pid_id, get_data_attributes)
                sig_data: dict[str, Any] = {
                    "rel_type": RelType.SIGNAL.value,
                    "dexpi_class": "SignalConveyingFunction",
                    "pid_id": pid_id,
                }
                sig_type = get_data_attributes(scf).get("signalConveyingType", "")
                if sig_type:
                    sig_data["signal_type"] = str(sig_type)
                graph.add_edge(source_obj.id, target_obj.id, **sig_data)

    # --- Phase 4: infer implicit relationships ------------------------------
    _infer_relationships(graph)

    return graph


# -- helpers for DexpiModel path ---------------------------------------------


def _add_dexpi_equipment_node(
    graph: nx.DiGraph,
    obj: Any,
    pid_id: str,
    get_data_attributes: Any,
) -> None:
    """Add an equipment node derived from a pyDEXPI TaggedPlantItem."""
    if obj.id in graph:
        return
    attrs = get_data_attributes(obj)
    dexpi_class = obj.__class__.__name__
    component_class = _derive_component_class(dexpi_class, attrs)
    node_type = classify_dexpi_class(dexpi_class, component_class)

    tag_number = _derive_tag_number(dexpi_class, attrs, node_type, component_class)

    data: dict[str, Any] = {
        "pid_id": pid_id,
        "tag_number": tag_number,
        "dexpi_class": dexpi_class,
        "dexpi_component_class": component_class,
        "node_type": node_type.value,
        "label": tag_number or dexpi_class,
    }

    # Equipment-specific fields
    _copy_equipment_attrs(data, attrs)

    graph.add_node(obj.id, **data)


def _add_dexpi_piping_item_node(
    graph: nx.DiGraph,
    obj: Any,
    pid_id: str,
    piping_system: Any,
    segment: Any,
    get_data_attributes: Any,
) -> None:
    """Add a piping component item (valve, reducer, etc.) as a node."""
    if obj.id in graph:
        return
    attrs = get_data_attributes(obj)
    dexpi_class = obj.__class__.__name__
    component_class = _derive_component_class(dexpi_class, attrs)
    node_type = classify_dexpi_class(dexpi_class, component_class)

    tag_number = _derive_tag_number(dexpi_class, attrs, node_type, component_class)

    data: dict[str, Any] = {
        "pid_id": pid_id,
        "tag_number": tag_number,
        "dexpi_class": dexpi_class,
        "dexpi_component_class": component_class,
        "node_type": node_type.value,
        "label": tag_number or dexpi_class,
    }

    # Piping-specific fields
    _copy_piping_attrs(data, attrs, node_type)
    _copy_valve_attrs(data, attrs, node_type)

    # Enrich with system/segment data
    if piping_system is not None:
        sys_attrs = get_data_attributes(piping_system)
        if sys_attrs.get("fluidCode"):
            data.setdefault("fluid_code", str(sys_attrs["fluidCode"]))
    if segment is not None:
        seg_attrs = get_data_attributes(segment)
        if seg_attrs.get("nominalDiameter"):
            data.setdefault("nominal_diameter", str(seg_attrs["nominalDiameter"]))
        if seg_attrs.get("materialOfConstructionCode"):
            data.setdefault("material_spec", str(seg_attrs["materialOfConstructionCode"]))

    graph.add_node(obj.id, **data)


def _add_dexpi_instrument_node(
    graph: nx.DiGraph,
    obj: Any,
    pid_id: str,
    get_data_attributes: Any,
) -> None:
    """Add an instrumentation function node."""
    if obj.id in graph:
        return
    attrs = get_data_attributes(obj)
    dexpi_class = obj.__class__.__name__
    component_class = _derive_component_class(dexpi_class, attrs)

    # Override node_type to INSTRUMENT for instrumentation objects
    node_type = NodeType.INSTRUMENT

    tag_number = _derive_tag_number(dexpi_class, attrs, node_type, component_class)

    data: dict[str, Any] = {
        "pid_id": pid_id,
        "tag_number": tag_number,
        "dexpi_class": dexpi_class,
        "dexpi_component_class": component_class,
        "node_type": node_type.value,
        "label": tag_number or dexpi_class,
    }

    # Instrument-specific fields
    _copy_instrument_attrs(data, attrs, node_type)

    graph.add_node(obj.id, **data)


def _add_dexpi_generic_node(
    graph: nx.DiGraph,
    obj: Any,
    pid_id: str,
    get_data_attributes: Any,
) -> None:
    """Add a generic pyDEXPI object as a graph node (catch-all)."""
    if obj.id in graph:
        return
    attrs = get_data_attributes(obj)
    dexpi_class = obj.__class__.__name__
    component_class = _derive_component_class(dexpi_class, attrs)
    node_type = classify_dexpi_class(dexpi_class, component_class)
    tag_number = _derive_tag_number(dexpi_class, attrs, node_type, component_class)

    data: dict[str, Any] = {
        "pid_id": pid_id,
        "tag_number": tag_number,
        "dexpi_class": dexpi_class,
        "dexpi_component_class": component_class,
        "node_type": node_type.value,
        "label": tag_number or dexpi_class,
    }
    graph.add_node(obj.id, **data)


def _resolve_signal_reference(
    ref_obj: Any,
    conceptual: Any,
    nozzle_to_equipment: dict,
    pip_mod: Any,
    eq_mod: Any,
    inst_mod: Any,
) -> Any | None:
    """Resolve a signal conveying function source/target to the actual object.

    Mirrors the resolution logic from MLGraphLoader.determine_reference().
    """
    if ref_obj is None:
        return None

    if isinstance(ref_obj, inst_mod.ProcessSignalGeneratingFunction):
        sensing = getattr(ref_obj, "sensingLocation", None)
        if sensing is None:
            return None
        if isinstance(sensing, eq_mod.Nozzle):
            return nozzle_to_equipment.get(sensing)
        if isinstance(sensing, pip_mod.PipingComponent):
            return sensing
        return None
    if isinstance(ref_obj, inst_mod.ActuatingFunction):
        systems = getattr(ref_obj, "systems", None)
        if systems is not None:
            actuator = getattr(systems, "controlledActuator", None)
            return actuator
        return None
    # ProcessInstrumentationFunction, SignalOffPageConnector, etc.
    return ref_obj


# -- attribute derivation helpers -------------------------------------------

def _derive_component_class(dexpi_class: str, attrs: dict[str, Any]) -> str:
    """Extract or infer a component class code from pyDEXPI attributes."""
    cat = attrs.get("processInstrumentationFunctionCategory", "")
    if cat:
        return cat
    prefix = attrs.get("tagNamePrefix", "")
    if prefix:
        return prefix
    return ""


def _derive_tag_number(
    dexpi_class: str,
    attrs: dict[str, Any],
    node_type: NodeType,
    component_class: str,
) -> str:
    """Build a human-readable tag number from pyDEXPI attributes."""
    tag_name = attrs.get("tagName", "")
    if tag_name:
        return tag_name

    prefix = attrs.get("tagNamePrefix", "")
    seq = attrs.get("tagNameSequenceNumber", "")
    suffix = attrs.get("tagNameSuffix", "")

    if prefix and seq:
        tag = f"{prefix}-{seq}"
        if suffix:
            tag += suffix
        return tag

    # For instruments: use category + number
    cat = attrs.get("processInstrumentationFunctionCategory", "")
    num = attrs.get("processInstrumentationFunctionNumber", "")
    if cat and num:
        return f"{cat}-{num}"

    return ""


def _copy_equipment_attrs(data: dict[str, Any], attrs: dict[str, Any]) -> None:
    """Copy equipment-related attributes into data dict."""
    for key in ("design_pressure", "design_temperature", "capacity", "power", "material"):
        camel = _snake_to_camel(key)
        val = attrs.get(camel) or attrs.get(key)
        if val:
            data[key] = str(val)


def _copy_instrument_attrs(
    data: dict[str, Any], attrs: dict[str, Any], node_type: NodeType
) -> None:
    """Copy instrument-related attributes."""
    if node_type != NodeType.INSTRUMENT:
        return
    cat = attrs.get("processInstrumentationFunctionCategory", "")
    modifier = attrs.get("processInstrumentationFunctionModifier", "")
    data.setdefault("measured_variable", _infer_measured_variable(cat))
    data.setdefault("function", modifier or _infer_function(cat))
    data.setdefault("signal_type", "")


def _copy_piping_attrs(
    data: dict[str, Any], attrs: dict[str, Any], node_type: NodeType
) -> None:
    """Copy piping-related attributes."""
    if node_type not in (NodeType.PIPING_SEGMENT, NodeType.UTILITY_LINE):
        return
    for key in ("line_number", "nominal_diameter", "fluid_code", "material_spec", "insulation"):
        camel = _snake_to_camel(key)
        val = attrs.get(camel) or attrs.get(key)
        if val:
            data[key] = str(val)
    # pyDEXPI uses fluidCode at segment level
    if attrs.get("fluidCode"):
        data.setdefault("fluid_code", str(attrs["fluidCode"]))


def _copy_valve_attrs(
    data: dict[str, Any], attrs: dict[str, Any], node_type: NodeType
) -> None:
    """Copy valve-related attributes."""
    if node_type != NodeType.VALVE:
        return
    for key in ("size", "rating", "valve_type"):
        camel = _snake_to_camel(key)
        val = attrs.get(camel) or attrs.get(key)
        if val:
            data[key] = str(val)


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


_VARIABLE_MAP: dict[str, str] = {
    "T": "Temperature",
    "P": "Pressure",
    "F": "Flow",
    "L": "Level",
    "A": "Analysis",
    "S": "Speed",
    "V": "Vibration",
    "W": "Weight",
}


def _infer_measured_variable(category: str) -> str:
    """Infer the measured variable from ISA function letters (first letter)."""
    if category:
        return _VARIABLE_MAP.get(category[0], "")
    return ""


_FUNCTION_MAP: dict[str, str] = {
    "I": "Indicator",
    "IC": "Indicating Controller",
    "C": "Controller",
    "T": "Transmitter",
    "A": "Alarm",
    "R": "Recorder",
    "S": "Switch",
    "V": "Valve",
    "E": "Element",
}


def _infer_function(category: str) -> str:
    """Infer the instrument function from ISA function letters (after first)."""
    if len(category) > 1:
        suffix = category[1:]
        return _FUNCTION_MAP.get(suffix, suffix)
    return ""


# ===================================================================
# PATH B -- from .drawio file  (fallback / original)
# ===================================================================


def build_graph_from_drawio(drawio_path: Path, pid_id: str = "") -> nx.DiGraph:
    """Parse a ``.drawio`` file and return a fully-typed directed graph.

    Parameters
    ----------
    drawio_path:
        Path to the ``.drawio`` (mxGraph XML) file.
    pid_id:
        Optional identifier for the P&ID drawing.  When empty the file stem
        is used.

    Returns
    -------
    nx.DiGraph
        Directed graph with typed nodes and edges.
    """
    drawio_path = Path(drawio_path)
    if not pid_id:
        pid_id = drawio_path.stem

    tree = etree.parse(str(drawio_path))  # noqa: S320
    root = tree.getroot()

    graph = nx.DiGraph()
    graph.graph["pid_id"] = pid_id
    graph.graph["source"] = "drawio"

    # --- Phase 1: collect all <object> elements with dexpi_class -----------
    objects = _collect_objects(root)
    for obj in objects:
        _add_node(graph, obj, pid_id)

    # --- Phase 2: collect edges (mxCells with edge="1") --------------------
    _add_drawio_edges(root, graph, objects, pid_id)

    # --- Phase 3: infer implicit relationships ----------------------------
    _infer_relationships(graph)

    return graph


# ---------------------------------------------------------------------------
# Internal helpers -- drawio parsing
# ---------------------------------------------------------------------------

_SKIP_ATTRS = frozenset({"id", "label", "style"})


def _collect_objects(root: etree._Element) -> list[dict[str, Any]]:
    """Return a list of dicts, one per ``<object>`` with a ``dexpi_class``."""
    results: list[dict[str, Any]] = []
    for obj in root.iter("object"):
        dexpi_class = obj.get("dexpi_class")
        if not dexpi_class:
            continue
        attrs: dict[str, Any] = dict(obj.attrib)
        # Also check if the child mxCell is an edge (has source/target)
        child_cell = obj.find("mxCell")
        if child_cell is not None:
            attrs["_is_edge"] = child_cell.get("edge") == "1"
            attrs["_source_point"] = child_cell.get("source", "")
            attrs["_target_point"] = child_cell.get("target", "")
            # Store geometry for proximity-based inference
            geo = child_cell.find("mxGeometry")
            if geo is not None:
                for pt_tag in ("sourcePoint", "targetPoint"):
                    pt = geo.find(f"mxPoint[@as='{pt_tag}']")
                    if pt is not None:
                        attrs[f"_{pt_tag}_x"] = float(pt.get("x", 0))
                        attrs[f"_{pt_tag}_y"] = float(pt.get("y", 0))
                # Also store x, y from geometry itself
                attrs["_geo_x"] = float(geo.get("x", 0))
                attrs["_geo_y"] = float(geo.get("y", 0))
                attrs["_geo_w"] = float(geo.get("width", 0))
                attrs["_geo_h"] = float(geo.get("height", 0))
            # Store parent layer
            attrs["_parent"] = child_cell.get("parent", "")
        results.append(attrs)
    return results


def _node_data(attrs: dict[str, Any], pid_id: str) -> dict[str, Any]:
    """Build the dict stored as node data in NetworkX."""
    dexpi_class = attrs.get("dexpi_class", "")
    component_class = attrs.get("dexpi_component_class", "")
    node_type = classify_dexpi_class(dexpi_class, component_class)

    tag_number = attrs.get("tag_number", "")
    # For instruments, build tag from component class + tag_number
    if node_type == NodeType.INSTRUMENT and not tag_number.startswith(component_class):
        if component_class and tag_number:
            tag_number = f"{component_class}-{tag_number}"

    data: dict[str, Any] = {
        "pid_id": pid_id,
        "tag_number": tag_number,
        "dexpi_class": dexpi_class,
        "dexpi_component_class": component_class,
        "node_type": node_type.value,
        "label": attrs.get("label", ""),
    }

    # Copy domain-specific attributes
    for key, val in attrs.items():
        if key in _SKIP_ATTRS:
            continue
        # Keep geometry keys (_geo_*) for proximity inference, skip other internal keys
        if key.startswith("_") and not key.startswith("_geo_"):
            continue
        if key not in data:
            data[key] = val

    return data


def _add_node(graph: nx.DiGraph, attrs: dict[str, Any], pid_id: str) -> None:
    """Add a single node to the graph from an <object> attribute dict."""
    node_id = attrs["id"]
    data = _node_data(attrs, pid_id)
    graph.add_node(node_id, **data)


def _add_drawio_edges(
    root: etree._Element,
    graph: nx.DiGraph,
    objects: list[dict[str, Any]],
    pid_id: str,
) -> None:
    """Create edges for objects that are themselves edges (ProcessLine, SignalLine, etc.)."""
    # Build a lookup for quick nearest-node resolution
    node_positions = _build_position_map(objects)

    for attrs in objects:
        if not attrs.get("_is_edge"):
            continue

        node_id = attrs["id"]
        dexpi_class = attrs.get("dexpi_class", "")

        # Determine relationship type based on dexpi_class
        if dexpi_class == "SignalLine":
            rel_type = RelType.SIGNAL.value
        elif dexpi_class in PIPING_CLASSES or dexpi_class == "UtilityLine":
            rel_type = RelType.SEND_TO.value
        else:
            rel_type = RelType.SEND_TO.value

        # Try explicit source/target first
        source = attrs.get("_source_point", "")
        target = attrs.get("_target_point", "")

        # If explicit source/target aren't node IDs, use proximity
        if source and source in graph:
            src_id = source
        else:
            src_x = attrs.get("_sourcePoint_x", attrs.get("_geo_x", 0))
            src_y = attrs.get("_sourcePoint_y", attrs.get("_geo_y", 0))
            src_id = _nearest_non_edge_node(src_x, src_y, node_positions, exclude={node_id})

        if target and target in graph:
            tgt_id = target
        else:
            tgt_x = attrs.get("_targetPoint_x", attrs.get("_geo_x", 0))
            tgt_y = attrs.get("_targetPoint_y", attrs.get("_geo_y", 0))
            tgt_id = _nearest_non_edge_node(tgt_x, tgt_y, node_positions, exclude={node_id, src_id})

        if src_id and tgt_id and src_id != tgt_id:
            graph.add_edge(
                src_id,
                tgt_id,
                edge_id=node_id,
                rel_type=rel_type,
                pid_id=pid_id,
                dexpi_class=dexpi_class,
                line_number=attrs.get("line_number", ""),
                nominal_diameter=attrs.get("nominal_diameter", ""),
                fluid_code=attrs.get("fluid_code", ""),
                material_spec=attrs.get("material_spec", ""),
                insulation=attrs.get("insulation", ""),
                signal_type=attrs.get("signal_type", ""),
                instrument_tag=attrs.get("instrument_tag", ""),
            )


def _build_position_map(objects: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    """Build a dict  {node_id: (center_x, center_y)} for non-edge objects."""
    positions: dict[str, tuple[float, float]] = {}
    for attrs in objects:
        if attrs.get("_is_edge"):
            continue
        cx = attrs.get("_geo_x", 0) + attrs.get("_geo_w", 0) / 2
        cy = attrs.get("_geo_y", 0) + attrs.get("_geo_h", 0) / 2
        positions[attrs["id"]] = (cx, cy)
    return positions


def _nearest_non_edge_node(
    x: float,
    y: float,
    positions: dict[str, tuple[float, float]],
    exclude: set[str] | None = None,
) -> str:
    """Return the node ID closest to (x, y), excluding specified IDs."""
    exclude = exclude or set()
    best_id = ""
    best_dist = float("inf")
    for nid, (nx_, ny_) in positions.items():
        if nid in exclude:
            continue
        dist = (nx_ - x) ** 2 + (ny_ - y) ** 2
        if dist < best_dist:
            best_dist = dist
            best_id = nid
    return best_id


# ---------------------------------------------------------------------------
# Shared: implicit relationship inference
# ---------------------------------------------------------------------------


def _infer_relationships(graph: nx.DiGraph) -> None:
    """Add implicit relationships that are not explicit edges in the source.

    - Nozzle -> Equipment: ``BELONGS_TO`` (based on geometric proximity)
    - Instrument -> Equipment: ``MEASURED_BY`` (based on signal lines connecting them)
    """
    equipment_nodes = [
        n for n, d in graph.nodes(data=True) if d.get("node_type") == NodeType.EQUIPMENT.value
    ]
    nozzle_nodes = [
        n for n, d in graph.nodes(data=True) if d.get("node_type") == NodeType.NOZZLE.value
    ]
    instrument_nodes = [
        n for n, d in graph.nodes(data=True) if d.get("node_type") == NodeType.INSTRUMENT.value
    ]

    # --- Nozzle -> nearest Equipment: BELONGS_TO ---
    if equipment_nodes and nozzle_nodes:
        eq_positions: dict[str, tuple[float, float]] = {}
        for eq_id in equipment_nodes:
            d = graph.nodes[eq_id]
            x = float(d.get("_geo_x", 0)) + float(d.get("_geo_w", 0)) / 2
            y = float(d.get("_geo_y", 0)) + float(d.get("_geo_h", 0)) / 2
            eq_positions[eq_id] = (x, y)

        for nz_id in nozzle_nodes:
            d = graph.nodes[nz_id]
            nx_ = float(d.get("_geo_x", 0)) + float(d.get("_geo_w", 0)) / 2
            ny_ = float(d.get("_geo_y", 0)) + float(d.get("_geo_h", 0)) / 2
            nearest_eq = _nearest_non_edge_node(nx_, ny_, eq_positions)
            if nearest_eq:
                graph.add_edge(
                    nz_id,
                    nearest_eq,
                    rel_type=RelType.BELONGS_TO.value,
                    inferred=True,
                )

    # --- Instrument -> Equipment: via signal line connectivity ---
    # If an instrument is connected (through signal lines) to a process node
    # near an equipment, infer a MEASURED_BY relationship.
    for inst_id in instrument_nodes:
        # Look at all neighbours reachable through signal edges
        for neighbor in list(graph.predecessors(inst_id)) + list(graph.successors(inst_id)):
            n_data = graph.nodes.get(neighbor, {})
            if n_data.get("node_type") == NodeType.EQUIPMENT.value:
                if not graph.has_edge(inst_id, neighbor):
                    graph.add_edge(
                        inst_id,
                        neighbor,
                        rel_type=RelType.MEASURED_BY.value,
                        inferred=True,
                    )
