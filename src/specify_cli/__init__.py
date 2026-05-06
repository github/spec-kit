#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "json5",
#     "pyyaml",
#     "packaging",
# ]
# ///
"""
Specify CLI - Setup tool for Specify projects

Usage:
    uvx specify-cli.py init <project-name>
    uvx specify-cli.py init .
    uvx specify-cli.py init --here

Or install globally:
    uv tool install --from specify-cli.py specify-cli
    specify init <project-name>
    specify init .
    specify init --here
"""

import sys
import urllib
import urllib.request
import urllib.error
from pathlib import Path

from typing import Optional

import typer
from rich.panel import Panel
from rich.align import Align
from rich.table import Table

from ._console import console
from ._ui import StepTracker, BannerGroup, show_banner
from ._assets import _asset_service as _svc
from ._git import _git_service as _git_svc
from ._version import _version_service as _ver_svc
from ._fs import save_init_options as save_init_options, load_init_options as load_init_options, merge_json_files as merge_json_files, handle_vscode_settings as handle_vscode_settings
from ._helpers import (
    check_tool,
    get_speckit_version,
    AGENT_CONFIG,
    AI_ASSISTANT_ALIASES as AI_ASSISTANT_ALIASES,
    AI_ASSISTANT_HELP as AI_ASSISTANT_HELP,
    _get_skills_dir as _get_skills_dir,
    _parse_integration_options as _parse_integration_options,
)
from ._ui import select_with_arrows as select_with_arrows


def _install_shared_infra(
    project_path: Path,
    script_type: str,
    tracker=None,
    force: bool = False,
    invoke_separator: str = ".",
) -> bool:
    """Install shared infrastructure files into *project_path*."""
    from .shared_infra import install_shared_infra
    from ._assets import _asset_service as _svc

    def _get_version() -> str:
        import importlib.metadata
        try:
            return importlib.metadata.version("specify-cli")
        except Exception:
            return "unknown"

    return install_shared_infra(
        project_path,
        script_type,
        version=_get_version(),
        core_pack=_svc.locate_core_pack(),
        repo_root=Path(__file__).parent.parent.parent,
        console=console,
        force=force,
        invoke_separator=invoke_separator,
    )


def _refresh_shared_templates(
    project_path: Path,
    invoke_separator: str,
    force: bool = False,
) -> None:
    """Refresh default-sensitive shared templates without touching scripts."""
    from .shared_infra import refresh_shared_templates
    from ._assets import _asset_service as _svc

    def _get_version() -> str:
        import importlib.metadata
        try:
            return importlib.metadata.version("specify-cli")
        except Exception:
            return "unknown"

    refresh_shared_templates(
        project_path,
        version=_get_version(),
        core_pack=_svc.locate_core_pack(),
        repo_root=Path(__file__).parent.parent.parent,
        console=console,
        invoke_separator=invoke_separator,
        force=force,
    )
from .commands import init as _init_cmd
from .commands.extension import extension_app
from .commands.integration import integration_app
from .commands.preset import preset_app
from .commands.workflow import workflow_app

app = typer.Typer(
    name="specify",
    help="Setup tool for Specify spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def _version_callback(value: bool):
    if value:
        console.print(f"specify {get_speckit_version()}")
        raise typer.Exit()

@app.callback()
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit."),
):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
        console.print()

def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    return _git_svc.is_repo(path)


def init_git_repo(project_path: Path, quiet: bool = False) -> tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path."""
    ok, err = _git_svc.init_repo(project_path)
    if not quiet:
        if ok:
            console.print("[green]✓[/green] Git repository initialized")
        else:
            console.print(f"[red]Error initializing git repository:[/red] {err}")
    return ok, err


def _locate_core_pack() -> Path | None:
    return _svc.locate_core_pack()


def _repo_root() -> Path:
    """Return the source checkout root used for editable installs."""
    return Path(__file__).parent.parent.parent


def _locate_bundled_extension(extension_id: str) -> Path | None:
    return _svc.locate_bundled_extension(extension_id)


def _locate_bundled_workflow(workflow_id: str) -> Path | None:
    return _svc.locate_bundled_workflow(workflow_id)


def _locate_bundled_preset(preset_id: str) -> Path | None:
    return _svc.locate_bundled_preset(preset_id)

# Constants kept for backward compatibility with presets and extensions.
DEFAULT_SKILLS_DIR = ".agents/skills"
SKILL_DESCRIPTIONS = {
    "specify": "Create or update feature specifications from natural language descriptions.",
    "plan": "Generate technical implementation plans from feature specifications.",
    "tasks": "Break down implementation plans into actionable task lists.",
    "implement": "Execute all tasks from the task breakdown to build the feature.",
    "analyze": "Perform cross-artifact consistency analysis across spec.md, plan.md, and tasks.md.",
    "clarify": "Structured clarification workflow for underspecified requirements.",
    "constitution": "Create or update project governing principles and development guidelines.",
    "checklist": "Generate custom quality checklists for validating requirements completeness and clarity.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues.",
}


_init_cmd.register(app)

@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        if agent_key == "generic":
            continue  # Generic is not a real agent to check
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install a coding agent for the best experience[/dim]")

@app.command()
def version():
    """Display version and system information."""
    import platform

    show_banner()

    cli_version = get_speckit_version()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("CLI Version", cli_version)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]Specify CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()

def _get_installed_version() -> str:
    return _ver_svc.get_installed_version()

def _normalize_tag(tag: str) -> str:
    return _ver_svc._normalize_tag(tag)

def _is_newer(latest: str, current: str) -> bool:
    return _ver_svc.is_newer(latest, current)

def _fetch_latest_release_tag() -> tuple[str | None, str | None]:
    return _ver_svc.fetch_latest_tag()


# ===== Self Commands =====
self_app = typer.Typer(
    name="self",
    help="Manage the specify CLI itself (read-only check and reserved upgrade command).",
    add_completion=False,
)
app.add_typer(self_app, name="self")

@self_app.command("check")
def self_check() -> None:
    """Check whether a newer specify-cli release is available. Read-only.

    This command only checks for updates; it does not modify your installation.
    The reserved (and currently non-destructive) `specify self upgrade` command
    is the name that a future release will use for actual self-upgrade — its
    behavior is not implemented in this release and is intentionally out of
    scope here. See `specify self upgrade --help` for its current status.
    """

    installed = _get_installed_version()
    tag, failure_reason = _fetch_latest_release_tag()

    if tag is None:
        # Graceful-failure path (FR-008). `failure_reason` is one of the
        # enumerated strings produced by _fetch_latest_release_tag() — it
        # never contains a URL, headers, response body, or traceback.
        assert failure_reason is not None
        console.print(f"Installed: {installed}")
        console.print(f"[yellow]Could not check latest release:[/yellow] {failure_reason}")
        return

    latest_normalized = _normalize_tag(tag)

    if installed == "unknown":
        # FR-020: surface the latest release and the recovery action even
        # when the local distribution metadata is unavailable.
        console.print("Current version could not be determined.")
        console.print(f"Latest release: {latest_normalized}")
        console.print("\nTo reinstall:")
        console.print("  uv tool install specify-cli --force \\")
        console.print(f"    --from git+https://github.com/github/spec-kit.git@{tag}")
        return

    if _is_newer(latest_normalized, installed):
        console.print(f"[green]Update available:[/green] {installed} → {latest_normalized}")
        console.print("\nTo upgrade:")
        console.print("  uv tool install specify-cli --force \\")
        console.print(f"    --from git+https://github.com/github/spec-kit.git@{tag}")
        return

    # Installed is parseable AND is >= latest → "up to date" (FR-006).
    # Also reached when the tag is unparseable (InvalidVersion) → _is_newer
    # returns False, and the up-to-date branch is the safer default per
    # FR-004 / test T016.
    console.print(f"[green]Up to date:[/green] {installed}")


@self_app.command("upgrade")
def self_upgrade() -> None:
    """Reserved command surface for self-upgrade; not implemented in this release.

    This command is a documented non-destructive stub in this release: it
    performs no outbound network request, no install-method detection, and
    invokes no installer. It prints a three-line guidance message and exits 0.
    Actual self-upgrade is planned as follow-up work.

    Use `specify self check` today to see whether a newer release is available
    and to get a copy-pasteable reinstall command.
    """
    console.print("specify self upgrade is not implemented yet.")
    console.print("Run 'specify self check' to see whether a newer release is available.")
    console.print("Actual self-upgrade is planned as follow-up work.")


# ===== Extension Commands =====

app.add_typer(extension_app, name="extension")

# ===== Integration Commands =====

app.add_typer(integration_app, name="integration")


# ===== Preset Commands =====

app.add_typer(preset_app, name="preset")


# ===== Workflow Commands =====

app.add_typer(workflow_app, name="workflow")


def main():
    app()

if __name__ == "__main__":
    main()
