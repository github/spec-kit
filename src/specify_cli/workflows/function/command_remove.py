"""CLI for removing installed workflow function packages."""

from __future__ import annotations

from .. import _commands as cli
from .. import _package_install as package_install
from . import function_app
from ._domain import FunctionRegistry, WorkflowFunctionError, _validate_function_id
from .installer import _function_install_transaction, _function_spec


@function_app.command("remove")
def workflow_function_remove(
    function_id: str = cli.typer.Argument(..., help="Function package ID to remove")
):
    """Remove a project workflow function package and its metadata."""
    project_root = cli._require_specify_project()
    try:
        _validate_function_id(function_id)
        outcome = package_install.remove_package(
            package_install.RemoveRequest(project_root, function_id),
            _function_spec(),
            package_install.RemoveHooks(
                open_registry=FunctionRegistry,
                transaction=lambda root: _function_install_transaction(root),
            ),
        )
    except WorkflowFunctionError as exc:
        cli._print_package_error(exc)
        raise cli.typer.Exit(1) from exc
    if outcome.orphaned:
        cli.console.print(
            "[yellow]Warning:[/yellow] "
            f"{cli._escape_markup(package_install.orphan_warning(function_id))}"
        )
    cli.console.print(
        f"[green]✓[/green] Workflow function package '{cli._escape_markup(function_id)}' uninstalled"
    )
