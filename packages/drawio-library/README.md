# drawio-library

Biblioteca de simbolos P&ID semanticos para Draw.io con metadatos DEXPI embebidos.

Contiene ~60 custom shapes organizados por categoria (equipment, piping, instrumentation, lines) con atributos como `dexpi_class`, `tag_number` y condiciones de diseno. Incluye una plantilla base `.drawio` con capas preconfiguradas (Process, Instrumentation, Annotations).

## Contenido

```
drawio-library/
  shapes/
    equipment/        -- Bombas, tanques, intercambiadores, columnas...
    piping/           -- Valvulas, reducciones, filtros, bridas...
    instrumentation/  -- Transmisores, controladores, indicadores...
    lines/            -- Estilos de lineas de proceso y senal
  templates/          -- Plantilla .drawio base con capas
  pid-library.xml     -- Biblioteca empaquetada lista para cargar
```

## Instalacion

### Cargar en Draw.io (desktop o web)

1. Abrir Draw.io
2. Menu: **File > Open Library from > URL**
3. Pegar la URL del archivo `pid-library.xml`:
   ```
   https://raw.githubusercontent.com/<org>/pid-inteligente/main/packages/drawio-library/pid-library.xml
   ```
4. La biblioteca aparecera en el panel lateral

### Cargar desde archivo local

1. Descargar `pid-library.xml`
2. En Draw.io: **File > Open Library from > Device**
3. Seleccionar el archivo descargado

### Via parametro clibs (automatico)

Agregar `?clibs=U<url-del-xml>` a la URL de Draw.io para cargar la biblioteca automaticamente al abrir.

## Uso basico

1. Cargar la biblioteca en Draw.io (ver arriba)
2. Abrir la plantilla base desde `templates/` o crear un nuevo diagrama
3. Arrastrar simbolos de la biblioteca al canvas
4. Rellenar los metadatos DEXPI en el panel de propiedades del shape (dexpi_class, tag_number, etc.)
5. Conectar equipos con lineas de proceso (que representan PipingNetworkSegments)
6. Guardar como `.drawio` -- listo para conversion a DEXPI con `pid-converter`

## Categorias de simbolos

| Categoria | Ejemplos | Cantidad aprox. |
|-----------|----------|----------------|
| Equipment | CentrifugalPump, Tank, HeatExchanger, Column, Reactor | ~9 |
| Piping Components | GateValve, ControlValve, CheckValve, Reducer, Tee, Flange | ~15 |
| Instrumentation | Transmitter, Controller, Indicator, Alarm, InstrumentationLoop | ~5 |
| Lines | Process line, Signal line (con atributos diferenciados) | ~2 |
