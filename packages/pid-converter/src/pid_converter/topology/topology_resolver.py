"""Resolve topological connections from Draw.io edges.

This module converts raw mxCell edges (identified by source/target cell IDs or
by proximity of source/target *points* to node bounding boxes) into semantic
:class:`~pid_converter.models.Connection` objects.

Current capabilities
--------------------
* Linear topology: A -> B -> C
* Simple branching: A -> B, A -> C
* Proximity-based matching when edges lack explicit source/target IDs
* Flow direction inference from arrow endpoints (left-to-right / top-to-bottom)

Limitations
-----------
* Does not yet resolve complex recycles or feedback loops
* Nozzle-to-line assignment is proximity-based and may be ambiguous when
  multiple nozzles are very close together
"""

from __future__ import annotations

import math

from pid_converter.models import (
    Connection,
    DexpiCategory,
    FlowDirection,
    PidEdge,
    PidModel,
    PidNode,
    Position,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _center(pos: Position) -> tuple[float, float]:
    """Return the centre point of a bounding box."""
    return pos.x + pos.width / 2, pos.y + pos.height / 2


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


def _point_in_bbox(px: float, py: float, pos: Position, margin: float = 30.0) -> bool:
    """Check whether a point is inside (or within *margin* of) a bounding box."""
    return (
        pos.x - margin <= px <= pos.x + pos.width + margin
        and pos.y - margin <= py <= pos.y + pos.height + margin
    )


def _nearest_node(
    px: float,
    py: float,
    nodes: list[PidNode],
    max_dist: float = 60.0,
) -> PidNode | None:
    """Return the node whose bounding-box centre is closest to *(px, py)*."""
    best: PidNode | None = None
    best_dist = max_dist
    for n in nodes:
        # First, cheap bbox check
        if _point_in_bbox(px, py, n.position, margin=max_dist):
            cx, cy = _center(n.position)
            d = _distance(px, py, cx, cy)
            if d < best_dist:
                best_dist = d
                best = n
    return best


def _infer_direction(edge: PidEdge) -> FlowDirection:
    """Infer flow direction from endpoint coordinates.

    Heuristic: if the target point is to the right of or below the source
    point the flow is *forward*.  Otherwise *reverse*.
    """
    sp = edge.source_point
    tp = edge.target_point
    if sp is None or tp is None:
        return FlowDirection.UNKNOWN

    dx = tp.x - sp.x
    dy = tp.y - sp.y
    if abs(dx) > abs(dy):
        return FlowDirection.FORWARD if dx > 0 else FlowDirection.REVERSE
    return FlowDirection.FORWARD if dy > 0 else FlowDirection.REVERSE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_topology(model: PidModel) -> list[Connection]:
    """Resolve edges in *model* to :class:`Connection` objects.

    The function modifies ``model.connections`` **in-place** and also returns
    the list.

    Resolution strategy
    -------------------
    1. If the edge has explicit ``source_id`` / ``target_id`` referencing known
       nodes, use those directly.
    2. Otherwise fall back to proximity matching: find the node whose bounding-
       box centre is closest to the edge's sourcePoint / targetPoint.
    """
    id_lookup: dict[str, PidNode] = {n.id: n for n in model.nodes}
    connections: list[Connection] = []

    for edge in model.edges:
        from_node = _resolve_endpoint(
            edge.source_id, edge.source_point, id_lookup, model.nodes
        )
        to_node = _resolve_endpoint(
            edge.target_id, edge.target_point, id_lookup, model.nodes
        )

        if from_node is None and to_node is None:
            continue  # orphan edge -- skip

        conn = Connection(
            from_node_id=from_node.id if from_node else "",
            to_node_id=to_node.id if to_node else "",
            via_edge_id=edge.id,
            flow_direction=_infer_direction(edge),
        )
        connections.append(conn)

    model.connections = connections
    return connections


def _resolve_endpoint(
    explicit_id: str,
    point: Position | None,
    id_lookup: dict[str, PidNode],
    all_nodes: list[PidNode],
) -> PidNode | None:
    """Resolve one end of an edge to a node."""
    if explicit_id and explicit_id in id_lookup:
        return id_lookup[explicit_id]
    if point is not None:
        return _nearest_node(point.x, point.y, all_nodes)
    return None


# ---------------------------------------------------------------------------
# Nozzle ownership inference
# ---------------------------------------------------------------------------

def assign_nozzles_to_equipment(model: PidModel) -> dict[str, str]:
    """Return a mapping ``nozzle_id -> equipment_id`` based on proximity.

    A nozzle is assigned to the equipment whose bounding box is closest to
    (and contains or nearly contains) the nozzle centre.
    """
    equip = [n for n in model.nodes if n.category == DexpiCategory.EQUIPMENT]
    nozzles = [n for n in model.nodes if n.category == DexpiCategory.NOZZLE]

    mapping: dict[str, str] = {}
    for noz in nozzles:
        ncx, ncy = _center(noz.position)
        best: PidNode | None = None
        best_dist = float("inf")
        for eq in equip:
            ecx, ecy = _center(eq.position)
            d = _distance(ncx, ncy, ecx, ecy)
            if d < best_dist:
                best_dist = d
                best = eq
        if best is not None:
            mapping[noz.id] = best.id

    return mapping
