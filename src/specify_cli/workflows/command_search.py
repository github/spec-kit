"""Command handler for ``specify workflow search``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("search")
def workflow_search(
    query: str | None = cli.typer.Argument(None, help="Search query"),
    tag: str | None = cli.typer.Option(None, "--tag", help="Filter by tag"),
    author: str | None = cli.typer.Option(None, "--author", help="Filter by author"),
):
    """Search workflow catalogs."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = cli._require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except WorkflowCatalogError as exc:
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)

    if not results:
        cli.console.print("[yellow]No workflows found.[/yellow]")
        return

    cli.console.print(f"\n[bold cyan]Workflows ({len(results)}):[/bold cyan]\n")
    for wf in results:
        name = cli._escape_markup(str(wf.get("name", wf.get("id", "?"))))
        wf_id = cli._escape_markup(str(wf.get("id", "?")))
        version = cli._escape_markup(str(wf.get("version", "?")))
        cli.console.print(f"  [bold]{name}[/bold] ({wf_id}) v{version}")
        desc = wf.get("description", "")
        if desc:
            cli.console.print(f"    {cli._escape_markup(str(desc))}")
        tags = wf.get("tags", [])
        if isinstance(tags, list) and tags:
            safe_tags = cli._escape_markup(", ".join(str(t) for t in tags))
            cli.console.print(f"    [dim]Tags: {safe_tags}[/dim]")
        cli.console.print()
