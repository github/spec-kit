"""CLI for listing installed workflow function metadata."""

from __future__ import annotations

import json

from .. import _commands as cli
from . import function_app
from ._domain import FunctionRegistry
from ..expressions.filters import format_filter_usage, valid_arg_bounds


@function_app.command("list")
def workflow_function_list(
    json_output: bool = cli.typer.Option(False, "--json", help="Emit machine-readable JSON")
):
    """List installed workflow functions without importing package code."""
    project_root = cli._require_specify_project()
    registry = FunctionRegistry(project_root)
    installed = registry.list()
    rows = []
    for function_id in sorted(installed):
        metadata = installed[function_id]
        if not isinstance(metadata, dict):
            continue
        functions = []
        for item in metadata.get("functions", []):
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            minimum = item.get("min_args", 0)
            maximum = item.get("max_args", 0)
            if not valid_arg_bounds(minimum, maximum):
                minimum, maximum = 0, 0
            functions.append({
                "name": name,
                "handler": item.get("handler", ""),
                "min_args": minimum,
                "max_args": maximum,
                "description": item.get("description", ""),
                "usage": format_filter_usage(name, minimum, maximum),
            })
        rows.append({
            "id": function_id,
            "name": metadata.get("name", function_id),
            "version": metadata.get("version", "0.0.0"),
            "source": metadata.get("source", ""),
            "description": metadata.get("description", ""),
            "functions": functions,
        })
    if json_output:
        print(json.dumps(rows, ensure_ascii=False))
        return
    cli.console.print("\n[bold cyan]Installed Workflow Functions:[/bold cyan]\n")
    if not rows:
        cli.console.print("[yellow]No workflow functions installed.[/yellow]")
        return
    for row in rows:
        cli.console.print(
            f"  • [bold]{cli._escape_markup(str(row['name']))}[/bold] "
            f"({cli._escape_markup(str(row['id']))}) v{cli._escape_markup(str(row['version']))}"
        )
        for function in row["functions"]:
            cli.console.print(
                f"    - {cli._escape_markup(str(function['usage']))}: "
                f"{cli._escape_markup(str(function['description']))}"
            )
