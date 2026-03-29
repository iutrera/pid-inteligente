"""Auto-connect orphan instruments to equipment using ISA naming conventions.

When Claude (or any tool) generates a .drawio P&ID from a PDF, instruments
often end up without explicit signal line connections. This module infers
connections using:

1. **ISA tag number matching**: TIC-101 → equipment with tag *-101
2. **Tag prefix matching**: TT-101 (Temperature Transmitter) → TIC-101 (Temperature Controller)
3. **Proximity**: nearest equipment by coordinates if no tag match
4. **Control loop completion**: if sensor→controller exists, find the actuated valve

The result is a list of new edges (SignalLine) to add to the PidModel.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from pid_converter.models import PidModel, PidNode, PidEdge, DexpiCategory


def autoconnect_instruments(model: PidModel) -> PidModel:
    """Add missing signal line connections for orphan instruments.

    Modifies the model in-place by appending new edges and returns it.
    """
    node_map = {n.id: n for n in model.nodes}

    # Classify nodes
    equipment: dict[str, PidNode] = {}
    valves: dict[str, PidNode] = {}
    instruments: dict[str, PidNode] = {}

    for n in model.nodes:
        cat = n.category
        dc = (n.dexpi_class or "").lower()
        if cat == DexpiCategory.EQUIPMENT:
            equipment[n.id] = n
        elif cat == DexpiCategory.PIPING_COMPONENT or "valve" in dc:
            valves[n.id] = n
        elif cat == DexpiCategory.INSTRUMENT:
            instruments[n.id] = n

    # Find which instruments already have connections
    connected_instruments: set[str] = set()
    for e in model.edges:
        dc = (e.dexpi_class or "").lower()
        if "signal" in dc:
            if e.source_id in instruments:
                connected_instruments.add(e.source_id)
            if e.target_id in instruments:
                connected_instruments.add(e.target_id)

    # Find orphan instruments (no signal line at all)
    orphans = {iid: inst for iid, inst in instruments.items()
               if iid not in connected_instruments}

    if not orphans:
        return model

    # Build lookup tables for tag matching
    eq_by_tag = {n.tag_number: n for n in equipment.values() if n.tag_number}
    valve_by_tag = {n.tag_number: n for n in valves.values() if n.tag_number}
    inst_by_tag = {n.tag_number: n for n in instruments.values() if n.tag_number}

    # Tag number → equipment number (e.g., "P-101" → "101", "HE-301A" → "301")
    eq_by_number = _build_number_index(equipment.values())
    valve_by_number = _build_number_index(valves.values())
    inst_by_number = _build_number_index(instruments.values())

    new_edges: list[PidEdge] = []
    edge_id_counter = _max_numeric_id(model) + 500

    for orphan_id, orphan in orphans.items():
        tag = orphan.tag_number or ""
        dc = (orphan.dexpi_class or "").lower()

        # Extract the numeric suffix from the instrument tag
        # TIC-101 → "101", PAH-2301 → "2301", FT-100A → "100"
        inst_number = _extract_number(tag)

        target = None

        is_controller = "controller" in dc
        is_transmitter = "transmitter" in dc or "sensor" in dc or "indicator" in dc

        if is_controller:
            # Controllers connect to their ACTUATED VALVE first
            if inst_number:
                target = _find_by_number(inst_number, valve_by_number)
            if not target:
                target = _find_nearest(orphan, valves.values())
            if not target:
                # Fallback: connect to nearest equipment
                target = _find_nearest(orphan, equipment.values())

        elif is_transmitter:
            # Transmitters/sensors connect to the EQUIPMENT they measure
            # Prefer proximity over number match (TT-101 near HE-101, not T-101)
            target = _find_nearest(orphan, equipment.values())
            # If no position data, fall back to number match
            if not target and inst_number:
                target = _find_by_number(inst_number, eq_by_number)

        else:
            # Indicators, alarms, etc. → nearest equipment
            if inst_number:
                target = _find_by_number(inst_number, eq_by_number)
            if not target:
                target = _find_nearest(orphan, equipment.values())

        # --- Create signal line edge ---
        if target:
            edge_id_counter += 1
            new_edge = PidEdge(
                id=str(edge_id_counter),
                source_id=orphan_id,
                target_id=target.id,
                label="",
                dexpi_class="SignalLine",
                dexpi_component_class="SIGL",
                category=DexpiCategory.SIGNAL_LINE,
                attributes={
                    "signal_type": orphan.attributes.get("signal_type", "4-20mA"),
                    "instrument_tag": tag,
                    "auto_connected": "true",
                },
                style="strokeColor=#FF0000;strokeWidth=1.5;dashed=1;dashPattern=8 4;endArrow=block;endFill=1;",
            )
            new_edges.append(new_edge)

    # --- Strategy 4: Complete control loops ---
    # If we now have sensor→controller, find controller→valve
    all_inst = {**instruments}
    for e in [*model.edges, *new_edges]:
        dc = (e.dexpi_class or "").lower()
        if "signal" not in dc:
            continue
        src_node = node_map.get(e.source_id or "")
        tgt_node = node_map.get(e.target_id or "")
        if not src_node or not tgt_node:
            continue

        # If target is a controller and it doesn't yet connect to a valve
        tgt_dc = (tgt_node.dexpi_class or "").lower()
        if "controller" not in tgt_dc:
            continue

        # Check if controller already has an outgoing signal to a valve
        ctrl_id = tgt_node.id
        has_valve_connection = False
        for e2 in [*model.edges, *new_edges]:
            if (e2.source_id == ctrl_id and
                    "signal" in (e2.dexpi_class or "").lower()):
                tgt2 = node_map.get(e2.target_id or "")
                if tgt2 and (tgt2.id in valves or "valve" in (tgt2.dexpi_class or "").lower()):
                    has_valve_connection = True
                    break

        if not has_valve_connection:
            ctrl_number = _extract_number(tgt_node.tag_number or "")
            valve_target = _find_by_number(ctrl_number, valve_by_number) if ctrl_number else None
            if not valve_target:
                valve_target = _find_nearest(tgt_node, valves.values())
            if valve_target:
                edge_id_counter += 1
                new_edges.append(PidEdge(
                    id=str(edge_id_counter),
                    source_id=ctrl_id,
                    target_id=valve_target.id,
                    label="",
                    dexpi_class="SignalLine",
                    dexpi_component_class="SIGL",
                    category=DexpiCategory.SIGNAL_LINE,
                    attributes={
                        "signal_type": "4-20mA",
                        "instrument_tag": tgt_node.tag_number or "",
                        "auto_connected": "true",
                    },
                    style="strokeColor=#FF0000;strokeWidth=1.5;dashed=1;endArrow=block;endFill=1;",
                ))

    model.edges.extend(new_edges)
    return model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NUMBER_RE = re.compile(r"(\d{2,})")


def _extract_number(tag: str) -> str | None:
    """Extract the numeric equipment/loop number from a tag. TIC-101 → '101'."""
    m = _NUMBER_RE.search(tag)
    return m.group(1) if m else None


def _isa_prefix(tag: str) -> str | None:
    """Extract the ISA letter prefix. TIC-101 → 'T', FCV-200 → 'F'."""
    m = re.match(r"([A-Z])", tag)
    return m.group(1) if m else None


def _build_number_index(nodes: ...) -> dict[str, PidNode]:
    """Build a dict mapping equipment number → node. '101' → node(P-101)."""
    index: dict[str, list[PidNode]] = defaultdict(list)
    for n in nodes:
        num = _extract_number(n.tag_number or "")
        if num:
            index[num].append(n)
    # Return first match per number (equipment takes priority)
    return {num: nodes[0] for num, nodes in index.items()}


def _find_by_number(
    number: str | None,
    index: dict[str, PidNode],
    exclude: str | None = None,
) -> PidNode | None:
    """Find a node by equipment number."""
    if not number:
        return None
    node = index.get(number)
    if node and (exclude is None or node.id != exclude):
        return node
    return None


def _find_nearest(
    source: PidNode,
    candidates: ...,
) -> PidNode | None:
    """Find the nearest candidate node by coordinate distance."""
    sp = source.position
    if not sp or sp.x is None:
        return None

    best_node = None
    best_dist = float("inf")
    sx, sy = sp.x, sp.y or 0

    for cand in candidates:
        cp = cand.position
        if not cp or cp.x is None:
            continue
        d = math.sqrt((sx - cp.x) ** 2 + (sy - (cp.y or 0)) ** 2)
        if d < best_dist:
            best_dist = d
            best_node = cand

    return best_node


def _max_numeric_id(model: PidModel) -> int:
    """Find the highest numeric ID in the model."""
    max_id = 0
    for n in model.nodes:
        try:
            max_id = max(max_id, int(n.id))
        except ValueError:
            pass
    for e in model.edges:
        try:
            max_id = max(max_id, int(e.id))
        except ValueError:
            pass
    return max_id
