"""Implementation of ``specify artifact info``."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer

from . import ArtifactError, ArtifactKind
from ._commands import (
    _emit_error_and_exit,
    _require_json_flag,
    artifact_app,
)
from ._operation_info import (
    ArtifactInfoRequest,
    ArtifactInfoResolutionError,
    get_artifact_info,
)


def _project_directory_from_cli_context() -> Path:
    """Return the explicit project directory selected by the CLI invocation."""
    invocation_directory = Path.cwd()
    override = os.environ.get("SPECIFY_INIT_DIR", "")
    if not override:
        return invocation_directory
    return (invocation_directory / override).resolve()


def _resolve_project_root() -> Path:
    """Preserve the command module's established project-root patch seam."""
    return _project_directory_from_cli_context()


@artifact_app.command("info")
def artifact_info(
    name: str = typer.Argument(..., help="Artifact name, optionally 'kind:name'."),
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the composition stack as a JSON object on stdout.",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Narrow the lookup to one artifact family (command/template/script/hook).",
    ),
) -> None:
    """Show one artifact and its full composition stack."""
    _require_json_flag(json_flag)

    resolved_kind: ArtifactKind | None = None
    if kind is not None:
        if kind not in ("command", "template", "script", "hook"):
            print(
                f"invalid --kind {kind!r}: expected one of command, template, script, hook",
                file=sys.stderr,
            )
            raise typer.Exit(code=2)
        resolved_kind = kind  # type: ignore[assignment]

    try:
        result = get_artifact_info(
            ArtifactInfoRequest(
                project_directory=_resolve_project_root(),
                identifier=name,
                kind=resolved_kind,
            )
        )
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover
    except OSError:
        _emit_error_and_exit(ArtifactInfoResolutionError(Path("."), name))
        return  # pragma: no cover

    sys.stdout.write(
        json.dumps(
            result.to_json_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    sys.stdout.write("\n")
