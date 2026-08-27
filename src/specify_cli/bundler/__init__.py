"""Spec Kit bundler — importable, Typer-free logic for the ``specify bundle`` group.

This package holds the models, services, and helpers behind the ``specify bundle``
subcommand. It is intentionally free of any Typer/CLI imports so the orchestration
logic can be unit-tested independently of the command surface (Constitution
Principle I). The CLI wiring lives in ``specify_cli.commands.bundle``.
"""
from __future__ import annotations

__all__ = ["BundlerError"]


class BundlerError(Exception):
    """Base class for all actionable bundler errors.

    Carrying a clean message lets the CLI layer print a single, user-facing line
    on stderr and exit non-zero without leaking a traceback (Constitution
    Principle V — explicit, actionable errors).
    """
