"""Implementation of ``specify artifact list``."""

from __future__ import annotations

import json
import sys

import typer

from ..presets import PresetError
from . import ArtifactCatalog, ArtifactError, ArtifactResolutionError
from ._commands import (
    _emit_error_and_exit,
    _require_json_flag,
    _resolve_project_root,
    artifact_app,
)


@artifact_app.command("list")
def artifact_list(
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the inventory as a JSON array on stdout.",
    ),
) -> None:
    """List every command, template, script, and hook Spec Kit exposes."""
    _require_json_flag(json_flag)
    try:
        root = _resolve_project_root()
        catalog = ArtifactCatalog(root)
        rows = catalog.list_artifacts_with_stack()
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover — _emit_error_and_exit raises
    except (OSError, PresetError):
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover — _emit_error_and_exit raises

    sys.stdout.write(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False))
    sys.stdout.write("\n")
