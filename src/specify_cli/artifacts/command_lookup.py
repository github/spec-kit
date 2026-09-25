"""Implementation of ``specify artifact lookup``."""

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


@artifact_app.command("lookup")
def artifact_lookup(
    lookup_id: str = typer.Argument(..., help="Contribution lookupId from an artifact stack."),
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the validated manifest contribution used by Spec Kit as JSON.",
    ),
) -> None:
    """Resolve a stack lookupId to its effective preset or extension contribution."""
    _require_json_flag(json_flag)
    try:
        root = _resolve_project_root()
        payload = ArtifactCatalog(root).get_contribution_info(lookup_id)
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover
    except (OSError, PresetError):
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover

    try:
        rendered = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        rendered.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover

    sys.stdout.write(rendered)
    sys.stdout.write("\n")
