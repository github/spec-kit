"""Implementation of ``specify artifact lookup``."""

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
from ._operation_lookup import (
    ArtifactLookupRequest,
    ArtifactLookupResolutionError,
    lookup_artifact,
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


@artifact_app.command("lookup")
def artifact_lookup(
    lookup_id: str = typer.Argument(
        ..., help="Contribution lookupId from an artifact stack."
    ),
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the validated manifest contribution used by Spec Kit as JSON.",
    ),
) -> None:
    """Resolve a stack lookupId to its effective preset or extension contribution."""
    _require_json_flag(json_flag)
    try:
        project_directory = _resolve_project_root()
    except (OSError, RuntimeError):
        _emit_error_and_exit(ArtifactLookupResolutionError(Path("."), lookup_id))
        return  # pragma: no cover

    try:
        result = lookup_artifact(
            ArtifactLookupRequest(
                project_directory=project_directory,
                lookup_id=lookup_id,
            )
        )
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover
    except OSError:
        _emit_error_and_exit(ArtifactLookupResolutionError(Path("."), lookup_id))
        return  # pragma: no cover

    try:
        rendered = json.dumps(
            result.to_json_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        rendered.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError):
        _emit_error_and_exit(ArtifactLookupResolutionError(Path("."), lookup_id))
        return  # pragma: no cover

    sys.stdout.write(rendered)
    sys.stdout.write("\n")
