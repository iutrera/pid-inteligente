"""DEXPI Proteus XML structural validation tests.

Since the full DEXPI Proteus XSD is a proprietary specification,
these tests use a simplified schema that verifies the essential
structural requirements of the generated XML:

* ``<PlantModel>`` root element with correct namespace
* ``<Equipment>`` elements with ID and TagNumber
* ``<PipingNetworkSystem>``/``<PipingNetworkSegment>`` elements
* ``<InstrumentationLoopFunction>``/``<InstrumentComponent>`` elements
* Correct namespace declarations

The simplified XSD is embedded as a string constant so the tests
are fully self-contained.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lxml import etree

from pid_converter.parser import parse_drawio
from pid_converter.mapper import map_to_dexpi
from pid_converter.serializer import serialize_to_proteus
from pid_converter.serializer.proteus_serializer import PROTEUS_NS

# ---------------------------------------------------------------------------
# Simplified DEXPI Proteus XSD
# ---------------------------------------------------------------------------

_SIMPLIFIED_XSD = """\
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:dexpi="http://www.dexpi.org/schemas/Proteus"
           targetNamespace="http://www.dexpi.org/schemas/Proteus"
           elementFormDefault="qualified">

  <!-- Root element -->
  <xs:element name="PlantModel">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:PlantInformation" minOccurs="0" maxOccurs="1"/>
        <xs:element ref="dexpi:Equipment" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:PipingNetworkSystem" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:InstrumentationLoopFunction" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:SignalLine" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:Drawing" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- PlantInformation -->
  <xs:element name="PlantInformation">
    <xs:complexType>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- Equipment -->
  <xs:element name="Equipment">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:Extent" minOccurs="0" maxOccurs="1"/>
        <xs:element ref="dexpi:Nozzle" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="TagNumber" type="xs:string"/>
      <xs:attribute name="ComponentClass" type="xs:string"/>
      <xs:attribute name="ComponentName" type="xs:string"/>
      <xs:attribute name="DexpiClass" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- Nozzle -->
  <xs:element name="Nozzle">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:Position" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="NozzleID" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- PipingNetworkSystem -->
  <xs:element name="PipingNetworkSystem">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:PipingNetworkSegment" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:PipingComponent" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- PipingNetworkSegment -->
  <xs:element name="PipingNetworkSegment">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="LineNumber" type="xs:string"/>
      <xs:attribute name="NominalDiameter" type="xs:string"/>
      <xs:attribute name="FluidCode" type="xs:string"/>
      <xs:attribute name="MaterialSpec" type="xs:string"/>
      <xs:attribute name="Insulation" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- PipingComponent -->
  <xs:element name="PipingComponent">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:Extent" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="TagNumber" type="xs:string"/>
      <xs:attribute name="ComponentClass" type="xs:string"/>
      <xs:attribute name="DexpiClass" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- InstrumentationLoopFunction -->
  <xs:element name="InstrumentationLoopFunction">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:InstrumentComponent" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="LoopName" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- InstrumentComponent -->
  <xs:element name="InstrumentComponent">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="dexpi:Extent" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="TagNumber" type="xs:string"/>
      <xs:attribute name="ComponentClass" type="xs:string"/>
      <xs:attribute name="DexpiClass" type="xs:string"/>
      <xs:attribute name="MeasuredVariable" type="xs:string"/>
      <xs:attribute name="Function" type="xs:string"/>
      <xs:attribute name="SignalType" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- SignalLine -->
  <xs:element name="SignalLine">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:GenericAttribute" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string" use="required"/>
      <xs:attribute name="SignalType" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- GenericAttribute -->
  <xs:element name="GenericAttribute">
    <xs:complexType>
      <xs:attribute name="Name" type="xs:string" use="required"/>
      <xs:attribute name="Value" type="xs:string"/>
      <xs:attribute name="Format" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <!-- Extent -->
  <xs:element name="Extent">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:Min" minOccurs="0"/>
        <xs:element ref="dexpi:Max" minOccurs="0"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>

  <xs:element name="Min">
    <xs:complexType>
      <xs:attribute name="X" type="xs:string"/>
      <xs:attribute name="Y" type="xs:string"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="Max">
    <xs:complexType>
      <xs:attribute name="X" type="xs:string"/>
      <xs:attribute name="Y" type="xs:string"/>
    </xs:complexType>
  </xs:element>

  <!-- Position -->
  <xs:element name="Position">
    <xs:complexType>
      <xs:attribute name="Location" type="xs:string"/>
      <xs:attribute name="Width" type="xs:string"/>
      <xs:attribute name="Height" type="xs:string"/>
    </xs:complexType>
  </xs:element>

  <!-- Drawing (simplified) -->
  <xs:element name="Drawing">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:ShapeCatalogue" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="ShapeCatalogue">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:ShapeReference" minOccurs="0" maxOccurs="unbounded"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>

  <xs:element name="ShapeReference">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="dexpi:Position" minOccurs="0" maxOccurs="1"/>
        <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="ID" type="xs:string"/>
      <xs:attribute name="RefID" type="xs:string"/>
      <xs:attribute name="Type" type="xs:string"/>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>

</xs:schema>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_proteus_xml(drawio_file: Path) -> str:
    """Run the full drawio -> DEXPI pipeline and return the Proteus XML."""
    pid_model = parse_drawio(drawio_file)
    dexpi_model = map_to_dexpi(pid_model)
    return serialize_to_proteus(dexpi_model)


def _parse_xml(xml_str: str) -> etree._Element:
    """Parse an XML string into an lxml Element."""
    return etree.fromstring(xml_str.encode("utf-8"))  # noqa: S320


def _ns(tag: str) -> str:
    """Wrap *tag* with the DEXPI Proteus namespace."""
    return f"{{{PROTEUS_NS}}}{tag}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDexpiStructure:
    """Validate the structural correctness of generated DEXPI XML."""

    def test_root_is_plant_model(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        # Root tag should be PlantModel (possibly namespaced)
        local_name = etree.QName(root.tag).localname
        assert local_name == "PlantModel", f"Root tag is '{root.tag}', expected PlantModel"

    def test_has_correct_namespace(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        ns = etree.QName(root.tag).namespace
        assert ns == PROTEUS_NS, (
            f"Root namespace is '{ns}', expected '{PROTEUS_NS}'"
        )

    def test_has_plant_information(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        pi = root.find(_ns("PlantInformation"))
        assert pi is not None, "Missing <PlantInformation> element"
        assert pi.get("OriginatingSystem") == "pid-converter"

    def test_has_equipment_elements(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        equipment = root.findall(_ns("Equipment"))
        assert len(equipment) >= 3, (
            f"Expected at least 3 Equipment elements, got {len(equipment)}"
        )

    def test_equipment_has_required_attributes(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        for eq in root.findall(_ns("Equipment")):
            assert eq.get("ID"), "Equipment missing ID attribute"
            assert eq.get("TagNumber") is not None, (
                f"Equipment {eq.get('ID')} missing TagNumber attribute"
            )

    def test_equipment_has_nozzles(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        all_nozzles = []
        for eq in root.findall(_ns("Equipment")):
            nozzles = eq.findall(_ns("Nozzle"))
            all_nozzles.extend(nozzles)
        assert len(all_nozzles) >= 1, "Expected at least one Nozzle inside Equipment"

    def test_has_piping_network_system(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        pns = root.findall(_ns("PipingNetworkSystem"))
        assert len(pns) >= 1, "Missing <PipingNetworkSystem>"

    def test_has_piping_segments(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        segments = []
        for pns in root.findall(_ns("PipingNetworkSystem")):
            segments.extend(pns.findall(_ns("PipingNetworkSegment")))
        assert len(segments) >= 3, (
            f"Expected at least 3 PipingNetworkSegments, got {len(segments)}"
        )

    def test_piping_segments_have_attributes(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        for pns in root.findall(_ns("PipingNetworkSystem")):
            for seg in pns.findall(_ns("PipingNetworkSegment")):
                assert seg.get("ID"), "PipingNetworkSegment missing ID"

    def test_has_instrumentation_loops(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        loops = root.findall(_ns("InstrumentationLoopFunction"))
        assert len(loops) >= 1, "Missing <InstrumentationLoopFunction>"

    def test_instrument_components_have_attributes(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        for loop in root.findall(_ns("InstrumentationLoopFunction")):
            for ic in loop.findall(_ns("InstrumentComponent")):
                assert ic.get("ID"), "InstrumentComponent missing ID"
                assert ic.get("TagNumber") is not None, (
                    f"InstrumentComponent {ic.get('ID')} missing TagNumber"
                )

    def test_has_drawing_section(self, drawio_file: Path) -> None:
        xml = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml)
        drawing = root.find(_ns("Drawing"))
        assert drawing is not None, "Missing <Drawing> element"


class TestDexpiXsdValidation:
    """Validate generated XML against the simplified DEXPI XSD."""

    def test_validates_against_simplified_xsd(self, drawio_file: Path) -> None:
        """The generated Proteus XML must conform to the simplified schema."""
        xml_str = _get_proteus_xml(drawio_file)

        # Parse the XSD
        xsd_doc = etree.parse(BytesIO(_SIMPLIFIED_XSD.encode("utf-8")))  # noqa: S320
        xsd_schema = etree.XMLSchema(xsd_doc)

        # Parse the generated XML
        xml_doc = etree.parse(BytesIO(xml_str.encode("utf-8")))  # noqa: S320

        # Validate
        is_valid = xsd_schema.validate(xml_doc)
        if not is_valid:
            errors = "\n".join(str(e) for e in xsd_schema.error_log)
            pytest.fail(
                f"Generated DEXPI XML does not conform to simplified XSD:\n{errors}"
            )

    def test_xml_is_well_formed(self, drawio_file: Path) -> None:
        """The generated XML must be parseable."""
        xml_str = _get_proteus_xml(drawio_file)
        try:
            _parse_xml(xml_str)
        except etree.XMLSyntaxError as exc:
            pytest.fail(f"Generated XML is not well-formed: {exc}")

    def test_all_ids_are_unique(self, drawio_file: Path) -> None:
        """All ID attributes across elements should be unique."""
        xml_str = _get_proteus_xml(drawio_file)
        root = _parse_xml(xml_str)

        ids: list[str] = []
        for elem in root.iter():
            eid = elem.get("ID")
            if eid:
                ids.append(eid)

        duplicates = [eid for eid in ids if ids.count(eid) > 1]
        assert not duplicates, (
            f"Duplicate IDs found in DEXPI XML: {set(duplicates)}"
        )
