"""CLI adapter for ``specify check``."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape

from ._agent_config import AGENT_CONFIG
from ._console import StepTracker, console, show_banner


def check() -> None:
    """Check that all required tools are installed."""
    from . import check_tool
    from ._project import _resolve_init_dir_override
    from .integrations.installer import IntegrationInstallError, load_installed_integrations

    try:
        load_installed_integrations(_resolve_init_dir_override() or Path.cwd())
    except (IntegrationInstallError, OSError) as exc:
        console.print(f"[red]Error:[/red] {escape(str(exc))}")
        raise typer.Exit(1) from exc

    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        if agent_key == "generic":
            continue
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False

    tracker.add("code", "Visual Studio Code")
    check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install a coding agent for the best experience[/dim]")

    console.print(
        "[dim]Tip: Run 'specify self check' to verify you have the latest CLI version[/dim]"
    )


def register(app: typer.Typer) -> None:
    """Register ``specify check`` on the root application."""
    app.command()(check)
