"""Typer sub-app for the `specify artifact` command group.

Kept intentionally thin: the pure logic lives in ``specify_cli.artifacts``.
This module is only responsible for CLI wiring — argument parsing, JSON
serialization, exit-code selection, and error-envelope emission on stderr.

Mirrors the shape used by ``src/specify_cli/presets/_commands.py`` and
``src/specify_cli/extensions/_commands.py``: a module-level Typer app plus a
``register(app)`` entry point invoked from ``src/specify_cli/__init__.py``.

The user-facing contract for both subcommands — the ``list``/``info`` JSON
shapes, stack semantics (``active``/``hidden``, built-in rows, lookup IDs), and
the JSON error envelope — is documented in ``docs/reference/artifacts.md``.
"""

from __future__ import annotations

import contextlib
import io
import json
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
    help="Introspect commands, templates, scripts, and hooks SpecKit exposes.",
    no_args_is_help=True,
)


def _resolve_project_root() -> Path:
    """Return the project root without emitting Rich output on failure.

    Delegates to :func:`specify_cli._require_specify_project` — the same
    resolution chokepoint every other project-scoped subcommand (``preset``,
    ``extension``, ``workflow``, ...) uses, including its ``SPECIFY_INIT_DIR``
    override handling. That helper prints Rich error output and raises
    ``typer.Exit`` on failure, which would corrupt the strict JSON envelope
    ``specify artifact list --json`` and ``specify artifact info --json``
    emit on stdout/stderr. The Rich output is suppressed here and the
    failure is re-raised as the module-local :class:`NotASpecKitProjectError`
    for the shared error handler to serialize instead.
    """
    from .. import _require_specify_project  # lazy: avoids circular import

    with contextlib.redirect_stderr(io.StringIO()):
        try:
            return _require_specify_project()
        except typer.Exit:
            raise NotASpecKitProjectError() from None


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
def artifact_list(
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the inventory as a JSON array on stdout.",
    ),
) -> None:
    """List every command, template, script, and hook SpecKit exposes."""
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


@artifact_app.command("info")
def artifact_info(
    name: str = typer.Argument(..., help="Artifact name, optionally 'kind:name'."),
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the composition stack as a JSON object on stdout.",
    ),
    kind: Optional[str] = typer.Option(
        None,
        "--kind",
        help="Narrow the lookup to one artifact family (command/template/script/hook).",
    ),
) -> None:
    """Show one artifact and its full composition stack."""
    _require_json_flag(json_flag)

    resolved_kind: Optional[ArtifactKind] = None
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


def register(app: typer.Typer) -> None:
    """Attach the artifact command group to the root Typer app."""
    app.add_typer(artifact_app, name="artifact")
