"""Tests for the DEXPI importer (Proteus XML -> Draw.io)."""

from __future__ import annotations

from lxml import etree

from pid_converter.importer import import_dexpi
from pid_converter.mapper import map_to_dexpi
from pid_converter.models import PidModel
from pid_converter.parser import parse_drawio
from pid_converter.serializer import serialize_to_proteus


class TestImportDexpi:
    """Test round-trip: drawio -> dexpi -> drawio."""

    def test_roundtrip_produces_valid_drawio(self, parsed_model: PidModel) -> None:
        """Convert to DEXPI and back, verify the result is valid Draw.io XML."""
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)

        drawio_xml = import_dexpi(proteus_xml)
        assert isinstance(drawio_xml, str)
        assert "mxfile" in drawio_xml

        # Must be parseable XML
        root = etree.fromstring(drawio_xml.encode())  # noqa: S320
        assert root.tag == "mxfile"

    def test_roundtrip_preserves_equipment(self, parsed_model: PidModel) -> None:
        """Equipment tags should survive the round-trip."""
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        drawio_xml = import_dexpi(proteus_xml)

        # Re-parse the generated drawio
        model2 = parse_drawio(drawio_xml)
        equip = model2.equipment()
        tags = {e.tag_number for e in equip}
        assert "T-101" in tags
        assert "P-101" in tags
        assert "HE-101" in tags

    def test_roundtrip_preserves_instruments(self, parsed_model: PidModel) -> None:
        """Instruments should survive the round-trip."""
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        drawio_xml = import_dexpi(proteus_xml)

        model2 = parse_drawio(drawio_xml)
        instruments = model2.instruments()
        assert len(instruments) >= 4

    def test_roundtrip_preserves_nozzles(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        drawio_xml = import_dexpi(proteus_xml)

        model2 = parse_drawio(drawio_xml)
        nozzles = model2.nozzles()
        assert len(nozzles) >= 4

    def test_roundtrip_preserves_piping(self, parsed_model: PidModel) -> None:
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        drawio_xml = import_dexpi(proteus_xml)

        model2 = parse_drawio(drawio_xml)
        piping = [e for e in model2.edges if e.dexpi_class == "ProcessLine"]
        assert len(piping) >= 4

    def test_layers_present(self, parsed_model: PidModel) -> None:
        """The generated drawio should have Process and Instrumentation layers."""
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        drawio_xml = import_dexpi(proteus_xml)

        root = etree.fromstring(drawio_xml.encode())  # noqa: S320
        cells = root.findall(".//mxCell")
        layer_values = [c.get("value", "") for c in cells if c.get("parent") == "0"]
        assert "Process" in layer_values
        assert "Instrumentation" in layer_values

    def test_write_to_file(self, parsed_model: PidModel, tmp_path) -> None:
        dexpi = map_to_dexpi(parsed_model)
        proteus_xml = serialize_to_proteus(dexpi)
        out = tmp_path / "imported.drawio"
        import_dexpi(proteus_xml, out)
        assert out.exists()
        assert out.stat().st_size > 100
