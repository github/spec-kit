"""The ``specify integration use`` command."""
from __future__ import annotations


import typer

from .._console import console
from ..integration_state import installed_integration_keys as _installed_integration_keys
from ._commands import integration_app
from ._helpers import (
    _read_integration_json,
    _register_extensions_for_agent,
    _register_presets_for_agent,
    _resolve_integration_options,
    _set_default_integration_or_exit,
)


@integration_app.command("use")
def integration_use(
    key: str = typer.Argument(help="Installed integration key to make the default"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing shared infrastructure files, including customizations, while changing the default"),
):
    """Set the default integration without uninstalling other integrations."""
    from . import get_integration
    from .. import _require_specify_project

    project_root = _require_specify_project()
    current = _read_integration_json(project_root)
    installed_keys = _installed_integration_keys(current)
    if key not in installed_keys:
        console.print(f"[red]Error:[/red] Integration '{key}' is not installed.")
        if installed_keys:
            console.print(f"[yellow]Installed integrations:[/yellow] {', '.join(installed_keys)}")
        else:
            console.print("Install one with: [cyan]specify integration install <key>[/cyan]")
        raise typer.Exit(1)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        raise typer.Exit(1)

    raw_options, parsed_options = _resolve_integration_options(integration, current, key, None)
    _set_default_integration_or_exit(
        project_root,
        current,
        key,
        integration,
        installed_keys,
        raw_options=raw_options,
        parsed_options=parsed_options,
        refresh_templates_force=force,
        refresh_hint=(
            "To overwrite customizations, re-run with "
            f"[cyan]specify integration use {key} --force[/cyan]."
        ),
    )
    _register_extensions_for_agent(
        project_root,
        key,
        continuing="The integration was selected, but installed extensions may need re-registration.",
    )
    _register_presets_for_agent(
        project_root,
        key,
        continuing="The integration was selected, but installed presets may need re-registration.",
    )
    console.print(f"[green]✓[/green] Default integration set to [bold]{key}[/bold].")
