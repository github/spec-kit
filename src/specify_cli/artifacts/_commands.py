"""Shared infrastructure and registration for ``specify artifact`` commands.

Command handlers live in ``command_*.py`` modules. Domain behavior remains in
Typer-free modules in this package, following ``design/cli.md``.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import typer

from . import (
    ArtifactError,
    NotASpecKitProjectError,
)

artifact_app = typer.Typer(
    name="artifact",
    help="Introspect commands, templates, scripts, and hooks Spec Kit exposes.",
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
    """Enforce the opt-in ``--json`` contract shared by artifact commands.

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


def register(app: typer.Typer) -> None:
    """Attach the artifact command group to the root Typer app."""
    # isort: off
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_info  # noqa: F401 — registers handler via decorator
    from . import command_lookup  # noqa: F401 — registers handler via decorator
    # isort: on

    app.add_typer(artifact_app, name="artifact")
