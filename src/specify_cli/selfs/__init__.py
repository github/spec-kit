"""Nested command group for ``specify self``.

The plural Python package name follows the repository's command-hierarchy
convention even though the user-facing CLI namespace is singular.
"""

import typer

self_app = typer.Typer(
    name="self",
    help=(
        "Manage the specify CLI itself: check for newer releases, "
        "preview upgrades with --dry-run, and upgrade in place."
    ),
    add_completion=False,
)


def _register_commands():
    """Register command adapters and return compatibility exports."""
    from .command_check import self_check
    from .command_upgrade import self_upgrade

    return self_check, self_upgrade


self_check, self_upgrade = _register_commands()
del _register_commands
