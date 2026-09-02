"""Private JSON output helpers for installed preset and extension lists.

This module intentionally serves only the two installed-list commands.  Their
human-facing renderers retain the legacy manager records, while this adapter
defines the public machine-readable wire contract.
"""
from __future__ import annotations

import json
from typing import Any, NoReturn

import click
import typer
from typer.core import TyperCommand


class InstalledListJSONCommand(TyperCommand):
    """Keep JSON list parse failures on the JSON error contract."""

    def make_context(self, info_name, args, parent=None, **extra):
        json_output = "--json" in args
        try:
            return super().make_context(info_name, args, parent=parent, **extra)
        except click.UsageError as error:
            if json_output:
                emit_json_error(error, exit_code=error.exit_code)
            raise


def _normalized_source(source: Any) -> dict[str, str]:
    """Return the stable public source shape for an installed record."""
    if not isinstance(source, dict):
        return {"kind": "local"}

    kind = source.get("kind")
    if kind == "local":
        return {"kind": "local"}
    if kind == "catalog":
        catalog = source.get("catalog")
        if isinstance(catalog, str) and catalog.strip():
            return {"kind": "catalog", "catalog": catalog}

    return {"kind": "local"}


def installed_list_item(record: dict[str, Any], *, include_hooks: bool) -> dict[str, Any]:
    """Return the canonical public JSON object for one installed record."""
    provides = record["_json_provides"]
    if not include_hooks:
        provides = {
            "commands": provides["commands"],
            "templates": provides["templates"],
            "scripts": provides["scripts"],
        }

    return {
        "id": record["id"],
        "name": record["name"],
        "description": record["description"],
        "version": record["version"],
        "author": record["_json_author"],
        "priority": record["priority"],
        "enabled": record["enabled"],
        "source": _normalized_source(record["_json_source"]),
        "provides": provides,
    }


def emit_json(value: Any) -> None:
    """Write one JSON value to stdout without Rich rendering."""
    typer.echo(json.dumps(value, ensure_ascii=False))


def emit_json_error(error: Exception, exit_code: int = 1) -> NoReturn:
    """Write the list-command error contract and terminate unsuccessfully."""
    message = str(error).strip() or error.__class__.__name__
    typer.echo(json.dumps({"error": message}, ensure_ascii=False), err=True)
    raise typer.Exit(code=exit_code)
