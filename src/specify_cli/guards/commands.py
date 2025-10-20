"""
Guard CLI Commands

Guards are Python files that validate code and return structured JSON.
Category = Testing scope (static-analysis, unit, integration, api, architecture, ui)
Type = Technology (python, pytest, requests, generic)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from specify_cli.guards.executor import GuardExecutor, GuardHistory
from specify_cli.guards.registry import GuardRegistry
from specify_cli.guards.scaffolder import GuardScaffolder
from specify_cli.guards.types import Comment, CommentCategory, CommentNote

console = Console()
guard_app = typer.Typer(name="guard", help="Manage validation guards with teaching mechanisms")


def get_project_root() -> Path:
    """Get project root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists() or (current / ".specify").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_registry() -> GuardRegistry:
    """Get guard registry instance."""
    project_root = get_project_root()
    guards_base = project_root / ".specify" / "guards"
    return GuardRegistry(guards_base)


@guard_app.command("types")
def cmd_types(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information")
):
    """
    Display Category × Type matrix showing available guard types.
    
    Teaching mechanism: Shows how categories (technology) and types (purpose)
    combine to create guard types.
    """
    registry = get_registry()
    
    # Load guard types directly instead of relying on matrix
    registry._load_guard_types()
    if registry._guard_types_cache is None:
        available_types = []
    else:
        available_types = list(registry._guard_types_cache.values())
    
    # If no guard types available, show helpful message
    if not available_types:
        console.print("[yellow]No guard types available.[/yellow]")
        console.print("\n[dim]Guard types are stored in:[/dim]")
        console.print("  - guards/types/ (official)")
        console.print("  - .specify/guards/types-custom/ (custom)")
        console.print("\n[dim]Add guard types to:[/dim]")
        console.print("  guards/types/<guard-type-name>/")
        return
    
    # Teaching output: Explain Category × Type architecture
    console.print("\n[bold cyan]Available Guard Types[/bold cyan]")
    console.print("[dim]Category = Testing scope (static-analysis, unit, integration, api, architecture, ui)[/dim]")
    console.print("[dim]Type = Technology (python, pytest, requests, generic)[/dim]\n")
    
    # Build table showing guard types
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Guard Type", style="cyan", width=30)
    table.add_column("Category", style="green", width=20)
    table.add_column("Type", style="blue", width=15)
    
    for guard_type in sorted(available_types, key=lambda gt: (gt.category.name, gt.type.name)):
        table.add_row(
            guard_type.id,
            guard_type.category.name,
            guard_type.type.name
        )
    
    console.print(table)
    console.print(f"\n[green]✓[/green] {len(available_types)} guard types available")
    
    # Verbose: Show details
    if verbose:
        console.print("\n[bold]Available Guard Types:[/bold]\n")
        for guard_type in available_types:
            console.print(f"[cyan]{guard_type.id}[/cyan]")
            console.print(f"  Category: {guard_type.category.name}")
            console.print(f"  Type: {guard_type.type.name}")
            console.print(f"  Teaching: {guard_type.combined_teaching[:80]}...")
            console.print()


@guard_app.command("create")
def cmd_create(
    guard_type_id: str = typer.Option(..., "--type", help="Guard type ID (e.g., unit-pytest)"),
    name: str = typer.Option(..., "--name", help="Guard name (kebab-case)"),
    tasks: Optional[str] = typer.Option(None, "--task", help="Task IDs (comma-separated)"),
    tags: Optional[str] = typer.Option(None, "--tag", help="Tags (comma-separated)")
):
    """
    Create a new guard with teaching about category and type standards.
    
    Teaching mechanism: Explains category (how to build) and type (what to validate)
    standards when creating the guard.
    """
    registry = get_registry()
    
    # Get guard type
    guard_type = registry.get_guard_type(guard_type_id)
    if not guard_type:
        console.print(f"[red]✗ Error:[/red] Guard type '{guard_type_id}' not found\n")
        
        # Load all available guard types
        registry._load_guard_types()
        if registry._guard_types_cache:
            available = list(registry._guard_types_cache.keys())
            
            # Check for similar names (did you mean?)
            from difflib import get_close_matches
            suggestions = get_close_matches(guard_type_id, available, n=3, cutoff=0.6)
            
            if suggestions:
                console.print("[yellow]Did you mean?[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • {suggestion}")
                console.print()
            
            console.print("[dim]Available guard types:[/dim]")
            for gt_id in sorted(available):
                gt = registry._guard_types_cache[gt_id]
                console.print(f"  • [cyan]{gt_id}[/cyan] - {gt.category.name} × {gt.type.name}")
        else:
            console.print("[yellow]No guard types available.[/yellow]")
            console.print("\n[dim]Add guard types to:[/dim]")
            console.print("  guards/types/<guard-type-name>/")
        
        console.print("\n[dim]Example:[/dim]")
        console.print("  specify guard create --type static-analysis-python --name my-guard")
        raise typer.Exit(1)
    
    # Generate guard ID
    guard_id = registry.generate_id()
    
    # Load full guard-type.yaml for rich metadata
    from specify_cli.guards.utils import load_yaml
    guard_type_yaml_path = guard_type.templates_dir.parent / "guard-type.yaml"
    guard_metadata = {}
    if guard_type_yaml_path.exists():
        try:
            guard_metadata = load_yaml(guard_type_yaml_path)
        except Exception:
            pass
    
    # Teaching: Category (how to build) - Enhanced
    console.print(f"\n[bold cyan]Creating {guard_type_id} guard...[/bold cyan]\n")
    
    description = guard_metadata.get("description", guard_type.category.teaching_content)
    if isinstance(description, str) and "\n" in description:
        # Multi-line description - show key points
        lines = [line.strip() for line in description.split("\n") if line.strip()]
        display_text = "\n".join(lines[:8])  # Show first 8 lines
        if len(lines) > 8:
            display_text += f"\n[dim]... ({len(lines) - 8} more lines in full description)[/dim]"
    else:
        display_text = str(description)
    
    console.print(Panel(
        f"[bold]Category:[/bold] {guard_type.category.name}\n"
        f"[bold]Type:[/bold] {guard_type.type.name}\n\n"
        f"{display_text}",
        title="📚 What This Guard Does",
        border_style="cyan"
    ))
    
    # Show how_to_use if available
    how_to_use = guard_metadata.get("how_to_use", "")
    if how_to_use:
        # Extract just the key steps
        lines = [line.strip() for line in how_to_use.split("\n") if line.strip() and not line.startswith("```")]
        steps = [line for line in lines if line.startswith("**Step")][:5]
        if steps:
            steps_text = "\n".join(steps)
            console.print(Panel(
                f"{steps_text}\n\n[dim]Full instructions in guard README[/dim]",
                title="📖 Quick Start Steps",
                border_style="green"
            ))
    
    # Parse tasks and tags
    task_list = [t.strip() for t in tasks.split(",")] if tasks else []
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Scaffold guard files
    scaffolder = GuardScaffolder(
        guard_id=guard_id,
        guard_type=guard_type,
        name=name,
        project_root=get_project_root()
    )
    
    try:
        result = scaffolder.scaffold()
        
        # Register guard
        registry.add_guard(
            guard_id=guard_id,
            guard_type=guard_type_id,
            name=name,
            command=result["command"],
            files=result["files"],
            tags=tag_list,
            tasks=task_list
        )
        
        # Success output with combined standard
        console.print(f"\n[green]✓[/green] Created guard [cyan]{guard_id}[/cyan]: {name}")
        console.print(f"\n[bold]Guard Type:[/bold] {guard_type.category.name} × {guard_type.type.name}")
        
        console.print("\n[bold]Files created:[/bold]")
        for file_path in result["files"]:
            console.print(f"  - {file_path}")
        
        # Show parameter guidance
        params_schema = guard_metadata.get("params_schema", {})
        if params_schema:
            console.print(f"\n[bold]Configuration:[/bold] Edit [cyan].specify/guards/{guard_id}/guard.yaml[/cyan]")
            console.print("[dim]Key parameters:[/dim]")
            for param_name, param_info in list(params_schema.items())[:3]:
                if isinstance(param_info, dict):
                    desc = param_info.get("description", "").split("\n")[0][:60]
                    default = param_info.get("default", "")
                    console.print(f"  • [cyan]{param_name}[/cyan]: {desc}... (default: {default})")
            if len(params_schema) > 3:
                console.print(f"  [dim]... and {len(params_schema) - 3} more parameters[/dim]")
        
        console.print("\n[bold cyan]📋 Next Steps:[/bold cyan]")
        console.print(f"  1. [bold]Configure parameters[/bold] in .specify/guards/{guard_id}/guard.yaml")
        console.print(f"  2. [bold]Run the guard:[/bold] [cyan]specify guard run {guard_id}[/cyan]")
        console.print(f"  3. [bold]View results:[/bold] [cyan]specify guard history {guard_id}[/cyan]")
        
        # Emphasize comment requirement for failures
        console.print("\n[bold yellow]⚠️  Important - Comment on Every Failure:[/bold yellow]")
        console.print("[yellow]If the guard fails, you MUST add a diagnostic comment:[/yellow]")
        console.print(f"  [cyan]specify guard comment {guard_id} \\[/cyan]")
        console.print("    [cyan]--category root-cause \\[/cyan]")
        console.print("    [cyan]--done \"<what you found>\" \\[/cyan]")
        console.print("    [cyan]--expected \"<what should happen next>\" \\[/cyan]")
        console.print("    [cyan]--todo \"<what you'll do>\"[/cyan]")
        console.print("\n[dim]This builds institutional knowledge for future runs.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error creating guard:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@guard_app.command("run")
def cmd_run(
    guard_id: str = typer.Argument(..., help="Guard ID (e.g., G001)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Execute a guard and display analysis with teaching.
    
    Teaching mechanism: Shows diagnostic analysis, explains failures,
    and guides towards fixes.
    """
    registry = get_registry()
    
    # Get guard
    guard_data = registry.get_guard(guard_id)
    if not guard_data:
        console.print(f"[red]✗ Error:[/red] Guard '{guard_id}' not found\n")
        
        # Show available guards
        all_guards = registry.list_guards()
        if all_guards:
            console.print("[dim]Available guards:[/dim]")
            for g in all_guards[:5]:  # Show first 5
                console.print(f"  • [cyan]{g['id']}[/cyan] - {g['name']} ({g['guard_type']})")
            if len(all_guards) > 5:
                console.print(f"  ... and {len(all_guards) - 5} more")
            console.print()
        
        console.print("[dim]See all guards:[/dim]")
        console.print("  specify guard list")
        console.print("\n[dim]Create a guard:[/dim]")
        console.print("  specify guard create --type <type> --name <name>")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Running guard {guard_id}: {guard_data['name']}[/cyan]")
    console.print(f"[dim]Type: {guard_data['guard_type']}[/dim]\n")
    
    # Execute guard
    executor = GuardExecutor(guard_id=guard_id, registry=registry)
    result = executor.execute()
    
    # Display result header
    status_icon = "✓" if result.passed else "✗"
    status_color = "green" if result.passed else "red"
    status_text = "PASSED" if result.passed else "FAILED"
    
    console.print(f"\n[{status_color}]{status_icon} Guard {guard_id} {status_text}[/{status_color}]")
    console.print(f"  Duration: {result.duration_ms}ms")
    if not result.passed:
        console.print(f"  Exit code: {result.exit_code}")
    
    # Parse and display raw guard output (JSON details)
    console.print("\n[bold]Guard Output:[/bold]")
    try:
        guard_output = json.loads(result.stdout) if result.stdout else {}
        
        # Show analysis
        if guard_output.get("analysis"):
            console.print(f"  Analysis: {guard_output['analysis']}")
        
        # Show details if available
        details = guard_output.get("details", {})
        if details and verbose:
            console.print("\n  [dim]Details:[/dim]")
            for key, value in details.items():
                console.print(f"    {key}: {value}")
        
        # Show violations for code quality guards
        violations = guard_output.get("violations", [])
        if violations and verbose:
            console.print(f"\n  [dim]Violations (showing first {len(violations)}):[/dim]")
            for v in violations[:5]:
                file = v.get("filename", "unknown")
                line = v.get("location", {}).get("row", "?")
                code = v.get("code", "?")
                msg = v.get("message", "")
                console.print(f"    {file}:{line} [{code}] {msg}")
    except json.JSONDecodeError:
        # Fallback to analysis if JSON parse fails
        if result.analysis:
            console.print(f"  {result.analysis}")
    
    # Show recent history/comment timeline
    history = GuardHistory(guard_id, registry)
    recent_runs = history.get_lineage(limit=3)
    
    if len(recent_runs) > 1:  # More than just current run
        console.print("\n[bold]Recent History:[/bold]")
        for i, run in enumerate(recent_runs[1:], 1):  # Skip current run (first)
            timestamp = run.get("timestamp", "unknown")
            run_passed = run.get("passed", False)
            run_icon = "✓" if run_passed else "✗"
            run_color = "green" if run_passed else "red"
            
            # Parse timestamp for display
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_display = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                time_display = timestamp
            
            console.print(f"  [{run_color}]{run_icon}[/{run_color}] {time_display} - {run.get('analysis', 'No analysis')[:60]}")
            
            # Show comments if any
            comments = run.get("comments", [])
            if comments:
                latest_comment = comments[-1]
                note = latest_comment.get("note", {})
                console.print(f"     [dim]💬 {note.get('done', 'N/A')[:50]}[/dim]")
    
    # Show next steps based on result
    if not result.passed:
        console.print("\n[bold red]❌ GUARD FAILED - ACTION REQUIRED[/bold red]")
        console.print("\n[bold yellow]📝 YOU MUST ADD A DIAGNOSTIC COMMENT:[/bold yellow]")
        console.print("[yellow]This is REQUIRED to build institutional knowledge.[/yellow]\n")
        console.print(f"  [bold cyan]specify guard comment {guard_id} \\[/bold cyan]")
        console.print("    [cyan]--category root-cause \\[/cyan]")
        console.print("    [cyan]--done \"<describe what went wrong>\" \\[/cyan]")
        console.print("    [cyan]--expected \"<what should happen after fix>\" \\[/cyan]")
        console.print("    [cyan]--todo \"<steps to fix>\"[/cyan]")
        
        console.print("\n[yellow]Troubleshooting workflow:[/yellow]")
        console.print("  1. [bold]Analyze failure:[/bold] Review output above")
        console.print(f"  2. [bold]Check history:[/bold] specify guard history {guard_id}")
        console.print("  3. [bold]Document findings:[/bold] Add comment (REQUIRED)")
        console.print("  4. [bold]Apply fix:[/bold] Based on analysis")
        console.print(f"  5. [bold]Re-run:[/bold] specify guard run {guard_id}")
        console.print("  6. [bold]Document fix:[/bold] Add follow-up comment")
    else:
        console.print("\n[green]✓ Guard passed - next steps:[/green]")
        console.print("  • Mark related tasks complete in tasks.md")
        console.print("  • If this fixes a previous failure, document it:")
        console.print(f"    [cyan]specify guard comment {guard_id} --category fix-applied ...[/cyan]")
        console.print("  • Continue with implementation")
    
    # Show command reference
    console.print("\n[cyan]Commands:[/cyan]")
    console.print("  [bold]View full history:[/bold]")
    console.print(f"    specify guard history {guard_id}")
    console.print(f"    specify guard history {guard_id} --limit 10")
    console.print()
    console.print("  [bold]Add diagnostic comment:[/bold]")
    console.print(f"    specify guard comment {guard_id} \\")
    console.print("      --category <root-cause|fix-applied|investigation|workaround|false-positive> \\")
    console.print("      --done \"<what was changed/investigated since last run>\" \\")
    console.print("      --expected \"<what you expect to see in next run>\" \\")
    console.print("      --todo \"<what you plan to do before next run>\"")
    console.print()
    console.print("  [bold]Example comment:[/bold]")
    if not result.passed:
        console.print(f"    specify guard comment {guard_id} \\")
        console.print("      --category investigation \\")
        console.print("      --done \"Analyzed failure root cause\" \\")
        console.print("      --expected \"Guard passes after fix\" \\")
        console.print("      --todo \"Implement suggested changes\"")
    else:
        console.print(f"    specify guard comment {guard_id} \\")
        console.print("      --category fix-applied \\")
        console.print("      --done \"Applied fix for previous issue\" \\")
        console.print("      --expected \"Guard continues passing\" \\")
        console.print("      --todo \"Monitor for regressions\"")
    
    if not result.passed:
        raise typer.Exit(1)


@guard_app.command("list")
def cmd_list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag")
):
    """
    List guards grouped by category with history summary.
    
    Teaching mechanism: Shows guards organized by technology category,
    reveals relationships, displays execution history.
    """
    registry = get_registry()
    guards = registry.list_guards()
    
    if not guards:
        console.print("[yellow]No guards found.[/yellow]")
        console.print("\n[dim]Create a guard with:[/dim]")
        console.print("  specify guard create --type <type> --name <name>")
        return
    
    # Filter guards
    if category:
        guards = [g for g in guards if g.get("guard_type", "").startswith(category)]
    if tag:
        guards = [g for g in guards if tag in g.get("tags", [])]
    
    # Group by category and get guard type info
    by_category = {}
    for guard in guards:
        guard_type_id = guard["guard_type"]
        
        # Get guard type details from registry
        guard_type_obj = registry.get_guard_type(guard_type_id)
        if guard_type_obj:
            cat = guard_type_obj.category.name
            type_name = guard_type_obj.type.name
        else:
            cat = "unknown"
            type_name = "unknown"
        
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({**guard, "_type": type_name})
    
    # Display guards by category
    console.print("\n[bold cyan]Guards by Category × Type[/bold cyan]")
    console.print(f"[dim]Total: {len(guards)} guards[/dim]\n")
    
    for cat_name in sorted(by_category.keys()):
        cat_guards = by_category[cat_name]
        
        # Category header
        console.print(f"\n[bold green]Category: {cat_name}[/bold green] ({len(cat_guards)} guards)")
        
        # Table for this category
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Name", style="white", width=20)
        table.add_column("Type", style="blue", width=15)
        table.add_column("Last Run", style="yellow", width=12)
        table.add_column("Result", style="white", width=8)
        table.add_column("Comments", style="magenta", width=8)
        
        for guard in cat_guards:
            # Get last run info (placeholder - will implement with executor)
            last_run = "[dim]never[/dim]"
            result = "[dim]-[/dim]"
            comments = "0"
            
            table.add_row(
                guard["id"],
                guard["name"],
                guard["_type"],  # Show the type, not the full guard_type ID
                last_run,
                result,
                comments
            )
        
        console.print(table)
    
    # Teaching: Next actions
    console.print("\n[cyan]💡 Run a guard:[/cyan] specify guard run <ID>")
    console.print("[cyan]💡 View history:[/cyan] specify guard history <ID>")


@guard_app.command("history")
def cmd_history(
    guard_id: str = typer.Argument(..., help="Guard ID (e.g., G001)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of runs to show")
):
    """
    Display guard execution history with comment lineage.
    
    Teaching mechanism: Shows progression of runs with comments,
    reveals patterns, documents investigation journey.
    """
    registry = get_registry()
    
    # Get guard
    guard_data = registry.get_guard(guard_id)
    if not guard_data:
        console.print(f"[red]Error:[/red] Guard '{guard_id}' not found")
        raise typer.Exit(1)
    
    # Get history
    history = GuardHistory(guard_id, registry)
    runs = history.get_lineage(limit=limit)
    
    if not runs:
        console.print(f"[yellow]No execution history for {guard_id}[/yellow]")
        console.print("\n[dim]Run the guard first:[/dim]")
        console.print(f"  specify guard run {guard_id}")
        return
    
    # Display header
    console.print(f"\n[bold cyan]History for {guard_id}: {guard_data['name']}[/bold cyan]")
    console.print(f"[dim]Type: {guard_data['guard_type']}[/dim]")
    console.print(f"[dim]Total runs: {len(runs)}[/dim]\n")
    
    # Display each run with comments
    for i, run in enumerate(runs[:limit], 1):
        # Run info
        timestamp = run.get("timestamp", "unknown")
        passed = run.get("passed", False)
        status_icon = "✓" if passed else "✗"
        status_color = "green" if passed else "red"
        
        console.print(f"[bold]{i}. [{status_color}]{status_icon}[/{status_color}] {timestamp}[/bold]")
        console.print(f"   Duration: {run.get('duration_ms', 0)}ms")
        console.print(f"   Exit code: {run.get('exit_code', -1)}")
        
        # Comments for this run
        comments = run.get("comments", [])
        if comments:
            console.print(f"   [bold]Comments ({len(comments)}):[/bold]")
            for comment in comments:
                cat = comment.get("category", "unknown")
                note = comment.get("note", {})
                console.print(f"     [{cat}]")
                console.print(f"       Done: {note.get('done', 'N/A')}")
                console.print(f"       Expected: {note.get('expected', 'N/A')}")
                console.print(f"       Todo: {note.get('todo', 'N/A')}")
        
        console.print()
    
    # Teaching: Pattern analysis
    pass_rate = sum(1 for r in runs if r.get("passed")) / len(runs) * 100
    console.print(f"[cyan]Pass rate:[/cyan] {pass_rate:.1f}%")
    
    if pass_rate < 50:
        console.print("[yellow]💡 This guard is failing frequently.[/yellow]")
        console.print("   Review comments to understand patterns.")
        console.print("   Consider if the standard needs adjustment.")


@guard_app.command("comment")
def cmd_comment(
    guard_id: str = typer.Argument(..., help="Guard ID (e.g., G001)"),
    category: str = typer.Option(..., "--category", "-c", help="Comment category: root-cause, fix-applied, investigation, workaround, false-positive"),
    done: str = typer.Option(..., "--done", help="What was done since last run"),
    expected: str = typer.Option(..., "--expected", help="What is expected next run"),
    todo: str = typer.Option(..., "--todo", help="What will be done before next run"),
    run_id: Optional[str] = typer.Option(None, "--run", help="Specific run ID (defaults to latest)")
):
    """
    Add a diagnostic comment to a guard run.
    
    Teaching mechanism: Structured comment format (done → expected → todo)
    creates narrative of investigation and fixes.
    """
    registry = get_registry()
    
    # Validate guard exists
    guard_data = registry.get_guard(guard_id)
    if not guard_data:
        console.print(f"[red]Error:[/red] Guard '{guard_id}' not found")
        raise typer.Exit(1)
    
    # Validate category
    try:
        comment_cat = CommentCategory(category)
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid category '{category}'")
        console.print("\n[dim]Valid categories:[/dim]")
        for cat in CommentCategory:
            console.print(f"  - {cat.value}")
        raise typer.Exit(1)
    
    # Create comment
    note = CommentNote(done=done, expected=expected, todo=todo)
    comment = Comment(
        timestamp=datetime.now(),
        category=comment_cat,
        note=note
    )
    
    # Add comment to history
    history = GuardHistory(guard_id, registry)
    history.add_comment(comment, run_id=run_id)
    
    # Success output
    console.print(f"\n[green]✓[/green] Added comment to {guard_id}")
    console.print(Panel(
        f"[bold]Category:[/bold] {category}\n\n"
        f"[bold]Done:[/bold] {done}\n"
        f"[bold]Expected:[/bold] {expected}\n"
        f"[bold]Todo:[/bold] {todo}",
        title="📝 Comment Added",
        border_style="green"
    ))
    
    # Teaching: Show previous comments
    runs = history.get_lineage(limit=1)
    if runs and runs[0].get("comments"):
        prev_comments = runs[0]["comments"]
        if len(prev_comments) > 1:
            console.print(f"\n[cyan]💡 This run now has {len(prev_comments)} comments.[/cyan]")
            console.print(f"   View full history: specify guard history {guard_id}")


# Export commands for CLI registration
__all__ = [
    "guard_app",
    "cmd_types",
    "cmd_create",
    "cmd_run",
    "cmd_list",
    "cmd_history",
    "cmd_comment"
]
