"""Enrich graph nodes and edges with human-readable semantic labels.

These labels are designed to be consumed by an LLM as part of a Graph-RAG
pipeline.  They include units, design conditions, and service codes
wherever available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pid_knowledge_graph.models import NodeType, RelType

if TYPE_CHECKING:
    import networkx as nx


def enrich_labels(graph: nx.DiGraph) -> nx.DiGraph:
    """Add a ``label`` attribute to every node and edge in *graph*.

    The graph is modified **in place** and also returned for convenience.

    Parameters
    ----------
    graph:
        A P&ID graph (detailed or condensed) produced by this package.

    Returns
    -------
    nx.DiGraph
        The same graph with enriched ``label`` fields.
    """
    for node_id, data in graph.nodes(data=True):
        data["label"] = _node_label(node_id, data)

    for u, v, data in graph.edges(data=True):
        data["label"] = _edge_label(u, v, data, graph)

    return graph


# ---------------------------------------------------------------------------
# Node label formatters
# ---------------------------------------------------------------------------

_EQUIPMENT_CLASS_NAMES: dict[str, str] = {
    "CentrifugalPump": "Centrifugal Pump",
    "PositiveDisplacementPump": "Positive Displacement Pump",
    "VerticalVessel": "Vertical Vessel",
    "HorizontalVessel": "Horizontal Vessel",
    "ShellTubeHeatExchanger": "Shell & Tube Heat Exchanger",
    "PlateHeatExchanger": "Plate Heat Exchanger",
    "AirCooledHeatExchanger": "Air-Cooled Heat Exchanger",
    "Column": "Column",
    "Reactor": "Reactor",
    "Compressor": "Compressor",
    "Filter": "Filter",
    "Tank": "Tank",
    "Agitator": "Agitator",
    "Drum": "Drum",
}

_INSTRUMENT_FUNCTION_MAP: dict[str, str] = {
    "TemperatureTransmitter": "Temperature Transmitter",
    "PressureTransmitter": "Pressure Transmitter",
    "FlowTransmitter": "Flow Transmitter",
    "LevelTransmitter": "Level Transmitter",
    "TemperatureController": "Temperature Indicating Controller",
    "PressureController": "Pressure Indicating Controller",
    "FlowController": "Flow Indicating Controller",
    "LevelController": "Level Indicating Controller",
    "TemperatureIndicator": "Temperature Indicator",
    "PressureIndicator": "Pressure Indicator",
    "FlowIndicator": "Flow Indicator",
    "LevelIndicator": "Level Indicator",
}


def _node_label(node_id: str, data: dict) -> str:
    """Generate a semantic label for a single node."""
    node_type = data.get("node_type", "")

    if node_type == NodeType.EQUIPMENT.value:
        return _equipment_label(data)
    if node_type == NodeType.INSTRUMENT.value:
        return _instrument_label(data)
    if node_type == NodeType.PIPING_SEGMENT.value:
        return _piping_label(data)
    if node_type == NodeType.UTILITY_LINE.value:
        return _utility_line_label(data)
    if node_type == NodeType.NOZZLE.value:
        return _nozzle_label(data)
    if node_type == NodeType.VALVE.value:
        return _valve_label(data)
    if node_type == NodeType.STEAM_TRAP.value:
        return _steam_trap_label(data)
    if node_type == NodeType.SIGNAL_LINE.value:
        return _signal_line_label(data)
    if node_type == NodeType.CONTROL_LOOP.value:
        return _control_loop_label(data)

    # Fallback
    tag = data.get("tag_number", node_id)
    dexpi = data.get("dexpi_class", "")
    return f"{tag} ({dexpi})" if dexpi else tag


def _equipment_label(data: dict) -> str:
    tag = data.get("tag_number", "?")
    dexpi = data.get("dexpi_class", "")
    human_name = _EQUIPMENT_CLASS_NAMES.get(dexpi, dexpi)

    parts = [f"{human_name} {tag}"]

    details: list[str] = []
    if data.get("power"):
        details.append(data["power"])
    if data.get("capacity"):
        details.append(data["capacity"])

    design: list[str] = []
    if data.get("design_pressure"):
        design.append(data["design_pressure"])
    if data.get("design_temperature"):
        design.append(data["design_temperature"])
    if design:
        details.append("design: " + " / ".join(design))

    if data.get("material"):
        details.append(f"material: {data['material']}")

    if details:
        parts.append(f"({', '.join(details)})")

    return " ".join(parts)


def _instrument_label(data: dict) -> str:
    tag = data.get("tag_number", "?")
    dexpi = data.get("dexpi_class", "")
    human_func = _INSTRUMENT_FUNCTION_MAP.get(dexpi, data.get("function", dexpi))

    parts = [f"{tag} ({human_func}"]

    extras: list[str] = []
    if data.get("signal_type"):
        extras.append(data["signal_type"])

    # Detect if panel-mounted from the label or dexpi class hints
    func_lower = data.get("function", "").lower()
    if "controller" in func_lower or "indicating controller" in func_lower:
        extras.append("panel-mounted")

    if extras:
        parts.append(f", {', '.join(extras)}")

    parts.append(")")
    return "".join(parts)


def _piping_label(data: dict) -> str:
    diameter = data.get("nominal_diameter", "")
    material = data.get("material_spec", "")
    fluid = data.get("fluid_code", "")
    line_num = data.get("line_number", "")

    parts: list[str] = []
    if diameter:
        parts.append(diameter)
    if material:
        parts.append(material)

    result = ", ".join(parts) if parts else "Piping"

    extras: list[str] = []
    if fluid:
        extras.append(fluid.replace("_", " ").title())
    if line_num:
        extras.append(f"line {line_num}")

    if extras:
        result += f" ({', '.join(extras)})"

    return result


def _utility_line_label(data: dict) -> str:
    diameter = data.get("nominal_diameter", "")
    material = data.get("material_spec", "")
    fluid = data.get("fluid_code", "")
    line_num = data.get("line_number", "")

    parts: list[str] = []
    if diameter:
        parts.append(diameter)
    if material:
        parts.append(material)

    result = ", ".join(parts) if parts else "Utility Line"

    extras: list[str] = []
    if fluid:
        fluid_name = fluid.replace("-", " ").replace("_", " ").title()
        extras.append(fluid_name)
    if line_num:
        extras.append(f"line {line_num}")

    if extras:
        result += f" ({', '.join(extras)})"

    return result


def _nozzle_label(data: dict) -> str:
    nozzle_id = data.get("nozzle_id", "")
    size = data.get("size", "")
    rating = data.get("rating", "")
    service = data.get("service", "")

    parts = [f"Nozzle {nozzle_id}" if nozzle_id else "Nozzle"]
    details: list[str] = []
    if size:
        details.append(size)
    if rating:
        details.append(rating)
    if service:
        details.append(service)

    if details:
        parts.append(f"({', '.join(details)})")

    return " ".join(parts)


def _valve_label(data: dict) -> str:
    tag = data.get("tag_number", "?")
    valve_type = data.get("valve_type", data.get("dexpi_class", ""))
    size = data.get("size", "")
    rating = data.get("rating", "")

    parts = [f"{valve_type} Valve {tag}" if valve_type else f"Valve {tag}"]
    details: list[str] = []
    if size:
        details.append(size)
    if rating:
        details.append(rating)
    if details:
        parts.append(f"({', '.join(details)})")

    return " ".join(parts)


def _steam_trap_label(data: dict) -> str:
    tag = data.get("tag_number", "?")
    size = data.get("size", "")
    return f"Steam Trap {tag}" + (f" ({size})" if size else "")


def _signal_line_label(data: dict) -> str:
    sig_type = data.get("signal_type", "")
    inst_tag = data.get("instrument_tag", "")
    parts = ["Signal Line"]
    if inst_tag:
        parts.append(inst_tag)
    if sig_type:
        parts.append(f"({sig_type})")
    return " ".join(parts)


def _control_loop_label(data: dict) -> str:
    ctrl_tag = data.get("controller_tag", "")
    sensor_tag = data.get("sensor_tag", "")
    final_tag = data.get("final_element_tag", "")
    var = data.get("controlled_variable", "")

    parts = [f"Control Loop: {var}" if var else "Control Loop"]
    if ctrl_tag:
        parts.append(f"controller={ctrl_tag}")
    if sensor_tag:
        parts.append(f"sensor={sensor_tag}")
    if final_tag:
        parts.append(f"final_element={final_tag}")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Edge label formatter
# ---------------------------------------------------------------------------


def _edge_label(u: str, v: str, data: dict, graph: nx.DiGraph) -> str:
    """Generate a semantic label for an edge."""
    rel_type = data.get("rel_type", "")

    u_tag = graph.nodes[u].get("tag_number", u) if u in graph else u
    v_tag = graph.nodes[v].get("tag_number", v) if v in graph else v

    if rel_type == RelType.FLOW.value or rel_type == RelType.SEND_TO.value:
        return _flow_edge_label(u_tag, v_tag, data)
    if rel_type == RelType.CONTROLS.value:
        return data.get("label", f"{u_tag} controls {v_tag}")
    if rel_type == RelType.BELONGS_TO.value:
        return f"Nozzle {u_tag} belongs to {v_tag}"
    if rel_type == RelType.MEASURED_BY.value:
        return f"{u_tag} measures on {v_tag}"
    if rel_type == RelType.SIGNAL.value:
        sig_type = data.get("signal_type", "")
        if sig_type:
            return f"Signal ({sig_type}): {u_tag} -> {v_tag}"
        return f"Signal: {u_tag} -> {v_tag}"
    if rel_type == RelType.HAS_NOZZLE.value:
        return f"{u_tag} has nozzle {v_tag}"

    return f"{u_tag} -> {v_tag} ({rel_type})"


def _flow_edge_label(u_tag: str, v_tag: str, data: dict) -> str:
    """Build a descriptive label for a flow/send_to edge."""
    diameter = data.get("nominal_diameter", "")
    material = data.get("material_spec", "")
    line_num = data.get("line_number", "")

    via_parts: list[str] = []
    if diameter:
        via_parts.append(diameter)
    if material:
        via_parts.append(material)

    via = " ".join(via_parts)

    label = f"Process flow: from {u_tag} to {v_tag}"
    if via:
        label += f" via {via}"
    if line_num:
        label += f" line"

    return label
