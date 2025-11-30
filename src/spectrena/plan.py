"""
Plan initialization - prepares planning phase artifacts.

Replaces setup-plan.sh / setupplan.ps1
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()


def find_current_spec() -> Optional[Path]:
    """
    Find current spec directory from git branch or environment.

    Checks (in order):
    1. Git branch name (spec/NNN-name → specs/NNN-name/)
    2. SPECIFY_FEATURE environment variable
    3. Most recently modified specs/ subdirectory
    """
    import os
    from git import Repo, InvalidGitRepositoryError

    specs_dir = Path.cwd() / "specs"

    # Try git branch
    try:
        repo = Repo(Path.cwd(), search_parent_directories=True)
        branch = repo.active_branch.name
        if branch.startswith("spec/"):
            spec_name = branch[5:]  # Remove "spec/" prefix
            spec_path = specs_dir / spec_name
            if spec_path.exists():
                return spec_path
    except (InvalidGitRepositoryError, TypeError):
        pass

    # Try environment variable
    env_feature = os.environ.get("SPECIFY_FEATURE")
    if env_feature:
        spec_path = specs_dir / env_feature
        if spec_path.exists():
            return spec_path

    # Fall back to most recent spec directory
    if specs_dir.exists():
        spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
        if spec_dirs:
            return max(spec_dirs, key=lambda d: d.stat().st_mtime)

    return None


def plan_init(
    spec_dir: Optional[Path] = typer.Argument(
        None,
        help="Spec directory (auto-detected if not provided)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite existing plan files"
    ),
):
    """
    Initialize planning phase for a spec.

    Creates:
    - plan.md (from template)
    - data-model.md (empty)
    - contracts/ directory
    - research.md (empty)
    - quickstart.md (empty)
    """
    # Find spec directory
    if spec_dir is None:
        spec_dir = find_current_spec()
        if spec_dir is None:
            console.print("[red]✗ No spec directory found[/red]")
            console.print("  Run from a spec branch or specify directory")
            raise typer.Exit(1)

    if not spec_dir.exists():
        console.print(f"[red]✗ Spec directory not found: {spec_dir}[/red]")
        raise typer.Exit(1)

    # Check spec.md exists
    spec_md = spec_dir / "spec.md"
    if not spec_md.exists():
        console.print(f"[red]✗ No spec.md found in {spec_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Initializing plan for:[/bold] {spec_dir.name}\n")

    # Create plan.md from template
    plan_md = spec_dir / "plan.md"
    if plan_md.exists() and not force:
        console.print(f"[yellow]⚠ plan.md exists (use --force to overwrite)[/yellow]")
    else:
        template_path = Path.cwd() / "templates" / "plan-template.md"
        if not template_path.exists():
            console.print("[red]Template not found: templates/plan-template.md[/red]")
            console.print("[dim]Run 'spectrena init' to create project structure[/dim]")
            raise typer.Exit(1)

        plan_md.write_text(template_path.read_text())
        console.print("[green]✓ Created plan.md[/green]")

    # Create supporting files
    files_to_create = [
        ("data-model.md", "# Data Model\n\n## Entities\n"),
        ("research.md", "# Research Notes\n"),
        ("quickstart.md", "# Quickstart Guide\n"),
    ]

    for filename, content in files_to_create:
        filepath = spec_dir / filename
        if not filepath.exists() or force:
            filepath.write_text(content)
            console.print(f"[green]✓ Created {filename}[/green]")

    # Create contracts directory
    contracts_dir = spec_dir / "contracts"
    if not contracts_dir.exists():
        contracts_dir.mkdir()
        console.print("[green]✓ Created contracts/[/green]")

    # Create requirements.md checklist
    requirements_md = spec_dir / "requirements.md"
    if not requirements_md.exists() or force:
        requirements_md.write_text("# Requirements Checklist\n\n- [ ] All requirements testable\n- [ ] Success criteria defined\n- [ ] Assumptions documented\n")
        console.print("[green]✓ Created requirements.md[/green]")

    console.print(f"\n[bold green]✓ Plan initialized[/bold green]")
    console.print(f"\n  Next: Run /speckit.plan to generate technical plan")
