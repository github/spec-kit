"""Shared helpers for extension catalog commands."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .. import _commands


def load_catalog_command_config(project_root: Path, config_path: Path) -> dict:
    """Load extension catalog CLI config with user-facing shape errors."""
    try:
        config = _commands.yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as error:
        config_label = _escape_markup(
            str(_commands._display_project_path(project_root, config_path))
        )
        _commands.console.print(
            f"[red]Error:[/red] Failed to read {config_label}: "
            f"{_escape_markup(str(error))}"
        )
        raise typer.Exit(1)

    if config is None:
        return {}
    if not isinstance(config, dict):
        config_label = _escape_markup(
            str(_commands._display_project_path(project_root, config_path))
        )
        _commands.console.print(
            f"[red]Error:[/red] Invalid catalog config {config_label}: "
            "expected a YAML mapping at the root."
        )
        raise typer.Exit(1)
    return config
