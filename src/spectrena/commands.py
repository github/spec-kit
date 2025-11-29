#!/usr/bin/env python3
"""
Spectrena Config Command

Allows changing spec ID configuration after init, including migration
of existing specs to a new format.

Usage:
    spectrena config --spec-format component --components "A,B,C"
    spectrena config --migrate  # Rename existing specs to match new format
    spectrena config --show     # Display current configuration
"""

from pathlib import Path
import re
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================


def load_current_config(project_dir: Path | None = None) -> dict[str, Any]:
    """
    Load current configuration from .spectrena/config.yml

    Returns:
        Configuration dict, or defaults if no config exists
    """
    if project_dir is None:
        project_dir = Path.cwd()

    config_path = project_dir / ".spectrena" / "config.yml"

    defaults = {
        "spec_id": {
            "template": "{NNN}-{slug}",
            "padding": 3,
            "numbering_source": "both",
        }
    }

    if not config_path.exists():
        return defaults

    # Simple YAML parsing (avoiding external dependency)
    content = config_path.read_text()
    config: dict[str, Any] = {"spec_id": {}}

    # Parse template
    match = re.search(r'template:\s*["\']?([^"\']+)["\']?', content)
    if match:
        config["spec_id"]["template"] = match.group(1).strip()

    # Parse padding
    match = re.search(r"padding:\s*(\d+)", content)
    if match:
        config["spec_id"]["padding"] = int(match.group(1))

    # Parse project
    match = re.search(r'project:\s*["\']?(\w+)["\']?', content)
    if match:
        config["spec_id"]["project"] = match.group(1)

    # Parse components
    components = re.findall(r"^\s+-\s*(\w+)", content, re.MULTILINE)
    if components:
        # Filter out non-component matches (like stop_words)
        config["spec_id"]["components"] = [
            c for c in components if c.isupper() or c[0].isupper()
        ]

    # Parse numbering_source
    match = re.search(r'numbering_source:\s*["\']?(\w+)["\']?', content)
    if match:
        config["spec_id"]["numbering_source"] = match.group(1)

    # Merge with defaults
    for key, value in defaults["spec_id"].items():
        if key not in config["spec_id"]:
            config["spec_id"][key] = value

    return config


def save_config(config: dict[str, Any], project_dir: Path | None = None) -> Path:
    """
    Save configuration to .spectrena/config.yml
    """
    if project_dir is None:
        project_dir = Path.cwd()

    from .spectrena_config import (
        generate_config_yaml,
    )  # pyright: ignore[reportMissingImports]

    spec_id_config = config.get("spec_id", {})
    spectrena_config = config.get("spectrena", {})

    yaml_content = generate_config_yaml(spec_id_config, spectrena_config)

    config_dir = project_dir / ".spectrena"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.yml"
    _ = config_path.write_text(yaml_content)

    return config_path


def show_current_config(project_dir: Path | None = None) -> None:
    """
    Display current configuration in a nice format.
    """
    config = load_current_config(project_dir)
    spec_id = config.get("spec_id", {})

    console.print("\n")
    console.rule("[bold cyan]Current Spectrena Configuration[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold", width=20)
    table.add_column(style="cyan")

    table.add_row("Template:", spec_id.get("template", "{NNN}-{slug}"))
    table.add_row("Padding:", str(spec_id.get("padding", 3)))
    table.add_row("Numbering:", spec_id.get("numbering_source", "both"))

    if "project" in spec_id:
        table.add_row("Project:", spec_id["project"])

    if "components" in spec_id:
        table.add_row("Components:", ", ".join(spec_id["components"]))

    console.print(table)

    # Show example
    template = spec_id.get("template", "{NNN}-{slug}")
    example = template
    example = example.replace("{project}", spec_id.get("project", "PROJECT"))
    example = example.replace(
        "{component}",
        (
            spec_id.get("components", ["COMPONENT"])[0]
            if spec_id.get("components")
            else "COMPONENT"
        ),
    )
    example = example.replace("{NNN}", "001")
    example = example.replace("{slug}", "feature-name")

    console.print()
    console.print(f"[dim]Example spec ID:[/dim] [green]{example}[/green]")

    # Show config file path
    config_path = (project_dir or Path.cwd()) / ".spectrena" / "config.yml"
    console.print()
    console.print(f"[dim]Config file:[/dim] {config_path}")
    if not config_path.exists():
        console.print("[yellow]  (using defaults - no config file found)[/yellow]")


# =============================================================================
# SPEC MIGRATION
# =============================================================================


def scan_existing_specs(project_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Scan specs/ directory and parse existing spec IDs.

    Returns:
        List of dicts with spec info: {path, current_id, number, slug, component}
    """
    if project_dir is None:
        project_dir = Path.cwd()

    specs_dir = project_dir / "specs"
    if not specs_dir.exists():
        return []

    specs = []

    for spec_path in specs_dir.iterdir():
        if not spec_path.is_dir():
            continue

        spec_id = spec_path.name

        # Try to parse the spec ID
        # Patterns to try (most specific to least):
        # {project}-{component}-{NNN}-{slug}
        # {component}-{NNN}-{slug}
        # {project}-{NNN}-{slug}
        # {NNN}-{slug}

        spec_info: dict[str, Any] = {
            "path": spec_path,
            "current_id": spec_id,
            "number": None,
            "slug": None,
            "component": None,
            "project": None,
        }

        # Pattern: XXX-NNN-slug or NNN-slug
        patterns = [
            # PROJECT-COMPONENT-NNN-slug
            r"^([A-Z][A-Z0-9_]*)-([A-Z][A-Z0-9_]*)-(\d+)-(.+)$",
            # COMPONENT-NNN-slug
            r"^([A-Z][A-Z0-9_]*)-(\d+)-(.+)$",
            # NNN-slug
            r"^(\d+)-(.+)$",
        ]

        for i, pattern in enumerate(patterns):
            match = re.match(pattern, spec_id)
            if match:
                groups = match.groups()
                if i == 0:  # PROJECT-COMPONENT-NNN-slug
                    spec_info["project"] = groups[0]
                    spec_info["component"] = groups[1]
                    spec_info["number"] = int(groups[2])
                    spec_info["slug"] = groups[3]
                elif i == 1:  # COMPONENT-NNN-slug
                    spec_info["component"] = groups[0]
                    spec_info["number"] = int(groups[1])
                    spec_info["slug"] = groups[2]
                else:  # NNN-slug
                    spec_info["number"] = int(groups[0])
                    spec_info["slug"] = groups[1]
                break

        specs.append(spec_info)

    return sorted(specs, key=lambda s: s.get("number") or 0)


def generate_new_spec_id(
    spec_info: dict[str, Any],
    new_template: str,
    new_config: dict[str, Any],
    component_mapping: dict[str, str] | None = None,
) -> str:
    """
    Generate a new spec ID from existing spec info using new template.

    Args:
        spec_info: Parsed spec info from scan_existing_specs
        new_template: New template string
        new_config: New configuration dict
        component_mapping: Optional mapping of old components to new

    Returns:
        New spec ID string
    """
    number = spec_info.get("number", 1)
    slug = spec_info.get("slug", "unknown")

    padding = new_config.get("padding", 3)
    padded_number = str(number).zfill(padding)

    new_id = new_template
    new_id = new_id.replace("{NNN}", padded_number)
    new_id = new_id.replace("{slug}", slug)

    # Handle project
    if "{project}" in new_template:
        project = new_config.get("project", spec_info.get("project", "PROJECT"))
        new_id = new_id.replace("{project}", project)

    # Handle component
    if "{component}" in new_template:
        old_component = spec_info.get("component")

        if component_mapping and old_component in component_mapping:
            component = component_mapping[old_component]
        elif old_component:
            component = old_component
        else:
            # No component in old spec - need to assign one
            component = None

        if component:
            new_id = new_id.replace("{component}", component)
        else:
            new_id = new_id.replace("{component}-", "")  # Remove placeholder

    return new_id


def plan_migration(
    current_specs: list[dict[str, Any]],
    new_template: str,
    new_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Plan spec migration without executing it.

    Returns:
        List of migration plans: {spec_info, old_id, new_id, needs_component}
    """
    migrations = []

    for spec in current_specs:
        old_id = spec["current_id"]

        # Check if we need component assignment
        needs_component = "{component}" in new_template and not spec.get("component")

        if needs_component:
            new_id = generate_new_spec_id(spec, new_template, new_config)
            new_id = "[COMPONENT]-" + new_id.replace("{component}-", "")
        else:
            new_id = generate_new_spec_id(spec, new_template, new_config)

        if old_id != new_id:
            migrations.append(
                {
                    "spec_info": spec,
                    "old_id": old_id,
                    "new_id": new_id,
                    "needs_component": needs_component,
                    "old_path": spec["path"],
                    "new_path": spec["path"].parent / new_id,
                }
            )

    return migrations


def show_migration_plan(migrations: list[dict[str, Any]]) -> None:
    """
    Display the migration plan in a nice format.
    """
    if not migrations:
        console.print(
            "[green]No migrations needed - all specs match current format.[/green]"
        )
        return

    console.print("\n")
    console.rule("[bold cyan]Migration Plan[/bold cyan]")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Current", style="red")
    table.add_column("→", style="dim", width=3)
    table.add_column("New", style="green")
    table.add_column("Status", style="yellow")

    for m in migrations:
        status = "⚠ Needs component" if m["needs_component"] else "Ready"
        table.add_row(m["old_id"], "→", m["new_id"], status)

    console.print(table)
    console.print()

    needs_input = [m for m in migrations if m["needs_component"]]
    if needs_input:
        console.print(
            f"[yellow]⚠ {len(needs_input)} specs need component assignment[/yellow]"
        )


def execute_migration(
    migrations: list[dict[str, Any]],
    project_dir: Path | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Execute the migration plan.

    Args:
        migrations: Migration plan from plan_migration
        project_dir: Project root
        dry_run: If True, only show what would happen

    Returns:
        List of completed migrations
    """
    if project_dir is None:
        project_dir = Path.cwd()

    completed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Migrating specs...", total=len(migrations))

        for m in migrations:
            old_path = m["old_path"]
            new_path = m["new_path"]

            progress.update(task, description=f"Migrating {m['old_id']}...")

            if dry_run:
                console.print(
                    f"  [dim]Would rename:[/dim] {old_path.name} → {new_path.name}"
                )
            else:
                if new_path.exists():
                    console.print(
                        f"  [red]Skipping {old_path.name}: target exists[/red]"
                    )
                    continue

                # Rename directory
                old_path.rename(new_path)

                # Update spec.md header if it contains the old ID
                spec_file = new_path / "spec.md"
                if spec_file.exists():
                    content = spec_file.read_text()
                    updated = content.replace(m["old_id"], m["new_id"])
                    if updated != content:
                        spec_file.write_text(updated)

                completed.append(m)

            progress.advance(task)

    return completed


def prompt_for_component_assignment(
    migrations: list[dict[str, Any]],
    available_components: list[str],
) -> dict[str, str]:
    """
    Interactively assign components to specs that need them.

    Returns:
        Mapping of spec_id -> component
    """
    needs_assignment = [m for m in migrations if m["needs_component"]]

    if not needs_assignment:
        return {}

    console.print("\n")
    console.rule("[bold cyan]Component Assignment[/bold cyan]")
    console.print()
    console.print(f"[dim]Available components: {', '.join(available_components)}[/dim]")
    console.print()

    assignments = {}

    for m in needs_assignment:
        console.print(f"[bold]{m['old_id']}[/bold]")

        # Show spec content hint if available
        spec_file = m["old_path"] / "spec.md"
        if spec_file.exists():
            content = spec_file.read_text()
            # Extract title or first meaningful line
            for line in content.split("\n"):
                if line.startswith("# ") or line.startswith("**What**"):
                    console.print(f"  [dim]{line[:60]}...[/dim]")
                    break

        component = Prompt.ask(
            "  Component",
            choices=available_components,
            default=available_components[0],
        )

        assignments[m["old_id"]] = component

        # Update the migration plan
        new_id = m["new_id"].replace("[COMPONENT]", component)
        m["new_id"] = new_id
        m["new_path"] = m["old_path"].parent / new_id
        m["needs_component"] = False

        console.print(f"  [green]→ {new_id}[/green]")
        console.print()

    return assignments


# =============================================================================
# MAIN CONFIG COMMAND
# =============================================================================


def run_config(
    project_dir: Path | None = None,
    spec_format: str | None = None,
    components: list[str] | None = None,
    project_prefix: str | None = None,
    numbering_source: str | None = None,
    show: bool = False,
    migrate: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Main config command handler.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Just show current config
    if show or (
        not spec_format and not components and not project_prefix and not migrate
    ):
        show_current_config(project_dir)
        return

    # Load current config
    current = load_current_config(project_dir)
    spec_id_config = current.get("spec_id", {})

    # Apply changes
    if spec_format:
        from .spectrena_config import (
            SPEC_ID_FORMATS,
        )  # pyright: ignore[reportMissingImports]

        if spec_format in SPEC_ID_FORMATS:
            spec_id_config["template"] = SPEC_ID_FORMATS[spec_format]["template"]
        elif "{" in spec_format:
            spec_id_config["template"] = spec_format
        else:
            console.print(f"[red]Unknown format: {spec_format}[/red]")
            return

    if components:
        spec_id_config["components"] = [c.strip().upper() for c in components]

    if project_prefix:
        spec_id_config["project"] = project_prefix.upper()

    if numbering_source:
        spec_id_config["numbering_source"] = numbering_source

    # Show what we're changing to
    console.print("\n")
    console.rule("[bold cyan]Configuration Update[/bold cyan]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold", width=20)
    table.add_column(style="cyan")

    table.add_row("New Template:", spec_id_config.get("template", "{NNN}-{slug}"))
    if spec_id_config.get("components"):
        table.add_row("Components:", ", ".join(spec_id_config["components"]))
    if spec_id_config.get("project"):
        table.add_row("Project:", spec_id_config["project"])

    console.print(table)

    # Handle migration if requested
    if migrate:
        current_specs = scan_existing_specs(project_dir)

        if current_specs:
            migrations = plan_migration(
                current_specs,
                spec_id_config["template"],
                spec_id_config,
            )

            show_migration_plan(migrations)

            # Handle component assignment if needed
            needs_assignment = [m for m in migrations if m["needs_component"]]
            if needs_assignment and spec_id_config.get("components"):
                prompt_for_component_assignment(
                    migrations,
                    spec_id_config["components"],
                )

            # Confirm migration
            if migrations:
                console.print()
                if dry_run:
                    console.print("[yellow]DRY RUN - No changes will be made[/yellow]")

                if Confirm.ask("Execute migration?", default=False):
                    completed = execute_migration(migrations, project_dir, dry_run)
                    console.print(f"\n[green]✓ Migrated {len(completed)} specs[/green]")
                else:
                    console.print("[yellow]Migration cancelled[/yellow]")

    # Save config
    console.print()
    if Confirm.ask("Save configuration?", default=True):
        config_path = save_config({"spec_id": spec_id_config}, project_dir)
        console.print(f"[green]✓ Saved {config_path}[/green]")
    else:
        console.print("[yellow]Configuration not saved[/yellow]")


# =============================================================================
# CLI COMMAND DEFINITION
# =============================================================================


def add_config_command(app):
    """
    Add the config command to a Typer app.
    """
    import typer

    @app.command()
    def config(
        spec_format: str = typer.Option(
            None,
            "--spec-format",
            "-f",
            help="Spec ID format: simple, component, project, full, or custom template",
        ),
        components: str = typer.Option(
            None, "--components", "-c", help="Comma-separated component names"
        ),
        project_prefix: str = typer.Option(
            None, "--project", "-p", help="Project prefix"
        ),
        numbering_source: str = typer.Option(
            None,
            "--numbering",
            "-n",
            help="Numbering source: directory, branch, or both",
        ),
        show: bool = typer.Option(
            False, "--show", "-s", help="Show current configuration"
        ),
        migrate: bool = typer.Option(
            False, "--migrate", "-m", help="Migrate existing specs to new format"
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Show what migration would do without executing"
        ),
    ):
        """
        View or modify Spectrena configuration.

        Can be run anytime to change spec ID format, add components,
        or migrate existing specs to a new naming scheme.

        Examples:

            # Show current config
            spectrena config --show

            # Switch to component-based format
            spectrena config --spec-format component --components "CORE,API,UI"

            # Migrate existing specs to new format
            spectrena config --spec-format component --components "A,B" --migrate

            # Preview migration without executing
            spectrena config --migrate --dry-run
        """
        component_list = None
        if components:
            component_list = [c.strip() for c in components.split(",")]

        run_config(
            spec_format=spec_format,
            components=component_list,
            project_prefix=project_prefix,
            numbering_source=numbering_source,
            show=show,
            migrate=migrate,
            dry_run=dry_run,
        )

    return config


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    show_current_config()
