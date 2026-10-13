"""Command handler for ``specify workflow overlay add``."""

from __future__ import annotations

from .. import _commands as cli
from . import overlay_app


@overlay_app.command("add")
def workflow_overlay_add_cmd(
    source: cli.Path = cli.typer.Argument(..., help="Path to overlay YAML file"),
    priority: int = cli.typer.Option(
        10,
        "--priority",
        help="Resolution priority (lower = higher precedence, default 10)",
    ),
):
    """Add a project-local overlay for a workflow."""
    from .operations import workflow_overlay_add

    project_root = cli._require_specify_project()
    if workflow_overlay_add(project_root, source, priority) is None:
        raise cli.typer.Exit(1)
