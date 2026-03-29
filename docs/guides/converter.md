# Converter Guide

The `pid-converter` is a bidirectional converter between Draw.io (mxGraph XML) and DEXPI Proteus XML. It parses Draw.io files with semantic P&ID symbols, maps them to the pyDEXPI data model, reconstructs piping topology, and serializes to standard DEXPI Proteus XML. It also works in reverse: DEXPI XML to Draw.io.

## Installation

```bash
cd packages/pid-converter
pip install -e ".[dev]"
```

Requirements: Python 3.11+, lxml, pyDEXPI, Pydantic v2, NetworkX, Typer.

## CLI Usage

The CLI provides three commands: `convert`, `import`, and `validate`.

### Convert Draw.io to DEXPI

```bash
pid-converter convert input.drawio -o output.xml
```

If `-o` is omitted, the output file uses the same name with `.xml` extension:

```bash
pid-converter convert my-pid.drawio
# Produces: my-pid.xml
```

Example with the test file:

```bash
pid-converter convert packages/drawio-library/examples/test-simple.drawio -o test-output.xml
```

Output:

```
Parsing test-simple.drawio ...
  Found 8 nodes, 5 edges
Mapping to DEXPI model ...
  Equipment: 4, Nozzles: 6, Piping segments: 3, Instruments: 2
Serializing to test-output.xml ...
Done! Proteus XML written to test-output.xml
```

### Import DEXPI to Draw.io

```bash
pid-converter import input.xml -o output.drawio
```

If `-o` is omitted, the output uses the same name with `.drawio` extension:

```bash
pid-converter import dexpi-file.xml
# Produces: dexpi-file.drawio
```

### Validate a P&ID

```bash
pid-converter validate input.drawio
```

The validator checks for:

| Check | Error Type | Description |
|-------|-----------|-------------|
| Missing tag numbers | `missing_tag` | Equipment or instrument without `tag_number` |
| Missing line numbers | `missing_line_number` | Piping segments without `line_number` |
| Unconnected nozzles | `unconnected_nozzle` | Nozzles not connected to any piping segment |
| Orphan instruments | `orphan_instrument` | Instruments not connected by signal lines |
| Duplicate tags | `duplicate_tag` | Multiple elements sharing the same `tag_number` |

Example output when issues are found:

```
Validating my-pid.drawio ...
          Validation Results (3 issues)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Shape ID ┃ Error Type           ┃ Message                              ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 42       │ missing_tag          │ CentrifugalPump (id=42) has no ...   │
│ 55       │ missing_line_number  │ Piping segment (id=55) has no ...    │
│ 60       │ orphan_instrument    │ Instrument 'TT-101' (id=60) is ...  │
└──────────┴──────────────────────┴──────────────────────────────────────┘
```

Exit code is 0 if no errors are found, 1 otherwise. This makes it suitable for CI pipelines.

## Programmatic API (Python)

For integration into scripts or other applications, use the converter as a Python library.

### Draw.io to DEXPI

```python
from pid_converter.parser import parse_drawio
from pid_converter.mapper import map_to_dexpi
from pid_converter.serializer import serialize_to_proteus

# Parse the .drawio file into an internal PidModel
model = parse_drawio("my-pid.drawio")

# Map to pyDEXPI Pydantic model
dexpi_model = map_to_dexpi(model)

# Serialize to Proteus XML
serialize_to_proteus(dexpi_model, "output.xml")
```

### DEXPI to Draw.io

```python
from pid_converter.importer import import_dexpi

# Read DEXPI Proteus XML and generate .drawio file
import_dexpi("dexpi-input.xml", "output.drawio")
```

### Validate

```python
from pid_converter.parser import parse_drawio
from pid_converter.topology import resolve_topology
from pid_converter.validator import validate_pid

model = parse_drawio("my-pid.drawio")
resolve_topology(model)
errors = validate_pid(model)

for err in errors:
    print(f"[{err.error_type.value}] Shape {err.shape_id}: {err.message}")
```

### Inspect the intermediate model

```python
from pid_converter.parser import parse_drawio
from pid_converter.mapper import map_to_dexpi
from pid_converter.mapper.dexpi_mapper import (
    get_equipment,
    get_instruments,
    get_nozzles,
    get_piping_segments,
)

model = parse_drawio("my-pid.drawio")
dexpi = map_to_dexpi(model)

print(f"Equipment: {len(get_equipment(dexpi))}")
print(f"Nozzles: {len(get_nozzles(dexpi))}")
print(f"Piping segments: {len(get_piping_segments(dexpi))}")
print(f"Instruments: {len(get_instruments(dexpi))}")
```

## Internal Architecture

The converter processes files through a pipeline of four stages:

```
.drawio (mxGraph XML)
    |
    v
  parser/       -- Extracts <object> and <mxCell> elements with custom
    |               attributes and topology (connections between cells)
    v
  mapper/       -- Instantiates pyDEXPI Pydantic models from dexpi_class
    |               attributes (CentrifugalPump, ControlValve, etc.)
    v
  topology/     -- Reconstructs PipingNetworkSegments with nozzle-to-nozzle
    |               connections and infers flow direction
    v
  serializer/   -- Generates Proteus XML with graphic positioning
    |               in ShapeCatalogue (from original Draw.io coordinates)
    v
Proteus XML (DEXPI)
```

The reverse path (`import/`) reads Proteus XML, extracts elements and their coordinates, and generates a `.drawio` file with the appropriate library shapes and connections.

## Limitations

- **Complex topologies**: P&IDs with many branching piping networks may require manual review of the reconstructed topology. The algorithm uses nozzle-to-nozzle connections as anchors.
- **ProteusSerializer.save()**: The pyDEXPI library's `ProteusSerializer.save()` method is not fully implemented upstream. The converter uses its own serialization logic as a workaround.
- **Graphic fidelity on import**: When importing DEXPI to Draw.io, the layout is reconstructed from coordinate data in the XML. Complex or densely packed diagrams may need manual adjustment after import.
- **DEXPI subset**: Only the DEXPI classes listed in the [library guide](drawio-library.md) are supported. Elements outside this subset are preserved as generic shapes during import.

## Testing

```bash
cd packages/pid-converter
pytest                           # Run all tests
pytest --cov=pid_converter       # With coverage report
pytest tests/test_cli.py -v      # CLI tests only
```
