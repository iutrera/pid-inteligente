# Draw.io P&ID Library

The P&ID Inteligente library provides 62 semantic symbols for Draw.io, each with embedded DEXPI metadata. When you draw a P&ID using these symbols, the diagram carries machine-readable information that enables automatic conversion to DEXPI Proteus XML and Knowledge Graph construction.

## Loading the Library

### Draw.io Desktop

1. Open Draw.io desktop application
2. Go to **File > Open Library from > Device**
3. Navigate to `packages/drawio-library/pid-library.xml` and select it
4. The "P&ID Inteligente" section appears in the left sidebar

### Draw.io Web (diagrams.net)

1. Open https://app.diagrams.net
2. Go to **File > Open Library from > URL**
3. Paste the URL:
   ```
   https://raw.githubusercontent.com/<org>/pid-inteligente/main/packages/drawio-library/pid-library.xml
   ```
4. The library loads in the sidebar

### Automatic Loading via URL Parameter

Append the `clibs` parameter to the Draw.io URL to load the library automatically:

```
https://app.diagrams.net/?clibs=Uhttps://raw.githubusercontent.com/<org>/pid-inteligente/main/packages/drawio-library/pid-library.xml
```

## Symbol Categories

### Equipment (9 symbols)

| Symbol | DEXPI Class | Typical Tag | Description |
|--------|-------------|-------------|-------------|
| Centrifugal Pump | `CentrifugalPump` | P-101 | Standard centrifugal pump |
| Vertical Vessel / Tank | `VerticalVessel` | T-101 | Vertical storage tank or vessel |
| Horizontal Vessel | `HorizontalVessel` | V-101 | Horizontal pressure vessel |
| Shell & Tube Heat Exchanger | `ShellTubeHeatExchanger` | HE-101, E-101 | Shell and tube heat exchanger |
| Plate Heat Exchanger | `PlateHeatExchanger` | HE-201 | Plate-type heat exchanger |
| Distillation Column | `Column` | C-101 | Distillation or absorption column |
| Reactor | `Reactor` | R-101 | Chemical reactor |
| Compressor | `Compressor` | K-101 | Gas compressor |
| Filter | `Filter` | F-101 | Process filter / strainer |

### Piping Components (15 symbols)

| Symbol | DEXPI Class | Typical Tag | Description |
|--------|-------------|-------------|-------------|
| Gate Valve | `GateValve` | - | On/off isolation valve |
| Globe Valve | `GlobeValve` | - | Throttling valve |
| Ball Valve | `BallValve` | - | Quarter-turn isolation valve |
| Butterfly Valve | `ButterflyValve` | - | Large-diameter isolation valve |
| Check Valve | `CheckValve` | - | Prevents backflow |
| Control Valve | `ControlValve` | TCV-101 | Automated control valve |
| Safety Valve (PSV) | `SafetyValve` | PSV-101 | Pressure relief / safety valve |
| Reducer | `Reducer` | - | Pipe diameter reducer |
| Tee | `Tee` | - | Pipe tee junction |
| Elbow | `Elbow` | - | Pipe elbow / bend |
| Flange | `Flange` | - | Pipe flange connection |
| Blind Flange | `BlindFlange` | - | Blind (blanked) flange |
| Spectacle Blind | `SpectacleBlind` | - | Figure-8 spectacle blind |
| Strainer | `Strainer` | - | Inline strainer |
| Steam Trap | `SteamTrap` | - | Condensate steam trap |

### Instrumentation (5 symbols)

| Symbol | DEXPI Class | Typical Tag | Description |
|--------|-------------|-------------|-------------|
| Transmitter | `Transmitter` | TT-101, FT-201 | Process variable transmitter |
| Controller | `Controller` | TIC-101, FIC-201 | Instrument controller |
| Indicator | `Indicator` | TI-101, PI-201 | Local indicator |
| Alarm | `Alarm` | TAH-101, LAL-201 | Process alarm |
| Instrumentation Loop | `InstrumentationLoop` | TIC-101 loop | Group of related instruments |

### Lines (2 styles)

| Symbol | DEXPI Class | Description |
|--------|-------------|-------------|
| Process Line | `ProcessLine` / `PipingNetworkSegment` | Solid line for process piping |
| Signal Line | `SignalLine` | Dashed line for instrument signals |

### Structural

| Symbol | DEXPI Class | Description |
|--------|-------------|-------------|
| Nozzle | `Nozzle` | Equipment connection point |

## Using the Symbols

### Basic Workflow

1. **Open the template**: Start from `packages/drawio-library/templates/pid-template.drawio` which has three preconfigured layers
2. **Drag symbols** from the library sidebar onto the canvas
3. **Fill in metadata** by clicking on a symbol and editing its properties (the DEXPI attributes appear in the properties panel)
4. **Connect equipment** by drawing lines between nozzles using process line style
5. **Add instrumentation** on the Instrumentation layer with signal lines connecting instruments

### Filling in DEXPI Attributes

When you select a symbol and open **Edit Data** (right-click > Edit Data, or Ctrl+M), you see its DEXPI attributes:

| Attribute | Required | Example | Description |
|-----------|----------|---------|-------------|
| `dexpi_class` | Yes (pre-filled) | `CentrifugalPump` | DEXPI element class |
| `dexpi_component_class` | Auto | `CHBP` | DEXPI component class code |
| `tag_number` | Yes | `P-101` | ISA tag number |
| `design_pressure` | Recommended | `10 barg` | Design pressure with units |
| `design_temperature` | Recommended | `80 degC` | Design temperature with units |
| `capacity` | Optional | `50 m3/h` | Throughput / volume |
| `power` | Optional | `15 kW` | Motor power (for pumps, compressors) |
| `material` | Optional | `SS316L` | Material of construction |

For piping lines:

| Attribute | Required | Example | Description |
|-----------|----------|---------|-------------|
| `line_number` | Yes | `3"-P-001-CS-150#` | Line specification |
| `nominal_diameter` | Recommended | `3 inch` | Pipe diameter |
| `fluid_code` | Recommended | `P` (process) | Fluid service code |

For nozzles:

| Attribute | Required | Example | Description |
|-----------|----------|---------|-------------|
| `nozzle_id` | Yes | `N1` | Nozzle identifier on equipment |
| `size` | Recommended | `3 inch` | Nozzle size |
| `rating` | Recommended | `150#` | Pressure rating |
| `service` | Optional | `Outlet` | Nozzle service description |

## Tag Number Conventions (ISA 5.1)

Tag numbers follow the ISA 5.1 standard format:

```
[First Letter][Succeeding Letters]-[Loop/Equipment Number]
```

### Equipment Tags

| Equipment | Tag Format | Example |
|-----------|-----------|---------|
| Pump | P-NNN | P-101 |
| Tank/Vessel | T-NNN or V-NNN | T-101 |
| Heat Exchanger | HE-NNN or E-NNN | HE-101 |
| Column | C-NNN | C-101 |
| Reactor | R-NNN | R-101 |
| Compressor | K-NNN | K-101 |
| Filter | F-NNN | F-101 |

### Instrument Tags

The first letter indicates the measured variable; succeeding letters indicate the function:

| Tag | Meaning | Example |
|-----|---------|---------|
| TIC | Temperature Indicating Controller | TIC-101 |
| TT | Temperature Transmitter | TT-101 |
| TCV | Temperature Control Valve | TCV-101 |
| FIC | Flow Indicating Controller | FIC-201 |
| FT | Flow Transmitter | FT-201 |
| LIC | Level Indicating Controller | LIC-301 |
| PI | Pressure Indicator | PI-401 |
| PSV | Pressure Safety Valve | PSV-101 |
| LAH | Level Alarm High | LAH-301 |

## Layers

The template provides three preconfigured layers:

| Layer | Content | Visible by Default |
|-------|---------|-------------------|
| **Process** | Equipment, piping, valves, nozzles | Yes |
| **Instrumentation** | Transmitters, controllers, indicators, signal lines, control loops | Yes |
| **Annotations** | Text labels, notes, title block | Yes |

Place each type of element on its correct layer. This keeps the diagram organized and enables selective visibility when working on specific aspects of the P&ID.

To switch layers in Draw.io: **Edit > Layers** (or Ctrl+Shift+L) to open the layers panel.

## Example: Drawing the T-101 to HE-101 Circuit

This step-by-step example draws a simple process loop: tank T-101 feeds pump P-101, which pushes fluid through control valve TCV-101 to heat exchanger HE-101, with temperature control.

### Step 1: Place Equipment (Process Layer)

1. Ensure the **Process** layer is selected
2. Drag **Vertical Vessel** from the library. Set:
   - `tag_number`: `T-101`
   - `design_pressure`: `5 barg`
   - `design_temperature`: `80 degC`
   - `capacity`: `10 m3`
3. Drag **Centrifugal Pump** below the tank. Set:
   - `tag_number`: `P-101`
   - `power`: `15 kW`
4. Drag **Control Valve** to the right of the pump. Set:
   - `tag_number`: `TCV-101`
5. Drag **Shell & Tube Heat Exchanger** to the right. Set:
   - `tag_number`: `HE-101`
   - `design_temperature`: `150 degC`

### Step 2: Add Nozzles

Add nozzles to each equipment piece at the connection points:
- T-101: bottom outlet nozzle (N1)
- P-101: inlet (N1) and outlet (N2)
- HE-101: shell inlet (S1) and shell outlet (S2)

### Step 3: Connect with Process Lines

Draw lines between nozzles:
- T-101/N1 --> P-101/N1 (suction line)
- P-101/N2 --> TCV-101 (discharge line)
- TCV-101 --> HE-101/S1 (line to exchanger)

Set `line_number` on each process line (e.g., `3"-P-001-SS316L-150#`).

### Step 4: Add Instrumentation (Instrumentation Layer)

1. Switch to the **Instrumentation** layer
2. Drag a **Transmitter**. Set `tag_number`: `TT-101`
3. Drag a **Controller**. Set `tag_number`: `TIC-101`
4. Draw a **Signal Line** from TT-101 to TIC-101
5. Draw a **Signal Line** from TIC-101 to TCV-101

### Step 5: Validate and Convert

Save the file as `.drawio` and run:

```bash
pid-converter validate your-pid.drawio
pid-converter convert your-pid.drawio -o your-pid.xml
```

## Tips

- **Always fill `tag_number`**: The validator flags equipment and instruments without tags
- **Connect nozzle-to-nozzle**: Lines should start and end at nozzle shapes for proper topology reconstruction
- **Use the template**: Starting from `pid-template.drawio` ensures correct layer configuration
- **One tag per element**: The validator checks for duplicate tags within a category
- **Process lines need `line_number`**: The validator flags piping segments without line numbers

## Reference Files

| File | Path | Description |
|------|------|-------------|
| Library | `packages/drawio-library/pid-library.xml` | 62 symbols ready to load |
| Template | `packages/drawio-library/templates/pid-template.drawio` | Empty P&ID with layers |
| Example | `packages/drawio-library/examples/example-pid.drawio` | Complete example P&ID |
| Test file | `packages/drawio-library/examples/test-simple.drawio` | Minimal P&ID for testing |
