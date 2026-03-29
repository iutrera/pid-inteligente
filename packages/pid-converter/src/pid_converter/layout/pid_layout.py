"""Auto-layout algorithm for P&ID diagrams.

Uses graph-based layout algorithms (NetworkX) to handle complex P&IDs
with 50+ equipment, branching, parallel paths, and recycles.
"""

from __future__ import annotations

import math
from collections import defaultdict

import networkx as nx

from pid_converter.models import PidModel, PidNode, Position, DexpiCategory


CANVAS_WIDTH = 1500
CANVAS_HEIGHT = 1000
MARGIN = 120
MIN_NODE_DISTANCE = 100

SIZES: dict[str, tuple[int, int]] = {
    "vessel": (100, 180), "tank": (100, 180), "silo": (80, 160),
    "column": (80, 240), "tower": (80, 240), "reactor": (100, 160),
    "exchanger": (130, 100), "heater": (100, 100), "cooler": (100, 100),
    "pump": (70, 70), "compressor": (80, 80), "blower": (70, 70),
    "fan": (70, 70), "ejector": (90, 60), "valve": (50, 50),
    "instrument": (45, 45), "nozzle": (12, 12),
    "default_equipment": (90, 90), "default": (60, 60),
}


def _pos(n: PidNode) -> Position:
    """Get or create a Position for a node."""
    if n.position is None:
        n.position = Position(x=0, y=0, width=60, height=60)
    return n.position


def _get_size(dexpi_class: str | None) -> tuple[int, int]:
    if not dexpi_class:
        return SIZES["default"]
    dc = dexpi_class.lower()
    for key, size in SIZES.items():
        if key in dc:
            return size
    return SIZES["default_equipment"]


def layout_pid(model: PidModel) -> PidModel:
    """Compute proper coordinates for all nodes in a PidModel."""
    if not model.nodes:
        return model

    node_map = {n.id: n for n in model.nodes}

    # --- Classify ---
    equipment_ids: set[str] = set()
    valve_ids: set[str] = set()
    instrument_ids: set[str] = set()
    nozzle_ids: set[str] = set()
    other_ids: set[str] = set()

    for n in model.nodes:
        cat = n.category
        dc = (n.dexpi_class or "").lower()
        if cat == DexpiCategory.EQUIPMENT:
            equipment_ids.add(n.id)
        elif cat == DexpiCategory.NOZZLE:
            nozzle_ids.add(n.id)
        elif cat == DexpiCategory.PIPING_COMPONENT or "valve" in dc:
            valve_ids.add(n.id)
        elif cat == DexpiCategory.INSTRUMENT:
            instrument_ids.add(n.id)
        else:
            other_ids.add(n.id)

    # --- Build topology graph ---
    process_ids = equipment_ids | valve_ids | other_ids
    G = nx.Graph()
    for nid in process_ids:
        G.add_node(nid)

    for e in model.edges:
        src, tgt = e.source_id or "", e.target_id or ""
        if "signal" in (e.dexpi_class or "").lower():
            continue
        sp = _resolve_to_process(src, process_ids, nozzle_ids, model)
        tp = _resolve_to_process(tgt, process_ids, nozzle_ids, model)
        if sp and tp and sp != tp:
            G.add_edge(sp, tp)

    for nid in process_ids:
        if nid not in G:
            G.add_node(nid)

    if len(G.nodes) == 0:
        return model

    # --- Compute layout ---
    if len(G.nodes) == 1:
        positions = {list(G.nodes)[0]: (CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)}
    elif len(G.nodes) <= 3:
        positions = nx.spring_layout(G, k=3.0, iterations=100, seed=42)
    else:
        try:
            positions = nx.kamada_kawai_layout(G)
        except Exception:
            positions = nx.spring_layout(G, k=2.0 / math.sqrt(len(G.nodes)), iterations=200, seed=42)

    positions = _scale_to_canvas(positions)
    positions = _resolve_overlaps(positions)

    # --- Apply to process nodes ---
    for nid, (cx, cy) in positions.items():
        node = node_map.get(nid)
        if not node:
            continue
        w, h = _get_size(node.dexpi_class)
        p = _pos(node)
        p.x = cx - w / 2
        p.y = cy - h / 2
        p.width = w
        p.height = h

    # --- Instruments ---
    _layout_instruments(instrument_ids, model, node_map, positions, equipment_ids, valve_ids)

    # --- Nozzles ---
    _layout_nozzles(nozzle_ids, model, node_map, equipment_ids)

    return model


def _scale_to_canvas(positions: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    if not positions:
        return positions
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    rx = (max(xs) - min(xs)) or 1
    ry = (max(ys) - min(ys)) or 1
    uw = CANVAS_WIDTH - 2 * MARGIN
    uh = CANVAS_HEIGHT - 2 * MARGIN
    return {
        nid: (MARGIN + (x - min(xs)) / rx * uw, MARGIN + (y - min(ys)) / ry * uh)
        for nid, (x, y) in positions.items()
    }


def _resolve_overlaps(positions: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    ids = list(positions.keys())
    pos = dict(positions)
    for _ in range(50):
        moved = False
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                ax, ay = pos[ids[i]]
                bx, by = pos[ids[j]]
                dx, dy = bx - ax, by - ay
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < MIN_NODE_DISTANCE:
                    if dist < 1:
                        dx, dy, dist = 1, 0, 1
                    push = (MIN_NODE_DISTANCE - dist) / 2 + 5
                    ux, uy = dx / dist * push, dy / dist * push
                    pos[ids[i]] = (ax - ux, ay - uy)
                    pos[ids[j]] = (bx + ux, by + uy)
                    moved = True
        if not moved:
            break
    return pos


def _layout_instruments(
    instrument_ids: set[str], model: PidModel, node_map: dict,
    process_positions: dict[str, tuple[float, float]],
    equipment_ids: set[str], valve_ids: set[str],
) -> None:
    inst_to_eq: dict[str, str] = {}
    for e in model.edges:
        if "signal" not in (e.dexpi_class or "").lower():
            continue
        src, tgt = e.source_id or "", e.target_id or ""
        inst_id = src if src in instrument_ids else tgt if tgt in instrument_ids else None
        other_id = tgt if inst_id == src else src
        if not inst_id:
            continue
        if other_id in equipment_ids or other_id in valve_ids:
            inst_to_eq[inst_id] = other_id
        elif inst_id not in inst_to_eq:
            for e2 in model.edges:
                if "signal" in (e2.dexpi_class or "").lower():
                    continue
                if e2.source_id == other_id and (e2.target_id or "") in equipment_ids:
                    inst_to_eq[inst_id] = e2.target_id  # type: ignore[assignment]
                    break
                if e2.target_id == other_id and (e2.source_id or "") in equipment_ids:
                    inst_to_eq[inst_id] = e2.source_id  # type: ignore[assignment]
                    break

    eq_count: dict[str, int] = defaultdict(int)
    for inst_id in instrument_ids:
        node = node_map.get(inst_id)
        if not node:
            continue
        w, h = _get_size("instrument")
        p = _pos(node)
        eq_id = inst_to_eq.get(inst_id)
        if eq_id and eq_id in process_positions:
            ecx, ecy = process_positions[eq_id]
            c = eq_count[eq_id]
            p.x = ecx + (c - 1) * 70 - w / 2
            p.y = ecy - 140 - h / 2
            eq_count[eq_id] = c + 1
        else:
            idx = list(instrument_ids).index(inst_id)
            p.x = MARGIN + idx * 80
            p.y = MARGIN / 2
        p.width = w
        p.height = h


def _layout_nozzles(
    nozzle_ids: set[str], model: PidModel, node_map: dict, equipment_ids: set[str],
) -> None:
    nozzle_per_eq: dict[str, list[str]] = defaultdict(list)
    for nz_id in nozzle_ids:
        parent_eq = None
        nz = node_map.get(nz_id)
        if not nz:
            continue
        for e in model.edges:
            s, t = e.source_id or "", e.target_id or ""
            if s == nz_id and t in equipment_ids:
                parent_eq = t; break
            if t == nz_id and s in equipment_ids:
                parent_eq = s; break
        if not parent_eq and nz.position:
            best_d = float("inf")
            for eq_id in equipment_ids:
                eq = node_map.get(eq_id)
                ep = eq.position if eq else None
                if ep and ep.x is not None:
                    nzp = nz.position
                    d = math.sqrt(((nzp.x or 0) - ep.x) ** 2 + ((nzp.y or 0) - ep.y) ** 2)
                    if d < best_d:
                        best_d = d; parent_eq = eq_id
        if parent_eq:
            nozzle_per_eq[parent_eq].append(nz_id)

    for eq_id, nz_list in nozzle_per_eq.items():
        eq = node_map.get(eq_id)
        ep = eq.position if eq else None
        if not ep or ep.x is None:
            continue
        for i, nz_id in enumerate(nz_list):
            nz = node_map.get(nz_id)
            if not nz:
                continue
            p = _pos(nz)
            side = i % 4
            off = (i // 4) * 20
            if side == 0:
                p.x = ep.x + (ep.width or 90) - 6; p.y = ep.y + (ep.height or 90) * 0.3 + off
            elif side == 1:
                p.x = ep.x - 6; p.y = ep.y + (ep.height or 90) * 0.3 + off
            elif side == 2:
                p.x = ep.x + (ep.width or 90) * 0.3 + off; p.y = ep.y + (ep.height or 90) - 6
            else:
                p.x = ep.x + (ep.width or 90) * 0.3 + off; p.y = ep.y - 6
            p.width = 12; p.height = 12


def _resolve_to_process(
    node_id: str, process_ids: set[str], nozzle_ids: set[str], model: PidModel,
) -> str | None:
    if node_id in process_ids:
        return node_id
    if node_id in nozzle_ids:
        for e in model.edges:
            if e.source_id == node_id and (e.target_id or "") in process_ids:
                return e.target_id
            if e.target_id == node_id and (e.source_id or "") in process_ids:
                return e.source_id
    return None
