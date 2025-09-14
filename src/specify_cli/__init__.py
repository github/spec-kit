"""
hjLabs Specify CLI - AI Model Switching and Task Tracking

This is a Python wrapper that bridges to the Node.js implementation.
"""

import os
import sys
import subprocess
import shutil
import tempfile
import tarfile
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

app = typer.Typer(help="AI Model Switching and Task Tracking CLI for Spec-Driven Development", no_args_is_help=True)
console = Console()

def get_node_cli_path():
    """Get the path to the Node.js CLI executable."""
    # Use the bundled JavaScript CLI
    package_dir = Path(__file__).parent
    node_cli = package_dir / "js_cli" / "bundle.js"

    if node_cli.exists():
        return str(node_cli)

    # Check if Node.js is available
    if not shutil.which("node"):
        console.print()
        console.print(Panel.fit(
            "[red]Node.js is required but not found![/red]\n\n"
            "Please install Node.js from: https://nodejs.org/\n"
            "Or use your system's package manager:\n"
            "  • Ubuntu/Debian: sudo apt install nodejs npm\n"
            "  • macOS: brew install node\n"
            "  • Windows: Download from nodejs.org",
            title="Installation Required",
            border_style="red"
        ))
        return None

    return None

def show_helpful_error():
    """Show a helpful error message with solutions."""
    console.print()
    console.print(Panel.fit(
        "[red]Could not find the Node.js CLI implementation![/red]\n\n"
        "[yellow]Possible solutions:[/yellow]\n"
        "1. Install Node.js and npm: https://nodejs.org/\n"
        "2. Run this command in a directory with Node.js access\n"
        "3. Check that Node.js and npm are in your PATH\n\n"
        "[cyan]To verify your setup:[/cyan]\n"
        "  node --version\n"
        "  npm --version",
        title="Setup Required",
        border_style="yellow"
    ))

def run_node_cli(args):
    """Run the Node.js CLI with the given arguments."""
    node_cli = get_node_cli_path()

    if not node_cli:
        show_helpful_error()
        return 1

    try:
        # Run the Node.js CLI with the provided arguments
        cmd = ["node", node_cli] + list(args)
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running CLI: {e}[/red]")
        return 1
    except FileNotFoundError:
        console.print("[red]Error: Node.js is not installed or not in PATH[/red]")
        show_helpful_error()
        return 1

def show_welcome():
    """Show welcome message and available commands."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Welcome to hjLabs Specify CLI![/bold cyan]\n\n"
        "[yellow]Available commands:[/yellow]\n"
        "• specify switch-model <target>  - Switch AI models\n"
        "• specify list-models            - Show available models\n"
        "• specify detect-project         - Auto-detect projects\n"
        "• specify reset-project          - Reset project with backup\n"
        "• specify track-tasks <action>   - Manage task tracking\n\n"
        "[cyan]Get help for any command:[/cyan]\n"
        "  specify <command> --help",
        title="hjLabs Specify CLI",
        border_style="cyan"
    ))

@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """AI Model Switching and Task Tracking CLI for Spec-Driven Development."""
    if version:
        console.print("[bold cyan]hjLabs Specify CLI v0.1.0[/bold cyan]")
        return

    if ctx.invoked_subcommand is None:
        show_welcome()

@app.command()
def switch_model(
    target: str = typer.Argument(..., help="Target AI model to switch to (e.g., claude, gemini, copilot)")
):
    """Switch AI models without losing progress."""
    console.print(f"[cyan]Switching to AI model: {target}[/cyan]")
    exit_code = run_node_cli(["switch-model", target])
    raise typer.Exit(exit_code)

@app.command()
def list_models():
    """Show available AI models and compatibility."""
    console.print("[cyan]Fetching available AI models...[/cyan]")
    exit_code = run_node_cli(["list-models"])
    raise typer.Exit(exit_code)

@app.command()
def detect_project():
    """Auto-detect existing spec-kit projects."""
    console.print("[cyan]Scanning for spec-kit projects...[/cyan]")
    exit_code = run_node_cli(["detect-project"])
    raise typer.Exit(exit_code)

@app.command()
def reset_project():
    """Clean project reset with backup."""
    if Confirm.ask("[yellow]This will reset your project. Are you sure?[/yellow]"):
        console.print("[cyan]Resetting project with backup...[/cyan]")
        exit_code = run_node_cli(["reset-project"])
        raise typer.Exit(exit_code)
    else:
        console.print("[green]Project reset cancelled.[/green]")
        raise typer.Exit(0)

@app.command()
def track_tasks(
    action: str = typer.Argument(..., help="Action to perform: enable, disable, or status")
):
    """Manage task tracking UI."""
    valid_actions = ["enable", "disable", "status"]
    if action not in valid_actions:
        console.print(f"[red]Invalid action: {action}[/red]")
        console.print(f"[yellow]Valid actions: {', '.join(valid_actions)}[/yellow]")
        raise typer.Exit(1)

    console.print(f"[cyan]Managing task tracking: {action}[/cyan]")
    exit_code = run_node_cli(["track-tasks", action])
    raise typer.Exit(exit_code)

@app.command()
def init(
    project_name: str = typer.Argument(None, help="Project name to initialize"),
    here: bool = typer.Option(False, "--here", help="Initialize in current directory"),
    ai: str = typer.Option(None, "--ai", help="Specify AI agent: claude, gemini, or copilot"),
    script: str = typer.Option(None, "--script", help="Script type: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip agent tools check")
):
    """Initialize a new spec-kit project."""
    args = ["init"]

    if project_name:
        args.append(project_name)

    if here:
        args.append("--here")

    if ai:
        args.extend(["--ai", ai])

    if script:
        args.extend(["--script", script])

    if ignore_agent_tools:
        args.append("--ignore-agent-tools")

    if project_name or here:
        console.print(f"[cyan]Initializing spec-kit project...[/cyan]")
        exit_code = run_node_cli(args)
        raise typer.Exit(exit_code)
    else:
        console.print("[red]Please specify a project name or use --here flag[/red]")
        console.print("[yellow]Examples:[/yellow]")
        console.print("  specify init my-project")
        console.print("  specify init --here")
        raise typer.Exit(1)

def main():
    """Entry point for the CLI when called via uvx."""
    app()

if __name__ == "__main__":
    main()