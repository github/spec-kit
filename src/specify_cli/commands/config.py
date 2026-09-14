"""Project configuration commands for settings persisted by ``specify init``."""

from __future__ import annotations

import json
from typing import Any

import typer
from rich.table import Table
from rich.text import Text

from .._console import console
from .._init_options import INIT_OPTIONS_FILE, load_init_options, save_init_options
from ..extensions import ExtensionManager
from ..extensions._commands import extension_app


config_app = typer.Typer(
    name="config",
    help="View and manage project configuration",
    add_completion=False,
)
config_app.add_typer(extension_app, name="extension")


_INIT_OPTION_KEYS = {
    "ai": "ai",
    "ai-skills": "ai_skills",
    "feature-numbering": "feature_numbering",
    "here": "here",
    "integration": "integration",
    "script": "script",
    "speckit-version": "speckit_version",
}
_FEATURE_NUMBERING = {"sequential", "timestamp"}


def _require_specify_project():
    from .. import _require_specify_project as require_project

    return require_project()


def _canonical_key(key: str) -> str | None:
    return _INIT_OPTION_KEYS.get(key.replace("_", "-").lower())


def _display_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _print_extensions(project_root) -> None:
    installed = ExtensionManager(project_root).list_installed()
    if not installed:
        console.print("\nNo extensions installed.")
        return

    table = Table(title="Extensions")
    table.add_column("ID")
    table.add_column("Status")
    table.add_column("Priority", justify="right")
    table.add_column("Config")
    for extension in installed:
        extension_id = extension["id"]
        table.add_row(
            extension_id,
            "enabled" if extension["enabled"] else "disabled",
            str(extension["priority"]),
            f".specify/extensions/{extension_id}/",
        )
    console.print()
    console.print(table)


@config_app.command("list")
def config_list(
    as_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON"),
) -> None:
    """List initialization settings and installed extensions."""
    project_root = _require_specify_project()
    options = load_init_options(project_root)
    extensions = ExtensionManager(project_root).list_installed()

    if as_json:
        console.print_json(
            json.dumps({"init": options, "extensions": extensions}, ensure_ascii=False)
        )
        return

    table = Table(title="Initialization Settings")
    table.add_column("Key")
    table.add_column("Value")
    for display_key, stored_key in _INIT_OPTION_KEYS.items():
        if stored_key in options:
            table.add_row(display_key, Text(_display_value(options[stored_key])))
    console.print(table)
    _print_extensions(project_root)


@config_app.command("get")
def config_get(key: str = typer.Argument(help="Configuration key")) -> None:
    """Show one persisted initialization setting."""
    stored_key = _canonical_key(key)
    if stored_key is None:
        raise typer.BadParameter(f"Unknown configuration key: {key}")

    options = load_init_options(_require_specify_project())
    if stored_key not in options:
        console.print(f"{key.replace('_', '-')} is not set")
        raise typer.Exit(1)
    console.print(_display_value(options[stored_key]), markup=False)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Configuration key"),
    value: str = typer.Argument(help="New value"),
) -> None:
    """Change a supported initialization setting."""
    normalized_key = key.replace("_", "-").lower()
    project_root = _require_specify_project()
    # A failed read must not turn a partial update into replacement of all settings.
    try:
        options = load_init_options(project_root, strict=True)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            "Cannot read .specify/init-options.json. Repair the file before changing settings."
        ) from exc

    if normalized_key == "script":
        raise typer.BadParameter(
            "script is managed by specify integration upgrade <key> --script <type>"
        )
    if normalized_key == "feature-numbering":
        normalized_value = value.lower()
        if normalized_value not in _FEATURE_NUMBERING:
            raise typer.BadParameter(
                "feature-numbering must be one of: sequential, timestamp"
            )
        options["feature_numbering"] = normalized_value
    elif normalized_key in {"ai", "integration"}:
        raise typer.BadParameter(
            f"{normalized_key} is managed by specify integration use {value}"
        )
    elif normalized_key == "ai-skills":
        raise typer.BadParameter(
            "ai-skills is managed by specify integration upgrade <key> --integration-options. "
            "Options depend on the integration; see specify integration upgrade --help."
        )
    elif normalized_key in {"here", "speckit-version"}:
        raise typer.BadParameter(f"{normalized_key} is read-only")
    else:
        raise typer.BadParameter(f"Unknown configuration key: {key}")

    # An options file without an active agent disables legacy command registration.
    if not (project_root / INIT_OPTIONS_FILE).exists():
        raise typer.BadParameter(
            "This legacy project has no .specify/init-options.json. "
            "Run specify integration install <key> first "
            "(or specify integration use <key> if already installed), then retry."
        )

    save_init_options(project_root, options)
    console.print(f"Updated {normalized_key}")


def register(app: typer.Typer) -> None:
    """Attach the configuration command group to the root Typer app."""
    app.add_typer(config_app, name="config")
