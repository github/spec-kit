"""Command handler for ``specify workflow update``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("update")
def workflow_update(
    workflow_id: str | None = cli.typer.Argument(
        None, help="Workflow ID to update (default: all)"
    ),
):
    """Update installed workflow(s) to the latest catalog version."""
    from packaging import version as pkg_version

    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = cli._require_specify_project()
    registry = cli._open_workflow_registry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"
    cli._reject_unsafe_dir(project_root / ".specify", ".specify")
    cli._reject_unsafe_dir(workflows_dir, ".specify/workflows")

    installed = registry.list()
    if workflow_id:
        if not registry.is_installed(workflow_id):
            cli.console.print(
                f"[red]Error:[/red] Workflow '{cli._escape_markup(workflow_id)}' is not installed"
            )
            raise cli.typer.Exit(1)
        targets = [workflow_id]
    else:
        targets = list(installed)

    if not targets:
        cli.console.print("[yellow]No workflows installed[/yellow]")
        raise cli.typer.Exit(0)

    catalog = WorkflowCatalog(project_root)
    cli.console.print("🔄 Checking for updates...\n")

    updates_available: list[dict[str, str]] = []
    checked = 0
    for wf_id in targets:
        safe_id = cli._escape_markup(str(wf_id))
        metadata = installed.get(wf_id)
        if not isinstance(metadata, dict):
            cli.console.print(f"⚠  {safe_id}: Registry entry is corrupted (skipping)")
            continue
        if metadata.get("source") != "catalog":
            cli.console.print(
                f"⚠  {safe_id}: Not installed from a catalog — re-add to update (skipping)"
            )
            continue
        try:
            installed_version = pkg_version.Version(str(metadata.get("version")))
        except pkg_version.InvalidVersion:
            cli.console.print(
                f"⚠  {safe_id}: Invalid installed version '{cli._escape_markup(str(metadata.get('version')))}' in registry (skipping)"
            )
            continue
        try:
            info = catalog.get_workflow_info(wf_id)
        except WorkflowCatalogError as exc:
            cli.console.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
            raise cli.typer.Exit(1)
        if not info:
            cli.console.print(f"⚠  {safe_id}: Not found in catalog (skipping)")
            continue
        if not info.get("_install_allowed", True):
            cli.console.print(
                f"⚠  {safe_id}: Updates not allowed from '{cli._escape_markup(str(info.get('_catalog_name', 'catalog')))}' (skipping)"
            )
            continue
        try:
            catalog_version = pkg_version.Version(str(info.get("version")))
        except pkg_version.InvalidVersion:
            cli.console.print(
                f"⚠  {safe_id}: Invalid catalog version '{cli._escape_markup(str(info.get('version')))}' (skipping)"
            )
            continue
        if catalog_version > installed_version:
            checked += 1
            updates_available.append(
                {
                    "id": wf_id,
                    "installed": str(installed_version),
                    "available": str(catalog_version),
                }
            )
        else:
            checked += 1
            cli.console.print(f"✓ {safe_id}: Up to date (v{installed_version})")

    if not updates_available:
        if not checked:
            cli.console.print(
                "\n[yellow]No workflows were eligible for update[/yellow]"
            )
        elif checked == len(targets):
            cli.console.print("\n[green]All workflows are up to date![/green]")
        else:
            cli.console.print(
                f"\n[green]All checked workflows are up to date[/green] "
                f"[yellow]({len(targets) - checked} skipped)[/yellow]"
            )
        raise cli.typer.Exit(0)

    cli.console.print("\n[bold]Updates available:[/bold]\n")
    for update in updates_available:
        cli.console.print(
            f"  • {cli._escape_markup(update['id'])}: {update['installed']} → {update['available']}"
        )
    cli.console.print()
    if not cli.typer.confirm("Update these workflows?"):
        cli.console.print("Cancelled")
        raise cli.typer.Exit(0)

    cli.console.print()
    failed: list[str] = []
    for update in updates_available:
        # _install_workflow_from_catalog is fully transactional (staged
        # download, atomic commit, rename-based rollback on registry
        # failure): it never leaves a partially-written workflow.yml, so
        # this loop only needs to record success/failure, not perform its
        # own backup/restore.
        try:
            cli._install_workflow_from_catalog(
                project_root,
                workflows_dir,
                update["id"],
                expected_version=update["available"],
                expected_installed_version=update["installed"],
            )
        except (cli.typer.Exit, OSError) as exc:
            if isinstance(exc, OSError):
                cli.console.print(
                    f"[red]Error:[/red] Filesystem error updating "
                    f"'{cli._escape_markup(update['id'])}': {cli._escape_markup(str(exc))}"
                )
            failed.append(update["id"])

    if failed:
        cli.console.print(
            f"\n[red]Failed to update:[/red] {', '.join(cli._escape_markup(f) for f in failed)}"
        )
        raise cli.typer.Exit(1)
