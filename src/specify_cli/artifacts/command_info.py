"""Implementation of ``specify artifact info``."""

from __future__ import annotations

import json
import sys

import typer

from ..presets import PresetError
from . import (
    ArtifactCatalog,
    ArtifactError,
    ArtifactKind,
    ArtifactResolutionError,
)
from ._commands import (
    _emit_error_and_exit,
    _require_json_flag,
    _resolve_project_root,
    artifact_app,
)


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
        root = _resolve_project_root()
        catalog = ArtifactCatalog(root)
        payload = catalog.get_artifact_info(name, kind=resolved_kind)
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover
    except (OSError, PresetError):
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover

    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    sys.stdout.write("\n")
