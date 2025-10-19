import typer
import importlib.util
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from specify_cli.guards.registry import GuardRegistry
from specify_cli.guards.types import GuardType
from specify_cli.guards.utils import get_project_root


console = Console()
guard_app = typer.Typer(name="guard", help="Manage validation guards for features")


@guard_app.command("create")
def create_guard(
    guard_type: str = typer.Option(..., "--type", help="Guard type (e.g., unit-pytest, api, database)"),
    name: str = typer.Option(..., "--name", help="Guard name (kebab-case)")
):
    """Create a new guard with opinionated boilerplate."""
    
    project_root = get_project_root()
    guards_base = project_root / ".specify" / "guards"
    
    guard_type_obj = GuardType.load_type(guards_base, guard_type)
    if not guard_type_obj:
        console.print(f"[red]Error:[/red] Guard type '{guard_type}' not found")
        console.print(f"\nAvailable types: {', '.join(GuardType.list_types(guards_base))}")
        raise typer.Exit(1)
    
    registry = GuardRegistry(guards_base)
    guard_id = registry.generate_id()
    
    # Scaffolder could be in types/ or types-custom/
    scaffolder_path = guard_type_obj.guard_type_dir / "scaffolder.py"
    spec = importlib.util.spec_from_file_location("scaffolder", scaffolder_path)
    if not spec or not spec.loader:
        console.print(f"[red]Error:[/red] Could not load scaffolder from {scaffolder_path}")
        raise typer.Exit(1)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    scaffolder_class_name = guard_type_obj.manifest.get("scaffolder_class", f"{guard_type.title()}Scaffolder")
    scaffolder_class = getattr(module, scaffolder_class_name)
    
    scaffolder = scaffolder_class(guard_id, name, guard_type, project_root)
    result = scaffolder.scaffold()
    
    registry.add_guard(
        guard_id=guard_id,
        guard_type=guard_type,
        name=name,
        command=result["command"],
        files=result["files_created"]
    )
    
    console.print(result["next_steps"])


@guard_app.command("run")
def run_guard(
    guard_id: str = typer.Argument(..., help="Guard ID (e.g., G001)")
):
    """Execute a guard validation."""
    from specify_cli.guards.executor import GuardExecutor
    
    project_root = get_project_root()
    guards_base = project_root / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    guard = registry.get_guard(guard_id)
    if not guard:
        console.print(f"[red]Error:[/red] Guard '{guard_id}' not found")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Running guard {guard_id}...[/cyan]")
    
    executor = GuardExecutor(guard_id, guard["command"], registry=registry)
    result = executor.execute()
    
    if result["passed"]:
        console.print(f"[green]✓ Guard {guard_id} PASSED[/green]")
        console.print(f"  Duration: {result['duration_ms']}ms")
        raise typer.Exit(0)
    else:
        console.print(f"[red]✗ Guard {guard_id} FAILED[/red]")
        console.print(f"  Exit code: {result['exit_code']}")
        console.print(f"  Duration: {result['duration_ms']}ms")
        if result["timed_out"]:
            console.print(f"  [yellow]Guard timed out[/yellow]")
        if result["stderr"]:
            console.print(f"\n[dim]STDERR:[/dim]\n{result['stderr']}")
        raise typer.Exit(1)


@guard_app.command("list")
def list_guards():
    """List all guards for current feature."""
    
    project_root = get_project_root()
    guards_base = project_root / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    guards = registry.list_guards()
    
    if not guards:
        console.print("[yellow]No guards found.[/yellow]")
        console.print("\nCreate a guard with: specify guard create --type <type> --name <name>")
        return
    
    table = Table(title="Guards")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Command", style="dim")
    
    for guard in guards:
        table.add_row(
            guard["id"],
            guard["type"],
            guard["name"],
            guard["status"],
            guard["command"]
        )
    
    console.print(table)


@guard_app.command("types")
def list_types():
    """List available guard types."""
    from rich.table import Table
    
    project_root = get_project_root()
    guards_base = project_root / ".specify" / "guards"
    
    type_names = GuardType.list_types(guards_base)
    
    if not type_names:
        console.print("[yellow]No guard types found.[/yellow]")
        return
    
    table = Table(title="Available Guard Types")
    table.add_column("Type", style="cyan")
    table.add_column("Version", style="blue")
    table.add_column("Category", style="green")
    table.add_column("Source", style="magenta")
    table.add_column("Description", style="dim")
    
    for type_name in type_names:
        guard_type = GuardType.load_type(guards_base, type_name)
        if guard_type:
            manifest = guard_type.manifest
            # Determine source by checking which directory it came from
            source = "custom" if (guards_base / "types-custom" / type_name).exists() else "official"
            table.add_row(
                type_name,
                manifest.get("version", "?"),
                manifest.get("category", "?"),
                source,
                manifest.get("description", "").split('\n')[0][:50] + "..."
            )
    
    console.print(table)


@guard_app.command("create-type")
def create_guard_type(
    name: str = typer.Option(..., "--name", help="Guard type name (kebab-case)"),
    category: str = typer.Option(..., "--category", help="Category (e.g., testing, validation, quality)"),
    description: str = typer.Option("Custom guard type", "--description", help="Short description")
):
    """Create a custom guard type scaffold in types-custom/."""
    
    project_root = get_project_root()
    custom_types_dir = project_root / ".specify" / "guards" / "types-custom"
    type_dir = custom_types_dir / name
    
    if type_dir.exists():
        console.print(f"[red]Error:[/red] Guard type '{name}' already exists at {type_dir}")
        raise typer.Exit(1)
    
    # Create directory structure
    type_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = type_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create guard-type.yaml manifest
    manifest_content = f"""name: {name}
version: 1.0.0
category: {category}
description: |
  {description}

ai_hints:
  when_to_use: "Describe when AI agents should use this guard type"
  boilerplate_explanation: "Explain what the scaffolded files do"

dependencies:
  tools: []
  python_packages: []

scaffolder_class: {name.replace('-', ' ').title().replace(' ', '')}Scaffolder
"""
    
    manifest_path = type_dir / "guard-type.yaml"
    manifest_path.write_text(manifest_content)
    
    # Create scaffolder.py template
    scaffolder_content = f'''from pathlib import Path
from specify_cli.guards.scaffolder import BaseScaffolder


class {name.replace('-', ' ').title().replace(' ', '')}Scaffolder(BaseScaffolder):
    """Scaffolder for {name} guard type."""
    
    def scaffold(self):
        """Generate guard files."""
        # TODO: Implement your scaffolding logic
        # Use self.render_template() to generate files from templates/
        
        test_file = self.project_root / "tests" / f"{{self.guard_id}}_{{self.name}}.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.render_template(
            "test.py.j2",
            guard_id=self.guard_id,
            name=self.name
        )
        
        test_file.write_text(content)
        
        return {{
            "files_created": [str(test_file)],
            "command": f"python {{test_file}}",
            "next_steps": f"[green]✓[/green] Created {{self.guard_type}} guard {{self.guard_id}}\\n\\nFiles created:\\n  - {{test_file}}\\n\\nRun with: specify guard run {{self.guard_id}}"
        }}
'''
    
    scaffolder_path = type_dir / "scaffolder.py"
    scaffolder_path.write_text(scaffolder_content)
    
    # Create example template
    template_content = '''# Guard: {{ guard_id }}
# Name: {{ name }}
# Auto-generated by specify guard create --type {name} --name {{ name }}

def test_{{ name.replace("-", "_") }}():
    """TODO: Implement your validation logic."""
    assert True  # Replace with actual validation

if __name__ == "__main__":
    test_{{ name.replace("-", "_") }}()
    print("✓ Guard passed")
'''
    
    template_path = templates_dir / "test.py.j2"
    template_path.write_text(template_content)
    
    console.print(f"[green]✓[/green] Created custom guard type: {name}")
    console.print(f"\nFiles created:")
    console.print(f"  - {manifest_path}")
    console.print(f"  - {scaffolder_path}")
    console.print(f"  - {template_path}")
    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Edit {manifest_path} to customize metadata")
    console.print(f"  2. Edit {scaffolder_path} to implement scaffolding logic")
    console.print(f"  3. Add templates to {templates_dir}/")
    console.print(f"  4. Test with: specify guard create --type {name} --name test-guard")
