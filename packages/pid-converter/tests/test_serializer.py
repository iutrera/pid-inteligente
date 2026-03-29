"""Tests for the Proteus XML serializer."""

from __future__ import annotations

from lxml import etree
from pydexpi.dexpi_classes.dexpiModel import DexpiModel

from pid_converter.mapper import map_to_dexpi
from pid_converter.models import PidModel
from pid_converter.serializer import serialize_to_proteus


class TestSerializeToProteus:
    """Serialisation of the example P&ID to Proteus XML."""

    def test_returns_xml_string(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        assert isinstance(xml, str)
        assert xml.startswith("<?xml")

    def test_valid_xml(self, parsed_model: PidModel) -> None:
        """The output must be well-formed XML."""
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        assert root.tag.endswith("PlantModel")

    def test_contains_equipment(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        # Equipment elements (no namespace prefix in simplified output)
        equip = root.findall(".//{http://www.dexpi.org/schemas/Proteus}Equipment")
        if not equip:
            equip = root.findall(".//Equipment")
        assert len(equip) >= 3

    def test_contains_piping(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        ns = {"p": "http://www.dexpi.org/schemas/Proteus"}
        segs = root.findall(".//p:PipingNetworkSegment", ns)
        if not segs:
            segs = root.findall(".//PipingNetworkSegment")
        assert len(segs) >= 4

    def test_contains_instruments(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        ns = {"p": "http://www.dexpi.org/schemas/Proteus"}
        insts = root.findall(".//p:InstrumentComponent", ns)
        if not insts:
            insts = root.findall(".//InstrumentComponent")
        assert len(insts) >= 4

    def test_contains_drawing_section(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        ns = {"p": "http://www.dexpi.org/schemas/Proteus"}
        drawing = root.find(".//p:Drawing", ns)
        if drawing is None:
            drawing = root.find(".//Drawing")
        assert drawing is not None

    def test_nozzles_nested_under_equipment(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        xml = serialize_to_proteus(dexpi)
        root = etree.fromstring(xml.encode())  # noqa: S320
        ns = {"p": "http://www.dexpi.org/schemas/Proteus"}
        equip = root.findall(".//p:Equipment", ns)
        if not equip:
            equip = root.findall(".//Equipment")
        # At least one equipment should have nozzle children
        has_nozzle = any(
            eq.findall("p:Nozzle", ns) or eq.findall("Nozzle")
            for eq in equip
        )
        assert has_nozzle

    def test_write_to_file(self, parsed_model: PidModel, tmp_path) -> None:
        dexpi = map_to_dexpi(parsed_model)
        out = tmp_path / "output.xml"
        serialize_to_proteus(dexpi, out)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_model_is_pydexpi(self, parsed_model: PidModel) -> None:
        """The mapper must produce a pyDEXPI DexpiModel."""
        dexpi = map_to_dexpi(parsed_model)
        assert isinstance(dexpi, DexpiModel)
