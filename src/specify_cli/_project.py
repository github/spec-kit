"""Shared project-resolution helpers for the Specify CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from ._console import err_console


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
    raw = os.environ.get("SPECIFY_INIT_DIR", "")
    if not raw:
        return None
    # Relative values resolve against cwd; an absolute value stands alone (Path's
    # `/` drops the left operand when the right is absolute). resolve() also
    # collapses a trailing slash and canonicalizes symlinks.
    init_root = (Path.cwd() / raw).resolve()
    if not init_root.is_dir():
        err_console.print(
            f"[red]Error:[/red] SPECIFY_INIT_DIR does not point to an existing directory: {raw}"
        )
        raise typer.Exit(1)
    if not (init_root / ".specify").is_dir():
        err_console.print(
            f"[red]Error:[/red] SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): {init_root}"
        )
        raise typer.Exit(1)
    return init_root
