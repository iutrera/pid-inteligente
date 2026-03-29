"""Import DEXPI Proteus XML and generate a Draw.io (.drawio) file.

This is the reverse path of the parser + mapper + serializer pipeline.
It reads a Proteus XML document using pyDEXPI's ``ProteusSerializer`` when
possible, and falls back to direct lxml parsing for raw XML strings or
files that pyDEXPI cannot load.  The DEXPI content is then converted into a
valid ``.drawio`` (mxGraph XML) file that can be opened in Draw.io.

For XML *strings* (as opposed to file paths) the importer still uses lxml
directly because pyDEXPI's ProteusSerializer only accepts file paths.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from pid_converter.models import Position

# DEXPI namespace -- tolerant of files with or without namespace
PROTEUS_NS = "http://www.dexpi.org/schemas/Proteus"


# ---------------------------------------------------------------------------
# Style mappings: dexpi_class -> Draw.io style string
# ---------------------------------------------------------------------------

_EQUIPMENT_STYLES: dict[str, str] = {
    "CentrifugalPump": (
        "shape=ellipse;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "fontSize=11;fontStyle=1;"
    ),
    "PositiveDisplacementPump": (
        "shape=ellipse;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "fontSize=11;fontStyle=1;"
    ),
    "VerticalVessel": (
        "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "rounded=1;arcSize=50;fontSize=11;fontStyle=1;"
    ),
    "HorizontalVessel": (
        "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "rounded=1;arcSize=50;fontSize=11;fontStyle=1;"
    ),
    "ShellTubeHeatExchanger": (
        "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "rounded=1;arcSize=30;fontSize=11;fontStyle=1;"
    ),
    # Also accept pyDEXPI class names:
    "Vessel": (
        "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "rounded=1;arcSize=50;fontSize=11;fontStyle=1;"
    ),
    "TubularHeatExchanger": (
        "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "rounded=1;arcSize=30;fontSize=11;fontStyle=1;"
    ),
    "Pump": (
        "shape=ellipse;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "fontSize=11;fontStyle=1;"
    ),
}

_DEFAULT_EQUIPMENT_STYLE = (
    "shape=rectangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
    "rounded=1;arcSize=20;fontSize=11;fontStyle=1;"
)

_NOZZLE_STYLE = (
    "shape=ellipse;whiteSpace=wrap;fillColor=#000000;strokeColor=#000000;strokeWidth=2;"
)

_INSTRUMENT_STYLE = (
    "shape=ellipse;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
    "fontSize=9;fontStyle=1;"
)

_PROCESS_LINE_STYLE = (
    "endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;endSize=8;"
    "fontSize=8;labelPosition=center;verticalLabelPosition=top;"
    "align=center;verticalAlign=bottom;"
)

_SIGNAL_LINE_STYLE = (
    "endArrow=block;strokeColor=#000000;strokeWidth=1;dashed=1;dashPattern=8 4;"
    "endFill=1;endSize=6;"
)

_PIPING_COMPONENT_STYLES: dict[str, str] = {
    "ControlValve": (
        "shape=triangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;"
        "strokeWidth=2;direction=east;"
    ),
    "OperatedValve": (
        "shape=triangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;"
        "strokeWidth=2;direction=east;"
    ),
    "SteamTrap": (
        "shape=rhombus;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
    ),
}

_DEFAULT_COMPONENT_STYLE = (
    "shape=triangle;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
)


# ---------------------------------------------------------------------------
# XML helpers (namespace-tolerant find)
# ---------------------------------------------------------------------------

def _find_all(parent: etree._Element, tag: str) -> list[etree._Element]:
    """Find all child elements matching *tag* with or without namespace."""
    # Try with namespace first
    results = parent.findall(f"{{{PROTEUS_NS}}}{tag}")
    if not results:
        results = parent.findall(tag)
    return results


def _find(parent: etree._Element, tag: str) -> etree._Element | None:
    el = parent.find(f"{{{PROTEUS_NS}}}{tag}")
    if el is None:
        el = parent.find(tag)
    return el


def _get_position(elem: etree._Element) -> Position:
    """Extract position from ``<Position>`` or ``<Extent>`` child."""
    pos_el = _find(elem, "Position")
    if pos_el is not None:
        loc = pos_el.get("Location", "0,0")
        parts = loc.split(",")
        x = float(parts[0]) if len(parts) > 0 else 0
        y = float(parts[1]) if len(parts) > 1 else 0
        w = float(pos_el.get("Width", "60"))
        h = float(pos_el.get("Height", "60"))
        return Position(x=x, y=y, width=w, height=h)

    ext = _find(elem, "Extent")
    if ext is not None:
        mn = _find(ext, "Min")
        mx = _find(ext, "Max")
        if mn is not None and mx is not None:
            x1 = float(mn.get("X", "0"))
            y1 = float(mn.get("Y", "0"))
            x2 = float(mx.get("X", "0"))
            y2 = float(mx.get("Y", "0"))
            return Position(x=x1, y=y1, width=x2 - x1, height=y2 - y1)

    return Position(x=0, y=0, width=60, height=60)


def _get_generic_attrs(elem: etree._Element) -> dict[str, str]:
    """Read ``<GenericAttribute>`` children into a dict."""
    attrs: dict[str, str] = {}
    for ga in _find_all(elem, "GenericAttribute"):
        name = ga.get("Name", "")
        value = ga.get("Value", "")
        if name:
            attrs[name] = value
    return attrs


# ---------------------------------------------------------------------------
# ID counter
# ---------------------------------------------------------------------------

class _IdGen:
    """Simple integer ID generator for mxCell IDs."""

    def __init__(self, start: int = 10) -> None:
        self._next = start

    def __call__(self) -> str:
        val = self._next
        self._next += 1
        return str(val)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def import_dexpi(source: str | Path, output: str | Path | None = None) -> str:
    """Read a Proteus XML file and produce a ``.drawio`` XML string.

    Parameters
    ----------
    source:
        Path to a Proteus XML file **or** a raw XML string.
    output:
        Optional path to write the resulting ``.drawio`` file.

    Returns
    -------
    str
        The Draw.io mxGraph XML as a Unicode string.
    """
    source_path = Path(source) if not isinstance(source, str) or "\n" not in source else None

    if source_path is not None and source_path.exists():
        tree = etree.parse(str(source_path))  # noqa: S320
        proteus_root = tree.getroot()
    else:
        proteus_root = etree.fromstring(  # noqa: S320
            source.encode() if isinstance(source, str) else source
        )

    idgen = _IdGen(start=10)

    # Build the Draw.io document skeleton
    mxfile = etree.Element("mxfile")
    mxfile.set("host", "pid-converter")
    mxfile.set("type", "device")
    diagram = etree.SubElement(mxfile, "diagram")
    diagram.set("id", "imported-pid")
    diagram.set("name", "Imported P&ID")
    graph_model = etree.SubElement(diagram, "mxGraphModel")
    graph_model.set("dx", "1422")
    graph_model.set("dy", "762")
    graph_model.set("grid", "1")
    graph_model.set("gridSize", "10")
    graph_model.set("guides", "1")
    graph_model.set("tooltips", "1")
    graph_model.set("connect", "1")
    graph_model.set("arrows", "1")
    graph_model.set("fold", "1")
    graph_model.set("page", "1")
    graph_model.set("pageScale", "1")
    graph_model.set("pageWidth", "1654")
    graph_model.set("pageHeight", "1169")
    root = etree.SubElement(graph_model, "root")

    # Layer 0 (mxGraph internal root)
    cell0 = etree.SubElement(root, "mxCell")
    cell0.set("id", "0")

    # Layer 1: Process
    cell1 = etree.SubElement(root, "mxCell")
    cell1.set("id", "1")
    cell1.set("value", "Process")
    cell1.set("parent", "0")

    # Layer 2: Instrumentation
    cell2 = etree.SubElement(root, "mxCell")
    cell2.set("id", "2")
    cell2.set("value", "Instrumentation")
    cell2.set("parent", "0")

    # Layer 3: Annotations
    cell3 = etree.SubElement(root, "mxCell")
    cell3.set("id", "3")
    cell3.set("value", "Annotations")
    cell3.set("parent", "0")

    # --- Equipment ---
    for eq_el in _find_all(proteus_root, "Equipment"):
        _import_equipment(eq_el, root, idgen)

    # --- PipingNetworkSystem ---
    for pns in _find_all(proteus_root, "PipingNetworkSystem"):
        for seg in _find_all(pns, "PipingNetworkSegment"):
            _import_piping_segment(seg, root, idgen)
        for comp in _find_all(pns, "PipingComponent"):
            _import_piping_component(comp, root, idgen)

    # --- Instrumentation ---
    for ilf in _find_all(proteus_root, "InstrumentationLoopFunction"):
        for ic in _find_all(ilf, "InstrumentComponent"):
            _import_instrument(ic, root, idgen)

    # --- Signal Lines ---
    for sl in _find_all(proteus_root, "SignalLine"):
        _import_signal_line(sl, root, idgen)

    xml_bytes = etree.tostring(
        mxfile,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    xml_str = xml_bytes.decode("utf-8")

    if output is not None:
        Path(output).write_text(xml_str, encoding="utf-8")

    return xml_str


# ---------------------------------------------------------------------------
# Element importers
# ---------------------------------------------------------------------------

def _import_equipment(
    eq_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    eq_id = eq_el.get("ID", idgen())
    tag = eq_el.get("TagNumber", "")
    dexpi_class = eq_el.get("DexpiClass", "")
    comp_class = eq_el.get("ComponentClass", "")
    pos = _get_position(eq_el)
    attrs = _get_generic_attrs(eq_el)

    style = _EQUIPMENT_STYLES.get(dexpi_class, _DEFAULT_EQUIPMENT_STYLE)

    obj = etree.SubElement(root, "object")
    obj.set("label", tag)
    obj.set("dexpi_class", dexpi_class)
    obj.set("dexpi_component_class", comp_class)
    obj.set("tag_number", tag)
    obj.set("id", eq_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", style)
    cell.set("vertex", "1")
    cell.set("parent", "1")
    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("x", str(pos.x))
    geo.set("y", str(pos.y))
    geo.set("width", str(pos.width))
    geo.set("height", str(pos.height))
    geo.set("as", "geometry")

    # Nozzles
    for noz_el in _find_all(eq_el, "Nozzle"):
        _import_nozzle(noz_el, root, idgen)


def _import_nozzle(
    noz_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    noz_id = noz_el.get("ID", idgen())
    nozzle_tag = noz_el.get("NozzleID", "")
    pos = _get_position(noz_el)
    attrs = _get_generic_attrs(noz_el)

    obj = etree.SubElement(root, "object")
    obj.set("label", "")
    obj.set("dexpi_class", "Nozzle")
    obj.set("dexpi_component_class", "NOZL")
    obj.set("nozzle_id", nozzle_tag)
    obj.set("id", noz_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", _NOZZLE_STYLE)
    cell.set("vertex", "1")
    cell.set("parent", "1")
    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("x", str(pos.x))
    geo.set("y", str(pos.y))
    geo.set("width", str(pos.width))
    geo.set("height", str(pos.height))
    geo.set("as", "geometry")


def _import_piping_segment(
    seg_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    seg_id = seg_el.get("ID", idgen())
    line_number = seg_el.get("LineNumber", "")
    nominal_dia = seg_el.get("NominalDiameter", "")
    fluid_code = seg_el.get("FluidCode", "")
    material = seg_el.get("MaterialSpec", "")
    insulation = seg_el.get("Insulation", "")
    attrs = _get_generic_attrs(seg_el)

    # Label like "3\"-PL-101-SS316L"
    label = f'{nominal_dia}-{line_number}-{material}'.strip("- ")

    # Find connection points
    source_pt = _find_connection_point(seg_el, "Source")
    target_pt = _find_connection_point(seg_el, "Target")

    obj = etree.SubElement(root, "object")
    obj.set("label", label)
    obj.set("dexpi_class", "ProcessLine")
    obj.set("dexpi_component_class", "PRCL")
    obj.set("line_number", line_number)
    obj.set("nominal_diameter", nominal_dia)
    obj.set("fluid_code", fluid_code)
    obj.set("material_spec", material)
    obj.set("insulation", insulation)
    obj.set("id", seg_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", _PROCESS_LINE_STYLE)
    cell.set("edge", "1")
    cell.set("parent", "1")

    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("relative", "1")
    geo.set("as", "geometry")

    if source_pt:
        sp = etree.SubElement(geo, "mxPoint")
        sp.set("x", str(source_pt[0]))
        sp.set("y", str(source_pt[1]))
        sp.set("as", "sourcePoint")
    if target_pt:
        tp = etree.SubElement(geo, "mxPoint")
        tp.set("x", str(target_pt[0]))
        tp.set("y", str(target_pt[1]))
        tp.set("as", "targetPoint")


def _find_connection_point(
    seg_el: etree._Element, point_type: str
) -> tuple[float, float] | None:
    """Find a ``<ConnectionPoint>`` child with the given Type."""
    for cp in _find_all(seg_el, "ConnectionPoint"):
        if cp.get("Type") == point_type:
            return float(cp.get("X", "0")), float(cp.get("Y", "0"))
    return None


def _import_piping_component(
    comp_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    comp_id = comp_el.get("ID", idgen())
    tag = comp_el.get("TagNumber", "")
    dexpi_class = comp_el.get("DexpiClass", "")
    comp_class = comp_el.get("ComponentClass", "")
    pos = _get_position(comp_el)
    attrs = _get_generic_attrs(comp_el)

    style = _PIPING_COMPONENT_STYLES.get(dexpi_class, _DEFAULT_COMPONENT_STYLE)

    obj = etree.SubElement(root, "object")
    obj.set("label", tag)
    obj.set("dexpi_class", dexpi_class)
    obj.set("dexpi_component_class", comp_class)
    obj.set("tag_number", tag)
    obj.set("id", comp_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", style)
    cell.set("vertex", "1")
    cell.set("parent", "1")
    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("x", str(pos.x))
    geo.set("y", str(pos.y))
    geo.set("width", str(pos.width))
    geo.set("height", str(pos.height))
    geo.set("as", "geometry")


def _import_instrument(
    inst_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    inst_id = inst_el.get("ID", idgen())
    tag = inst_el.get("TagNumber", "")
    dexpi_class = inst_el.get("DexpiClass", "")
    comp_class = inst_el.get("ComponentClass", "")
    measured_var = inst_el.get("MeasuredVariable", "")
    function = inst_el.get("Function", "")
    signal_type = inst_el.get("SignalType", "")
    pos = _get_position(inst_el)
    attrs = _get_generic_attrs(inst_el)

    # Label like "TT\n101"
    label_prefix = comp_class or dexpi_class[:2] if dexpi_class else ""
    label = f"{label_prefix}<br>{tag}" if tag else label_prefix

    obj = etree.SubElement(root, "object")
    obj.set("label", label)
    obj.set("dexpi_class", dexpi_class)
    obj.set("dexpi_component_class", comp_class)
    obj.set("tag_number", tag)
    obj.set("measured_variable", measured_var)
    obj.set("function", function)
    obj.set("signal_type", signal_type)
    obj.set("id", inst_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", _INSTRUMENT_STYLE)
    cell.set("vertex", "1")
    cell.set("parent", "2")  # Instrumentation layer
    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("x", str(pos.x))
    geo.set("y", str(pos.y))
    geo.set("width", str(pos.width))
    geo.set("height", str(pos.height))
    geo.set("as", "geometry")


def _import_signal_line(
    sl_el: etree._Element,
    root: etree._Element,
    idgen: _IdGen,
) -> None:
    sl_id = sl_el.get("ID", idgen())
    signal_type = sl_el.get("SignalType", "")
    attrs = _get_generic_attrs(sl_el)

    obj = etree.SubElement(root, "object")
    obj.set("label", "")
    obj.set("dexpi_class", "SignalLine")
    obj.set("dexpi_component_class", "SIGL")
    obj.set("signal_type", signal_type)
    obj.set("id", sl_id)
    for k, v in attrs.items():
        obj.set(k, v)

    cell = etree.SubElement(obj, "mxCell")
    cell.set("style", _SIGNAL_LINE_STYLE)
    cell.set("edge", "1")
    cell.set("parent", "2")  # Instrumentation layer
    geo = etree.SubElement(cell, "mxGeometry")
    geo.set("relative", "1")
    geo.set("as", "geometry")
