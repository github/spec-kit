"""Command handler for ``specify workflow step remove``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app

from . import _helpers as step_helpers


@step_app.command("remove")
def workflow_step_remove(
    step_id: str = cli.typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    from .catalog import StepRegistry, StepValidationError

    project_root = cli._require_specify_project()

    step_helpers._validate_step_id_or_exit(step_id)

    registry = StepRegistry(project_root)
    in_registry = registry.is_installed(step_id)

    steps_base_dir = step_helpers._resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: even though step_helpers._validate_step_id_or_exit rejects path
    # separators, ensure that the resolved directory is a single child of
    # steps_base_dir and is not steps_base_dir itself.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        cli.console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise cli.typer.Exit(1)
    if rel_parts != (step_id,):
        cli.console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise cli.typer.Exit(1)

    dir_exists = step_dir.exists()

    if not in_registry and not dir_exists:
        cli.console.print(f"[red]Error:[/red] Step type '{step_id}' is not installed")
        raise cli.typer.Exit(1)

    if not in_registry and dir_exists:
        # The registry was likely reset due to corruption.  Warn the user that the
        # directory is being removed even though there is no registry entry, so
        # the orphaned package can be cleaned up and a fresh install attempted.
        cli.console.print(
            f"[yellow]Warning:[/yellow] '{step_id}' has no registry entry "
            "(registry may have been reset). Removing the orphaned directory."
        )

    if dir_exists and not in_registry:
        # No registry write needed; just delete the orphaned directory.
        import shutil

        try:
            shutil.rmtree(step_dir)
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
            )
            raise cli.typer.Exit(1)
    elif in_registry:
        # Remove the registry entry, then the directory. If the directory
        # delete fails, restore the registry entry so state stays consistent
        # and a future `step add` isn't blocked by an orphaned directory
        # with no registry entry.
        registry_metadata = registry.get(step_id)
        try:
            registry.remove(step_id)
        except StepValidationError as exc:
            cli.console.print(f"[red]Error:[/red] {exc}")
            raise cli.typer.Exit(1)
        if dir_exists:
            import shutil

            try:
                shutil.rmtree(step_dir)
            except OSError as exc:
                # Restore the original registry entry verbatim (bypass add()
                # which would overwrite timestamps).
                try:
                    if registry_metadata is not None:
                        registry.data["steps"][step_id] = registry_metadata
                        registry.save()
                except Exception as restore_exc:  # noqa: BLE001
                    cli.console.print(
                        f"[yellow]Warning:[/yellow] Failed to restore registry entry "
                        f"for '{step_id}' after directory removal failure: {restore_exc}"
                    )
                cli.console.print(
                    f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
                )
                raise cli.typer.Exit(1)
    cli.console.print(f"[green]✓[/green] Step type '{step_id}' uninstalled")
