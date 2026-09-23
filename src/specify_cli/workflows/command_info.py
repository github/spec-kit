"""Command handler for ``specify workflow info``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("info")
def workflow_info(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID"),
):
    """Show workflow details and step graph."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError
    from .engine import WorkflowEngine

    project_root = cli._require_specify_project()

    # Check installed first
    registry = cli._open_workflow_registry(project_root)
    installed = registry.get(workflow_id)

    engine = WorkflowEngine(project_root)

    definition = None
    try:
        definition = engine.load_workflow(workflow_id)
    except FileNotFoundError:
        # Local workflow definition not found on disk; fall back to
        # catalog/registry lookup below.
        pass
    except ValueError as exc:
        cli.console.print(
            f"[red]Error:[/red] Invalid workflow: {cli._escape_markup(str(exc))}"
        )
        raise cli.typer.Exit(1)

    if definition:
        # Escape every user-controlled field: workflow.yml values (name,
        # version, author, description, integration, input names/types) are not
        # trusted, and console.print has Rich markup enabled, so an unescaped
        # `[...]` in any of them is parsed as a style tag and silently swallowed
        # (same defect fixed for the step graph below; the sibling workflow_list
        # already escapes all of these).
        cli.console.print(
            f"\n[bold cyan]{cli._escape_markup(str(definition.name))}[/bold cyan] "
            f"({cli._escape_markup(str(definition.id))})"
        )
        cli.console.print(
            f"  Version:     {cli._escape_markup(str(definition.version))}"
        )
        if definition.author:
            cli.console.print(
                f"  Author:      {cli._escape_markup(str(definition.author))}"
            )
        if definition.description:
            cli.console.print(
                f"  Description: {cli._escape_markup(str(definition.description))}"
            )
        if definition.default_integration:
            cli.console.print(
                f"  Integration: {cli._escape_markup(str(definition.default_integration))}"
            )
        if installed:
            cli.console.print("  [green]Installed[/green]")

        if definition.inputs:
            cli.console.print("\n  [bold]Inputs:[/bold]")
            for name, inp in definition.inputs.items():
                if isinstance(inp, dict):
                    req = "required" if inp.get("required") else "optional"
                    cli.console.print(
                        f"    {cli._escape_markup(str(name))} "
                        f"({cli._escape_markup(str(inp.get('type', 'string')))}) — {req}"
                    )

        if definition.steps:
            cli.console.print(f"\n  [bold]Steps ({len(definition.steps)}):[/bold]")
            for step in definition.steps:
                stype = step.get("type", "command")
                # Escape the literal bracket (\[) so Rich renders `[<type>]`
                # instead of parsing it as a style tag named after the step
                # type (which it silently swallows); escape id/type too, as
                # the sibling workflow_list does. Mirrors the `\[disabled]`
                # precedent above.
                cli.console.print(
                    f"    → {cli._escape_markup(str(step.get('id', '?')))} "
                    f"\\[{cli._escape_markup(str(stype))}]"
                )
        return

    # Try catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError:
        info = None

    if info:
        # Catalog-derived fields are untrusted; escape them so bracketed content
        # is rendered literally rather than parsed (and swallowed) as Rich markup.
        cli.console.print(
            f"\n[bold cyan]{cli._escape_markup(str(info.get('name', workflow_id)))}[/bold cyan] "
            f"({cli._escape_markup(str(workflow_id))})"
        )
        cli.console.print(
            f"  Version:     {cli._escape_markup(str(info.get('version', '?')))}"
        )
        if info.get("description"):
            cli.console.print(
                f"  Description: {cli._escape_markup(str(info['description']))}"
            )
        info_tags = info.get("tags", [])
        if isinstance(info_tags, list) and info_tags:
            safe_tags = cli._escape_markup(", ".join(str(t) for t in info_tags))
            cli.console.print(f"  Tags:        {safe_tags}")
        cli.console.print("  [yellow]Not installed[/yellow]")
    else:
        cli.console.print(
            f"[red]Error:[/red] Workflow '{cli._escape_markup(str(workflow_id))}' not found"
        )
        raise cli.typer.Exit(1)
