"""Parser for Draw.io mxGraph XML (.drawio) files.

Extracts ``<object>`` elements with their custom DEXPI attributes and
``<mxCell>`` edges with their source/target topology to produce a
:class:`~pid_converter.models.PidModel`.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from pid_converter.classification import classify
from pid_converter.models import (
    DexpiCategory,
    PidEdge,
    PidModel,
    PidNode,
    Position,
)

# Attributes that are part of the mxGraph DOM, not DEXPI custom properties.
_MXGRAPH_ATTRS = frozenset({
    "id", "label", "parent", "vertex", "edge", "source", "target",
    "style", "value", "connectable",
})


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _parse_geometry(cell: etree._Element) -> Position:
    """Extract position/size from the ``<mxGeometry>`` child."""
    geo = cell.find(".//mxGeometry")
    if geo is None:
        return Position()
    return Position(
        x=float(geo.get("x", "0")),
        y=float(geo.get("y", "0")),
        width=float(geo.get("width", "0")),
        height=float(geo.get("height", "0")),
    )


def _parse_edge_points(cell: etree._Element) -> tuple[Position | None, Position | None, list[Position]]:
    """Extract source point, target point and intermediate waypoints from an edge cell."""
    geo = cell.find(".//mxGeometry")
    source_pt: Position | None = None
    target_pt: Position | None = None
    waypoints: list[Position] = []

    if geo is None:
        return source_pt, target_pt, waypoints

    for child in geo:
        tag = child.tag
        if tag == "mxPoint":
            as_attr = child.get("as", "")
            pt = Position(
                x=float(child.get("x", "0")),
                y=float(child.get("y", "0")),
            )
            if as_attr == "sourcePoint":
                source_pt = pt
            elif as_attr == "targetPoint":
                target_pt = pt
        elif tag == "Array":
            # Intermediate waypoints
            for mp in child.findall("mxPoint"):
                waypoints.append(Position(
                    x=float(mp.get("x", "0")),
                    y=float(mp.get("y", "0")),
                ))
    return source_pt, target_pt, waypoints


# ---------------------------------------------------------------------------
# Custom attribute extraction
# ---------------------------------------------------------------------------

def _extract_custom_attrs(elem: etree._Element) -> dict[str, str]:
    """Return non-mxGraph attributes as a plain dict."""
    return {
        k: v
        for k, v in elem.attrib.items()
        if k not in _MXGRAPH_ATTRS
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_drawio(source: str | Path) -> PidModel:
    """Parse a ``.drawio`` file and return a :class:`PidModel`.

    Parameters
    ----------
    source:
        Path to a ``.drawio`` file **or** a string containing the XML directly.

    Returns
    -------
    PidModel
        Intermediate model with nodes, edges, and raw metadata.
    """
    source_path = Path(source) if not isinstance(source, str) or "\n" not in source else None

    if source_path is not None and source_path.exists():
        tree = etree.parse(str(source_path))  # noqa: S320
        root = tree.getroot()
    else:
        # Treat source as raw XML string
        root = etree.fromstring(source.encode() if isinstance(source, str) else source)  # noqa: S320

    nodes: list[PidNode] = []
    edges: list[PidEdge] = []
    metadata: dict[str, str] = {}

    # Navigate to the <root> element inside <mxGraphModel>
    # Structure: <mxfile><diagram><mxGraphModel><root>...
    root_elem = root.find(".//root")
    if root_elem is None:
        # Maybe the root *is* the mxGraphModel
        root_elem = root.find(".//mxGraphModel/root")
    if root_elem is None:
        # Last resort: assume `root` itself contains the cells
        root_elem = root

    # Build a lookup of cell id -> parent id for layer resolution
    cell_parents: dict[str, str] = {}
    for cell in root_elem.iter("mxCell"):
        cid = cell.get("id", "")
        parent = cell.get("parent", "")
        if cid and parent:
            cell_parents[cid] = parent

    # Process all children of <root>
    for elem in root_elem:
        tag = elem.tag

        if tag == "object":
            _process_object(elem, nodes, edges, cell_parents)
        elif tag == "mxCell":
            _process_mxcell(elem, nodes, edges, cell_parents)

    # Extract diagram-level metadata
    diagram = root.find(".//diagram")
    if diagram is not None:
        metadata["diagram_name"] = diagram.get("name", "")
        metadata["diagram_id"] = diagram.get("id", "")

    return PidModel(nodes=nodes, edges=edges, metadata=metadata)


# ---------------------------------------------------------------------------
# Internal processors
# ---------------------------------------------------------------------------

def _process_object(
    obj: etree._Element,
    nodes: list[PidNode],
    edges: list[PidEdge],
    cell_parents: dict[str, str],
) -> None:
    """Process an ``<object>`` element which wraps an ``<mxCell>``."""
    obj_id = obj.get("id", "")
    label = obj.get("label", "")
    dexpi_class = obj.get("dexpi_class", "")
    dexpi_cc = obj.get("dexpi_component_class", "")
    custom_attrs = _extract_custom_attrs(obj)

    # The inner <mxCell> carries the visual style and geometry
    inner_cell = obj.find("mxCell")
    if inner_cell is None:
        return

    style = inner_cell.get("style", "")
    is_edge = inner_cell.get("edge") == "1"
    parent_layer = inner_cell.get("parent", "")

    # Also register in cell_parents
    cell_parents[obj_id] = parent_layer

    if is_edge:
        source_pt, target_pt, waypoints = _parse_edge_points(inner_cell)
        edge = PidEdge(
            id=obj_id,
            label=label,
            dexpi_class=dexpi_class,
            dexpi_component_class=dexpi_cc,
            source_id=inner_cell.get("source", ""),
            target_id=inner_cell.get("target", ""),
            source_point=source_pt,
            target_point=target_pt,
            waypoints=waypoints,
            attributes=custom_attrs,
            parent_layer=parent_layer,
            style=style,
        )
        edges.append(edge)
    else:
        category = classify(dexpi_class)
        tag = custom_attrs.get("tag_number", "")
        node = PidNode(
            id=obj_id,
            label=label,
            dexpi_class=dexpi_class,
            dexpi_component_class=dexpi_cc,
            category=category,
            tag_number=tag,
            attributes=custom_attrs,
            position=_parse_geometry(inner_cell),
            parent_layer=parent_layer,
            style=style,
        )
        nodes.append(node)


def _process_mxcell(
    cell: etree._Element,
    nodes: list[PidNode],
    edges: list[PidEdge],
    cell_parents: dict[str, str],
) -> None:
    """Process a bare ``<mxCell>`` (not wrapped in ``<object>``)."""
    cell_id = cell.get("id", "")
    parent = cell.get("parent", "")

    # Skip the root cells (id 0, 1, 2, 3 are usually layer definitions)
    if cell_id in {"0"}:
        return

    is_edge = cell.get("edge") == "1"
    is_vertex = cell.get("vertex") == "1"
    style = cell.get("style", "")
    value = cell.get("value", "")

    cell_parents[cell_id] = parent

    if is_edge:
        source_pt, target_pt, waypoints = _parse_edge_points(cell)
        edge = PidEdge(
            id=cell_id,
            label=value,
            source_id=cell.get("source", ""),
            target_id=cell.get("target", ""),
            source_point=source_pt,
            target_point=target_pt,
            waypoints=waypoints,
            parent_layer=parent,
            style=style,
        )
        edges.append(edge)
    elif is_vertex and value:
        # Bare vertex with a value but no dexpi_class -- treat as annotation / decoration
        node = PidNode(
            id=cell_id,
            label=value,
            category=DexpiCategory.UNKNOWN,
            position=_parse_geometry(cell),
            parent_layer=parent,
            style=style,
        )
        nodes.append(node)
