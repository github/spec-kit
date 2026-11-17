"""Command handler for ``specify workflow step remove``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app

from . import _helpers as step_helpers


def _step_remove_hooks(installer):
    from .. import _package_install as package_install

    return package_install.RemoveHooks(
        open_registry=lambda root: installer._open_registry(root),
        transaction=lambda root: installer._step_install_transaction(root),
    )


def _print_orphan_warning(step_id: str) -> None:
    from .. import _package_install as package_install

    cli.console.print(
        "[yellow]Warning:[/yellow] "
        f"{cli._escape_markup(package_install.orphan_warning(step_id))}"
    )


def _remove_step_locked(project_root: cli.Path, step_id: str) -> None:
    """Remove a step's registry entry and directory while the lock is held.

    The registry and step directory are resolved here, after the lock is
    acquired, so a concurrent install cannot be lost or resurrected by a stale
    registry snapshot. Domain failures are rendered and exit with code 1.
    """
    from .. import _package_install as package_install
    from . import installer

    try:
        outcome = package_install.remove_package_locked(
            package_install.RemoveRequest(project_root, step_id),
            installer._step_spec(),
            _step_remove_hooks(installer),
        )
    except installer.StepInstallError as exc:
        cli._print_package_error(exc)
        raise cli.typer.Exit(1) from exc
    if outcome.orphaned:
        _print_orphan_warning(step_id)


@step_app.command("remove")
def workflow_step_remove(
    step_id: str = cli.typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    from .. import _package_install as package_install
    from . import installer

    project_root = cli._require_specify_project()

    step_helpers._validate_step_id_or_exit(step_id)

    # Removal mutates the same directory and registry as `step add`, so it
    # shares the install lock to prevent lost or resurrected registry entries.
    try:
        outcome = package_install.remove_package(
            package_install.RemoveRequest(project_root, step_id),
            installer._step_spec(),
            _step_remove_hooks(installer),
        )
    except installer.StepInstallError as exc:
        cli._print_package_error(exc)
        raise cli.typer.Exit(1) from exc

    if outcome.orphaned:
        _print_orphan_warning(step_id)
    cli.console.print(
        f"[green]✓[/green] Step type '{cli._escape_markup(step_id)}' uninstalled"
    )
