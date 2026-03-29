"""Serialize a pyDEXPI ``DexpiModel`` to DEXPI Proteus XML.

Produces an XML document conforming (in simplified form) to the DEXPI / Proteus
schema.  The output includes:

* ``<PlantModel>`` root with metadata
* ``<Equipment>`` elements with ``<Nozzle>`` children
* ``<PipingNetworkSystem>`` containing ``<PipingNetworkSegment>`` elements
* ``<InstrumentationLoopFunction>`` with instrument references
* ``<Drawing>`` / ``<ShapeCatalogue>`` with graphic coordinates

.. note::

   ``pyDEXPI``'s own ``ProteusSerializer.save()`` is not yet implemented
   (raises ``NotImplementedError``), so we keep our own lxml-based writer
   that reads from the canonical pyDEXPI model objects.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from pydexpi.dexpi_classes.dexpiModel import DexpiModel
from pydexpi.dexpi_classes.instrumentation import SignalLineFunction
from pydexpi.dexpi_classes.piping import PipingComponent
from pydexpi.dexpi_classes.pydantic_classes import CustomAttribute

from pid_converter.mapper.dexpi_mapper import (
    get_equipment,
    get_instruments,
    get_piping_components,
)

# DEXPI / Proteus namespaces (simplified)
PROTEUS_NS = "http://www.dexpi.org/schemas/Proteus"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
NSMAP = {
    None: PROTEUS_NS,
    "xsi": XSI_NS,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_generic_attrs(
    elem: etree._Element,
    custom_attrs: list[CustomAttribute],
) -> None:
    """Append ``<GenericAttribute>`` children for each CustomAttribute."""
    for ca in sorted(custom_attrs, key=lambda a: a.attributeName):
        ga = etree.SubElement(elem, "GenericAttribute")
        ga.set("Name", ca.attributeName)
        ga.set("Value", str(ca.value))
        ga.set("Format", "string")


def _add_extent(
    parent: etree._Element,
    x: float = 0,
    y: float = 0,
    w: float = 60,
    h: float = 60,
) -> None:
    """Add ``<Extent>`` with ``<Min>``/``<Max>`` coordinate children."""
    ext = etree.SubElement(parent, "Extent")
    mn = etree.SubElement(ext, "Min")
    mn.set("X", str(x))
    mn.set("Y", str(y))
    mx = etree.SubElement(ext, "Max")
    mx.set("X", str(x + w))
    mx.set("Y", str(y + h))


def _add_position(
    parent: etree._Element,
    x: float = 0,
    y: float = 0,
    w: float = 60,
    h: float = 60,
) -> None:
    """Add a ``<Position>`` element with coordinate attributes."""
    p = etree.SubElement(parent, "Position")
    p.set("Location", f"{x},{y}")
    p.set("Width", str(w))
    p.set("Height", str(h))


def _dexpi_class_name(obj: object) -> str:
    """Return the DEXPI class name from a pyDEXPI object's type."""
    return type(obj).__name__


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_equipment_section(
    plant: etree._Element,
    dexpi: DexpiModel,
) -> None:
    for eq in get_equipment(dexpi):
        el = etree.SubElement(plant, "Equipment")
        el.set("ID", eq.id)
        el.set("TagNumber", eq.tagName or "")
        # Recover original dexpi_class and component_class from custom attrs
        ca_dict = {ca.attributeName: str(ca.value) for ca in eq.customAttributes}
        el.set("ComponentClass", ca_dict.get("_dexpi_component_class", ""))
        el.set("ComponentName", eq.tagName or "")
        el.set(
            "DexpiClass",
            ca_dict.get("_dexpi_class", _dexpi_class_name(eq)),
        )
        # Write custom attributes, excluding internal roundtrip markers
        public_attrs = [
            ca for ca in eq.customAttributes
            if not ca.attributeName.startswith("_dexpi_")
        ]
        _set_generic_attrs(el, public_attrs)
        _add_extent(el)

        # Child nozzles
        for noz in eq.nozzles:
            nz = etree.SubElement(el, "Nozzle")
            nz.set("ID", noz.id)
            nz.set("NozzleID", noz.subTagName or "")
            _set_generic_attrs(nz, noz.customAttributes)
            _add_position(nz)


def _build_piping_section(
    plant: etree._Element,
    dexpi: DexpiModel,
) -> None:
    cm = dexpi.conceptualModel
    if cm is None:
        return
    for pns_obj in cm.pipingNetworkSystems:
        pns = etree.SubElement(plant, "PipingNetworkSystem")
        pns.set("ID", pns_obj.id)

        for seg in pns_obj.segments:
            el = etree.SubElement(pns, "PipingNetworkSegment")
            el.set("ID", seg.id)
            el.set("LineNumber", seg.segmentNumber or "")
            el.set(
                "NominalDiameter",
                seg.nominalDiameterRepresentation or "",
            )
            el.set("FluidCode", seg.fluidCode or "")
            el.set("MaterialSpec", seg.pipingClassCode or "")
            el.set("Insulation", seg.insulationType or "")
            _set_generic_attrs(el, seg.customAttributes)

        # Piping components within segment items
        for seg in pns_obj.segments:
            for item in seg.items:
                if isinstance(item, PipingComponent):
                    el = etree.SubElement(pns, "PipingComponent")
                    el.set("ID", item.id)
                    tag = ""
                    if hasattr(item, "pipingComponentName"):
                        tag = item.pipingComponentName or ""
                    el.set("TagNumber", tag)
                    el.set("ComponentClass", "")
                    el.set("DexpiClass", _dexpi_class_name(item))
                    _set_generic_attrs(el, item.customAttributes)
                    _add_extent(el)


def _build_instrumentation_section(
    plant: etree._Element,
    dexpi: DexpiModel,
) -> None:
    cm = dexpi.conceptualModel
    if cm is None:
        return
    for ilf_obj in cm.instrumentationLoopFunctions:
        ilf = etree.SubElement(plant, "InstrumentationLoopFunction")
        ilf.set("ID", ilf_obj.id)
        ilf.set(
            "LoopName",
            ilf_obj.instrumentationLoopFunctionNumber or "",
        )

        for inst in ilf_obj.processInstrumentationFunctions:
            el = etree.SubElement(ilf, "InstrumentComponent")
            el.set("ID", inst.id)
            el.set(
                "TagNumber",
                inst.processInstrumentationFunctionNumber or "",
            )
            # Recover original dexpi_class and component_class from custom attrs
            ca_dict = {
                ca.attributeName: str(ca.value) for ca in inst.customAttributes
            }
            el.set("ComponentClass", ca_dict.get("_dexpi_component_class", ""))
            el.set(
                "DexpiClass",
                ca_dict.get("_dexpi_class", _dexpi_class_name(inst)),
            )
            el.set(
                "MeasuredVariable",
                inst.processInstrumentationFunctionCategory or "",
            )
            el.set(
                "Function",
                inst.processInstrumentationFunctions or "",
            )
            el.set("SignalType", inst.typicalInformation or "")
            public_attrs = [
                ca for ca in inst.customAttributes
                if not ca.attributeName.startswith("_dexpi_")
            ]
            _set_generic_attrs(el, public_attrs)
            _add_extent(el)

    # Signal lines (from signalConveyingFunctions within instruments)
    for inst in get_instruments(dexpi):
        for scf in inst.signalConveyingFunctions:
            if isinstance(scf, SignalLineFunction):
                el = etree.SubElement(plant, "SignalLine")
                el.set("ID", scf.id)
                signal_type = ""
                if scf.signalConveyingType is not None:
                    signal_type = str(scf.signalConveyingType)
                el.set("SignalType", signal_type)
                _set_generic_attrs(el, scf.customAttributes)


def _build_drawing_section(
    plant: etree._Element,
    dexpi: DexpiModel,
) -> None:
    """Add a ``<Drawing>`` section with position data for all elements."""
    drawing = etree.SubElement(plant, "Drawing")
    catalog = etree.SubElement(drawing, "ShapeCatalogue")

    # Equipment shapes
    for eq in get_equipment(dexpi):
        shape = etree.SubElement(catalog, "ShapeReference")
        shape.set("ID", f"Shape-{eq.id}")
        shape.set("RefID", eq.id)
        shape.set("Type", "Equipment")
        _add_position(shape)

    # Instrument shapes
    for inst in get_instruments(dexpi):
        shape = etree.SubElement(catalog, "ShapeReference")
        shape.set("ID", f"Shape-{inst.id}")
        shape.set("RefID", inst.id)
        shape.set("Type", "Instrument")
        _add_position(shape)

    # Piping component shapes
    for comp in get_piping_components(dexpi):
        shape = etree.SubElement(catalog, "ShapeReference")
        shape.set("ID", f"Shape-{comp.id}")
        shape.set("RefID", comp.id)
        shape.set("Type", "PipingComponent")
        _add_position(shape)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize_to_proteus(
    dexpi: DexpiModel,
    output: str | Path | None = None,
) -> str:
    """Generate Proteus XML from a pyDEXPI :class:`DexpiModel`.

    Parameters
    ----------
    dexpi:
        The pyDEXPI model to serialise.
    output:
        Optional file path.  When provided the XML is written to disk.

    Returns
    -------
    str
        The Proteus XML as a Unicode string.
    """
    root = etree.Element("PlantModel", nsmap=NSMAP)
    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        "http://www.dexpi.org/schemas/Proteus",
    )

    # Metadata
    meta = etree.SubElement(root, "PlantInformation")
    if dexpi.originatingSystemName:
        meta.set("OriginatingSystem", dexpi.originatingSystemName)

    _build_equipment_section(root, dexpi)
    _build_piping_section(root, dexpi)
    _build_instrumentation_section(root, dexpi)
    _build_drawing_section(root, dexpi)

    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    xml_str = xml_bytes.decode("utf-8")

    if output is not None:
        Path(output).write_text(xml_str, encoding="utf-8")

    return xml_str
