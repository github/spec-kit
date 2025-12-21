"""
specify_cli.commands.spiff - SPIFF Workflow Management CLI

Rich CLI interface for BPMN workflow execution and validation.
Includes commands for workflow creation, execution, and OTEL validation.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.json import JSON as RichJSON

from ..core.shell import colour, dump_json
from ..spiff.ops import (
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
    discover_external_projects,
    validate_external_project_with_spiff,
    batch_validate_external_projects,
    run_8020_external_project_validation,
)

console = Console()

app = typer.Typer(help="SPIFF BPMN workflow management and validation")


@app.command()
def validate(
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of validation iterations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON file"),
):
    """Execute full OTEL validation workflow."""
    console.print(Panel("[bold cyan]SPIFF OTEL Validation[/bold cyan]", expand=False))

    for iteration in range(iterations):
        if iterations > 1:
            console.print(f"\n[cyan]Iteration {iteration + 1}/{iterations}[/cyan]")

        try:
            # Create workflow with critical tests
            test_commands = [
                "python -c 'import opentelemetry'",
                "python -c 'from specify_cli.spiff.runtime import run_bpmn'",
                "python -c 'from specify_cli.core import WorkflowAttributes'",
            ]

            workflow_path = Path.home() / ".cache" / "spec_kit" / "otel_validation.bpmn"

            colour("→ Creating OTEL validation workflow...", "cyan")
            create_otel_validation_workflow(workflow_path, test_commands)

            colour("→ Executing validation workflow...", "cyan")
            result = execute_otel_validation_workflow(workflow_path, test_commands)

            # Display results
            console.print()
            results_table = Table(title="Validation Results", show_header=True, header_style="bold cyan")
            results_table.add_column("Step", style="cyan")
            results_table.add_column("Status", style="white")
            results_table.add_column("Duration", style="magenta")

            for step in result.validation_steps:
                status = "[green]✓[/green]" if step.success else "[red]✗[/red]"
                results_table.add_row(
                    step.name,
                    status,
                    f"{step.duration_seconds:.2f}s"
                )

            console.print(results_table)

            # Summary
            console.print()
            if result.success:
                colour(f"✓ Validation succeeded ({result.duration_seconds:.2f}s)", "green")
            else:
                colour(f"✗ Validation failed ({result.duration_seconds:.2f}s)", "red")
                if result.errors:
                    console.print("\n[red]Errors:[/red]")
                    for error in result.errors:
                        console.print(f"  • {error}")

            # Export if requested
            if export_json:
                export_json.parent.mkdir(parents=True, exist_ok=True)
                import json
                export_json.write_text(json.dumps(result.to_dict(), indent=2))
                colour(f"✓ Results exported to {export_json}", "green")

        except Exception as e:
            colour(f"✗ Validation failed: {e}", "red")
            raise typer.Exit(1)


@app.command()
def validate_quick(
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON file"),
):
    """Quick 80/20 OTEL validation (critical path only)."""
    console.print(Panel("[bold cyan]SPIFF 80/20 OTEL Validation[/bold cyan]", expand=False))

    try:
        colour("→ Running critical path validation...", "cyan")
        result = run_8020_otel_validation(test_scope="core")

        # Display results
        console.print()
        results_table = Table(title="Validation Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Step", style="cyan")
        results_table.add_column("Status", style="white")
        results_table.add_column("Duration", style="magenta")

        for step in result.validation_steps:
            status = "[green]✓[/green]" if step.success else "[red]✗[/red]"
            results_table.add_row(step.name, status, f"{step.duration_seconds:.2f}s")

        console.print(results_table)

        # Summary
        console.print()
        if result.success:
            colour(f"✓ Validation succeeded ({result.duration_seconds:.2f}s)", "green")
        else:
            colour(f"✗ Validation failed ({result.duration_seconds:.2f}s)", "red")

        # Export if requested
        if export_json:
            export_json.parent.mkdir(parents=True, exist_ok=True)
            import json
            export_json.write_text(json.dumps(result.to_dict(), indent=2))
            colour(f"✓ Results exported to {export_json}", "green")

    except Exception as e:
        colour(f"✗ Validation failed: {e}", "red")
        raise typer.Exit(1)


@app.command()
def create_workflow(
    output: Path = typer.Option("workflow.bpmn", "--output", "-o", help="Output BPMN file"),
    test_cmd: Optional[str] = typer.Option(None, "--test", "-t", help="Test command to include (can be repeated)"),
):
    """Create custom BPMN validation workflow."""
    console.print(Panel("[bold cyan]Create BPMN Workflow[/bold cyan]", expand=False))

    try:
        test_commands = []
        if test_cmd:
            test_commands = [test_cmd]

        colour(f"→ Creating workflow with {len(test_commands)} test commands...", "cyan")
        workflow_path = create_otel_validation_workflow(output, test_commands)

        colour(f"✓ Workflow created: {workflow_path}", "green")
        colour(f"  File size: {workflow_path.stat().st_size} bytes", "blue")

    except Exception as e:
        colour(f"✗ Failed to create workflow: {e}", "red")
        raise typer.Exit(1)


@app.command()
def run_workflow(
    workflow_file: Path = typer.Argument(..., help="BPMN workflow file to execute"),
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON"),
):
    """Execute a BPMN workflow file."""
    console.print(Panel(f"[bold cyan]Execute Workflow: {workflow_file.name}[/bold cyan]", expand=False))

    try:
        if not workflow_file.exists():
            colour(f"✗ Workflow file not found: {workflow_file}", "red")
            raise typer.Exit(1)

        colour("→ Validating workflow...", "cyan")
        from ..spiff.runtime import validate_bpmn_file, run_bpmn

        if not validate_bpmn_file(workflow_file):
            colour("✗ Workflow validation failed", "red")
            raise typer.Exit(1)

        colour("✓ Workflow is valid", "green")

        colour("→ Executing workflow...", "cyan")
        result = run_bpmn(workflow_file)

        # Display results
        console.print()
        results_panel = Panel(
            f"[cyan]Status:[/cyan] {result['status']}\n"
            f"[cyan]Duration:[/cyan] {result['duration_seconds']:.2f}s\n"
            f"[cyan]Steps:[/cyan] {result['steps_executed']}\n"
            f"[cyan]Total Tasks:[/cyan] {result['total_tasks']}\n"
            f"[cyan]Completed:[/cyan] {result['completed_tasks']}",
            title="[bold cyan]Execution Results[/bold cyan]",
        )
        console.print(results_panel)

        if export_json:
            export_json.parent.mkdir(parents=True, exist_ok=True)
            import json
            export_json.write_text(json.dumps(result, indent=2))
            colour(f"✓ Results exported to {export_json}", "green")

    except Exception as e:
        colour(f"✗ Execution failed: {e}", "red")
        raise typer.Exit(1)


@app.command()
def discover_projects(
    search_path: Path = typer.Option(Path.home() / "projects", "--path", "-p", help="Path to search"),
    max_depth: int = typer.Option(3, "--depth", "-d", help="Maximum directory depth"),
    min_confidence: float = typer.Option(0.5, "--confidence", "-c", help="Minimum confidence threshold"),
):
    """Discover Python projects in a directory."""
    console.print(Panel("[bold cyan]Discover Python Projects[/bold cyan]", expand=False))

    try:
        colour(f"→ Searching {search_path}...", "cyan")
        projects = discover_external_projects(
            search_path=search_path,
            max_depth=max_depth,
            min_confidence=min_confidence,
        )

        if not projects:
            colour("No projects found matching criteria", "yellow")
            return

        # Display projects
        console.print()
        projects_table = Table(title="Discovered Projects", show_header=True, header_style="bold cyan")
        projects_table.add_column("Name", style="cyan")
        projects_table.add_column("Type", style="magenta")
        projects_table.add_column("Manager", style="blue")
        projects_table.add_column("Confidence", style="white", justify="right")

        for project in projects:
            projects_table.add_row(
                project.name,
                project.project_type,
                project.package_manager,
                f"{project.confidence:.0%}"
            )

        console.print(projects_table)

        colour(f"\n✓ Found {len(projects)} projects", "green")

    except Exception as e:
        colour(f"✗ Discovery failed: {e}", "red")
        raise typer.Exit(1)


@app.command()
def validate_external(
    project_path: Path = typer.Argument(..., help="Path to external project"),
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON"),
):
    """Validate an external project with spec-kit."""
    console.print(Panel(f"[bold cyan]Validate External Project: {project_path.name}[/bold cyan]", expand=False))

    try:
        if not project_path.exists():
            colour(f"✗ Project path not found: {project_path}", "red")
            raise typer.Exit(1)

        colour("→ Analyzing project...", "cyan")
        from ..spiff.ops.external_projects import _is_python_project

        project_info = _is_python_project(project_path)
        if not project_info:
            colour("✗ Not a Python project", "red")
            raise typer.Exit(1)

        colour(f"✓ Project analyzed: {project_info.project_type}", "green")

        colour("→ Validating with spec-kit...", "cyan")
        result = validate_external_project_with_spiff(project_info)

        # Display results
        console.print()
        results_panel = Panel(
            f"[cyan]Success:[/cyan] {result.success}\n"
            f"[cyan]Duration:[/cyan] {result.duration_seconds:.2f}s\n"
            f"[cyan]Tests Passed:[/cyan] {sum(1 for v in result.test_results.values() if v)}/{len(result.test_results)}",
            title="[bold cyan]Validation Results[/bold cyan]",
        )
        console.print(results_panel)

        if export_json:
            export_json.parent.mkdir(parents=True, exist_ok=True)
            import json
            export_json.write_text(json.dumps(result.to_dict(), indent=2))
            colour(f"✓ Results exported to {export_json}", "green")

    except Exception as e:
        colour(f"✗ Validation failed: {e}", "red")
        raise typer.Exit(1)


@app.command()
def batch_validate(
    search_path: Path = typer.Option(Path.home() / "projects", "--path", "-p", help="Path to search"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Use parallel execution"),
    max_workers: int = typer.Option(4, "--workers", "-w", help="Maximum worker threads"),
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON"),
):
    """Validate multiple projects in batch."""
    console.print(Panel("[bold cyan]Batch Validate Projects[/bold cyan]", expand=False))

    try:
        colour("→ Discovering projects...", "cyan")
        projects = discover_external_projects(search_path=search_path, max_depth=2)

        if not projects:
            colour("No projects found", "yellow")
            return

        colour(f"→ Validating {len(projects)} projects (parallel={parallel})...", "cyan")
        results = batch_validate_external_projects(
            projects,
            parallel=parallel,
            max_workers=max_workers,
        )

        # Display results
        console.print()
        results_table = Table(title="Batch Validation Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Project", style="cyan")
        results_table.add_column("Status", style="white")
        results_table.add_column("Duration", style="magenta")

        for result in results:
            status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
            results_table.add_row(
                result.project_name,
                status,
                f"{result.duration_seconds:.2f}s"
            )

        console.print(results_table)

        # Summary
        successful = sum(1 for r in results if r.success)
        console.print()
        colour(f"✓ Completed: {successful}/{len(results)} successful", "green")

        if export_json:
            export_json.parent.mkdir(parents=True, exist_ok=True)
            import json
            export_json.write_text(json.dumps(
                [r.to_dict() for r in results],
                indent=2
            ))
            colour(f"✓ Results exported to {export_json}", "green")

    except Exception as e:
        colour(f"✗ Batch validation failed: {e}", "red")
        raise typer.Exit(1)


@app.command()
def validate_8020(
    search_path: Path = typer.Option(Path.home() / "projects", "--path", "-p", help="Path to search"),
    max_depth: int = typer.Option(2, "--depth", "-d", help="Maximum directory depth"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by project type"),
    export_json: Optional[Path] = typer.Option(None, "--export-json", help="Export results to JSON"),
):
    """Quick 80/20 validation of critical external projects."""
    console.print(Panel("[bold cyan]SPIFF 80/20 External Project Validation[/bold cyan]", expand=False))

    try:
        colour("→ Running critical path validation...", "cyan")
        summary = run_8020_external_project_validation(
            search_path=search_path,
            max_depth=max_depth,
            project_type_filter=project_type,
            parallel=True,
        )

        # Display results
        console.print()
        console.print(f"[cyan]Discovered:[/cyan] {summary['total_discovered']} projects")
        console.print(f"[cyan]Selected (80/20):[/cyan] {summary['critical_selected']} projects")
        console.print(f"[cyan]Validated:[/cyan] {summary['validated']} projects")
        console.print(f"[cyan]Successful:[/cyan] {summary['successful']} projects")
        console.print(f"[cyan]Success Rate:[/cyan] {summary['success_rate']:.0%}")

        if export_json:
            export_json.parent.mkdir(parents=True, exist_ok=True)
            import json
            export_json.write_text(json.dumps(summary, indent=2))
            colour(f"✓ Results exported to {export_json}", "green")

    except Exception as e:
        colour(f"✗ Validation failed: {e}", "red")
        raise typer.Exit(1)
