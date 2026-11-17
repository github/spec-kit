"""Shared infrastructure and registration for ``specify artifact`` commands.

Command handlers live in ``command_*.py`` modules. Domain behavior remains in
Typer-free modules in this package, following ``design/cli.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ..symlink_warning import symlink_error_message
from . import (
    ArtifactError,
    ArtifactResolutionError,
    NotASpecKitProjectError,
)

artifact_app = typer.Typer(
    name="artifact",
    help="Introspect commands, templates, scripts, and hooks Spec Kit exposes.",
    no_args_is_help=True,
)


def _resolve_project_root() -> Path:
    """Resolve the project without rendering or consuming pending diagnostics."""
    from .._file_policy import ProjectPolicyError
    from .._project import ProjectResolutionError, resolve_specify_project_root

    try:
        root = resolve_specify_project_root()
    except ProjectResolutionError as exc:
        if isinstance(exc.__cause__, ProjectPolicyError):
            error = ArtifactError(str(exc))
            error.message = str(exc)
            raise error from exc
        raise NotASpecKitProjectError() from None
    from ..integrations.installer import (
        IntegrationInstallError,
        load_installed_integrations,
    )

    try:
        load_installed_integrations(root)
    except (IntegrationInstallError, OSError) as exc:
        raise ArtifactResolutionError(str(exc)) from exc
    return root


def _emit_error_and_exit(exc: ArtifactError) -> None:
    """Write ``{"error": "..."}`` to stderr and exit with code 1.

    The stdout stream is left completely untouched — the contract is that
    machine consumers can rely on an empty stdout when the exit code is
    non-zero, so no partial JSON payload leaks even on a late-stage failure.
    """
    payload = json.dumps({"error": symlink_error_message(exc.message)}, ensure_ascii=False)
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
