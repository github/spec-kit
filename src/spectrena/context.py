"""
Update AI agent context files from plan.md.

Replaces update-agent-context.sh / updateagentcontext.ps1
"""

import re
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()


def extract_tech_stack(plan_path: Path) -> dict[str, list[str]]:
    """
    Extract tech stack from plan.md.

    Looks for a "## Tech Stack" or "## Technology Stack" section
    and parses bullet points into categories.
    """
    if not plan_path.exists():
        return {}

    content = plan_path.read_text()

    # Find tech stack section
    tech_pattern = r'##\s*(?:Tech(?:nology)?\s*Stack|Technologies)\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(tech_pattern, content, re.IGNORECASE | re.DOTALL)

    if not match:
        return {}

    section = match.group(1)

    tech_stack = {
        "languages": [],
        "frameworks": [],
        "databases": [],
        "tools": [],
        "other": [],
    }

    current_category = "other"

    for line in section.split('\n'):
        line = line.strip()

        # Check for category headers (### or **)
        if line.startswith('###') or line.startswith('**'):
            cat_lower = line.lower()
            if 'language' in cat_lower:
                current_category = "languages"
            elif 'framework' in cat_lower or 'backend' in cat_lower or 'frontend' in cat_lower:
                current_category = "frameworks"
            elif 'database' in cat_lower or 'storage' in cat_lower:
                current_category = "databases"
            elif 'tool' in cat_lower or 'infra' in cat_lower:
                current_category = "tools"
            else:
                current_category = "other"

        # Parse bullet points
        elif line.startswith('-') or line.startswith('*'):
            item = line.lstrip('-* ').split(':')[0].split('(')[0].strip()
            if item:
                tech_stack[current_category].append(item)

    return tech_stack


def generate_tech_section(tech_stack: dict[str, list[str]]) -> str:
    """Generate markdown section for tech stack."""
    lines = ["## Active Technologies", ""]

    if tech_stack.get("languages"):
        lines.append(f"**Languages:** {', '.join(tech_stack['languages'])}")
    if tech_stack.get("frameworks"):
        lines.append(f"**Frameworks:** {', '.join(tech_stack['frameworks'])}")
    if tech_stack.get("databases"):
        lines.append(f"**Databases:** {', '.join(tech_stack['databases'])}")
    if tech_stack.get("tools"):
        lines.append(f"**Tools:** {', '.join(tech_stack['tools'])}")

    return '\n'.join(lines)


def update_context(
    agent_file: Path = typer.Option(
        Path("CLAUDE.md"), "--file", "-f",
        help="Agent context file to update"
    ),
    spec_dir: Optional[Path] = typer.Option(
        None, "--spec", "-s",
        help="Spec directory containing plan.md"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n",
        help="Show changes without writing"
    ),
):
    """
    Update agent context file with tech stack from plan.md.

    Parses the Tech Stack section from plan.md and updates
    the "Active Technologies" section in CLAUDE.md (or similar).
    """
    from spectrena.plan import find_current_spec

    # Find spec directory
    if spec_dir is None:
        spec_dir = find_current_spec()
        if spec_dir is None:
            console.print("[red]✗ No spec directory found[/red]")
            raise typer.Exit(1)

    plan_path = spec_dir / "plan.md"
    if not plan_path.exists():
        console.print(f"[red]✗ No plan.md found in {spec_dir}[/red]")
        console.print("  Run /speckit.plan first")
        raise typer.Exit(1)

    console.print(f"[bold]Updating context from:[/bold] {plan_path}\n")

    # Extract tech stack
    tech_stack = extract_tech_stack(plan_path)

    if not any(tech_stack.values()):
        console.print("[yellow]⚠ No tech stack found in plan.md[/yellow]")
        console.print("  Looking for '## Tech Stack' section with bullet points")
        raise typer.Exit(1)

    # Show what was found
    console.print("[cyan]Found technologies:[/cyan]")
    for category, items in tech_stack.items():
        if items:
            console.print(f"  {category}: {', '.join(items)}")

    # Generate new section
    new_section = generate_tech_section(tech_stack)

    if dry_run:
        console.print(f"\n[yellow]Would update {agent_file}:[/yellow]")
        console.print(new_section)
        return

    # Update or create agent file
    if agent_file.exists():
        content = agent_file.read_text()

        # Replace existing Active Technologies section
        pattern = r'## Active Technologies\n.*?(?=\n##|\Z)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_section, content, flags=re.DOTALL)
            console.print(f"\n[green]✓ Updated {agent_file}[/green]")
        else:
            # Append to end
            content = content.rstrip() + '\n\n' + new_section + '\n'
            console.print(f"\n[green]✓ Added tech section to {agent_file}[/green]")

        agent_file.write_text(content)
    else:
        # Create new file with tech section
        content = f"# Project Context\n\n{new_section}\n"
        agent_file.write_text(content)
        console.print(f"\n[green]✓ Created {agent_file}[/green]")

    console.print("\n[dim]Tech stack synced from plan.md[/dim]")
