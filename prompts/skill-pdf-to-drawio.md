# Skill: Interpretar PDF de P&ID y generar .drawio con metadatos DEXPI

## Instrucciones para Claude Desktop

Cuando el usuario te pida interpretar un P&ID desde un PDF o imagen y generar un archivo .drawio, sigue estas reglas ESTRICTAMENTE.

## Estructura del archivo .drawio

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" type="device">
  <diagram id="pid" name="P&ID">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
      tooltips="1" connect="1" arrows="1" fold="1" page="1"
      pageScale="1" pageWidth="1654" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" value="Process" parent="0"/>
        <mxCell id="2" value="Instrumentation" parent="0"/>
        <mxCell id="3" value="Annotations" parent="0"/>
        <!-- Nodos y conexiones aquí -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

- **3 capas obligatorias**: id="1" (Process), id="2" (Instrumentation), id="3" (Annotations)
- Equipos, válvulas, líneas de proceso → parent="1"
- Instrumentos, líneas de señal → parent="2"
- Textos, notas → parent="3"

## Atributos obligatorios en cada nodo

Cada equipo, válvula o instrumento es un `<object>` con estos atributos:

| Atributo | Descripción | Ejemplo |
|----------|-------------|---------|
| `id` | Identificador numérico único | "10", "20", "30" |
| `label` | Tag visible | "P-101", "TIC-201" |
| `dexpi_class` | Tipo DEXPI del elemento | "CentrifugalPump", "ControlValve", "TemperatureController" |
| `tag_number` | Tag ISA del elemento | "P-101", "TIC-201" |

### Atributos adicionales por tipo

**Equipos** (parent="1"):
- `design_pressure`, `design_temperature`, `capacity`, `power`, `material`

**Válvulas** (parent="1"):
- `size`, `rating`, `valve_type`

**Instrumentos** (parent="2"):
- `measured_variable` (Temperature, Pressure, Flow, Level)
- `function` (Transmitter, Controller, Indicator, Alarm)
- `signal_type` (4-20mA, digital, pneumatic)

## Clases DEXPI válidas

### Equipos
CentrifugalPump, PositiveDisplacementPump, HorizontalVessel, VerticalVessel, Tank,
ShellTubeHeatExchanger, PlateHeatExchanger, Column, Reactor, Compressor, Filter,
Agitator, Blower, Fan, Ejector, Cyclone, Furnace, Boiler, CoolingTower

### Válvulas y componentes de piping
GateValve, GlobeValve, BallValve, ButterflyValve, CheckValve, ControlValve,
SafetyValve, Reducer, Tee, Flange, BlindFlange, SpectacleBlind, Strainer, SteamTrap

### Instrumentos
TemperatureTransmitter, PressureTransmitter, FlowTransmitter, LevelTransmitter,
TemperatureController, PressureController, FlowController, LevelController,
TemperatureIndicator, PressureIndicator, FlowIndicator, LevelIndicator,
PressureAlarm, TemperatureAlarm, AnalysisTransmitter

### Líneas
ProcessLine, SignalLine, UtilityLine

## CONEXIONES — REGLA CRÍTICA

**Cada conexión DEBE tener `source` y `target` apuntando a IDs de nodos existentes.**

### Líneas de proceso
```xml
<object label="3&quot;-PL-101" dexpi_class="ProcessLine" line_number="PL-101"
        nominal_diameter="3 inch" fluid_code="PROCESS" material_spec="CS" id="101">
  <mxCell style="endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;"
          edge="1" source="10" target="30" parent="1">
    <mxGeometry relative="1" as="geometry"/>
  </mxCell>
</object>
```

### Líneas de señal
```xml
<object label="" dexpi_class="SignalLine" signal_type="4-20mA" id="301">
  <mxCell style="strokeColor=#FF0000;strokeWidth=1.5;dashed=1;dashPattern=8 4;endArrow=block;endFill=1;"
          edge="1" source="220" target="70" parent="2">
    <mxGeometry relative="1" as="geometry"/>
  </mxCell>
</object>
```

### REGLAS DE CONEXIÓN
1. **NUNCA** uses `sourcePoint`/`targetPoint` con coordenadas como forma de conexión
2. **SIEMPRE** usa `source="ID"` y `target="ID"` apuntando a IDs de `<object>` existentes
3. Cada línea de proceso conecta: equipo→equipo, equipo→válvula, válvula→equipo
4. Cada línea de señal conecta: instrumento→equipo, instrumento→válvula, instrumento→instrumento

## Lazos de control

Para cada lazo de control identificado en el P&ID, crea las signal lines necesarias:

```
Sensor/Transmisor (TT-101) ──signal──→ Controlador (TIC-101) ──signal──→ Válvula (TCV-101)
```

Esto requiere **2 signal lines**:
1. `source="ID_TT101" target="ID_TIC101"`
2. `source="ID_TIC101" target="ID_TCV101"`

## Estilos de shapes

### Equipos
| Tipo | Style |
|------|-------|
| Bomba | `shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;` |
| Tanque/Vessel | `shape=rectangle;rounded=1;arcSize=50;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;` |
| Intercambiador | `shape=rectangle;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;` |
| Válvula control | `shape=rhombus;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=11;fontStyle=1;` |
| Válvula manual | `shape=rhombus;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=10;` |

### Instrumentos
```
shape=ellipse;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontStyle=1;
```

### Líneas
| Tipo | Style |
|------|-------|
| Proceso | `endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;endSize=8;` |
| Señal | `strokeColor=#FF0000;strokeWidth=1.5;dashed=1;dashPattern=8 4;endArrow=block;endFill=1;` |
| Utilidad | `endArrow=block;strokeColor=#0000FF;strokeWidth=2;endFill=1;` |

## Tamaños recomendados

| Elemento | Width | Height |
|----------|-------|--------|
| Tanque/Vessel vertical | 100 | 180 |
| Intercambiador | 130 | 100 |
| Bomba | 70 | 70 |
| Compresor | 80 | 80 |
| Columna/Reactor | 80 | 240 |
| Válvula | 50 | 50 |
| Instrumento | 45 | 45 |

## Espaciado

- Entre equipos: mínimo 250px horizontal
- Instrumentos: 140px por encima de su equipo asociado
- Canvas: 1654x1169 (ANSI D)
- Flujo de proceso: preferentemente izquierda → derecha

## Proceso de interpretación del PDF

1. **Identificar todos los equipos** con sus tags (P-101, T-201, HE-301, etc.)
2. **Identificar todas las válvulas** con sus tags (XV-101, TCV-201, etc.)
3. **Identificar todos los instrumentos** con sus tags (TIC-101, FT-201, LI-301, etc.)
4. **Trazar las líneas de proceso** — qué equipo conecta con cuál, a través de qué válvulas
5. **Trazar los lazos de control** — qué transmisor alimenta a qué controlador, qué controlador actúa sobre qué válvula
6. **Generar el .drawio** con TODOS los nodos y TODAS las conexiones

## Verificación obligatoria antes de entregar

- [ ] Todo equipo tiene dexpi_class y tag_number
- [ ] Todo instrumento tiene al menos 1 signal line conectándolo
- [ ] Toda línea de proceso tiene source y target válidos
- [ ] Toda línea de señal tiene source y target válidos
- [ ] No hay IDs duplicados
- [ ] No hay nodos huérfanos (sin conexión alguna)
- [ ] Los lazos de control están completos (sensor → controlador → válvula)

## Ejemplo completo mínimo

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" type="device">
  <diagram id="pid-example" name="P&amp;ID Example">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
      tooltips="1" connect="1" arrows="1" fold="1" page="1"
      pageScale="1" pageWidth="1654" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" value="Process" parent="0"/>
        <mxCell id="2" value="Instrumentation" parent="0"/>
        <mxCell id="3" value="Annotations" parent="0"/>

        <!-- Equipment -->
        <object label="T-101" dexpi_class="VerticalVessel" tag_number="T-101"
                design_pressure="5 barg" design_temperature="80 degC" id="10">
          <mxCell style="shape=rectangle;rounded=1;arcSize=50;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;"
                  vertex="1" parent="1">
            <mxGeometry x="150" y="350" width="100" height="180" as="geometry"/>
          </mxCell>
        </object>

        <object label="P-101" dexpi_class="CentrifugalPump" tag_number="P-101"
                power="15 kW" id="30">
          <mxCell style="shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;"
                  vertex="1" parent="1">
            <mxGeometry x="420" y="405" width="70" height="70" as="geometry"/>
          </mxCell>
        </object>

        <object label="TCV-101" dexpi_class="ControlValve" tag_number="TCV-101"
                size="3 inch" id="50">
          <mxCell style="shape=rhombus;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=11;fontStyle=1;"
                  vertex="1" parent="1">
            <mxGeometry x="670" y="415" width="50" height="50" as="geometry"/>
          </mxCell>
        </object>

        <object label="HE-101" dexpi_class="ShellTubeHeatExchanger" tag_number="HE-101" id="70">
          <mxCell style="shape=rectangle;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=12;fontStyle=1;"
                  vertex="1" parent="1">
            <mxGeometry x="920" y="390" width="130" height="100" as="geometry"/>
          </mxCell>
        </object>

        <!-- Process Lines (source/target = IDs of equipment/valves) -->
        <object label="PL-101" dexpi_class="ProcessLine" line_number="PL-101" id="101">
          <mxCell style="endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;"
                  edge="1" source="10" target="30" parent="1">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>
        <object label="PL-102" dexpi_class="ProcessLine" line_number="PL-102" id="102">
          <mxCell style="endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;"
                  edge="1" source="30" target="50" parent="1">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>
        <object label="PL-103" dexpi_class="ProcessLine" line_number="PL-103" id="103">
          <mxCell style="endArrow=block;strokeColor=#000000;strokeWidth=3;endFill=1;"
                  edge="1" source="50" target="70" parent="1">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>

        <!-- Instruments -->
        <object label="TT-101" dexpi_class="TemperatureTransmitter" tag_number="TT-101"
                measured_variable="Temperature" function="Transmitter" id="200">
          <mxCell style="shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontStyle=1;"
                  vertex="1" parent="2">
            <mxGeometry x="950" y="260" width="45" height="45" as="geometry"/>
          </mxCell>
        </object>
        <object label="TIC-101" dexpi_class="TemperatureController" tag_number="TIC-101"
                measured_variable="Temperature" function="Indicating Controller" id="220">
          <mxCell style="shape=ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontStyle=1;"
                  vertex="1" parent="2">
            <mxGeometry x="670" y="260" width="45" height="45" as="geometry"/>
          </mxCell>
        </object>

        <!-- Signal Lines (source/target = IDs of instruments/equipment) -->
        <object label="" dexpi_class="SignalLine" signal_type="4-20mA" id="301">
          <mxCell style="strokeColor=#FF0000;strokeWidth=1.5;dashed=1;endArrow=block;endFill=1;"
                  edge="1" source="200" target="220" parent="2">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>
        <object label="" dexpi_class="SignalLine" signal_type="4-20mA" id="302">
          <mxCell style="strokeColor=#FF0000;strokeWidth=1.5;dashed=1;endArrow=block;endFill=1;"
                  edge="1" source="220" target="50" parent="2">
            <mxGeometry relative="1" as="geometry"/>
          </mxCell>
        </object>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
