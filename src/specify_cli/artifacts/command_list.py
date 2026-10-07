"""Implementation of ``specify artifact list``."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer

from . import ArtifactError
from ._commands import (
    _emit_error_and_exit,
    _require_json_flag,
    artifact_app,
)
from ._operation_list import (
    ArtifactListRequest,
    ArtifactListResolutionError,
    list_artifacts,
)


def _project_directory_from_cli_context() -> Path:
    """Return the explicit project directory selected by the CLI invocation."""
    invocation_directory = Path.cwd()
    override = os.environ.get("SPECIFY_INIT_DIR", "")
    if not override:
        return invocation_directory
    return (invocation_directory / override).resolve()


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
        result = list_artifacts(
            ArtifactListRequest(
                project_directory=_project_directory_from_cli_context(),
            )
        )
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover — _emit_error_and_exit raises
    except OSError:
        _emit_error_and_exit(ArtifactListResolutionError(Path(".")))
        return  # pragma: no cover — _emit_error_and_exit raises

    sys.stdout.write(
        json.dumps(result.rows, indent=2, sort_keys=True, ensure_ascii=False)
    )
    sys.stdout.write("\n")
