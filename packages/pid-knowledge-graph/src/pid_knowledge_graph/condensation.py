"""Condense a detailed P&ID graph into a high-level equipment flow graph.

The condensed graph keeps only *major equipment* as nodes and collapses
intermediate piping segments, nozzles, and valves into direct
equipment-to-equipment flow edges.  Control loops are represented as
simplified relationship annotations on the edges.
"""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

from pid_knowledge_graph.models import NodeType, RelType

# Node types that can be traversed (collapsed) during condensation.
_TRAVERSABLE_TYPES = frozenset({
    NodeType.NOZZLE.value,
    NodeType.PIPING_SEGMENT.value,
    NodeType.VALVE.value,
    NodeType.UTILITY_LINE.value,
    NodeType.STEAM_TRAP.value,
})

# Relationship types that represent physical flow.
_FLOW_REL_TYPES = frozenset({
    RelType.SEND_TO.value,
    RelType.FLOW.value,
})


def condense_graph(detailed_graph: nx.DiGraph) -> nx.DiGraph:
    """Produce an equipment-level graph from a detailed P&ID graph.

    Parameters
    ----------
    detailed_graph:
        A graph produced by :func:`graph_builder.build_graph`.

    Returns
    -------
    nx.DiGraph
        A new directed graph where nodes are major equipment items and
        edges represent direct process flows (piping collapsed) and
        simplified control relationships.
    """
    cg = nx.DiGraph()
    pid_id = detailed_graph.graph.get("pid_id", "")
    cg.graph["pid_id"] = pid_id
    cg.graph["condensed"] = True

    # --- Step 1: identify equipment nodes --------------------------------
    equipment_ids: set[str] = set()
    for node_id, data in detailed_graph.nodes(data=True):
        ntype = data.get("node_type", "")
        if ntype == NodeType.EQUIPMENT.value:
            equipment_ids.add(node_id)
            cg.add_node(node_id, **data)

    if not equipment_ids:
        return cg

    # --- Step 2: build nozzle-to-equipment map ---------------------------
    nozzle_to_eq: dict[str, str] = {}
    for u, v, ed in detailed_graph.edges(data=True):
        if ed.get("rel_type") == RelType.BELONGS_TO.value:
            if v in equipment_ids:
                nozzle_to_eq[u] = v

    # --- Step 3: find equipment-to-equipment flow paths ------------------
    for eq_id in equipment_ids:
        _walk_from_equipment(
            detailed_graph, cg, eq_id, equipment_ids, nozzle_to_eq,
        )

    # --- Step 4: add simplified control-loop annotations -----------------
    _add_control_annotations(detailed_graph, cg, equipment_ids)

    return cg


# ---------------------------------------------------------------------------
# Flow path discovery
# ---------------------------------------------------------------------------


def _walk_from_equipment(
    dg: nx.DiGraph,
    cg: nx.DiGraph,
    start_eq: str,
    equipment_ids: set[str],
    nozzle_to_eq: dict[str, str],
) -> None:
    """BFS from *start_eq* through traversable nodes to other equipment.

    The walk considers both directions of the BELONGS_TO relationship
    so that nozzles attached to the starting equipment are included in
    the search frontier.
    """
    # Seed the BFS with the equipment itself plus its nozzles
    visited: set[str] = set()
    # (current_node, accumulated_edge_data)
    queue: list[tuple[str, list[dict]]] = [(start_eq, [])]

    # Also add nozzles that belong to this equipment as starting points
    for nozzle_id, eq_id in nozzle_to_eq.items():
        if eq_id == start_eq:
            queue.append((nozzle_id, []))

    while queue:
        current, path = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        # Follow outgoing edges
        for _, succ, edge_data in dg.out_edges(current, data=True):
            rel = edge_data.get("rel_type", "")

            # Skip BELONGS_TO outgoing (nozzle -> equipment) --
            # we handle equipment discovery differently.
            if rel == RelType.BELONGS_TO.value:
                continue

            if rel not in _FLOW_REL_TYPES and rel not in {
                RelType.SIGNAL.value
            }:
                continue

            # Only traverse flow-type edges (skip SIGNAL)
            if rel == RelType.SIGNAL.value:
                continue

            succ_data = dg.nodes.get(succ, {})
            succ_type = succ_data.get("node_type", "")

            if succ in equipment_ids and succ != start_eq:
                _add_condensed_flow_edge(
                    cg, start_eq, succ, path + [edge_data], dg,
                )
            elif succ_type in _TRAVERSABLE_TYPES and succ not in visited:
                # Check if this traversable node is a nozzle of another
                # equipment -- if so, record the flow to that equipment
                if succ in nozzle_to_eq:
                    target_eq = nozzle_to_eq[succ]
                    if target_eq != start_eq:
                        _add_condensed_flow_edge(
                            cg, start_eq, target_eq,
                            path + [edge_data], dg,
                        )
                else:
                    queue.append((succ, path + [edge_data]))


def _add_condensed_flow_edge(
    cg: nx.DiGraph,
    source_eq: str,
    target_eq: str,
    path_edges: list[dict],
    dg: nx.DiGraph,
) -> None:
    """Add (or update) a condensed flow edge between two equipment."""
    if cg.has_edge(source_eq, target_eq):
        return  # already recorded

    # Collect representative line info from path
    line_number = ""
    nominal_diameter = ""
    fluid_code = ""
    material_spec = ""
    for ed in path_edges:
        if ed.get("line_number"):
            line_number = ed["line_number"]
        if ed.get("nominal_diameter"):
            nominal_diameter = ed["nominal_diameter"]
        if ed.get("fluid_code"):
            fluid_code = ed["fluid_code"]
        if ed.get("material_spec"):
            material_spec = ed["material_spec"]

    src_tag = (
        dg.nodes[source_eq].get("tag_number", source_eq)
        if source_eq in dg else source_eq
    )
    tgt_tag = (
        dg.nodes[target_eq].get("tag_number", target_eq)
        if target_eq in dg else target_eq
    )

    label = f"Process flow: {src_tag} -> {tgt_tag}"
    if nominal_diameter:
        label += f" via {nominal_diameter}"
    if material_spec:
        label += f" {material_spec}"
    if line_number:
        label += f" (line {line_number})"

    cg.add_edge(
        source_eq,
        target_eq,
        rel_type=RelType.FLOW.value,
        line_number=line_number,
        nominal_diameter=nominal_diameter,
        fluid_code=fluid_code,
        material_spec=material_spec,
        label=label,
    )


# ---------------------------------------------------------------------------
# Control loop annotations
# ---------------------------------------------------------------------------


def _add_control_annotations(
    dg: nx.DiGraph,
    cg: nx.DiGraph,
    equipment_ids: set[str],
) -> None:
    """Detect control loops and add simplified annotations."""
    controllers: list[str] = []
    for node_id, data in dg.nodes(data=True):
        if data.get("node_type") == NodeType.INSTRUMENT.value:
            func = data.get("function", "").lower()
            dexpi = data.get("dexpi_class", "").lower()
            if "controller" in func or "controller" in dexpi:
                controllers.append(node_id)

    for ctrl_id in controllers:
        ctrl_data = dg.nodes[ctrl_id]
        ctrl_tag = ctrl_data.get("tag_number", ctrl_id)

        # Find sensors (predecessors via SIGNAL)
        sensor_tags: list[str] = []
        for pred, _, ed in dg.in_edges(ctrl_id, data=True):
            if ed.get("rel_type") == RelType.SIGNAL.value:
                pred_data = dg.nodes.get(pred, {})
                ptype = pred_data.get("node_type", "")
                if ptype == NodeType.INSTRUMENT.value:
                    sensor_tags.append(
                        pred_data.get("tag_number", pred)
                    )

        # Find actuated valves (successors via SIGNAL)
        valve_ids: list[str] = []
        for _, succ, ed in dg.out_edges(ctrl_id, data=True):
            if ed.get("rel_type") == RelType.SIGNAL.value:
                succ_data = dg.nodes.get(succ, {})
                if succ_data.get("node_type") == NodeType.VALVE.value:
                    valve_ids.append(succ)

        for valve_id in valve_ids:
            valve_data = dg.nodes.get(valve_id, {})
            valve_tag = valve_data.get("tag_number", valve_id)

            target_eq = _find_equipment_near_valve(
                dg, valve_id, equipment_ids,
            )
            if target_eq:
                eq_tag = dg.nodes[target_eq].get(
                    "tag_number", target_eq,
                )
                annotation = (
                    f"{ctrl_tag} controls {valve_tag} on {eq_tag}"
                )

                if not cg.has_node(ctrl_id):
                    cg.add_node(
                        ctrl_id, **ctrl_data,
                        condensed_role="control_loop",
                    )
                cg.add_edge(
                    ctrl_id,
                    target_eq,
                    rel_type=RelType.CONTROLS.value,
                    label=annotation,
                    controller_tag=ctrl_tag,
                    valve_tag=valve_tag,
                    sensor_tags=sensor_tags,
                )

    # Annotate FLOW edges with control info
    control_map: dict[str, list[str]] = defaultdict(list)
    for _, tgt, ed in cg.edges(data=True):
        if ed.get("rel_type") == RelType.CONTROLS.value:
            control_map[tgt].append(ed.get("label", ""))

    for u, v, ed in cg.edges(data=True):
        if (
            ed.get("rel_type") == RelType.FLOW.value
            and v in control_map
        ):
            ed["control_annotations"] = control_map[v]


def _find_equipment_near_valve(
    dg: nx.DiGraph,
    valve_id: str,
    equipment_ids: set[str],
) -> str | None:
    """Walk from a valve along flow/belongs_to edges to find equipment."""
    allowed = _FLOW_REL_TYPES | {RelType.BELONGS_TO.value}
    visited: set[str] = set()
    queue = [valve_id]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for _, succ, ed in dg.out_edges(current, data=True):
            rel = ed.get("rel_type")
            if rel in allowed:
                if succ in equipment_ids:
                    return succ
                if succ not in visited:
                    queue.append(succ)
        for pred, _, ed in dg.in_edges(current, data=True):
            rel = ed.get("rel_type")
            if rel in allowed:
                if pred in equipment_ids:
                    return pred
    return None
