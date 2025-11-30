#!/usr/bin/env python3
"""
Create new specs with configurable ID generation.

Replaces create-new-feature.sh with pure Python implementation.
"""

import re
from datetime import datetime
from pathlib import Path

import typer
from git import Repo, InvalidGitRepositoryError
from rich.console import Console
from rich.prompt import Prompt

from spectrena.config import Config

console = Console()


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def get_next_number(
    config: Config,
    component: str | None = None,
) -> int:
    """
    Get next spec number based on numbering_source config.

    Scans either:
    - "directory": existing specs/ folders
    - "branch": git branches matching pattern
    - "global": across all components
    - "component": per-component numbering
    """
    specs_dir = Path.cwd() / "specs"
    numbering = config.spec_id.numbering_source or "directory"

    existing_numbers: list[int] = []

    if numbering in ("directory", "global", "component"):
        if specs_dir.exists():
            for entry in specs_dir.iterdir():
                if entry.is_dir():
                    # Extract number from directory name
                    match = re.search(r"(\d{3,})", entry.name)
                    if match:
                        # If component-scoped, only count matching component
                        if numbering == "component" and component:
                            if entry.name.upper().startswith(component.upper()):
                                existing_numbers.append(int(match.group(1)))
                        else:
                            existing_numbers.append(int(match.group(1)))

    elif numbering == "branch":
        try:
            repo = Repo(Path.cwd(), search_parent_directories=True)
            for branch in repo.branches:
                if branch.name.startswith("spec/"):
                    match = re.search(r"(\d{3,})", branch.name)
                    if match:
                        if component and component.upper() in branch.name.upper():
                            existing_numbers.append(int(match.group(1)))
                        elif not component:
                            existing_numbers.append(int(match.group(1)))
        except InvalidGitRepositoryError:
            pass

    return max(existing_numbers, default=0) + 1


def generate_spec_id(
    config: Config,
    description: str,
    component: str | None = None,
    number: int | None = None,
) -> str:
    """Generate spec ID from template and inputs."""
    template = config.spec_id.template
    padding = config.spec_id.padding or 3
    project = config.spec_id.project or ""

    if number is None:
        number = get_next_number(config, component)

    slug = slugify(description)

    # Build replacements
    replacements = {
        "{NNN}": str(number).zfill(padding),
        "{slug}": slug,
        "{project}": project,
        "{component}": component.upper() if component else "",
    }

    spec_id = template
    for key, value in replacements.items():
        spec_id = spec_id.replace(key, value)

    # Clean up any leftover empty segments
    spec_id = re.sub(r"-+", "-", spec_id)
    spec_id = spec_id.strip("-")

    return spec_id


def template_requires_component(config: Config) -> bool:
    """Check if template includes {component} placeholder."""
    return "{component}" in config.spec_id.template


def create_spec_directory(
    spec_id: str, description: str, component: str | None
) -> Path:
    """Create spec directory with initial files."""
    specs_dir = Path.cwd() / "specs"
    spec_dir = specs_dir / spec_id

    spec_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.md from template
    spec_file = spec_dir / "spec.md"

    template_path = Path.cwd() / "templates" / "spec-template.md"
    if not template_path.exists():
        console.print("[red]Template not found: templates/spec-template.md[/red]")
        console.print("[dim]Run 'spectrena init' to create project structure[/dim]")
        raise typer.Exit(1)

    content = template_path.read_text()

    # Fill placeholders
    content = content.replace("{FEATURE_TITLE}", description)
    content = content.replace("{SPEC_ID}", spec_id)
    content = content.replace("{DATE}", datetime.now().strftime("%Y-%m-%d"))
    content = content.replace("{COMPONENT}", component or "N/A")
    content = content.replace("{WEIGHT}", "Medium")

    _ = spec_file.write_text(content)

    return spec_dir


def create_spec_branch(spec_id: str) -> bool:
    """Create git branch for spec."""
    try:
        repo = Repo(Path.cwd(), search_parent_directories=True)
        branch_name = f"spec/{spec_id}"

        if branch_name in [b.name for b in repo.branches]:
            console.print(f"[yellow]Branch {branch_name} already exists[/yellow]")
            return False

        _ = repo.create_head(branch_name)
        console.print(f"[dim]Created branch: {branch_name}[/dim]")
        return True

    except InvalidGitRepositoryError:
        console.print("[yellow]Not a git repository, skipping branch creation[/yellow]")
        return False


async def register_in_lineage(spec_id: str, title: str, component: str | None):
    """Register spec in lineage database if enabled."""
    try:
        from spectrena.config import Config
        from spectrena.lineage.db import LineageDB

        config = Config.load()
        if not config.spectrena.enabled:
            return

        lineage_db_path = (
            Path(config.spectrena.lineage_db) if config.spectrena.lineage_db else None
        )
        db = LineageDB(lineage_db_path)
        _ = await db.register_spec(spec_id, title, component or "")
        console.print("[dim]Registered in lineage database[/dim]")

    except ImportError:
        pass  # Lineage not installed
    except Exception as e:
        console.print(f"[yellow]Lineage registration failed: {e}[/yellow]")

# =============================================================================
# CLI COMMAND
# =============================================================================


def new(
    description: str = typer.Argument(
        ...,
        help="Brief title for the spec (becomes ID slug). Detail added via /spectrena.specify"
    ),
    component: str | None = typer.Option(
        None, "-c", "--component",
        help="Component (e.g., CORE, API, UI)"
    ),
    number: int | None = typer.Option(None, "-n", "--number", help="Override spec number"),
    no_branch: bool = typer.Option(False, "--no-branch", help="Skip git branch creation"),
    no_lineage: bool = typer.Option(False, "--no-lineage", help="Skip lineage registration"),
):
    """
    Create a new spec scaffold with auto-generated ID.

    This creates the directory structure and template. For detailed content,
    run /spectrena.specify in Claude Code - it will ask clarifying questions.

    Examples:
        spectrena new -c CORE "User authentication"
        spectrena new -c API "REST endpoints"
    """
    import asyncio

    config = Config.load()

    # Validate component if required
    if template_requires_component(config):
        if not component:
            components = config.spec_id.components or []
            if components:
                console.print(
                    f"[yellow]Template requires component. Available: {', '.join(components)}[/yellow]"
                )
                component = Prompt.ask("Component", choices=components)
            else:
                component = Prompt.ask("Component (e.g., CORE, API, UI)")

        # Validate against allowed components
        if config.spec_id.components:
            if component.upper() not in [c.upper() for c in config.spec_id.components]:
                console.print(f"[red]Invalid component '{component}'[/red]")
                console.print(f"Allowed: {', '.join(config.spec_id.components)}")
                raise typer.Exit(1)

    # Generate spec ID
    spec_id = generate_spec_id(config, description, component, number)

    console.print(f"\n[bold]Creating spec:[/bold] {spec_id}\n")

    # Create directory and files
    spec_dir = create_spec_directory(spec_id, description, component)
    console.print(f"[green]✓ Created {spec_dir}[/green]")

    # Create git branch
    if not no_branch:
        _ = create_spec_branch(spec_id)

    # Register in lineage
    if not no_lineage:
        asyncio.run(register_in_lineage(spec_id, description, component))

    # Summary
    console.print(f"\n[bold green]✓ Spec scaffold created[/bold green]")
    console.print(f"\n  [cyan]{spec_dir / 'spec.md'}[/cyan]")
    console.print(f"  Branch: [dim]spec/{spec_id}[/dim]")

    console.print(f"\n[bold]Next:[/bold] Generate detailed content")
    console.print(f"  In Claude Code: [cyan]/spectrena.specify[/cyan]")
    console.print(f"  Claude will ask clarifying questions if needed")
