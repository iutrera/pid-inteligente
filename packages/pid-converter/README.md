# pid-converter

Conversor bidireccional entre Draw.io (mxGraph XML) y DEXPI Proteus XML para diagramas P&ID.

Lee archivos `.drawio` con simbolos de la biblioteca semantica, los convierte a modelo pyDEXPI (Pydantic), y serializa a Proteus XML conforme al estandar DEXPI. Tambien soporta la direccion inversa: Proteus XML a `.drawio`.

## Arquitectura interna

```
.drawio (mxGraph XML)
    |
    v
  parser/       -- Extrae <object> y <mxCell> con atributos custom y topologia
    |
    v
  mapper/       -- Instancia clases Pydantic pyDEXPI desde atributos dexpi_class
    |
    v
  topology/     -- Reconstruye PipingNetworkSegments con conexiones nozzle-a-nozzle
    |
    v
  serializer/   -- Genera Proteus XML con posicionamiento grafico
    |
    v
Proteus XML (DEXPI)
```

El camino inverso usa `importer/` para leer Proteus XML y generar `.drawio`.

## Instalacion

```bash
# Desde el monorepo (modo desarrollo)
cd packages/pid-converter
pip install -e ".[dev]"

# Desde PyPI (cuando se publique)
pip install pid-converter
```

### Requisitos

- Python >= 3.11
- Dependencias: lxml, pyDEXPI, Pydantic v2, NetworkX, Typer

## Uso basico

### CLI

```bash
# Convertir Draw.io a DEXPI
pid-converter drawio2dexpi input.drawio -o output.xml

# Convertir DEXPI a Draw.io
pid-converter dexpi2drawio input.xml -o output.drawio

# Validar un P&ID
pid-converter validate input.drawio
```

### API programatica

```python
from pid_converter.parser import parse_drawio
from pid_converter.mapper import map_to_dexpi
from pid_converter.serializer import serialize_to_proteus

# Parse .drawio
model = parse_drawio("my-pid.drawio")

# Map to pyDEXPI
dexpi_model = map_to_dexpi(model)

# Serialize to Proteus XML
serialize_to_proteus(dexpi_model, "output.xml")
```

## Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=pid_converter
```
