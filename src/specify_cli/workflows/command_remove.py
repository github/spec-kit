"""Command handler for ``specify workflow remove``."""

from __future__ import annotations

from . import _commands as cli


def _remove_workflow_locked(
    project_root: cli.Path, workflows_dir: cli.Path, workflow_id: str
) -> cli.Path | None:
    """Stage a workflow directory and persist removal while locked."""
    registry = cli._open_workflow_registry(project_root)
    safe_id = cli._escape_markup(workflow_id)
    if not registry.is_installed(workflow_id):
        cli.console.print(f"[red]Error:[/red] Workflow '{safe_id}' is not installed")
        raise cli.typer.Exit(1)

    workflow_dir_unresolved = workflows_dir / workflow_id
    if workflow_dir_unresolved.is_symlink():
        cli.console.print(
            f"[red]Error:[/red] Refusing to remove symlinked "
            f".specify/workflows/{safe_id}"
        )
        raise cli.typer.Exit(1)

    workflow_dir = workflow_dir_unresolved.resolve()
    try:
        rel_parts = workflow_dir.relative_to(workflows_dir.resolve()).parts
    except ValueError:
        cli.console.print(
            f"[red]Error:[/red] Invalid workflow ID: "
            f"{cli._escape_markup(repr(workflow_id))}"
        )
        raise cli.typer.Exit(1)
    if rel_parts != (workflow_id,):
        cli.console.print(
            f"[red]Error:[/red] Invalid workflow ID: "
            f"{cli._escape_markup(repr(workflow_id))}"
        )
        raise cli.typer.Exit(1)

    if workflow_dir.exists() and not workflow_dir.is_dir():
        cli.console.print(
            f"[red]Error:[/red] .specify/workflows/{safe_id} exists "
            "but is not a directory"
        )
        raise cli.typer.Exit(1)

    import tempfile

    staged_dir: cli.Path | None = None
    if workflow_dir.exists():
        try:
            reserved = cli.Path(
                tempfile.mkdtemp(prefix=f".{workflow_id}.removing-", dir=workflows_dir)
            )
            reserved.rmdir()
            cli.os.rename(workflow_dir, reserved)
            staged_dir = reserved
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to stage workflow directory "
                f"{cli._escape_markup(str(workflow_dir))} for removal: "
                f"{cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)

    try:
        registry.remove(workflow_id)
    except (OSError, TypeError, ValueError) as exc:
        if staged_dir is not None:
            try:
                cli.os.rename(staged_dir, workflow_dir)
            except OSError as restore_exc:
                cli.console.print(
                    f"[yellow]Warning:[/yellow] Failed to restore workflow "
                    "directory after registry update failure; it remains "
                    f"staged at {cli._escape_markup(str(staged_dir))}: "
                    f"{cli._escape_markup(str(restore_exc))}"
                )
        cli.console.print(
            f"[red]Error:[/red] Failed to update workflow registry for "
            f"'{safe_id}': {cli._escape_markup(str(exc))}"
        )
        raise cli.typer.Exit(1)
    return staged_dir


@cli.workflow_app.command("remove")
def workflow_remove(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID to uninstall"),
):
    """Uninstall a workflow."""
    project_root = cli._require_specify_project()
    workflows_dir = project_root / ".specify" / "workflows"
    cli._validate_workflow_id_or_exit(workflow_id)
    safe_id = cli._escape_markup(workflow_id)
    import shutil

    try:
        with cli._workflow_install_transaction(project_root):
            staged_dir = _remove_workflow_locked(
                project_root, workflows_dir, workflow_id
            )
    except OSError as exc:
        cli.console.print(
            f"[red]Error:[/red] Failed to lock workflow removal "
            f"'{safe_id}': {cli._escape_markup(str(exc))}"
        )
        raise cli.typer.Exit(1)

    cli.console.print(f"[green]✓[/green] Workflow '{workflow_id}' removed")

    # The registry has already durably committed the removal at this point,
    # so it must stand regardless of what happens below: deleting the staged
    # directory is now just cleanup, not a data-integrity concern, and a
    # failure here is reported as a warning (not an error) to avoid
    # contradicting the registry state that already succeeded.
    if staged_dir is not None:
        try:
            shutil.rmtree(staged_dir)
        except OSError as exc:
            cli.console.print(
                f"[yellow]Warning:[/yellow] Workflow '{safe_id}' was removed, but its "
                f"staged directory could not be deleted: {cli._escape_markup(str(exc))}. "
                f"Remove it manually: {cli._escape_markup(str(staged_dir))}"
            )
