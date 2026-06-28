"""specify integration scaffold command handler."""
from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from .._console import console
from ..integration_scaffold import supported_integration_scaffold_types
from ._commands import integration_app


INTEGRATION_SCAFFOLD_TYPES = supported_integration_scaffold_types()
_IntegrationScaffoldType = Enum(
    "_IntegrationScaffoldType",
    {name: name for name in INTEGRATION_SCAFFOLD_TYPES},
    type=str,
)


@integration_app.command("scaffold")
def integration_scaffold(
    key: str = typer.Argument(help="Integration key in lowercase kebab-case, e.g. my-agent"),
    integration_type: _IntegrationScaffoldType = typer.Option(
        _IntegrationScaffoldType.markdown,
        "--type",
        case_sensitive=False,
        help=f"Scaffold type: {', '.join(INTEGRATION_SCAFFOLD_TYPES)}",
    ),
):
    """Create a minimal built-in integration package and test skeleton."""
    from ..integration_scaffold import scaffold_integration

    project_root = Path.cwd()
    try:
        result = scaffold_integration(project_root, key, integration_type.value)
    except (OSError, ValueError) as exc:
        # OSError covers filesystem failures during mkdir()/write_text()
        # (permission denied, read-only checkout, a path component that is a
        # file, ...) as well as FileExistsError; surface them as a clean CLI
        # error instead of a traceback.
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]Created integration scaffold:[/green] {result.key}")
    console.print(f"  {result.integration_file.relative_to(project_root).as_posix()}")
    console.print(f"  {result.test_file.relative_to(project_root).as_posix()}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    for index, step in enumerate(result.next_steps, start=1):
        console.print(f"{index}. {step}")
