"""
System diagnostics and prerequisite checking.

Replaces check-prerequisites.sh / checkprerequisites.ps1
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def check_command(name: str, version_flag: str = "--version") -> tuple[bool, str]:
    """Check if a command exists and get its version."""
    path = shutil.which(name)
    if not path:
        return False, "not found"

    try:
        result = subprocess.run(
            [name, version_flag],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip() or result.stderr.strip()
        # Extract first line, trim to reasonable length
        version = version.split('\n')[0][:50]
        return True, version
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True, "installed (version unknown)"


def check_python_package(name: str) -> tuple[bool, str]:
    """Check if a Python package is installed."""
    try:
        result = subprocess.run(
            ["python", "-c", f"import {name}; print({name}.__version__ if hasattr({name}, '__version__') else 'installed')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "not installed"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "error checking"


def doctor(
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show additional diagnostic info"
    ),
    check_optional: bool = typer.Option(
        False, "--all", "-a",
        help="Also check optional dependencies"
    ),
):
    """
    Check system for required dependencies.

    Validates:
    - Required: git, python, uv
    - Optional: node, npm (if check-optional)
    - Python packages: typer, rich, GitPython
    """
    console.print("[bold]Spectrena Doctor[/bold]\n")

    all_ok = True

    # Required CLI tools
    console.print("[bold cyan]Required Tools[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Tool", width=15)
    table.add_column("Status", width=10)
    table.add_column("Details", width=40)

    required_tools = [
        ("git", "--version"),
        ("python", "--version"),
        ("uv", "--version"),
    ]

    for tool, flag in required_tools:
        found, version = check_command(tool, flag)
        if found:
            table.add_row(tool, "[green]✓[/green]", version)
        else:
            table.add_row(tool, "[red]✗[/red]", "[red]Missing - required[/red]")
            all_ok = False

    console.print(table)

    # Python packages
    console.print("\n[bold cyan]Python Packages[/bold cyan]")
    pkg_table = Table(show_header=True, header_style="bold")
    pkg_table.add_column("Package", width=15)
    pkg_table.add_column("Status", width=10)
    pkg_table.add_column("Version", width=20)

    required_packages = ["typer", "rich", "git"]  # git = GitPython

    for pkg in required_packages:
        found, version = check_python_package(pkg)
        display_name = "GitPython" if pkg == "git" else pkg
        if found:
            pkg_table.add_row(display_name, "[green]✓[/green]", version)
        else:
            pkg_table.add_row(display_name, "[red]✗[/red]", "[red]Missing[/red]")
            all_ok = False

    console.print(pkg_table)

    # Optional tools
    if check_optional:
        console.print("\n[bold cyan]Optional Tools[/bold cyan]")
        opt_table = Table(show_header=True, header_style="bold")
        opt_table.add_column("Tool", width=15)
        opt_table.add_column("Status", width=10)
        opt_table.add_column("Details", width=40)

        optional_tools = [
            ("node", "--version"),
            ("npm", "--version"),
            ("docker", "--version"),
            ("surreal", "--version"),
        ]

        for tool, flag in optional_tools:
            found, version = check_command(tool, flag)
            if found:
                opt_table.add_row(tool, "[green]✓[/green]", version)
            else:
                opt_table.add_row(tool, "[dim]—[/dim]", "[dim]Not installed[/dim]")

        console.print(opt_table)

    # Project checks
    console.print("\n[bold cyan]Project Structure[/bold cyan]")
    proj_table = Table(show_header=True, header_style="bold")
    proj_table.add_column("Item", width=25)
    proj_table.add_column("Status", width=10)
    proj_table.add_column("Path", width=30)

    project_checks = [
        (".spectrena/", Path(".spectrena")),
        (".spectrena/config.yml", Path(".spectrena/config.yml")),
        ("templates/", Path("templates")),
        ("specs/", Path("specs")),
        ("CLAUDE.md", Path("CLAUDE.md")),
    ]

    for name, path in project_checks:
        if path.exists():
            proj_table.add_row(name, "[green]✓[/green]", str(path))
        else:
            proj_table.add_row(name, "[yellow]—[/yellow]", "[dim]Not found[/dim]")

    console.print(proj_table)

    # Summary
    console.print()
    if all_ok:
        console.print("[bold green]✓ All required dependencies satisfied[/bold green]")
    else:
        console.print("[bold red]✗ Missing required dependencies[/bold red]")
        console.print("\nInstall missing items:")
        console.print("  uv tool install spectrena")
        raise typer.Exit(1)

    if verbose:
        console.print("\n[dim]Run with --all to check optional dependencies[/dim]")
