"""Command-line interface for pid-converter.

Commands
--------
* ``pid-converter convert <input.drawio> -o <output.xml>``  -- Draw.io to DEXPI
* ``pid-converter import <input.xml> -o <output.drawio>``   -- DEXPI to Draw.io
* ``pid-converter validate <input.drawio>``                 -- validate P&ID
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="pid-converter",
    help="Bidirectional converter between Draw.io and DEXPI Proteus XML for P&ID diagrams.",
    add_completion=False,
)
console = Console()


@app.command()
def convert(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to a .drawio file to convert"),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("-o", "--output", help="Output path for the Proteus XML file"),
    ] = None,
) -> None:
    """Convert a Draw.io P&ID to DEXPI Proteus XML."""
    from pid_converter.mapper import map_to_dexpi
    from pid_converter.mapper.dexpi_mapper import (
        get_equipment,
        get_instruments,
        get_nozzles,
        get_piping_segments,
    )
    from pid_converter.parser import parse_drawio
    from pid_converter.serializer import serialize_to_proteus

    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(code=1)

    out_path = output or input_file.with_suffix(".xml")

    console.print(f"[cyan]Parsing[/cyan] {input_file} ...")
    model = parse_drawio(input_file)
    console.print(
        f"  Found [green]{len(model.nodes)}[/green] nodes, "
        f"[green]{len(model.edges)}[/green] edges"
    )

    console.print("[cyan]Mapping[/cyan] to DEXPI model ...")
    dexpi = map_to_dexpi(model)
    console.print(
        f"  Equipment: {len(get_equipment(dexpi))}, "
        f"Nozzles: {len(get_nozzles(dexpi))}, "
        f"Piping segments: {len(get_piping_segments(dexpi))}, "
        f"Instruments: {len(get_instruments(dexpi))}"
    )

    console.print(f"[cyan]Serializing[/cyan] to {out_path} ...")
    serialize_to_proteus(dexpi, out_path)
    console.print(f"[green]Done![/green] Proteus XML written to {out_path}")


@app.command(name="import")
def import_cmd(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to a DEXPI Proteus XML file"),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("-o", "--output", help="Output path for the .drawio file"),
    ] = None,
) -> None:
    """Import a DEXPI Proteus XML file and generate a Draw.io file."""
    from pid_converter.importer import import_dexpi

    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(code=1)

    out_path = output or input_file.with_suffix(".drawio")

    console.print(f"[cyan]Importing[/cyan] {input_file} ...")
    import_dexpi(input_file, out_path)
    console.print(f"[green]Done![/green] Draw.io file written to {out_path}")


@app.command()
def validate(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to a .drawio file to validate"),
    ],
) -> None:
    """Validate a P&ID for completeness and consistency."""
    from pid_converter.parser import parse_drawio
    from pid_converter.topology import resolve_topology
    from pid_converter.validator import validate_pid

    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Validating[/cyan] {input_file} ...")
    model = parse_drawio(input_file)
    resolve_topology(model)
    errors = validate_pid(model)

    if not errors:
        console.print("[green]No validation errors found.[/green]")
        return

    table = Table(title=f"Validation Results ({len(errors)} issues)")
    table.add_column("Shape ID", style="cyan")
    table.add_column("Error Type", style="yellow")
    table.add_column("Message")

    for err in errors:
        table.add_row(err.shape_id, err.error_type.value, err.message)

    console.print(table)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
