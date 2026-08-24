"""Typer sub-app for the `specify artifact` command group.

Kept intentionally thin: the pure logic lives in ``specify_cli.artifacts``.
This module is only responsible for CLI wiring — argument parsing, JSON
serialization, exit-code selection, and error-envelope emission on stderr.

Mirrors the shape used by ``src/specify_cli/presets/_commands.py`` and
``src/specify_cli/extensions/_commands.py``: a module-level Typer app plus a
``register(app)`` entry point invoked from ``src/specify_cli/__init__.py``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer

from . import (
    ArtifactCatalog,
    ArtifactError,
    ArtifactKind,
    ArtifactResolutionError,
    NotASpecKitProjectError,
)
from ..presets import PresetError

artifact_app = typer.Typer(
    name="artifact",
    help="Introspect commands, templates, and scripts SpecKit exposes.",
    no_args_is_help=True,
)


def _resolve_project_root() -> Path:
    """Return the project root without emitting Rich output on failure.

    The stdout of ``specify artifact list --json`` and ``specify artifact
    info <name> --json`` is a strict JSON envelope; any incidental Rich
    output would corrupt it. The shared ``_resolve_init_dir_override`` emits
    Rich errors for invalid overrides, so validate the override quietly here
    and raise the module-local :class:`NotASpecKitProjectError` for the shared
    error handler to serialize.
    """
    raw_override = os.environ.get("SPECIFY_INIT_DIR", "")
    cwd = (Path.cwd() / raw_override).resolve() if raw_override else Path.cwd()
    if not (cwd / ".specify").is_dir():
        raise NotASpecKitProjectError()
    return cwd


def _emit_error_and_exit(exc: ArtifactError) -> None:
    """Write ``{"error": "..."}`` to stderr and exit with code 1.

    The stdout stream is left completely untouched — the contract is that
    machine consumers can rely on an empty stdout when the exit code is
    non-zero, so no partial JSON payload leaks even on a late-stage failure.
    """
    payload = json.dumps({"error": exc.message}, ensure_ascii=False)
    print(payload, file=sys.stderr)
    raise typer.Exit(code=1)


def _require_json_flag(json_flag: bool) -> None:
    """Enforce the opt-in ``--json`` contract shared by both subcommands.

    A text-mode formatter is intentionally deferred so the initial release
    can commit to exactly one output shape. Callers that omit ``--json``
    get a usage error (exit 2) with no stdout output — this makes future
    addition of a default text renderer a purely additive, non-breaking
    change.
    """
    if json_flag:
        return
    print(
        "specify artifact requires --json for now; text output is not yet implemented.",
        file=sys.stderr,
    )
    raise typer.Exit(code=2)


@artifact_app.command("list")
def list_command(
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the inventory as a JSON array on stdout.",
    ),
) -> None:
    """List every command, template, and script SpecKit exposes."""
    _require_json_flag(json_flag)
    try:
        root = _resolve_project_root()
        catalog = ArtifactCatalog(root)
        rows = [artifact.to_json_dict() for artifact in catalog.list_artifacts()]
    except ArtifactError as exc:
        _emit_error_and_exit(exc)
        return  # pragma: no cover — _emit_error_and_exit raises
    except PresetError:
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover — _emit_error_and_exit raises

    sys.stdout.write(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False))
    sys.stdout.write("\n")


@artifact_app.command("info")
def info_command(
    name: str = typer.Argument(..., help="Artifact name, optionally 'kind:name'."),
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the composition stack as a JSON object on stdout.",
    ),
    kind: Optional[str] = typer.Option(
        None,
        "--kind",
        help="Narrow the lookup to one artifact family (command/template/script).",
    ),
) -> None:
    """Show one artifact and its full composition stack."""
    _require_json_flag(json_flag)

    resolved_kind: Optional[ArtifactKind] = None
    if kind is not None:
        if kind not in ("command", "template", "script"):
            print(
                f"invalid --kind {kind!r}: expected one of command, template, script",
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
    except PresetError:
        _emit_error_and_exit(ArtifactResolutionError())
        return  # pragma: no cover

    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    sys.stdout.write("\n")


def register(app: typer.Typer) -> None:
    """Attach the artifact command group to the root Typer app."""
    app.add_typer(artifact_app, name="artifact")
