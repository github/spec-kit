"""CLI adapter for ``specify check``."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import typer
from rich.markup import escape

from ._agent_config import AGENT_CONFIG
from ._console import StepTracker, console, show_banner


def _check_external_tools(
    project_root: Path, key: str, record: dict[str, Any], requires_cli: bool, tracker: StepTracker,
) -> bool:
    from .integrations import get_integration
    from .integrations.installer import IntegrationInstallError

    integration = get_integration(key)
    if integration is None:
        raise IntegrationInstallError(f"Installed integration '{key}' is not registered")
    tools = [
        tool["name"] for tool in record["requires"].get("tools", [])
        if tool.get("required", True)
    ]
    if not tools and requires_cli:
        args = integration.build_exec_args("test", project_root=project_root)
        tools = [args[0] if args else integration._resolve_executable()]
    if not tools:
        tracker.skip(key, "IDE-based, no CLI check")
        return False
    tools = list(dict.fromkeys(tools))
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        tracker.error(key, "not found: " + escape(", ".join(missing)))
        return False
    tracker.complete(key, "available: " + escape(", ".join(tools)))
    return True


def check() -> None:
    """Check that all required tools are installed."""
    from . import check_tool
    from ._project import _resolve_init_dir_override
    from .integrations.installer import IntegrationInstallError, load_installed_integrations, read_records

    try:
        project_root = _resolve_init_dir_override() or Path.cwd()
        load_installed_integrations(project_root)
        records = read_records(project_root)
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

        tracker.add(agent_key, escape(agent_name))

        if agent_key in records:
            try:
                agent_results[agent_key] = _check_external_tools(
                    project_root, agent_key, records[agent_key], requires_cli, tracker,
                )
            except (ValueError, OSError, NotImplementedError) as exc:
                console.print(
                    f"[red]Error:[/red] Cannot check integration '{escape(agent_key)}': {escape(str(exc))}"
                )
                raise typer.Exit(1) from exc
        elif requires_cli:
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
