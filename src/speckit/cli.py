"""
Command-line interface for spec-kit.

This module provides a Typer-based CLI that exposes all library functions
with human-readable and JSON output modes.

Usage:
    speckit init                    # Initialize a new project
    speckit specify "description"   # Generate a specification
    speckit plan --feature 001-xxx  # Generate a technical plan
    speckit tasks --feature 001-xxx # Generate task breakdown
"""

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from speckit.config import LLMConfig, SpecKitConfig
from speckit.speckit import SpecKit

# Create Typer app
app = typer.Typer(
    name="speckit",
    help="Spec-driven development with universal LLM support.",
    add_completion=False,
)

# Rich console for output
console = Console()
err_console = Console(stderr=True)


class OutputFormat(str, Enum):
    """Output format options."""

    RICH = "rich"
    JSON = "json"
    QUIET = "quiet"


# Global options
class GlobalOptions:
    """Global CLI options."""

    project_path: Path = Path.cwd()
    format: OutputFormat = OutputFormat.RICH
    verbose: bool = False


_global_opts = GlobalOptions()


def get_kit() -> SpecKit:
    """Get SpecKit instance with current configuration."""
    return SpecKit(_global_opts.project_path)


def output(content: str, format_type: Optional[OutputFormat] = None) -> None:
    """Output content in the specified format."""
    fmt = format_type or _global_opts.format

    if fmt == OutputFormat.QUIET:
        return
    elif fmt == OutputFormat.JSON:
        console.print_json(content) if content.startswith("{") else console.print(content)
    else:
        # Rich format - render markdown
        if content.startswith("#") or "**" in content:
            console.print(Markdown(content))
        else:
            console.print(content)


def output_json(data: dict) -> None:
    """Output data as JSON."""
    if _global_opts.format == OutputFormat.JSON:
        console.print_json(json.dumps(data, indent=2, default=str))
    elif _global_opts.format != OutputFormat.QUIET:
        console.print_json(json.dumps(data, indent=2, default=str))


def progress_context(description: str):
    """Create a progress context for LLM operations."""
    if _global_opts.format == OutputFormat.RICH:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    else:
        # Return a no-op context manager for non-rich formats
        from contextlib import nullcontext

        return nullcontext()


@app.callback()
def main(
    project_path: Optional[Path] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project directory (default: current directory)",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.RICH,
        "--format",
        "-f",
        help="Output format",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Spec-kit: Spec-driven development with universal LLM support."""
    _global_opts.project_path = project_path or Path.cwd()
    _global_opts.format = output_format
    _global_opts.verbose = verbose


# =============================================================================
# Init Command
# =============================================================================


@app.command()
def init(
    project_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name (default: directory name)",
    ),
):
    """Initialize a new spec-kit project."""
    kit = get_kit()
    project_path = kit.config.project_path

    # Use directory name if no name provided
    if project_name is None:
        project_name = project_path.name

    # Create directories
    kit.config.ensure_directories()

    # Create default config
    kit.config.save()

    if _global_opts.format == OutputFormat.RICH:
        console.print(
            Panel.fit(
                f"[green]Project initialized:[/green] {project_name}\n\n"
                f"[dim]Config:[/dim] {kit.config.config_path / 'config.yaml'}\n"
                f"[dim]Specs:[/dim] {kit.config.specs_path}",
                title="[bold]spec-kit[/bold]",
            )
        )
    elif _global_opts.format == OutputFormat.JSON:
        output_json(
            {
                "status": "initialized",
                "project_name": project_name,
                "project_path": str(project_path),
                "config_path": str(kit.config.config_path),
                "specs_path": str(kit.config.specs_path),
            }
        )


# =============================================================================
# Constitution Command
# =============================================================================


@app.command()
def constitution(
    project_name: str = typer.Argument(..., help="Project name"),
    principles: Optional[list[str]] = typer.Option(
        None,
        "--principle",
        "-p",
        help="Seed principles (can specify multiple)",
    ),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to file"),
):
    """Create or update project constitution."""
    kit = get_kit()

    with progress_context("Generating constitution...") as progress:
        if progress:
            task = progress.add_task("Generating constitution...", total=None)

        result = kit.constitution(project_name, principles)

        if progress:
            progress.update(task, completed=True)

    if save:
        path = kit.save(result)
        if _global_opts.verbose:
            console.print(f"[dim]Saved to: {path}[/dim]")

    if _global_opts.format == OutputFormat.JSON:
        output_json(result.model_dump())
    else:
        output(result.to_markdown())


# =============================================================================
# Specify Command
# =============================================================================


@app.command()
def specify(
    description: str = typer.Argument(..., help="Feature description"),
    feature_id: Optional[str] = typer.Option(
        None,
        "--feature-id",
        "-f",
        help="Feature ID (auto-generated if not provided)",
    ),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to file"),
):
    """Generate a feature specification from natural language."""
    kit = get_kit()

    with progress_context("Generating specification...") as progress:
        if progress:
            task = progress.add_task("Generating specification...", total=None)

        result = kit.specify(description, feature_id)

        if progress:
            progress.update(task, completed=True)

    if save:
        path = kit.save(result)
        if _global_opts.verbose:
            console.print(f"[dim]Saved to: {path}[/dim]")

    if _global_opts.format == OutputFormat.JSON:
        output_json(result.model_dump())
    else:
        output(result.to_markdown())


# =============================================================================
# Clarify Command
# =============================================================================


@app.command()
def clarify(
    feature: str = typer.Option(..., "--feature", "-f", help="Feature ID"),
    max_questions: int = typer.Option(5, "--max", "-m", help="Max questions"),
):
    """Identify clarification questions for a specification."""
    kit = get_kit()

    # Load specification
    spec = kit.load_specification(feature)
    if spec is None:
        err_console.print(f"[red]Specification not found: {feature}[/red]")
        raise typer.Exit(1)

    with progress_context("Analyzing specification...") as progress:
        if progress:
            task = progress.add_task("Analyzing specification...", total=None)

        updated_spec, questions = kit.clarify(spec, max_questions)

        if progress:
            progress.update(task, completed=True)

    if _global_opts.format == OutputFormat.JSON:
        output_json(
            {
                "feature_id": feature,
                "questions": [q.model_dump() for q in questions],
            }
        )
    else:
        if not questions:
            console.print("[green]No clarification questions needed.[/green]")
        else:
            console.print(f"\n[bold]Clarification Questions ({len(questions)}):[/bold]\n")
            for q in questions:
                console.print(q.to_markdown())
                console.print()


# =============================================================================
# Plan Command
# =============================================================================


@app.command()
def plan(
    feature: str = typer.Option(..., "--feature", "-f", help="Feature ID"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to file"),
):
    """Generate a technical implementation plan."""
    kit = get_kit()

    # Load specification
    spec = kit.load_specification(feature)
    if spec is None:
        err_console.print(f"[red]Specification not found: {feature}[/red]")
        raise typer.Exit(1)

    with progress_context("Generating technical plan...") as progress:
        if progress:
            task = progress.add_task("Generating technical plan...", total=None)

        result = kit.plan(spec)

        if progress:
            progress.update(task, completed=True)

    if save:
        path = kit.save(result)
        if _global_opts.verbose:
            console.print(f"[dim]Saved to: {path}[/dim]")

    if _global_opts.format == OutputFormat.JSON:
        output_json(result.model_dump())
    else:
        output(result.to_markdown())


# =============================================================================
# Tasks Command
# =============================================================================


@app.command()
def tasks(
    feature: str = typer.Option(..., "--feature", "-f", help="Feature ID"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to file"),
):
    """Generate implementation task breakdown."""
    kit = get_kit()

    # Load plan
    plan_obj = kit.load_plan(feature)
    if plan_obj is None:
        err_console.print(f"[red]Technical plan not found: {feature}[/red]")
        raise typer.Exit(1)

    with progress_context("Generating tasks...") as progress:
        if progress:
            task = progress.add_task("Generating tasks...", total=None)

        result = kit.tasks(plan_obj)

        if progress:
            progress.update(task, completed=True)

    if save:
        path = kit.save(result)
        if _global_opts.verbose:
            console.print(f"[dim]Saved to: {path}[/dim]")

    if _global_opts.format == OutputFormat.JSON:
        output_json(result.model_dump())
    else:
        output(result.to_markdown())


# =============================================================================
# Analyze Command
# =============================================================================


@app.command()
def analyze(
    feature: str = typer.Option(..., "--feature", "-f", help="Feature ID"),
):
    """Check consistency across all artifacts."""
    kit = get_kit()

    # Load all artifacts
    spec = kit.load_specification(feature)
    plan_obj = kit.load_plan(feature)
    tasks_obj = kit.load_tasks(feature)

    if spec is None or plan_obj is None or tasks_obj is None:
        err_console.print(f"[red]Missing artifacts for feature: {feature}[/red]")
        err_console.print("Required: spec.md, plan.md, tasks.md")
        raise typer.Exit(1)

    with progress_context("Analyzing artifacts...") as progress:
        if progress:
            task = progress.add_task("Analyzing artifacts...", total=None)

        result = kit.analyze(spec, plan_obj, tasks_obj)

        if progress:
            progress.update(task, completed=True)

    if _global_opts.format == OutputFormat.JSON:
        output_json(result.model_dump())
    else:
        output(result.to_markdown())

    # Exit with error code if there are errors
    if result.has_errors:
        raise typer.Exit(1)


# =============================================================================
# Config Commands
# =============================================================================


config_app = typer.Typer(help="Configuration management")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Show current configuration."""
    kit = get_kit()
    config = kit.config

    if _global_opts.format == OutputFormat.JSON:
        output_json(
            {
                "llm": {
                    "model": config.llm.model,
                    "temperature": config.llm.temperature,
                    "max_tokens": config.llm.max_tokens,
                    "timeout": config.llm.timeout,
                    "fallback_models": config.llm.fallback_models,
                },
                "storage": {
                    "backend": config.storage.backend,
                    "base_dir": config.storage.base_dir,
                    "specs_dir": config.storage.specs_dir,
                },
                "project_path": str(config.project_path),
                "language": config.language,
                "verbose": config.verbose,
            }
        )
    else:
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("Model", config.llm.model)
        table.add_row("Temperature", str(config.llm.temperature))
        table.add_row("Max Tokens", str(config.llm.max_tokens))
        table.add_row("Timeout", f"{config.llm.timeout}s")
        table.add_row("Fallback Models", ", ".join(config.llm.fallback_models))
        table.add_row("Specs Directory", config.storage.specs_dir)
        table.add_row("Project Path", str(config.project_path))

        console.print(table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g., 'model', 'temperature')"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    kit = get_kit()
    config = kit.config

    # Map keys to config attributes
    key_map = {
        "model": ("llm", "model"),
        "temperature": ("llm", "temperature"),
        "max_tokens": ("llm", "max_tokens"),
        "timeout": ("llm", "timeout"),
        "language": (None, "language"),
        "verbose": (None, "verbose"),
    }

    if key not in key_map:
        err_console.print(f"[red]Unknown config key: {key}[/red]")
        err_console.print(f"Valid keys: {', '.join(key_map.keys())}")
        raise typer.Exit(1)

    section, attr = key_map[key]

    # Convert value to appropriate type
    if attr in ("temperature",):
        value = float(value)
    elif attr in ("max_tokens", "timeout"):
        value = int(value)
    elif attr in ("verbose",):
        value = value.lower() in ("true", "1", "yes")

    # Set the value
    if section:
        obj = getattr(config, section)
        setattr(obj, attr, value)
    else:
        setattr(config, attr, value)

    # Save config
    config.save()

    if _global_opts.format != OutputFormat.QUIET:
        console.print(f"[green]Set {key} = {value}[/green]")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key to get"),
):
    """Get a configuration value."""
    kit = get_kit()
    config = kit.config

    key_map = {
        "model": config.llm.model,
        "temperature": config.llm.temperature,
        "max_tokens": config.llm.max_tokens,
        "timeout": config.llm.timeout,
        "language": config.language,
        "verbose": config.verbose,
    }

    if key not in key_map:
        err_console.print(f"[red]Unknown config key: {key}[/red]")
        raise typer.Exit(1)

    value = key_map[key]

    if _global_opts.format == OutputFormat.JSON:
        output_json({key: value})
    else:
        console.print(str(value))


# =============================================================================
# List Command
# =============================================================================


@app.command("list")
def list_features():
    """List all features in the project."""
    kit = get_kit()
    features = kit.list_features()

    if _global_opts.format == OutputFormat.JSON:
        output_json({"features": features})
    elif not features:
        console.print("[dim]No features found.[/dim]")
    else:
        table = Table(title="Features")
        table.add_column("Feature ID", style="cyan")
        table.add_column("Has Spec")
        table.add_column("Has Plan")
        table.add_column("Has Tasks")

        for feature_id in features:
            has_spec = "Yes" if kit.storage.artifact_exists(feature_id, "spec") else "-"
            has_plan = "Yes" if kit.storage.artifact_exists(feature_id, "plan") else "-"
            has_tasks = "Yes" if kit.storage.artifact_exists(feature_id, "tasks") else "-"
            table.add_row(feature_id, has_spec, has_plan, has_tasks)

        console.print(table)


# =============================================================================
# Entry Point
# =============================================================================


def main_cli():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main_cli()
