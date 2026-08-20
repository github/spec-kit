"""Shared project-resolution helpers for the Specify CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from ._console import err_console


class ProjectResolutionError(RuntimeError):
    """A project-root error that callers can render for their own surface."""


def _resolve_init_dir_override_unrendered() -> Path | None:
    """Resolve ``SPECIFY_INIT_DIR`` without emitting user-facing output."""
    raw = os.environ.get("SPECIFY_INIT_DIR", "")
    if not raw:
        return None
    init_root = (Path.cwd() / raw).resolve()
    if not init_root.is_dir():
        raise ProjectResolutionError(
            f"SPECIFY_INIT_DIR does not point to an existing directory: {raw}"
        )
    if not (init_root / ".specify").is_dir():
        raise ProjectResolutionError(
            "SPECIFY_INIT_DIR is not a Spec Kit project "
            f"(no .specify/ directory): {init_root}"
        )
    return init_root


def _resolve_init_dir_override() -> Path | None:
    """Resolve the ``SPECIFY_INIT_DIR`` project override for the Python CLI.

    Applies the same validation rules as the shell resolver
    (``resolve_specify_init_dir`` in ``scripts/bash/common.sh``): the value names
    the project root — the directory *containing* ``.specify/`` — and is strict.
    Relative paths resolve against the current directory; the path must exist and
    contain ``.specify/``, otherwise this hard-errors with no fallback to cwd
    (which would silently operate on the wrong project's files). The error
    messages mirror the shell resolver's wording (rendered here as a Rich
    ``Error:`` line, plain ``ERROR:`` in the shell) so the two surfaces read
    consistently.

    Returns the validated absolute project root, or ``None`` when the variable is
    unset/empty, in which case callers keep their existing cwd-based behavior.

    Note: this canonicalizes symlinks via :meth:`Path.resolve` (physical path),
    whereas the shell ``cd -- "$X" && pwd`` keeps the logical path. The two agree
    for non-symlinked paths; a symlinked ``SPECIFY_INIT_DIR`` can resolve to
    different strings across the surfaces. The canonical form is the safer choice
    here (a stable project identity), so this is a deliberate, documented variance,
    not a parity guarantee on the resolved string.
    """
    try:
        return _resolve_init_dir_override_unrendered()
    except ProjectResolutionError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(1)


def resolve_specify_project_root() -> Path:
    """Return the active project root without rendering errors.

    This is deliberately separate from ``_require_specify_project`` so the
    installed-list JSON contract can send structured failures to stderr without
    changing the Rich diagnostics used by every other project-scoped command.
    """
    override = _resolve_init_dir_override_unrendered()
    if override is not None:
        return override
    project_root = Path.cwd()
    if not (project_root / ".specify").is_dir():
        raise ProjectResolutionError("Not a Spec Kit project (no .specify/ directory)")
    return project_root
