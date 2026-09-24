"""Shared validation helpers for workflow step commands.

This module preserves the CLI-coupled ``*_or_exit`` entry points used by the
registered step commands. The behavior now lives in
:mod:`specify_cli.workflows.step.installer`; these wrappers print the shared
error prefix and exit, while the domain module stays CLI-independent.
"""

from __future__ import annotations

from .. import _commands as cli
from .installer import (
    _MAX_STEP_PACKAGE_BYTES,
    _MAX_STEP_PACKAGE_FILES,
    StepInstallError,
    resolve_steps_base_dir,
    validate_step_id,
)

__all__ = [
    "_MAX_STEP_PACKAGE_BYTES",
    "_MAX_STEP_PACKAGE_FILES",
    "StepInstallError",
    "resolve_steps_base_dir",
    "validate_step_id",
]


def _validate_step_id_or_exit(step_id: str) -> None:
    """Validate that ``step_id`` is a single safe path component.

    Exits with code 1 on failure.
    """
    try:
        validate_step_id(step_id)
    except StepInstallError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1) from exc


def _resolve_steps_base_dir_or_exit(project_root: cli.Path) -> cli.Path:
    """Resolve .specify/workflows/steps while refusing symlinked parent directories."""
    try:
        return resolve_steps_base_dir(project_root)
    except StepInstallError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1) from exc
