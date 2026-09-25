"""Command handler for ``specify workflow step remove``."""

from __future__ import annotations

from .. import _commands as cli
from . import _helpers as step_helpers
from . import step_app


@step_app.command("remove")
def workflow_step_remove(
    step_id: str = cli.typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    import shutil

    from . import installer

    project_root = cli._require_specify_project()

    step_helpers._validate_step_id_or_exit(step_id)

    try:
        staged_dir, removed_orphan = installer.remove_step_package(project_root, step_id)
    except installer.StepInstallError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1) from exc
    if removed_orphan:
        cli.console.print(
            f"[yellow]Warning:[/yellow] '{cli._escape_markup(step_id)}' had no registry "
            "entry. Removing the orphaned directory."
        )
    cli.console.print(f"[green]✓[/green] Step type '{cli._escape_markup(step_id)}' uninstalled")
    if staged_dir is not None:
        try:
            shutil.rmtree(staged_dir)
        except OSError as exc:
            cli.console.print(
                "[yellow]Warning:[/yellow] Step was uninstalled, but its staged "
                f"directory could not be deleted: {cli._escape_markup(str(exc))}. "
                f"Remove it manually: {cli._escape_markup(str(staged_dir))}"
            )
