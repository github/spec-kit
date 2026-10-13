"""Implementation of the ``specify preset update`` command."""

from __future__ import annotations

import os
import shlex

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands
from ._commands import preset_app


@preset_app.command("update")
def preset_update(
    preset_id: str = typer.Argument(..., help="Installed preset ID to replace"),
    from_url: str = typer.Option(
        None,
        "--from",
        help="Install the replacement from a .zip, .tar.gz, or .tgz URL",
    ),
    dev: str = typer.Option(
        None,
        "--dev",
        help="Install the replacement from a local directory (development mode)",
    ),
    priority: int = typer.Option(
        10,
        "--priority",
        help="Resolution priority for the replacement (default 10)",
    ),
):
    """Replace an installed preset using the normal remove and add flows."""
    from .. import _require_specify_project
    from . import PresetManager

    if from_url is not None and dev is not None:
        console.print("[red]Error:[/red] --from and --dev are mutually exclusive")
        raise typer.Exit(1)
    if from_url == "":
        console.print("[red]Error:[/red] --from must not be empty")
        raise typer.Exit(1)
    if dev == "":
        console.print("[red]Error:[/red] --dev must not be empty")
        raise typer.Exit(1)

    _commands._validate_priority(priority)

    project_root = _require_specify_project()
    manager = PresetManager(project_root)
    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    _commands.preset_remove(preset_id)

    retry_args = ["specify", "preset", "add"]
    retry_options = []
    if from_url is not None:
        retry_options.extend(["--from", from_url])
    if dev is not None:
        retry_options.extend(["--dev", dev])
    retry_options.extend(["--priority", str(priority)])
    if preset_id.startswith("-"):
        retry_args.extend([*retry_options, "--", preset_id])
    else:
        retry_args.extend([preset_id, *retry_options])

    def report_add_failure() -> None:
        if os.name == "nt":
            retry_label = "Retry in PowerShell: "
            rendered_args = _commands._render_powershell_argv(retry_args)
        else:
            retry_label = "Retry with: "
            rendered_args = shlex.join(retry_args)
        console.print(
            "[red]Error:[/red] Preset update failed; the previous preset was removed."
        )
        console.print(
            f"{retry_label}[cyan]{_escape_markup(rendered_args)}[/cyan]",
            soft_wrap=True,
        )

    try:
        _commands.preset_add(
            preset_id=preset_id,
            from_url=from_url,
            dev=dev,
            priority=priority,
        )
    except typer.Exit as error:
        report_add_failure()
        raise typer.Exit(error.exit_code or 1)
    except Exception as error:
        console.print(f"[red]Error:[/red] {_escape_markup(str(error))}")
        report_add_failure()
        raise typer.Exit(1)
