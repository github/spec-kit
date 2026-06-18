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

import contextlib
import os
import sys
import zipfile
import json
import yaml
from pathlib import Path

from typing import Any, Optional

import typer
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from .shared_infra import (
    install_shared_infra as _install_shared_infra_impl,
    refresh_shared_templates as _refresh_shared_templates_impl,
)

from ._console import (
    BANNER as BANNER,
    TAGLINE as TAGLINE,
    BannerGroup,
    StepTracker,
    console,
    get_key as get_key,
    select_with_arrows as select_with_arrows,
    show_banner,
)
from ._assets import (
    _locate_bundled_extension,
    _locate_bundled_preset as _locate_bundled_preset,
    _locate_bundled_workflow as _locate_bundled_workflow,
    _locate_core_pack,
    _repo_root,
    get_speckit_version as get_speckit_version,
)
from ._utils import (
    CLAUDE_LOCAL_PATH as CLAUDE_LOCAL_PATH,
    CLAUDE_NPM_LOCAL_PATH as CLAUDE_NPM_LOCAL_PATH,
    _display_project_path,
    check_tool as check_tool,
    handle_vscode_settings as handle_vscode_settings,
    merge_json_files as merge_json_files,
    run_command as run_command,
)
from ._version import (
    GITHUB_API_LATEST as GITHUB_API_LATEST,
    self_app as _self_app,
    self_check as self_check,
    self_upgrade as self_upgrade,
)
from ._agent_config import (
    AGENT_CONFIG as AGENT_CONFIG,
    DEFAULT_INIT_INTEGRATION as DEFAULT_INIT_INTEGRATION,
    SCRIPT_TYPE_CHOICES as SCRIPT_TYPE_CHOICES,
)
from ._init_options import (
    INIT_OPTIONS_FILE as INIT_OPTIONS_FILE,
    is_ai_skills_enabled as _is_ai_skills_enabled,
    load_init_options as load_init_options,
    save_init_options as save_init_options,
)

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

def _refresh_shared_templates(
    project_path: Path,
    *,
    invoke_separator: str,
    force: bool = False,
) -> None:
    """Refresh default-sensitive shared templates without touching scripts."""
    _refresh_shared_templates_impl(
        project_path,
        version=get_speckit_version(),
        core_pack=_locate_core_pack(),
        repo_root=_repo_root(),
        console=console,
        invoke_separator=invoke_separator,
        force=force,
    )


def _install_shared_infra(
    project_path: Path,
    script_type: str,
    tracker: StepTracker | None = None,
    force: bool = False,
    invoke_separator: str = ".",
    refresh_managed: bool = False,
    refresh_hint: str | None = None,
) -> bool:
    """Install shared infrastructure files into *project_path*.

    Copies ``.specify/scripts/<variant>/`` and ``.specify/templates/`` from
    the bundled core_pack or source checkout, where ``<variant>`` is
    ``bash`` when *script_type* is ``"sh"`` and ``powershell`` when it is
    ``"ps"``.  Tracks all installed files in ``speckit.manifest.json``.

    Shared scripts and page templates are processed to resolve
    ``__SPECKIT_COMMAND_<NAME>__`` placeholders using *invoke_separator*
    (``"."`` for markdown agents, ``"-"`` for skills agents).

    Overwrite policy:

    * ``force=True``  — overwrite every existing file (still skips symlinks
      to avoid following links outside the project root).
    * ``refresh_managed=True`` — overwrite only files whose on-disk hash
      still matches the previously recorded manifest hash (i.e. unmodified
      files installed by spec-kit). Files with diverging hashes are
      treated as user customizations and preserved with a warning.
    * Default — only add missing files; existing ones are skipped.

    *refresh_hint* — caller-supplied rich-text fragment shown after the
    "Preserved customized files" warning to tell the user which flag/command
    they should re-run with to overwrite their customizations. Each caller
    passes the flag that's actually valid in its CLI surface (e.g.
    ``--refresh-shared-infra`` for ``integration switch``,
    ``--force`` for ``init``/``integration upgrade``). When ``None``, no
    remediation hint is printed for customizations.

    Returns ``True`` on success.
    """
    return _install_shared_infra_impl(
        project_path,
        script_type,
        version=get_speckit_version(),
        core_pack=_locate_core_pack(),
        repo_root=_repo_root(),
        console=console,
        force=force,
        invoke_separator=invoke_separator,
        refresh_managed=refresh_managed,
        refresh_hint=refresh_hint,
    )


def _install_shared_infra_or_exit(
    project_path: Path,
    script_type: str,
    tracker: StepTracker | None = None,
    force: bool = False,
    invoke_separator: str = ".",
    refresh_managed: bool = False,
    refresh_hint: str | None = None,
) -> bool:
    try:
        return _install_shared_infra(
            project_path,
            script_type,
            tracker=tracker,
            force=force,
            invoke_separator=invoke_separator,
            refresh_managed=refresh_managed,
            refresh_hint=refresh_hint,
        )
    except (ValueError, OSError) as exc:
        console.print(f"[red]Error:[/red] Failed to install shared infrastructure: {exc}")
        raise typer.Exit(1)


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts and .specify/extensions (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scan_roots = [
        project_path / ".specify" / "scripts",
        project_path / ".specify" / "extensions",
    ]
    failures: list[str] = []
    updated = 0
    for scripts_root in scan_roots:
        if not scripts_root.is_dir():
            continue
        for script in scripts_root.rglob("*.sh"):
            try:
                if script.is_symlink() or not script.is_file():
                    continue
                try:
                    with script.open("rb") as f:
                        if f.read(2) != b"#!":
                            continue
                except Exception:
                    continue
                st = script.stat()
                mode = st.st_mode
                if mode & 0o111:
                    continue
                new_mode = mode
                if mode & 0o400:
                    new_mode |= 0o100
                if mode & 0o040:
                    new_mode |= 0o010
                if mode & 0o004:
                    new_mode |= 0o001
                if not (new_mode & 0o100):
                    new_mode |= 0o100
                os.chmod(script, new_mode)
                updated += 1
            except Exception as e:
                failures.append(f"{_display_project_path(project_path, script)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")

# ---------------------------------------------------------------------------
# Agent-context extension config helpers
# ---------------------------------------------------------------------------

_AGENT_CTX_EXT_CONFIG = (
    Path(".specify") / "extensions" / "agent-context" / "agent-context-config.yml"
)


def _load_agent_context_config(project_root: Path) -> dict[str, Any]:
    """Load the agent-context extension config, returning defaults on failure."""
    from .integrations.base import IntegrationBase

    defaults: dict[str, Any] = {
        "context_file": "",
        "context_markers": {
            "start": IntegrationBase.CONTEXT_MARKER_START,
            "end": IntegrationBase.CONTEXT_MARKER_END,
        },
    }
    path = project_root / _AGENT_CTX_EXT_CONFIG
    if not path.exists():
        return defaults
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return defaults
    if not isinstance(raw, dict):
        return defaults
    return raw


def _save_agent_context_config(
    project_root: Path, config: dict[str, Any]
) -> None:
    """Persist *config* to the agent-context extension config file."""
    path = project_root / _AGENT_CTX_EXT_CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _update_agent_context_config_file(
    project_root: Path,
    context_file: str | None,
    *,
    preserve_markers: bool = True,
) -> None:
    """Update the agent-context extension config with *context_file*.

    When *preserve_markers* is True (default), any existing
    ``context_markers`` values are kept unchanged so user customisations
    survive integration changes and reinit.  When False, the default
    markers are written unconditionally.
    """
    from .integrations.base import IntegrationBase

    cfg = _load_agent_context_config(project_root)
    cfg["context_file"] = context_file or ""
    if not preserve_markers or not isinstance(cfg.get("context_markers"), dict):
        cfg["context_markers"] = {
            "start": IntegrationBase.CONTEXT_MARKER_START,
            "end": IntegrationBase.CONTEXT_MARKER_END,
        }
    _save_agent_context_config(project_root, cfg)


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory.

    Returns ``project_path / <agent_folder> / "skills"``, falling back
    to ``project_path / ".agents/skills"`` for unknown agents.
    """
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"
    return project_path / ".agents" / "skills"


def resolve_active_skills_dir(project_root: Path) -> Path | None:
    """Return the active skills directory, creating it on demand when enabled.

    Reads ``.specify/init-options.json`` to determine whether skills are
    enabled and which agent was selected.  Only ``ai_skills`` set to boolean
    ``True`` creates the directory safely (symlink/containment checks); when
    ``ai_skills`` is not boolean ``True``, only Kimi's native-skills fallback
    is honoured, and the native skills directory must already exist.

    Returns:
        The skills directory ``Path``, or ``None`` if skills are not active.

    Raises:
        ValueError: If the resolved skills path escapes the project root,
            a parent component is a symlink, or a path component exists
            but is not a directory.
        OSError: If the directory cannot be created (e.g. permission denied).
    """
    from .shared_infra import _ensure_safe_shared_directory

    opts = load_init_options(project_root)
    if not isinstance(opts, dict):
        opts = {}

    agent = opts.get("ai")
    if not isinstance(agent, str) or not agent:
        return None

    ai_skills_enabled = _is_ai_skills_enabled(opts)
    if not ai_skills_enabled and agent != "kimi":
        return None

    skills_dir = _get_skills_dir(project_root, agent)

    if not ai_skills_enabled:
        # Kimi native-skills fallback when ai_skills is not boolean True:
        # use the native skills directory only if it already exists.
        if not skills_dir.is_dir():
            return None
        _ensure_safe_shared_directory(
            project_root, skills_dir,
            create=False, context="agent skills directory",
        )
        return skills_dir

    # ai_skills is boolean True: create the directory safely.
    _ensure_safe_shared_directory(
        project_root, skills_dir, context="agent skills directory",
    )
    return skills_dir


def _cli_error_detail(exc: BaseException) -> str:
    """Return a compact one-line exception detail for CLI output."""
    detail = str(exc).replace("\n", " ").strip()
    return detail or exc.__class__.__name__


def _cli_phase_label(phase: str, target_kind: str, target: str | None = None) -> str:
    """Format a stable operation label for user-visible diagnostics."""
    label = f"{phase} {target_kind}".strip()
    if target:
        label = f"{label} '{target}'"
    return label


def _print_cli_warning(
    phase: str,
    target_kind: str,
    target: str | None,
    exc: BaseException,
    *,
    continuing: str | None = None,
) -> None:
    """Print a warning that names the failed CLI phase and target."""
    label = _cli_phase_label(phase, target_kind, target)
    console.print(f"[yellow]Warning:[/yellow] Failed to {label}: {_cli_error_detail(exc)}")
    if continuing:
        console.print(f"[dim]{continuing}[/dim]")


# Constants kept for backward compatibility with presets and extensions.
DEFAULT_SKILLS_DIR = ".agents/skills"
SKILL_DESCRIPTIONS = {
    "specify": "Create or update feature specifications from natural language descriptions.",
    "plan": "Generate technical implementation plans from feature specifications.",
    "tasks": "Break down implementation plans into actionable task lists.",
    "implement": "Execute all tasks from the task breakdown to build the feature.",
    "converge": "Assess the codebase against spec.md, plan.md, and tasks.md and append remaining work as new tasks.",
    "analyze": "Perform cross-artifact consistency analysis across spec.md, plan.md, and tasks.md.",
    "clarify": "Structured clarification workflow for underspecified requirements.",
    "constitution": "Create or update project governing principles and development guidelines.",
    "checklist": "Generate custom quality checklists for validating requirements completeness and clarity.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues.",
}


# ===== init command =====
# Moved to commands/init.py — registered here to preserve CLI surface.
from .commands import init as _init_cmd  # noqa: E402
_init_cmd.register(app)


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

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

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install a coding agent for the best experience[/dim]")

    console.print("[dim]Tip: Run 'specify self check' to verify you have the latest CLI version[/dim]")


def _feature_capabilities() -> dict[str, bool]:
    """Return stable local CLI capability flags for humans and agents."""
    return {
        "controlled_multi_install_integrations": True,
        "integration_use_command": True,
        "multi_install_safe_registry_metadata": True,
        "integration_upgrade_command": True,
        "self_check_command": True,
        "workflow_catalog": True,
        "bundled_templates": True,
    }


@app.command()
def version(
    features: bool = typer.Option(
        False,
        "--features",
        help="Show local CLI feature capabilities.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit feature capabilities as JSON. Requires --features.",
    ),
):
    """Display version and system information."""
    import platform

    cli_version = get_speckit_version()

    if json_output and not features:
        console.print("[red]Error:[/red] --json requires --features.")
        raise typer.Exit(1)

    if features:
        capabilities = _feature_capabilities()
        if json_output:
            payload = {"version": cli_version, "features": capabilities}
            console.print(json.dumps(payload, indent=2))
            return

        console.print(f"Spec Kit CLI: {cli_version}")
        console.print()
        console.print("Features:")
        for key, enabled in capabilities.items():
            label = key.replace("_", " ")
            console.print(f"- {label}: {'yes' if enabled else 'no'}")
        return

    show_banner()

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

app.add_typer(_self_app, name="self")


# ===== Extension Commands =====

extension_app = typer.Typer(
    name="extension",
    help="Manage spec-kit extensions",
    add_completion=False,
)
app.add_typer(extension_app, name="extension")

catalog_app = typer.Typer(
    name="catalog",
    help="Manage extension catalogs",
    add_completion=False,
)
extension_app.add_typer(catalog_app, name="catalog")


# ===== Integration Commands =====

# Moved to integrations/_commands.py — registered here to preserve CLI surface.
from .integrations._commands import register as _register_integration_cmds  # noqa: E402
_register_integration_cmds(app)

# Re-exported from integrations/_helpers.py to preserve the public import surface.
from .integrations._helpers import (  # noqa: E402
    _clear_init_options_for_integration as _clear_init_options_for_integration,
    _update_init_options_for_integration as _update_init_options_for_integration,
)


def _require_specify_project() -> Path:
    """Return the current project root if it is a spec-kit project, else exit."""
    project_root = Path.cwd()
    if (project_root / ".specify").is_dir():
        return project_root
    console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
    console.print("Run this command from a spec-kit project root")
    raise typer.Exit(1)



# ===== Preset Commands =====

# Moved to presets/_commands.py — registered here to preserve CLI surface.
from .presets._commands import register as _register_preset_cmds  # noqa: E402
_register_preset_cmds(app)


# ===== Extension Commands =====


def _resolve_installed_extension(
    argument: str,
    installed_extensions: list,
    command_name: str = "command",
    allow_not_found: bool = False,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve an extension argument (ID or display name) to an installed extension.

    Args:
        argument: Extension ID or display name provided by user
        installed_extensions: List of installed extension dicts from manager.list_installed()
        command_name: Name of the command for error messages (e.g., "enable", "disable")
        allow_not_found: If True, return (None, None) when not found instead of raising

    Returns:
        Tuple of (extension_id, display_name), or (None, None) if allow_not_found=True and not found

    Raises:
        typer.Exit: If extension not found (and allow_not_found=False) or name is ambiguous
    """
    from rich.table import Table

    # First, try exact ID match
    for ext in installed_extensions:
        if ext["id"] == argument:
            return (ext["id"], ext["name"])

    # If not found by ID, try display name match
    name_matches = [ext for ext in installed_extensions if ext["name"].lower() == argument.lower()]

    if len(name_matches) == 1:
        # Unique display-name match
        return (name_matches[0]["id"], name_matches[0]["name"])
    elif len(name_matches) > 1:
        # Ambiguous display-name match
        console.print(
            f"[red]Error:[/red] Extension name '{argument}' is ambiguous. "
            "Multiple installed extensions share this name:"
        )
        table = Table(title="Matching extensions")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Version", style="green")
        for ext in name_matches:
            table.add_row(ext.get("id", ""), ext.get("name", ""), str(ext.get("version", "")))
        console.print(table)
        console.print("\nPlease rerun using the extension ID:")
        console.print(f"  [bold]specify extension {command_name} <extension-id>[/bold]")
        raise typer.Exit(1)
    else:
        # No match by ID or display name
        if allow_not_found:
            return (None, None)
        console.print(f"[red]Error:[/red] Extension '{argument}' is not installed")
        raise typer.Exit(1)


def _resolve_catalog_extension(
    argument: str,
    catalog,
    command_name: str = "info",
) -> tuple[Optional[dict], Optional[Exception]]:
    """Resolve an extension argument (ID or display name) from the catalog.

    Args:
        argument: Extension ID or display name provided by user
        catalog: ExtensionCatalog instance
        command_name: Name of the command for error messages

    Returns:
        Tuple of (extension_info, catalog_error)
        - If found: (ext_info_dict, None)
        - If catalog error: (None, error)
        - If not found: (None, None)
    """
    from rich.table import Table
    from .extensions import ExtensionError

    try:
        # First try by ID
        ext_info = catalog.get_extension_info(argument)
        if ext_info:
            return (ext_info, None)

        # Try by display name - search using argument as query, then filter for exact match
        search_results = catalog.search(query=argument)
        name_matches = [ext for ext in search_results if ext["name"].lower() == argument.lower()]

        if len(name_matches) == 1:
            return (name_matches[0], None)
        elif len(name_matches) > 1:
            # Ambiguous display-name match in catalog
            console.print(
                f"[red]Error:[/red] Extension name '{argument}' is ambiguous. "
                "Multiple catalog extensions share this name:"
            )
            table = Table(title="Matching extensions")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Version", style="green")
            table.add_column("Catalog", style="dim")
            for ext in name_matches:
                table.add_row(
                    ext.get("id", ""),
                    ext.get("name", ""),
                    str(ext.get("version", "")),
                    ext.get("_catalog_name", ""),
                )
            console.print(table)
            console.print("\nPlease rerun using the extension ID:")
            console.print(f"  [bold]specify extension {command_name} <extension-id>[/bold]")
            raise typer.Exit(1)

        # Not found
        return (None, None)

    except ExtensionError as e:
        return (None, e)


@extension_app.command("list")
def extension_list(
    available: bool = typer.Option(False, "--available", help="Show available extensions from catalog"),
    all_extensions: bool = typer.Option(False, "--all", help="Show both installed and available"),
):
    """List installed extensions."""
    from .extensions import ExtensionManager

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    if not installed and not (available or all_extensions):
        console.print("[yellow]No extensions installed.[/yellow]")
        console.print("\nInstall an extension with:")
        console.print("  specify extension add <extension-name>")
        return

    if installed:
        console.print("\n[bold cyan]Installed Extensions:[/bold cyan]\n")

        for ext in installed:
            status_icon = "✓" if ext["enabled"] else "✗"
            status_color = "green" if ext["enabled"] else "red"

            console.print(f"  [{status_color}]{status_icon}[/{status_color}] [bold]{ext['name']}[/bold] (v{ext['version']})")
            console.print(f"     [dim]{ext['id']}[/dim]")
            console.print(f"     {ext['description']}")
            console.print(f"     Commands: {ext['command_count']} | Hooks: {ext['hook_count']} | Priority: {ext['priority']} | Status: {'Enabled' if ext['enabled'] else 'Disabled'}")
            console.print()

    if available or all_extensions:
        console.print("\nInstall an extension:")
        console.print("  [cyan]specify extension add <name>[/cyan]")


@catalog_app.command("list")
def catalog_list():
    """List all active extension catalogs."""
    from .extensions import ExtensionCatalog, ValidationError

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Active Extension Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [bold]{entry.name}[/bold] (priority {entry.priority})")
        if entry.description:
            console.print(f"     {entry.description}")
        console.print(f"     URL: {entry.url}")
        console.print(f"     Install: {install_str}")
        console.print()

    config_path = project_root / ".specify" / "extension-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "extension-catalogs.yml"
    if os.environ.get("SPECKIT_CATALOG_URL"):
        console.print("[dim]Catalog configured via SPECKIT_CATALOG_URL environment variable.[/dim]")
    else:
        try:
            proj_loaded = config_path.exists() and catalog._load_catalog_config(config_path) is not None
        except ValidationError:
            proj_loaded = False
        if proj_loaded:
            console.print(f"[dim]Config: {_display_project_path(project_root, config_path)}[/dim]")
        else:
            try:
                user_loaded = user_config_path.exists() and catalog._load_catalog_config(user_config_path) is not None
            except ValidationError:
                user_loaded = False
            if user_loaded:
                console.print("[dim]Config: ~/.specify/extension-catalogs.yml[/dim]")
            else:
                console.print("[dim]Using built-in default catalog stack.[/dim]")
                console.print(
                    "[dim]Add .specify/extension-catalogs.yml to customize.[/dim]"
                )


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str = typer.Option(..., "--name", help="Catalog name"),
    priority: int = typer.Option(10, "--priority", help="Priority (lower = higher priority)"),
    install_allowed: bool = typer.Option(
        False, "--install-allowed/--no-install-allowed",
        help="Allow extensions from this catalog to be installed",
    ),
    description: str = typer.Option("", "--description", help="Description of the catalog"),
):
    """Add a catalog to .specify/extension-catalogs.yml."""
    from .extensions import ExtensionCatalog, ValidationError

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Validate URL
    tmp_catalog = ExtensionCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    config_path = specify_dir / "extension-catalogs.yml"

    # Load existing config
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            config_label = _display_project_path(project_root, config_path)
            console.print(f"[red]Error:[/red] Failed to read {config_label}: {e}")
            raise typer.Exit(1)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            console.print(f"[yellow]Warning:[/yellow] A catalog named '{name}' already exists.")
            console.print("Use 'specify extension catalog remove' first, or choose a different name.")
            raise typer.Exit(1)

    catalogs.append({
        "name": name,
        "url": url,
        "priority": priority,
        "install_allowed": install_allowed,
        "description": description,
    })

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    install_label = "install allowed" if install_allowed else "discovery only"
    console.print(f"\n[green]✓[/green] Added catalog '[bold]{name}[/bold]' ({install_label})")
    console.print(f"  URL: {url}")
    console.print(f"  Priority: {priority}")
    console.print(f"\nConfig saved to {_display_project_path(project_root, config_path)}")


@catalog_app.command("remove")
def catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
):
    """Remove a catalog from .specify/extension-catalogs.yml."""
    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    config_path = specify_dir / "extension-catalogs.yml"
    if not config_path.exists():
        console.print("[red]Error:[/red] No catalog config found. Nothing to remove.")
        raise typer.Exit(1)

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        console.print("[red]Error:[/red] Failed to read catalog config.")
        raise typer.Exit(1)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)
    original_count = len(catalogs)
    catalogs = [c for c in catalogs if isinstance(c, dict) and c.get("name") != name]

    if len(catalogs) == original_count:
        console.print(f"[red]Error:[/red] Catalog '{name}' not found.")
        raise typer.Exit(1)

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    console.print(f"[green]✓[/green] Removed catalog '{name}'")
    if not catalogs:
        console.print("\n[dim]No catalogs remain in config. Built-in defaults will be used.[/dim]")


@extension_app.command("add")
def extension_add(
    extension: str = typer.Argument(help="Extension name or path"),
    dev: bool = typer.Option(False, "--dev", help="Install from local directory"),
    from_url: Optional[str] = typer.Option(None, "--from", help="Install from custom URL"),
    force: bool = typer.Option(False, "--force", help="Overwrite if already installed"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
):
    """Install an extension."""
    from .extensions import ExtensionManager, ExtensionCatalog, ExtensionError, ValidationError, CompatibilityError, REINSTALL_COMMAND

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    speckit_version = get_speckit_version()

    if force:
        console.print("[yellow]--force:[/yellow] Will overwrite if already installed")

    # Prompt for URL-based installs BEFORE the spinner so the user can
    # actually see and respond to the confirmation (the Rich status
    # spinner overwrites the typer.confirm prompt line, making it appear
    # as though the command is hung).
    # Guard with ``not dev`` so that --dev + --from does not show a
    # confusing confirmation for a URL that will be ignored.
    if from_url and not dev:
        from urllib.parse import urlparse
        from rich.markup import escape as _escape_markup

        parsed = urlparse(from_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")

        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            console.print("[red]Error:[/red] URL must use HTTPS for security.")
            console.print("HTTP is only allowed for localhost URLs.")
            raise typer.Exit(1)

        safe_url = _escape_markup(from_url)

        # Warn about untrusted sources — default-deny confirmation
        console.print()
        console.print(Panel(
            f"[bold]You are installing an extension from an external URL that is not\n"
            f"listed in any of your configured extension catalogs.[/bold]\n\n"
            f"URL: {safe_url}\n\n"
            f"Only install extensions from sources you trust.",
            title="[bold yellow]⚠ Untrusted Source[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))
        console.print()
        confirm = typer.confirm("Continue with installation?", default=False)
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    try:
        with console.status(f"[cyan]Installing extension: {extension}[/cyan]"):
            if dev:
                # Install from local directory
                source_path = Path(extension).expanduser().resolve()
                if not source_path.exists():
                    console.print(f"[red]Error:[/red] Directory not found: {source_path}")
                    raise typer.Exit(1)

                if not (source_path / "extension.yml").exists():
                    console.print(f"[red]Error:[/red] No extension.yml found in {source_path}")
                    raise typer.Exit(1)

                if force:
                    console.print(f"[yellow]--force:[/yellow] Installing from [cyan]{source_path}[/cyan] (will overwrite if already installed)...")

                manifest = manager.install_from_directory(
                    source_path,
                    speckit_version,
                    priority=priority,
                    link_commands=True,
                    force=force
                )

            elif from_url:
                # Install from URL (ZIP file)
                import urllib.error

                console.print(f"Downloading from {safe_url}...")

                # Download ZIP to temp location
                download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
                download_dir.mkdir(parents=True, exist_ok=True)
                zip_path = download_dir / f"{extension}-url-download.zip"

                try:
                    from specify_cli.authentication.http import open_url as _open_url

                    with _open_url(from_url, timeout=60) as response:
                        zip_data = response.read()
                    zip_path.write_bytes(zip_data)

                    # Install from downloaded ZIP
                    manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority, force=force)
                except urllib.error.URLError as e:
                    console.print(f"[red]Error:[/red] Failed to download from {safe_url}: {e}")
                    raise typer.Exit(1)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

            else:
                # Try bundled extensions first (shipped with spec-kit)
                bundled_path = _locate_bundled_extension(extension)
                if bundled_path is not None:
                    manifest = manager.install_from_directory(
                        bundled_path, speckit_version, priority=priority, force=force
                    )
                else:
                    # Install from catalog (also resolves display names to IDs)
                    catalog = ExtensionCatalog(project_root)

                    # Check if extension exists in catalog (supports both ID and display name)
                    ext_info, catalog_error = _resolve_catalog_extension(extension, catalog, "add")
                    if catalog_error:
                        console.print(f"[red]Error:[/red] Could not query extension catalog: {catalog_error}")
                        raise typer.Exit(1)
                    if not ext_info:
                        console.print(f"[red]Error:[/red] Extension '{extension}' not found in catalog")
                        console.print("\nSearch available extensions:")
                        console.print("  specify extension search")
                        raise typer.Exit(1)

                    # If catalog resolved a display name to an ID, check bundled again
                    resolved_id = ext_info['id']
                    if resolved_id != extension:
                        bundled_path = _locate_bundled_extension(resolved_id)
                        if bundled_path is not None:
                            manifest = manager.install_from_directory(
                                bundled_path, speckit_version, priority=priority, force=force
                            )

                    if bundled_path is None:
                        # Bundled extensions without a download URL must come from the local package
                        if ext_info.get("bundled") and not ext_info.get("download_url"):
                            console.print(
                                f"[red]Error:[/red] Extension '{ext_info['id']}' is bundled with spec-kit "
                                f"but could not be found in the installed package."
                            )
                            console.print(
                                "\nThis usually means the spec-kit installation is incomplete or corrupted."
                            )
                            console.print("Try reinstalling spec-kit:")
                            console.print(f"  {REINSTALL_COMMAND}")
                            raise typer.Exit(1)

                        # Enforce install_allowed policy
                        if not ext_info.get("_install_allowed", True):
                            catalog_name = ext_info.get("_catalog_name", "community")
                            console.print(
                                f"[red]Error:[/red] '{extension}' is available in the "
                                f"'{catalog_name}' catalog but installation is not allowed from that catalog."
                            )
                            console.print(
                                f"\nTo enable installation, add '{extension}' to an approved catalog "
                                f"(install_allowed: true) in .specify/extension-catalogs.yml."
                            )
                            raise typer.Exit(1)

                        # Download extension ZIP (use resolved ID, not original argument which may be display name)
                        extension_id = ext_info['id']
                        console.print(f"Downloading {ext_info['name']} v{ext_info.get('version', 'unknown')}...")
                        zip_path = catalog.download_extension(extension_id)

                        try:
                            # Install from downloaded ZIP
                            manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority, force=force)
                        finally:
                            # Clean up downloaded ZIP
                            if zip_path.exists():
                                zip_path.unlink()

        console.print("\n[green]✓[/green] Extension installed successfully!")
        console.print(f"\n[bold]{manifest.name}[/bold] (v{manifest.version})")
        console.print(f"  {manifest.description}")

        for warning in manifest.warnings:
            console.print(f"\n[yellow]⚠  Compatibility warning:[/yellow] {warning}")

        is_cline = load_init_options(project_root).get("ai") == "cline"

        if is_cline:
            from specify_cli.integrations.cline import format_cline_command_name

        console.print("\n[bold cyan]Provided commands:[/bold cyan]")
        for cmd in manifest.commands:
            cmd_name = cmd['name']
            if is_cline:
                cmd_name = format_cline_command_name(cmd_name)
            console.print(f"  • {cmd_name} - {cmd.get('description', '')}")

        # Report agent skills registration
        reg_meta = manager.registry.get(manifest.id)
        reg_skills = reg_meta.get("registered_skills", []) if reg_meta else []
        # Normalize to guard against corrupted registry entries
        if not isinstance(reg_skills, list):
            reg_skills = []
        if reg_skills:
            console.print(f"\n[green]✓[/green] {len(reg_skills)} agent skill(s) auto-registered")

        console.print("\n[yellow]⚠[/yellow]  Configuration may be required")
        console.print(f"   Check: .specify/extensions/{manifest.id}/")

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {e}")
        raise typer.Exit(1)
    except CompatibilityError as e:
        console.print(f"\n[red]Compatibility Error:[/red] {e}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@extension_app.command("remove")
def extension_remove(
    extension: str = typer.Argument(help="Extension ID or name to remove"),
    keep_config: bool = typer.Option(False, "--keep-config", help="Don't remove config files"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Uninstall an extension."""
    from .extensions import ExtensionManager

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "remove")

    # Get extension info for command and skill counts
    ext_manifest = manager.get_extension(extension_id)
    reg_meta = manager.registry.get(extension_id)
    # Derive cmd_count from the registry's registered_commands (includes aliases)
    # rather than from the manifest (primary commands only). Use max() across
    # agents to get the per-agent count; sum() would double-count since users
    # think in logical commands, not per-agent file counts.
    # Use get() without a default so we can distinguish "key missing" (fall back
    # to manifest) from "key present but empty dict" (zero commands registered).
    registered_commands = reg_meta.get("registered_commands") if isinstance(reg_meta, dict) else None
    if isinstance(registered_commands, dict):
        cmd_count = max(
            (len(v) for v in registered_commands.values() if isinstance(v, list)),
            default=0,
        )
    else:
        cmd_count = len(ext_manifest.commands) if ext_manifest else 0
    raw_skills = reg_meta.get("registered_skills") if reg_meta else None
    skill_count = len(raw_skills) if isinstance(raw_skills, list) else 0

    # Confirm removal
    if not force:
        console.print("\n[yellow]⚠  This will remove:[/yellow]")
        console.print(f"   • {cmd_count} command{'s' if cmd_count != 1 else ''} per agent")
        if skill_count:
            console.print(f"   • {skill_count} agent skill(s)")
        console.print(f"   • Extension directory: .specify/extensions/{extension_id}/")
        if not keep_config:
            console.print("   • Config files (will be backed up)")
        console.print()

        confirm = typer.confirm("Continue?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    # Remove extension
    success = manager.remove(extension_id, keep_config=keep_config)

    if success:
        console.print(f"\n[green]✓[/green] Extension '{display_name}' removed successfully")
        if keep_config:
            console.print(f"\nConfig files preserved in .specify/extensions/{extension_id}/")
        else:
            console.print(f"\nConfig files backed up to .specify/extensions/.backup/{extension_id}/")
        console.print(f"\nTo reinstall: specify extension add {extension_id}")
    else:
        console.print("[red]Error:[/red] Failed to remove extension")
        raise typer.Exit(1)


@extension_app.command("search")
def extension_search(
    query: str = typer.Argument(None, help="Search query (optional)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    author: Optional[str] = typer.Option(None, "--author", help="Filter by author"),
    verified: bool = typer.Option(False, "--verified", help="Show only verified extensions"),
):
    """Search for available extensions in catalog."""
    from .extensions import ExtensionCatalog, ExtensionError

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        console.print("🔍 Searching extension catalog...")
        results = catalog.search(query=query, tag=tag, author=author, verified_only=verified)

        if not results:
            console.print("\n[yellow]No extensions found matching criteria[/yellow]")
            if query or tag or author or verified:
                console.print("\nTry:")
                console.print("  • Broader search terms")
                console.print("  • Remove filters")
                console.print("  • specify extension search (show all)")
            raise typer.Exit(0)

        console.print(f"\n[green]Found {len(results)} extension(s):[/green]\n")

        for ext in results:
            # Extension header
            verified_badge = " [green]✓ Verified[/green]" if ext.get("verified") else ""
            console.print(f"[bold]{ext['name']}[/bold] (v{ext['version']}){verified_badge}")
            console.print(f"  {ext['description']}")

            # Metadata
            console.print(f"\n  [dim]Author:[/dim] {ext.get('author', 'Unknown')}")
            if ext.get('tags'):
                tags_str = ", ".join(ext['tags'])
                console.print(f"  [dim]Tags:[/dim] {tags_str}")

            # Source catalog
            catalog_name = ext.get("_catalog_name", "")
            install_allowed = ext.get("_install_allowed", True)
            if catalog_name:
                if install_allowed:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name}")
                else:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name} [yellow](discovery only — not installable)[/yellow]")

            # Stats
            stats = []
            if ext.get('downloads') is not None:
                stats.append(f"Downloads: {ext['downloads']:,}")
            if ext.get('stars') is not None:
                stats.append(f"Stars: {ext['stars']}")
            if stats:
                console.print(f"  [dim]{' | '.join(stats)}[/dim]")

            # Links
            if ext.get('repository'):
                console.print(f"  [dim]Repository:[/dim] {ext['repository']}")

            # Install command (show warning if not installable)
            if install_allowed:
                console.print(f"\n  [cyan]Install:[/cyan] specify extension add {ext['id']}")
            else:
                console.print(f"\n  [yellow]⚠[/yellow]  Not directly installable from '{catalog_name}'.")
                console.print(
                    f"  Add to an approved catalog with install_allowed: true, "
                    f"or install from a ZIP URL: specify extension add {ext['id']} --from <zip-url>"
                )
            console.print()

    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\nTip: The catalog may be temporarily unavailable. Try again later.")
        raise typer.Exit(1)


@extension_app.command("info")
def extension_info(
    extension: str = typer.Argument(help="Extension ID or name"),
):
    """Show detailed information about an extension."""
    from .extensions import ExtensionCatalog, ExtensionManager, normalize_priority

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    # Try to resolve from installed extensions first (by ID or name)
    # Use allow_not_found=True since the extension may be catalog-only
    resolved_installed_id, resolved_installed_name = _resolve_installed_extension(
        extension, installed, "info", allow_not_found=True
    )

    # Try catalog lookup (with error handling)
    # If we resolved an installed extension by display name, use its ID for catalog lookup
    # to ensure we get the correct catalog entry (not a different extension with same name)
    lookup_key = resolved_installed_id if resolved_installed_id else extension
    ext_info, catalog_error = _resolve_catalog_extension(lookup_key, catalog, "info")

    # Case 1: Found in catalog - show full catalog info
    if ext_info:
        _print_extension_info(ext_info, manager)
        return

    # Case 2: Installed locally but catalog lookup failed or not in catalog
    if resolved_installed_id:
        # Get local manifest info
        ext_manifest = manager.get_extension(resolved_installed_id)
        metadata = manager.registry.get(resolved_installed_id)
        metadata_is_dict = isinstance(metadata, dict)
        if not metadata_is_dict:
            console.print(
                "[yellow]Warning:[/yellow] Extension metadata appears to be corrupted; "
                "some information may be unavailable."
            )
        version = metadata.get("version", "unknown") if metadata_is_dict else "unknown"

        console.print(f"\n[bold]{resolved_installed_name}[/bold] (v{version})")
        console.print(f"ID: {resolved_installed_id}")
        console.print()

        if ext_manifest:
            console.print(f"{ext_manifest.description}")
            console.print()
            # Author is optional in extension.yml, safely retrieve it
            author = ext_manifest.data.get("extension", {}).get("author")
            if author:
                console.print(f"[dim]Author:[/dim] {author}")
            if ext_manifest.category:
                console.print(f"[dim]Category:[/dim] {ext_manifest.category}")
            if ext_manifest.effect:
                console.print(f"[dim]Effect:[/dim] {ext_manifest.effect}")
            console.print()

            if ext_manifest.commands:
                console.print("[bold]Commands:[/bold]")
                for cmd in ext_manifest.commands:
                    console.print(f"  • {cmd['name']}: {cmd.get('description', '')}")
                console.print()

        # Show catalog status
        if catalog_error:
            console.print(f"[yellow]Catalog unavailable:[/yellow] {catalog_error}")
            console.print("[dim]Note: Using locally installed extension; catalog info could not be verified.[/dim]")
        else:
            console.print("[yellow]Note:[/yellow] Not found in catalog (custom/local extension)")

        console.print()
        console.print("[green]✓ Installed[/green]")
        priority = normalize_priority(metadata.get("priority") if metadata_is_dict else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {resolved_installed_id}")
        return

    # Case 3: Not found anywhere
    if catalog_error:
        console.print(f"[red]Error:[/red] Could not query extension catalog: {catalog_error}")
        console.print("\nTry again when online, or use the extension ID directly.")
    else:
        console.print(f"[red]Error:[/red] Extension '{extension}' not found")
        console.print("\nTry: specify extension search")
    raise typer.Exit(1)


def _print_extension_info(ext_info: dict, manager):
    """Print formatted extension info from catalog data."""
    from .extensions import normalize_priority

    # Header
    verified_badge = " [green]✓ Verified[/green]" if ext_info.get("verified") else ""
    console.print(f"\n[bold]{ext_info['name']}[/bold] (v{ext_info['version']}){verified_badge}")
    console.print(f"ID: {ext_info['id']}")
    console.print()

    # Description
    console.print(f"{ext_info['description']}")
    console.print()

    # Author and License
    console.print(f"[dim]Author:[/dim] {ext_info.get('author', 'Unknown')}")
    console.print(f"[dim]License:[/dim] {ext_info.get('license', 'Unknown')}")

    # Category and Effect
    if ext_info.get('category'):
        console.print(f"[dim]Category:[/dim] {ext_info['category']}")
    if ext_info.get('effect'):
        console.print(f"[dim]Effect:[/dim] {ext_info['effect']}")

    # Source catalog
    if ext_info.get("_catalog_name"):
        install_allowed = ext_info.get("_install_allowed", True)
        install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
        console.print(f"[dim]Source catalog:[/dim] {ext_info['_catalog_name']}{install_note}")
    console.print()

    # Requirements
    if ext_info.get('requires'):
        console.print("[bold]Requirements:[/bold]")
        reqs = ext_info['requires']
        if reqs.get('speckit_version'):
            console.print(f"  • Spec Kit: {reqs['speckit_version']}")
        if reqs.get('tools'):
            for tool in reqs['tools']:
                tool_name = tool['name']
                tool_version = tool.get('version', 'any')
                required = " (required)" if tool.get('required') else " (optional)"
                console.print(f"  • {tool_name}: {tool_version}{required}")
        console.print()

    # Provides
    if ext_info.get('provides'):
        console.print("[bold]Provides:[/bold]")
        provides = ext_info['provides']
        if provides.get('commands'):
            console.print(f"  • Commands: {provides['commands']}")
        if provides.get('hooks'):
            console.print(f"  • Hooks: {provides['hooks']}")
        console.print()

    # Tags
    if ext_info.get('tags'):
        tags_str = ", ".join(ext_info['tags'])
        console.print(f"[bold]Tags:[/bold] {tags_str}")
        console.print()

    # Statistics
    stats = []
    if ext_info.get('downloads') is not None:
        stats.append(f"Downloads: {ext_info['downloads']:,}")
    if ext_info.get('stars') is not None:
        stats.append(f"Stars: {ext_info['stars']}")
    if stats:
        console.print(f"[bold]Statistics:[/bold] {' | '.join(stats)}")
        console.print()

    # Links
    console.print("[bold]Links:[/bold]")
    if ext_info.get('repository'):
        console.print(f"  • Repository: {ext_info['repository']}")
    if ext_info.get('homepage'):
        console.print(f"  • Homepage: {ext_info['homepage']}")
    if ext_info.get('documentation'):
        console.print(f"  • Documentation: {ext_info['documentation']}")
    if ext_info.get('changelog'):
        console.print(f"  • Changelog: {ext_info['changelog']}")
    console.print()

    # Installation status and command
    is_installed = manager.registry.is_installed(ext_info['id'])
    install_allowed = ext_info.get("_install_allowed", True)
    if is_installed:
        console.print("[green]✓ Installed[/green]")
        metadata = manager.registry.get(ext_info['id'])
        priority = normalize_priority(metadata.get("priority") if isinstance(metadata, dict) else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {ext_info['id']}")
    elif install_allowed:
        console.print("[yellow]Not installed[/yellow]")
        console.print(f"\n[cyan]Install:[/cyan] specify extension add {ext_info['id']}")
    else:
        catalog_name = ext_info.get("_catalog_name", "community")
        console.print("[yellow]Not installed[/yellow]")
        console.print(
            f"\n[yellow]⚠[/yellow]  '{ext_info['id']}' is available in the '{catalog_name}' catalog "
            f"but not in your approved catalog. Add it to .specify/extension-catalogs.yml "
            f"with install_allowed: true to enable installation."
        )


@extension_app.command("update")
def extension_update(
    extension: str = typer.Argument(None, help="Extension ID or name to update (or all)"),
):
    """Update extension(s) to latest version."""
    from .extensions import (
        ExtensionManager,
        ExtensionCatalog,
        ExtensionError,
        ValidationError,
        CommandRegistrar,
        HookExecutor,
        normalize_priority,
    )
    from packaging import version as pkg_version
    import shutil

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    catalog = ExtensionCatalog(project_root)
    speckit_version = get_speckit_version()

    try:
        # Get list of extensions to update
        installed = manager.list_installed()
        if extension:
            # Update specific extension - resolve ID from argument (handles ambiguous names)
            extension_id, _ = _resolve_installed_extension(extension, installed, "update")
            extensions_to_update = [extension_id]
        else:
            # Update all extensions
            extensions_to_update = [ext["id"] for ext in installed]

        if not extensions_to_update:
            console.print("[yellow]No extensions installed[/yellow]")
            raise typer.Exit(0)

        console.print("🔄 Checking for updates...\n")

        updates_available = []

        for ext_id in extensions_to_update:
            # Get installed version
            metadata = manager.registry.get(ext_id)
            if metadata is None or not isinstance(metadata, dict) or "version" not in metadata:
                console.print(f"⚠  {ext_id}: Registry entry corrupted or missing (skipping)")
                continue
            try:
                installed_version = pkg_version.Version(metadata["version"])
            except pkg_version.InvalidVersion:
                console.print(
                    f"⚠  {ext_id}: Invalid installed version '{metadata.get('version')}' in registry (skipping)"
                )
                continue

            # Get catalog info
            ext_info = catalog.get_extension_info(ext_id)
            if not ext_info:
                console.print(f"⚠  {ext_id}: Not found in catalog (skipping)")
                continue

            # Check if installation is allowed from this catalog
            if not ext_info.get("_install_allowed", True):
                console.print(f"⚠  {ext_id}: Updates not allowed from '{ext_info.get('_catalog_name', 'catalog')}' (skipping)")
                continue

            try:
                catalog_version = pkg_version.Version(ext_info["version"])
            except pkg_version.InvalidVersion:
                console.print(
                    f"⚠  {ext_id}: Invalid catalog version '{ext_info.get('version')}' (skipping)"
                )
                continue

            if catalog_version > installed_version:
                updates_available.append(
                    {
                        "id": ext_id,
                        "name": ext_info.get("name", ext_id),  # Display name for status messages
                        "installed": str(installed_version),
                        "available": str(catalog_version),
                        "download_url": ext_info.get("download_url"),
                    }
                )
            else:
                console.print(f"✓ {ext_id}: Up to date (v{installed_version})")

        if not updates_available:
            console.print("\n[green]All extensions are up to date![/green]")
            raise typer.Exit(0)

        # Show available updates
        console.print("\n[bold]Updates available:[/bold]\n")
        for update in updates_available:
            console.print(
                f"  • {update['id']}: {update['installed']} → {update['available']}"
            )

        console.print()
        confirm = typer.confirm("Update these extensions?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

        # Perform updates with atomic backup/restore
        console.print()
        updated_extensions = []
        failed_updates = []
        registrar = CommandRegistrar()
        hook_executor = HookExecutor(project_root)
        from .agents import CommandRegistrar as _AgentReg  # used in backup and rollback paths

        # UNSET sentinel: backup not yet captured (exception before backup step)
        UNSET = object()

        for update in updates_available:
            extension_id = update["id"]
            ext_name = update["name"]  # Use display name for user-facing messages
            console.print(f"📦 Updating {ext_name}...")

            # Backup paths
            backup_base = manager.extensions_dir / ".backup" / f"{extension_id}-update"
            backup_ext_dir = backup_base / "extension"
            backup_commands_dir = backup_base / "commands"
            backup_config_dir = backup_base / "config"

            # Store backup state
            backup_registry_entry = None  # None means registry entry not yet captured
            backup_installed = UNSET  # Original installed list from extensions.yml
            backup_hooks = None  # None means backup step 4 not yet reached; {} or {...} means backup was captured
            backed_up_command_files = {}

            try:
                # 1. Backup registry entry (always, even if extension dir doesn't exist)
                backup_registry_entry = manager.registry.get(extension_id)

                # 2. Backup extension directory
                extension_dir = manager.extensions_dir / extension_id
                if extension_dir.exists():
                    backup_base.mkdir(parents=True, exist_ok=True)
                    if backup_ext_dir.exists():
                        shutil.rmtree(backup_ext_dir)
                    shutil.copytree(extension_dir, backup_ext_dir)

                    # Backup config files separately so they can be restored
                    # after a successful install (install_from_directory clears dest dir).
                    config_files = list(extension_dir.glob("*-config.yml")) + list(
                        extension_dir.glob("*-config.local.yml")
                    )
                    for cfg_file in config_files:
                        backup_config_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cfg_file, backup_config_dir / cfg_file.name)

                # 3. Backup command files for all agents
                registered_commands = backup_registry_entry.get("registered_commands", {}) if isinstance(backup_registry_entry, dict) else {}
                for agent_name, cmd_names in registered_commands.items():
                    if agent_name not in registrar.AGENT_CONFIGS:
                        continue
                    agent_config = registrar.AGENT_CONFIGS[agent_name]
                    commands_dir = _AgentReg._resolve_agent_dir(
                        agent_name, agent_config, project_root
                    )

                    for cmd_name in cmd_names:
                        output_name = _AgentReg._compute_output_name(agent_name, cmd_name, agent_config)
                        cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                        if cmd_file.exists():
                            backup_cmd_path = backup_commands_dir / agent_name / cmd_file.name
                            backup_cmd_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(cmd_file, backup_cmd_path)
                            backed_up_command_files[str(cmd_file)] = str(backup_cmd_path)

                        # Also backup copilot prompt files
                        if agent_name == "copilot":
                            prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                            if prompt_file.exists():
                                backup_prompt_path = backup_commands_dir / "copilot-prompts" / prompt_file.name
                                backup_prompt_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(prompt_file, backup_prompt_path)
                                backed_up_command_files[str(prompt_file)] = str(backup_prompt_path)

                # 4. Backup hooks and installed list from extensions.yml
                # get_project_config() always normalizes installed->[] and hooks->{},
                # so no sentinel is needed to distinguish key-absent from key-empty.
                config = hook_executor.get_project_config()
                if isinstance(config, dict):
                    import copy
                    # Deep-copy so nested mapping entries (e.g. version-pin dicts)
                    # are not affected by in-place mutations during the update.
                    backup_installed = copy.deepcopy(config.get("installed", []))
                    backup_hooks = {}
                    for hook_name, hook_list in config.get("hooks", {}).items():
                        if not isinstance(hook_list, list):
                            continue
                        ext_hooks = [h for h in hook_list if isinstance(h, dict) and h.get("extension") == extension_id]
                        if ext_hooks:
                            backup_hooks[hook_name] = ext_hooks

                # 5. Download new version
                zip_path = catalog.download_extension(extension_id)
                try:
                    # 6. Validate extension ID from ZIP BEFORE modifying installation
                    # Handle both root-level and nested extension.yml (GitHub auto-generated ZIPs)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        import yaml
                        manifest_data = None
                        namelist = zf.namelist()

                        # First try root-level extension.yml
                        if "extension.yml" in namelist:
                            with zf.open("extension.yml") as f:
                                manifest_data = yaml.safe_load(f) or {}
                        else:
                            # Look for extension.yml in a single top-level subdirectory
                            # (e.g., "repo-name-branch/extension.yml")
                            manifest_paths = [n for n in namelist if n.endswith("/extension.yml") and n.count("/") == 1]
                            if len(manifest_paths) == 1:
                                with zf.open(manifest_paths[0]) as f:
                                    manifest_data = yaml.safe_load(f) or {}

                        if manifest_data is None:
                            raise ValueError("Downloaded extension archive is missing 'extension.yml'")

                    zip_extension_id = manifest_data.get("extension", {}).get("id")
                    if zip_extension_id != extension_id:
                        raise ValueError(
                            f"Extension ID mismatch: expected '{extension_id}', got '{zip_extension_id}'"
                        )

                    # 7. Remove old extension (handles command file cleanup and registry removal)
                    manager.remove(extension_id, keep_config=True)

                    # 8. Install new version
                    _ = manager.install_from_zip(zip_path, speckit_version)

                    # Restore user config files from backup after successful install.
                    new_extension_dir = manager.extensions_dir / extension_id
                    if backup_config_dir.exists() and new_extension_dir.exists():
                        for cfg_file in backup_config_dir.iterdir():
                            if cfg_file.is_file():
                                shutil.copy2(cfg_file, new_extension_dir / cfg_file.name)

                    # 9. Restore metadata from backup (installed_at, enabled state)
                    if backup_registry_entry and isinstance(backup_registry_entry, dict):
                        # Copy current registry entry to avoid mutating internal
                        # registry state before explicit restore().
                        current_metadata = manager.registry.get(extension_id)
                        if current_metadata is None or not isinstance(current_metadata, dict):
                            raise RuntimeError(
                                f"Registry entry for '{extension_id}' missing or corrupted after install — update incomplete"
                            )
                        new_metadata = dict(current_metadata)

                        # Preserve the original installation timestamp
                        if "installed_at" in backup_registry_entry:
                            new_metadata["installed_at"] = backup_registry_entry["installed_at"]

                        # Preserve the original priority (normalized to handle corruption)
                        if "priority" in backup_registry_entry:
                            new_metadata["priority"] = normalize_priority(backup_registry_entry["priority"])

                        # If extension was disabled before update, disable it again
                        if not backup_registry_entry.get("enabled", True):
                            new_metadata["enabled"] = False

                        # Use restore() instead of update() because update() always
                        # preserves the existing installed_at, ignoring our override
                        manager.registry.restore(extension_id, new_metadata)

                        # Also disable hooks in extensions.yml if extension was disabled
                        if not backup_registry_entry.get("enabled", True):
                            config = hook_executor.get_project_config()
                            if "hooks" in config:
                                for hook_name in config["hooks"]:
                                    for hook in config["hooks"][hook_name]:
                                        if hook.get("extension") == extension_id:
                                            hook["enabled"] = False
                                hook_executor.save_project_config(config)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

                # 10. Clean up backup on success
                if backup_base.exists():
                    shutil.rmtree(backup_base)

                console.print(f"   [green]✓[/green] Updated to v{update['available']}")
                updated_extensions.append(ext_name)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"   [red]✗[/red] Failed: {e}")
                failed_updates.append((ext_name, str(e)))

                # Rollback on failure
                console.print(f"   [yellow]↩[/yellow] Rolling back {ext_name}...")

                try:
                    # Restore extension directory
                    # Only perform destructive rollback if backup exists (meaning we
                    # actually modified the extension). This avoids deleting a valid
                    # installation when failure happened before changes were made.
                    extension_dir = manager.extensions_dir / extension_id
                    if backup_ext_dir.exists():
                        if extension_dir.exists():
                            shutil.rmtree(extension_dir)
                        shutil.copytree(backup_ext_dir, extension_dir)

                    # Remove any NEW command files created by failed install
                    # (files that weren't in the original backup)
                    try:
                        new_registry_entry = manager.registry.get(extension_id)
                        if new_registry_entry is None or not isinstance(new_registry_entry, dict):
                            new_registered_commands = {}
                        else:
                            new_registered_commands = new_registry_entry.get("registered_commands", {})
                        for agent_name, cmd_names in new_registered_commands.items():
                            if agent_name not in registrar.AGENT_CONFIGS:
                                continue
                            agent_config = registrar.AGENT_CONFIGS[agent_name]
                            commands_dir = _AgentReg._resolve_agent_dir(
                                agent_name, agent_config, project_root
                            )

                            for cmd_name in cmd_names:
                                output_name = _AgentReg._compute_output_name(agent_name, cmd_name, agent_config)
                                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                                # Delete if it exists and wasn't in our backup
                                if cmd_file.exists() and str(cmd_file) not in backed_up_command_files:
                                    cmd_file.unlink()

                                # Also handle copilot prompt files
                                if agent_name == "copilot":
                                    prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                                    if prompt_file.exists() and str(prompt_file) not in backed_up_command_files:
                                        prompt_file.unlink()
                    except KeyError:
                        pass  # No new registry entry exists, nothing to clean up

                    # Restore backed up command files
                    for original_path, backup_path in backed_up_command_files.items():
                        backup_file = Path(backup_path)
                        if backup_file.exists():
                            original_file = Path(original_path)
                            original_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(backup_file, original_file)

                    # Restore metadata in extensions.yml (hooks and installed list).
                    # Only run if backup step 4 was reached (backup_hooks is not None);
                    # otherwise we have no safe baseline to restore from and could corrupt
                    # the config by removing pre-existing hooks.
                    if backup_hooks is not None:
                        config = hook_executor.get_project_config()
                        if not isinstance(config, dict):
                            config = {}

                        modified = False

                        # 1. Restore hooks in extensions.yml
                        if not isinstance(config.get("hooks"), dict):
                            config["hooks"] = {}
                            modified = True

                        # Remove any hooks for this extension added by the failed install
                        for hook_name in list(config["hooks"].keys()):
                            hooks_list = config["hooks"][hook_name]
                            if not isinstance(hooks_list, list):
                                config["hooks"][hook_name] = []
                                modified = True
                                continue

                            original_len = len(hooks_list)
                            config["hooks"][hook_name] = [
                                h for h in hooks_list
                                if isinstance(h, dict) and h.get("extension") != extension_id
                            ]
                            if len(config["hooks"][hook_name]) != original_len:
                                modified = True

                        # Add back the backed-up hooks
                        if backup_hooks:
                            for hook_name, hooks in backup_hooks.items():
                                if not isinstance(config["hooks"].get(hook_name), list):
                                    config["hooks"][hook_name] = []
                                config["hooks"][hook_name].extend(hooks)
                                modified = True

                        # 2. Restore installed list in extensions.yml
                        if backup_installed is not UNSET:
                            if config.get("installed") != backup_installed:
                                config["installed"] = backup_installed
                                modified = True

                        if modified:
                            hook_executor.save_project_config(config)

                    # Restore registry entry (use restore() since entry was removed)
                    if backup_registry_entry:
                        manager.registry.restore(extension_id, backup_registry_entry)

                    console.print("   [green]✓[/green] Rollback successful")
                    # Clean up backup directory only on successful rollback
                    if backup_base.exists():
                        shutil.rmtree(backup_base)
                except Exception as rollback_error:
                    console.print(f"   [red]✗[/red] Rollback failed: {rollback_error}")
                    console.print(f"   [dim]Backup preserved at: {backup_base}[/dim]")

        # Summary
        console.print()
        if updated_extensions:
            console.print(f"[green]✓[/green] Successfully updated {len(updated_extensions)} extension(s)")
        if failed_updates:
            console.print(f"[red]✗[/red] Failed to update {len(failed_updates)} extension(s):")
            for ext_name, error in failed_updates:
                console.print(f"   • {ext_name}: {error}")
            raise typer.Exit(1)

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {e}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@extension_app.command("enable")
def extension_enable(
    extension: str = typer.Argument(help="Extension ID or name to enable"),
):
    """Enable a disabled extension."""
    from .extensions import ExtensionManager, HookExecutor

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "enable")

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Extension '{extension_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    if metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{display_name}' is already enabled[/yellow]")
        raise typer.Exit(0)

    manager.registry.update(extension_id, {"enabled": True})

    # Enable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = True
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{display_name}' enabled")


@extension_app.command("disable")
def extension_disable(
    extension: str = typer.Argument(help="Extension ID or name to disable"),
):
    """Disable an extension without removing it."""
    from .extensions import ExtensionManager, HookExecutor

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "disable")

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Extension '{extension_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{display_name}' is already disabled[/yellow]")
        raise typer.Exit(0)

    manager.registry.update(extension_id, {"enabled": False})

    # Disable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = False
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{display_name}' disabled")
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(f"To re-enable: specify extension enable {extension_id}")


@extension_app.command("set-priority")
def extension_set_priority(
    extension: str = typer.Argument(help="Extension ID or name"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
):
    """Set the resolution priority of an installed extension."""
    from .extensions import ExtensionManager

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "set-priority")

    # Get current metadata
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Extension '{extension_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    from .extensions import normalize_priority
    raw_priority = metadata.get("priority")
    # Only skip if the stored value is already a valid int equal to requested priority
    # This ensures corrupted values (e.g., "high") get repaired even when setting to default (10)
    if isinstance(raw_priority, int) and raw_priority == priority:
        console.print(f"[yellow]Extension '{display_name}' already has priority {priority}[/yellow]")
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    # Update priority
    manager.registry.update(extension_id, {"priority": priority})

    console.print(f"[green]✓[/green] Extension '{display_name}' priority changed: {old_priority} → {priority}")
    console.print("\n[dim]Lower priority = higher precedence in template resolution[/dim]")


# ===== Workflow Commands =====

workflow_app = typer.Typer(
    name="workflow",
    help="Manage and run automation workflows",
    add_completion=False,
)
app.add_typer(workflow_app, name="workflow")

workflow_catalog_app = typer.Typer(
    name="catalog",
    help="Manage workflow catalogs",
    add_completion=False,
)
workflow_app.add_typer(workflow_catalog_app, name="catalog")

workflow_step_app = typer.Typer(
    name="step",
    help="Manage workflow step types",
    add_completion=False,
)
workflow_app.add_typer(workflow_step_app, name="step")

workflow_step_catalog_app = typer.Typer(
    name="catalog",
    help="Manage step catalogs",
    add_completion=False,
)
workflow_step_app.add_typer(workflow_step_catalog_app, name="catalog")


def _parse_input_values(input_values: list[str] | None) -> dict[str, Any]:
    """Parse repeated ``key=value`` CLI inputs into a dict.

    Shared by ``workflow run`` and ``workflow resume``. Exits with an error
    on any entry missing ``=``.
    """
    inputs: dict[str, Any] = {}
    for kv in input_values or []:
        if "=" not in kv:
            console.print(f"[red]Error:[/red] Invalid input format: {kv!r} (expected key=value)")
            raise typer.Exit(1)
        key, _, value = kv.partition("=")
        inputs[key.strip()] = value.strip()
    return inputs


def _workflow_run_payload(state: Any) -> dict[str, Any]:
    """Machine-readable summary of a run/resume outcome."""
    return {
        "run_id": state.run_id,
        "workflow_id": state.workflow_id,
        "status": state.status.value,
        "current_step_id": state.current_step_id,
        "current_step_index": state.current_step_index,
    }


def _run_outcome_exit_code(status_value: str) -> int:
    """Exit code for a finished run/resume: non-zero on terminal failure.

    ``failed`` and ``aborted`` map to 1 so scripts and orchestrators can
    rely on the process exit code; ``completed`` and ``paused`` map to 0
    (paused is a legitimate waiting state, not a failure).
    """
    return 1 if status_value in ("failed", "aborted") else 0


def _emit_workflow_json(payload: dict[str, Any]) -> None:
    """Write a workflow payload as machine-readable JSON to stdout.

    Uses the builtin ``print`` rather than ``console.print`` so Rich
    markup interpretation, syntax highlighting, and line-wrapping can
    never alter the emitted JSON.
    """
    print(json.dumps(payload, indent=2))


@contextlib.contextmanager
def _stdout_to_stderr_when(active: bool):
    """Redirect everything written to stdout onto stderr while *active*.

    Suppressing the banner and the step-start callback is not enough to
    keep a ``--json`` stream clean: individual steps may still write to
    stdout while the engine runs — the gate step prints its prompt,
    and the prompt step runs a subprocess that inherits the process's
    stdout file descriptor. Either would corrupt the single JSON object.

    Redirecting at the file-descriptor level (``dup2``) captures both
    Python-level writes and inherited-fd subprocess output, so step
    progress lands on stderr (still visible to a human) while stdout
    carries only the emitted JSON. A no-op when *active* is false.
    """
    if not active:
        yield
        return
    sys.stdout.flush()
    saved_stdout_fd = os.dup(1)
    try:
        os.dup2(2, 1)  # fd 1 (stdout) now points at fd 2 (stderr)
        with contextlib.redirect_stdout(sys.stderr):
            yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout_fd, 1)  # restore the real stdout
        os.close(saved_stdout_fd)


@workflow_app.command("run")
def workflow_run(
    source: str = typer.Argument(..., help="Workflow ID or YAML file path"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the run outcome as a single JSON object instead of formatted text.",
    ),
):
    """Run a workflow from an installed ID or local YAML path."""
    from .workflows import load_custom_steps
    from .workflows.engine import WorkflowEngine

    source_path = Path(source).expanduser()
    is_file_source = source_path.suffix.lower() in (".yml", ".yaml") and source_path.is_file()

    if is_file_source:
        # When running a YAML file directly, use cwd as project root
        # without requiring a .specify/ project directory.
        project_root = Path.cwd()
        specify_dir = project_root / ".specify"
        if specify_dir.is_symlink():
            console.print("[red]Error:[/red] Refusing to use symlinked .specify path in current directory")
            raise typer.Exit(1)
        if specify_dir.exists() and not specify_dir.is_dir():
            console.print("[red]Error:[/red] .specify path exists but is not a directory")
            raise typer.Exit(1)
    else:
        project_root = _require_specify_project()

    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    try:
        definition = engine.load_workflow(source_path if is_file_source else source)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Workflow not found: {source}")
        raise typer.Exit(1)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] Invalid workflow: {exc}")
        raise typer.Exit(1)

    # Validate
    errors = engine.validate(definition)
    if errors:
        console.print("[red]Workflow validation failed:[/red]")
        for err in errors:
            console.print(f"  • {err}")
        raise typer.Exit(1)

    # Parse inputs
    inputs = _parse_input_values(input_values)

    if not json_output:
        console.print(f"\n[bold cyan]Running workflow:[/bold cyan] {definition.name} ({definition.id})")
        console.print(f"[dim]Version: {definition.version}[/dim]\n")

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.execute(definition, inputs)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        console.print(f"[red]Workflow failed:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")
    console.print(f"[dim]Run ID: {state.run_id}[/dim]")

    if state.status.value == "paused":
        console.print(f"\nResume with: [cyan]specify workflow resume {state.run_id}[/cyan]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("resume")
def workflow_resume(
    run_id: str = typer.Argument(..., help="Run ID to resume"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Updated input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the resume outcome as a single JSON object instead of formatted text.",
    ),
):
    """Resume a paused or failed workflow run."""
    from .workflows import load_custom_steps
    from .workflows.engine import WorkflowEngine

    project_root = _require_specify_project()
    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    inputs = _parse_input_values(input_values)

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.resume(run_id, inputs or None)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise typer.Exit(1)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        console.print(f"[red]Resume failed:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("status")
def workflow_status(
    run_id: str | None = typer.Argument(None, help="Run ID to inspect (shows all if omitted)"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit run status as a single JSON object instead of formatted text.",
    ),
):
    """Show workflow run status."""
    from .workflows.engine import WorkflowEngine

    project_root = _require_specify_project()
    engine = WorkflowEngine(project_root)

    if run_id:
        try:
            from .workflows.engine import RunState
            state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)

        if json_output:
            # Build on the shared run/resume payload so the common fields
            # (including current_step_index) stay identical across commands.
            payload = {
                **_workflow_run_payload(state),
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "steps": {
                    sid: sd.get("status", "unknown")
                    for sid, sd in state.step_results.items()
                },
            }
            _emit_workflow_json(payload)
            return

        status_colors = {
            "completed": "green",
            "paused": "yellow",
            "failed": "red",
            "aborted": "red",
            "running": "blue",
            "created": "dim",
        }
        color = status_colors.get(state.status.value, "white")

        console.print(f"\n[bold cyan]Workflow Run: {state.run_id}[/bold cyan]")
        console.print(f"  Workflow: {state.workflow_id}")
        console.print(f"  Status:   [{color}]{state.status.value}[/{color}]")
        console.print(f"  Created:  {state.created_at}")
        console.print(f"  Updated:  {state.updated_at}")

        if state.current_step_id:
            console.print(f"  Current:  {state.current_step_id}")

        if state.step_results:
            console.print(f"\n  [bold]Steps ({len(state.step_results)}):[/bold]")
            for step_id, step_data in state.step_results.items():
                s = step_data.get("status", "unknown")
                sc = {"completed": "green", "failed": "red", "paused": "yellow"}.get(s, "white")
                console.print(f"    [{sc}]●[/{sc}] {step_id}: {s}")
    else:
        runs = engine.list_runs()

        if json_output:
            payload = {
                "runs": [
                    {
                        "run_id": r["run_id"],
                        "workflow_id": r.get("workflow_id"),
                        "status": r.get("status", "unknown"),
                        "updated_at": r.get("updated_at"),
                    }
                    for r in runs
                ]
            }
            _emit_workflow_json(payload)
            return

        if not runs:
            console.print("[yellow]No workflow runs found.[/yellow]")
            return

        console.print("\n[bold cyan]Workflow Runs:[/bold cyan]\n")
        for run_data in runs:
            s = run_data.get("status", "unknown")
            sc = {"completed": "green", "failed": "red", "paused": "yellow", "running": "blue"}.get(s, "white")
            console.print(
                f"  [{sc}]●[/{sc}] {run_data['run_id']}  "
                f"{run_data.get('workflow_id', '?')}  "
                f"[{sc}]{s}[/{sc}]  "
                f"[dim]{run_data.get('updated_at', '?')}[/dim]"
            )


@workflow_app.command("list")
def workflow_list():
    """List installed workflows."""
    from .workflows.catalog import WorkflowRegistry

    project_root = _require_specify_project()
    registry = WorkflowRegistry(project_root)
    installed = registry.list()

    if not installed:
        console.print("[yellow]No workflows installed.[/yellow]")
        console.print("\nInstall a workflow with:")
        console.print("  [cyan]specify workflow add <workflow-id>[/cyan]")
        return

    console.print("\n[bold cyan]Installed Workflows:[/bold cyan]\n")
    for wf_id, wf_data in installed.items():
        console.print(f"  [bold]{wf_data.get('name', wf_id)}[/bold] ({wf_id}) v{wf_data.get('version', '?')}")
        desc = wf_data.get("description", "")
        if desc:
            console.print(f"    {desc}")
        console.print()


@workflow_app.command("add")
def workflow_add(
    source: str = typer.Argument(..., help="Workflow ID, URL, or local path"),
):
    """Install a workflow from catalog, URL, or local path."""
    from .workflows.catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .workflows.engine import WorkflowDefinition

    project_root = _require_specify_project()
    registry = WorkflowRegistry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"

    def _validate_and_install_local(yaml_path: Path, source_label: str) -> None:
        """Validate and install a workflow from a local YAML file."""
        try:
            definition = WorkflowDefinition.from_yaml(yaml_path)
        except (ValueError, yaml.YAMLError) as exc:
            console.print(f"[red]Error:[/red] Invalid workflow YAML: {exc}")
            raise typer.Exit(1)
        if not definition.id or not definition.id.strip():
            console.print("[red]Error:[/red] Workflow definition has an empty or missing 'id'")
            raise typer.Exit(1)

        from .workflows.engine import validate_workflow
        errors = validate_workflow(definition)
        if errors:
            console.print("[red]Error:[/red] Workflow validation failed:")
            for err in errors:
                console.print(f"  \u2022 {err}")
            raise typer.Exit(1)

        dest_dir = workflows_dir / definition.id
        dest_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(yaml_path, dest_dir / "workflow.yml")
        registry.add(definition.id, {
            "name": definition.name,
            "version": definition.version,
            "description": definition.description,
            "source": source_label,
        })
        console.print(f"[green]✓[/green] Workflow '{definition.name}' ({definition.id}) installed")

    # Try as URL (http/https)
    if source.startswith("http://") or source.startswith("https://"):
        from ipaddress import ip_address
        from urllib.parse import urlparse
        from specify_cli.authentication.http import open_url as _open_url

        parsed_src = urlparse(source)
        src_host = parsed_src.hostname or ""
        src_loopback = src_host == "localhost"
        if not src_loopback:
            try:
                src_loopback = ip_address(src_host).is_loopback
            except ValueError:
                # Host is not an IP literal (e.g., a DNS name); keep default non-loopback.
                pass
        if parsed_src.scheme != "https" and not (parsed_src.scheme == "http" and src_loopback):
            console.print("[red]Error:[/red] Only HTTPS URLs are allowed, except HTTP for localhost.")
            raise typer.Exit(1)

        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset

        _wf_url_extra_headers = None
        _resolved_wf_url = _resolve_gh_asset(source, _open_url, timeout=30)
        if _resolved_wf_url:
            source = _resolved_wf_url
            _wf_url_extra_headers = {"Accept": "application/octet-stream"}

        import tempfile
        try:
            with _open_url(source, timeout=30, extra_headers=_wf_url_extra_headers) as resp:
                final_url = resp.geturl()
                final_parsed = urlparse(final_url)
                final_host = final_parsed.hostname or ""
                final_lb = final_host == "localhost"
                if not final_lb:
                    try:
                        final_lb = ip_address(final_host).is_loopback
                    except ValueError:
                        # Redirect host is not an IP literal; keep loopback as determined above.
                        pass
                if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_lb):
                    console.print(f"[red]Error:[/red] URL redirected to non-HTTPS: {final_url}")
                    raise typer.Exit(1)
                with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp:
                    tmp.write(resp.read())
                    tmp_path = Path(tmp.name)
        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download workflow: {exc}")
            raise typer.Exit(1)
        try:
            _validate_and_install_local(tmp_path, source)
        finally:
            tmp_path.unlink(missing_ok=True)
        return

    # Try as a local file/directory
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_file() and source_path.suffix in (".yml", ".yaml"):
            _validate_and_install_local(source_path, str(source_path))
            return
        elif source_path.is_dir():
            wf_file = source_path / "workflow.yml"
            if not wf_file.exists():
                console.print(f"[red]Error:[/red] No workflow.yml found in {source}")
                raise typer.Exit(1)
            _validate_and_install_local(wf_file, str(source_path))
            return

    # Try from catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(source)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Workflow '{source}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(f"[yellow]Warning:[/yellow] Workflow '{source}' is from a discovery-only catalog")
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    workflow_url = info.get("url")
    if not workflow_url:
        console.print(f"[red]Error:[/red] Workflow '{source}' does not have an install URL in the catalog")
        raise typer.Exit(1)

    # Validate URL scheme (HTTPS required, HTTP allowed for localhost only)
    from ipaddress import ip_address
    from urllib.parse import urlparse

    parsed_url = urlparse(workflow_url)
    url_host = parsed_url.hostname or ""
    is_loopback = False
    if url_host == "localhost":
        is_loopback = True
    else:
        try:
            is_loopback = ip_address(url_host).is_loopback
        except ValueError:
            # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
            pass
    if parsed_url.scheme != "https" and not (parsed_url.scheme == "http" and is_loopback):
        console.print(
            f"[red]Error:[/red] Workflow '{source}' has an invalid install URL. "
            "Only HTTPS URLs are allowed, except HTTP for localhost/loopback."
        )
        raise typer.Exit(1)

    workflow_dir = workflows_dir / source
    # Validate that source is a safe directory name (no path traversal)
    try:
        workflow_dir.resolve().relative_to(workflows_dir.resolve())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid workflow ID: {source!r}")
        raise typer.Exit(1)
    workflow_file = workflow_dir / "workflow.yml"

    try:
        from specify_cli.authentication.http import open_url as _open_url
        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset

        _wf_cat_extra_headers = None
        _resolved_workflow_url = _resolve_gh_asset(workflow_url, _open_url, timeout=30)
        if _resolved_workflow_url:
            workflow_url = _resolved_workflow_url
            _wf_cat_extra_headers = {"Accept": "application/octet-stream"}

        workflow_dir.mkdir(parents=True, exist_ok=True)
        with _open_url(workflow_url, timeout=30, extra_headers=_wf_cat_extra_headers) as response:
            # Validate final URL after redirects
            final_url = response.geturl()
            final_parsed = urlparse(final_url)
            final_host = final_parsed.hostname or ""
            final_loopback = final_host == "localhost"
            if not final_loopback:
                try:
                    final_loopback = ip_address(final_host).is_loopback
                except ValueError:
                    # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
                    pass
            if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_loopback):
                if workflow_dir.exists():
                    import shutil
                    shutil.rmtree(workflow_dir, ignore_errors=True)
                console.print(
                    f"[red]Error:[/red] Workflow '{source}' redirected to non-HTTPS URL: {final_url}"
                )
                raise typer.Exit(1)
            workflow_file.write_bytes(response.read())
    except Exception as exc:
        if workflow_dir.exists():
            import shutil
            shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Failed to install workflow '{source}' from catalog: {exc}")
        raise typer.Exit(1)

    # Validate the downloaded workflow before registering
    try:
        definition = WorkflowDefinition.from_yaml(workflow_file)
    except (ValueError, yaml.YAMLError) as exc:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Downloaded workflow is invalid: {exc}")
        raise typer.Exit(1)

    from .workflows.engine import validate_workflow
    errors = validate_workflow(definition)
    if errors:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print("[red]Error:[/red] Downloaded workflow validation failed:")
        for err in errors:
            console.print(f"  \u2022 {err}")
        raise typer.Exit(1)

    # Enforce that the workflow's internal ID matches the catalog key
    if definition.id and definition.id != source:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(
            f"[red]Error:[/red] Workflow ID in YAML ({definition.id!r}) "
            f"does not match catalog key ({source!r}). "
            f"The catalog entry may be misconfigured."
        )
        raise typer.Exit(1)

    registry.add(source, {
        "name": definition.name or info.get("name", source),
        "version": definition.version or info.get("version", "0.0.0"),
        "description": definition.description or info.get("description", ""),
        "source": "catalog",
        "catalog_name": info.get("_catalog_name", ""),
        "url": workflow_url,
    })
    console.print(f"[green]✓[/green] Workflow '{info.get('name', source)}' installed from catalog")


@workflow_app.command("remove")
def workflow_remove(
    workflow_id: str = typer.Argument(..., help="Workflow ID to uninstall"),
):
    """Uninstall a workflow."""
    from .workflows.catalog import WorkflowRegistry

    project_root = _require_specify_project()
    registry = WorkflowRegistry(project_root)

    if not registry.is_installed(workflow_id):
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' is not installed")
        raise typer.Exit(1)

    # Remove workflow files
    workflow_dir = project_root / ".specify" / "workflows" / workflow_id
    if workflow_dir.exists():
        import shutil
        shutil.rmtree(workflow_dir)

    registry.remove(workflow_id)
    console.print(f"[green]✓[/green] Workflow '{workflow_id}' removed")


@workflow_app.command("search")
def workflow_search(
    query: str | None = typer.Argument(None, help="Search query"),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag"),
):
    """Search workflow catalogs."""
    from .workflows.catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    console.print(f"\n[bold cyan]Workflows ({len(results)}):[/bold cyan]\n")
    for wf in results:
        console.print(f"  [bold]{wf.get('name', wf.get('id', '?'))}[/bold] ({wf.get('id', '?')}) v{wf.get('version', '?')}")
        desc = wf.get("description", "")
        if desc:
            console.print(f"    {desc}")
        tags = wf.get("tags", [])
        if tags:
            console.print(f"    [dim]Tags: {', '.join(tags)}[/dim]")
        console.print()


@workflow_app.command("info")
def workflow_info(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Show workflow details and step graph."""
    from .workflows.catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .workflows.engine import WorkflowEngine

    project_root = _require_specify_project()

    # Check installed first
    registry = WorkflowRegistry(project_root)
    installed = registry.get(workflow_id)

    engine = WorkflowEngine(project_root)

    definition = None
    try:
        definition = engine.load_workflow(workflow_id)
    except FileNotFoundError:
        # Local workflow definition not found on disk; fall back to
        # catalog/registry lookup below.
        pass

    if definition:
        console.print(f"\n[bold cyan]{definition.name}[/bold cyan] ({definition.id})")
        console.print(f"  Version:     {definition.version}")
        if definition.author:
            console.print(f"  Author:      {definition.author}")
        if definition.description:
            console.print(f"  Description: {definition.description}")
        if definition.default_integration:
            console.print(f"  Integration: {definition.default_integration}")
        if installed:
            console.print("  [green]Installed[/green]")

        if definition.inputs:
            console.print("\n  [bold]Inputs:[/bold]")
            for name, inp in definition.inputs.items():
                if isinstance(inp, dict):
                    req = "required" if inp.get("required") else "optional"
                    console.print(f"    {name} ({inp.get('type', 'string')}) — {req}")

        if definition.steps:
            console.print(f"\n  [bold]Steps ({len(definition.steps)}):[/bold]")
            for step in definition.steps:
                stype = step.get("type", "command")
                console.print(f"    → {step.get('id', '?')} [{stype}]")
        return

    # Try catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError:
        info = None

    if info:
        console.print(f"\n[bold cyan]{info.get('name', workflow_id)}[/bold cyan] ({workflow_id})")
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        if info.get("tags"):
            console.print(f"  Tags:        {', '.join(info['tags'])}")
        console.print("  [yellow]Not installed[/yellow]")
    else:
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found")
        raise typer.Exit(1)


@workflow_catalog_app.command("list")
def workflow_catalog_list():
    """List configured workflow catalog sources."""
    from .workflows.catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Workflow Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = "[green]install allowed[/green]" if cfg["install_allowed"] else "[yellow]discovery only[/yellow]"
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_catalog_app.command("add")
def workflow_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a workflow catalog source."""
    from .workflows.catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source added: {url}")


@workflow_catalog_app.command("remove")
def workflow_catalog_remove(
    index: int = typer.Argument(..., help="Catalog index to remove (from 'catalog list')"),
):
    """Remove a workflow catalog source by index."""
    from .workflows.catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")


# ===== Workflow Step Commands =====

@workflow_step_app.command("list")
def workflow_step_list():
    """List installed step types (built-in and custom)."""
    from .workflows import STEP_REGISTRY
    from .workflows.catalog import StepRegistry

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Read installed custom steps from registry only — no dynamic imports
    installed: dict = {}
    if specify_dir.exists():
        registry = StepRegistry(project_root)
        installed = registry.list()

    console.print("\n[bold cyan]Installed Step Types:[/bold cyan]\n")

    built_in = sorted(k for k in STEP_REGISTRY if k not in installed)
    if built_in:
        console.print("  [bold]Built-in:[/bold]")
        for key in built_in:
            console.print(f"    • {key}")
        console.print()

    if installed:
        console.print("  [bold]Custom (installed):[/bold]")
        for key in sorted(installed):
            meta = installed[key] or {}
            name = meta.get("name", key)
            version = meta.get("version", "?")
            console.print(f"    • [bold]{name}[/bold] ({key}) v{version}")
        console.print()

    if not built_in and not installed:
        console.print("[yellow]No step types found.[/yellow]")

    if specify_dir.exists():
        console.print(
            "  Install a new step type with: [cyan]specify workflow step add <id>[/cyan]"
        )


# IDs that map to internal names used under .specify/workflows/steps/ and must
# not be used as custom step IDs (dotfile check is done separately at runtime).
_RESERVED_STEP_IDS: frozenset[str] = frozenset({".cache", "step-registry.json"})

# Windows reserved device names (case-insensitive, with or without extensions)
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})

# Characters invalid in filenames on Windows
_WINDOWS_INVALID_CHARS: frozenset[str] = frozenset('<>:"|?*')


def _validate_step_id_or_exit(step_id: str) -> None:
    """Validate that ``step_id`` is a single safe path component.

    Rejects empty strings, whitespace-only strings, leading/trailing whitespace,
    path separators, ``.``/``..`` components, dotfile prefixes, reserved names,
    Windows-invalid filename characters, trailing dots/spaces, and Windows
    reserved device names. Exits with code 1 on failure.
    """
    # Strip the stem (before first dot) for Windows reserved-name check
    stem = step_id.split(".")[0].lower() if step_id else ""
    if (
        not step_id
        or not step_id.strip()
        or step_id != step_id.strip()
        or "/" in step_id
        or "\\" in step_id
        or step_id in (".", "..")
        or step_id.startswith(".")
        or step_id.endswith(".")
        or step_id.endswith(" ")
        or step_id.lower() in _RESERVED_STEP_IDS
        or stem in _WINDOWS_RESERVED_NAMES
        or any(c in _WINDOWS_INVALID_CHARS for c in step_id)
        or any(ord(c) < 32 for c in step_id)
    ):
        console.print(
            f"[red]Error:[/red] Invalid step id '{step_id}': must be a single safe "
            "path component (no separators, no leading dot, not a reserved name, "
            "no invalid filename characters)"
        )
        raise typer.Exit(1)


def _resolve_steps_base_dir_or_exit(project_root: Path) -> Path:
    """Resolve .specify/workflows/steps while refusing symlinked parent directories."""
    project_root_resolved = project_root.resolve()
    steps_base_dir_unresolved = project_root / ".specify" / "workflows" / "steps"

    current = project_root
    for part in (".specify", "workflows", "steps"):
        current = current / part
        if current.is_symlink():
            console.print(
                f"[red]Error:[/red] Refusing to use symlinked step directory '{current}'"
            )
            raise typer.Exit(1)
        if current.exists() and not current.is_dir():
            console.print(
                f"[red]Error:[/red] Step directory path is not a directory: '{current}'"
            )
            raise typer.Exit(1)

    steps_base_dir = steps_base_dir_unresolved.resolve()
    try:
        steps_base_dir.relative_to(project_root_resolved)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Step directory escapes project root: '{steps_base_dir}'"
        )
        raise typer.Exit(1)

    return steps_base_dir


@workflow_step_app.command("add")
def workflow_step_add(
    step_id: str = typer.Argument(..., help="Step type ID from catalog"),
):
    """Install a custom step type from the step catalog."""
    from .workflows.catalog import StepCatalog, StepCatalogError, StepRegistry, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(
            f"[yellow]Warning:[/yellow] Step type '{step_id}' is from a discovery-only catalog"
        )
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    # Reject step IDs that collide with built-in step types
    from .workflows import STEP_REGISTRY as _step_reg
    if step_id in _step_reg:
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' conflicts with a built-in step type"
        )
        raise typer.Exit(1)

    # Reject if already installed
    registry = StepRegistry(project_root)
    if registry.is_installed(step_id):
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' is already installed. "
            "Remove it first with: [cyan]specify workflow step remove "
            f"{step_id}[/cyan]"
        )
        raise typer.Exit(1)

    step_yml_url = info.get("step_yml_url") or info.get("url")
    if not step_yml_url:
        console.print(f"[red]Error:[/red] Catalog entry for '{step_id}' has no URL")
        raise typer.Exit(1)

    # Derive __init__.py URL: replace trailing step.yml with __init__.py
    # or use explicit init_url if provided.
    init_url = info.get("init_url")
    if not init_url:
        if step_yml_url.endswith("step.yml"):
            init_url = step_yml_url[: -len("step.yml")] + "__init__.py"
        else:
            console.print(
                f"[red]Error:[/red] Cannot derive __init__.py URL from '{step_yml_url}'. "
                "Catalog entry should provide 'init_url' or a 'url' ending in 'step.yml'."
            )
            raise typer.Exit(1)

    from urllib.parse import urlparse
    from specify_cli.authentication.http import open_url as _open_url

    def _safe_fetch(url: str) -> bytes:
        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise ValueError(f"Refusing to fetch from non-HTTPS URL: {url}")
        if not parsed.hostname:
            raise ValueError(f"Refusing to fetch from URL with no hostname: {url}")
        with _open_url(url, timeout=30) as resp:
            final_url = resp.geturl()
            final_parsed = urlparse(final_url)
            final_is_localhost = final_parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if final_parsed.scheme != "https" and not (
                final_parsed.scheme == "http" and final_is_localhost
            ):
                raise ValueError(f"Redirect to non-HTTPS URL: {final_url}")
            if not final_parsed.hostname:
                raise ValueError(f"Redirect to URL with no hostname: {final_url}")
            return resp.read()

    _validate_step_id_or_exit(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: ensure the resolved directory is a direct child of
    # steps_base_dir even after symlink resolution.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    import shutil
    import tempfile

    # Refuse if step_dir already exists (e.g. leftover from a previous failed/manual
    # install that wasn't registered). The user should remove it before retrying.
    if step_dir.exists():
        console.print(
            f"[red]Error:[/red] Step directory already exists at '{step_dir}'. "
            f"Remove it manually or use: [cyan]specify workflow step remove {step_id}[/cyan]"
        )
        raise typer.Exit(1)

    # Create steps_base_dir now so the staging temp dir is on the same filesystem,
    # enabling a truly atomic os.rename() below.
    try:
        steps_base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix="speckit_step_tmp_", dir=steps_base_dir))
    except OSError as exc:
        console.print(f"[red]Error:[/red] Failed to create staging directory: {exc}")
        raise typer.Exit(1)
    try:
        try:
            step_yml_content = _safe_fetch(step_yml_url)
            init_py_content = _safe_fetch(init_url)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download step files: {exc}")
            raise typer.Exit(1)

        # Validate step.yml
        try:
            import yaml as _yaml

            meta = _yaml.safe_load(step_yml_content.decode("utf-8")) or {}
        except Exception as exc:
            console.print(f"[red]Error:[/red] Invalid step.yml: {exc}")
            raise typer.Exit(1)

        if not isinstance(meta, dict):
            console.print("[red]Error:[/red] step.yml must be a YAML mapping")
            raise typer.Exit(1)

        step_meta = meta.get("step", {})
        if not isinstance(step_meta, dict):
            console.print("[red]Error:[/red] step.yml 'step' field must be a mapping")
            raise typer.Exit(1)
        type_key = step_meta.get("type_key", "")
        if not type_key:
            console.print("[red]Error:[/red] step.yml missing 'step.type_key' field")
            raise typer.Exit(1)

        if type_key != step_id:
            console.print(
                f"[red]Error:[/red] step.yml type_key ({type_key!r}) does not match "
                f"catalog ID ({step_id!r})"
            )
            raise typer.Exit(1)

        # Write the two required files.
        try:
            (tmp_path / "step.yml").write_bytes(step_yml_content)
            (tmp_path / "__init__.py").write_bytes(init_py_content)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to write step files to staging directory: {exc}"
            )
            raise typer.Exit(1)

        # Optionally download additional package files declared in the catalog entry
        # (e.g. helper modules). Each entry in ``extra_files`` is a mapping of
        # relative-path → URL. step.yml and __init__.py are ignored here (already
        # written). Paths are validated to stay within the step package directory to
        # prevent path-traversal attacks.
        extra_files = info.get("extra_files")
        if extra_files is not None and not isinstance(extra_files, dict):
            console.print(
                "[yellow]Warning:[/yellow] Catalog entry 'extra_files' is not a mapping; "
                "additional package files will not be downloaded."
            )
            extra_files = {}
        for rel_path, file_url in (extra_files or {}).items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                console.print(
                    "[red]Error:[/red] Catalog entry 'extra_files' contains an "
                    "empty or non-string path key"
                )
                raise typer.Exit(1)
            if rel_path in ("step.yml", "__init__.py"):
                continue  # already written above
            # Reject dot-path segments ('', '.', '..') that would refer to the
            # package directory itself (IsADirectoryError) or escape it.
            rel_parts = Path(rel_path).parts
            if not rel_parts or any(seg in ("", ".", "..") for seg in rel_parts):
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is not a "
                    "valid relative file path"
                )
                raise typer.Exit(1)
            if not isinstance(file_url, str) or not file_url.strip():
                console.print(
                    f"[red]Error:[/red] extra_files entry '{rel_path}' has an "
                    "empty or non-string URL"
                )
                raise typer.Exit(1)
            # Resolve both destination and base to handle any symlinks in tmp_path itself,
            # ensuring the traversal check is robust even on non-canonical paths.
            resolved_base = tmp_path.resolve()
            dest = (tmp_path / rel_path).resolve()
            try:
                dest.relative_to(resolved_base)
            except ValueError:
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is outside "
                    "the step package directory"
                )
                raise typer.Exit(1)
            try:
                file_content = _safe_fetch(file_url)
            except Exception as exc:
                console.print(
                    f"[red]Error:[/red] Failed to download extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file_content)
            except OSError as exc:
                console.print(
                    f"[red]Error:[/red] Failed to write extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)

        # Atomically rename the staging directory to the final location.
        # Both paths are under steps_base_dir (same filesystem), so os.rename()
        # is atomic on POSIX and won't leave a partially-written directory at
        # step_dir on failure.
        try:
            os.rename(tmp_path, step_dir)
        except OSError as exc:
            console.print(f"[red]Error:[/red] Failed to install step '{step_id}': {exc}")
            raise typer.Exit(1)
    finally:
        # Clean up if the rename hasn't moved tmp_path yet (i.e. on any failure).
        shutil.rmtree(tmp_path, ignore_errors=True)

    step_name = info.get("name") or step_id
    step_version = info.get("version") or step_meta.get("version") or "0.0.0"

    # Register in step registry
    registry = StepRegistry(project_root)
    try:
        registry.add(
            step_id,
            {
                "name": step_name,
                "version": step_version,
                "description": info.get("description", step_meta.get("description", "")),
                "author": info.get("author", step_meta.get("author", "")),
                "source": "catalog",
                "catalog_name": info.get("_catalog_name", ""),
                "type_key": type_key,
            },
        )
    except StepValidationError as exc:
        # Roll back the just-installed directory so the system isn't left with
        # an unregistered step package on disk after a registry write failure
        # (e.g. read-only filesystem, permission denied).
        shutil.rmtree(step_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(
        f"[green]✓[/green] Step type '{step_name}' ({step_id}) installed"
    )
    console.print(
        "  Use [cyan]specify workflow step list[/cyan] to verify the installation."
    )


@workflow_step_app.command("remove")
def workflow_step_remove(
    step_id: str = typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    from .workflows.catalog import StepRegistry, StepValidationError

    project_root = _require_specify_project()

    _validate_step_id_or_exit(step_id)

    registry = StepRegistry(project_root)
    in_registry = registry.is_installed(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: even though _validate_step_id_or_exit rejects path
    # separators, ensure that the resolved directory is a single child of
    # steps_base_dir and is not steps_base_dir itself.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    dir_exists = step_dir.exists()

    if not in_registry and not dir_exists:
        console.print(f"[red]Error:[/red] Step type '{step_id}' is not installed")
        raise typer.Exit(1)

    if not in_registry and dir_exists:
        # The registry was likely reset due to corruption.  Warn the user that the
        # directory is being removed even though there is no registry entry, so
        # the orphaned package can be cleaned up and a fresh install attempted.
        console.print(
            f"[yellow]Warning:[/yellow] '{step_id}' has no registry entry "
            "(registry may have been reset). Removing the orphaned directory."
        )

    if dir_exists and not in_registry:
        # No registry write needed; just delete the orphaned directory.
        import shutil
        try:
            shutil.rmtree(step_dir)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
            )
            raise typer.Exit(1)
    elif in_registry:
        # Remove the registry entry, then the directory. If the directory
        # delete fails, restore the registry entry so state stays consistent
        # and a future `step add` isn't blocked by an orphaned directory
        # with no registry entry.
        registry_metadata = registry.get(step_id)
        try:
            registry.remove(step_id)
        except StepValidationError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)
        if dir_exists:
            import shutil
            try:
                shutil.rmtree(step_dir)
            except OSError as exc:
                # Restore the original registry entry verbatim (bypass add()
                # which would overwrite timestamps).
                try:
                    if registry_metadata is not None:
                        registry.data["steps"][step_id] = registry_metadata
                        registry.save()
                except Exception as restore_exc:  # noqa: BLE001
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to restore registry entry "
                        f"for '{step_id}' after directory removal failure: {restore_exc}"
                    )
                console.print(
                    f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
                )
                raise typer.Exit(1)
    console.print(f"[green]✓[/green] Step type '{step_id}' uninstalled")


@workflow_step_app.command("search")
def workflow_step_search(
    query: str | None = typer.Argument(None, help="Search query"),
):
    """Search the step type catalog."""
    from .workflows.catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)

    try:
        results = catalog.search(query=query)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not results:
        if query:
            console.print(f"[yellow]No step types found matching '{query}'.[/yellow]")
        else:
            console.print("[yellow]No step types found in catalog.[/yellow]")
        return

    console.print(f"\n[bold cyan]Step Types ({len(results)}):[/bold cyan]\n")
    for step in results:
        install_note = (
            "" if step.get("_install_allowed", True) else " [dim](discovery only)[/dim]"
        )
        console.print(
            f"  [bold]{step.get('name', step.get('id', '?'))}[/bold]"
            f" ({step.get('id', '?')}) v{step.get('version', '?')}{install_note}"
        )
        desc = step.get("description", "")
        if desc:
            console.print(f"    {desc}")
        console.print()


@workflow_step_app.command("info")
def workflow_step_info(
    step_id: str = typer.Argument(..., help="Step type ID"),
):
    """Show details for a step type."""
    from .workflows import STEP_REGISTRY
    from .workflows.catalog import StepCatalog, StepCatalogError, StepRegistry

    project_root = _require_specify_project()

    registry = StepRegistry(project_root)
    installed_meta = registry.get(step_id)

    # Check if it's a built-in
    builtin_step = STEP_REGISTRY.get(step_id)
    is_builtin = builtin_step is not None and not installed_meta

    if is_builtin:
        console.print(f"\n[bold cyan]{step_id}[/bold cyan] [dim](built-in)[/dim]")
        console.print(f"  Type key: {step_id}")
        console.print("  [green]Built-in step type[/green]")
        return

    if installed_meta:
        console.print(
            f"\n[bold cyan]{installed_meta.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {installed_meta.get('version', '?')}")
        if installed_meta.get("author"):
            console.print(f"  Author:      {installed_meta['author']}")
        if installed_meta.get("description"):
            console.print(f"  Description: {installed_meta['description']}")
        console.print("  [green]Installed[/green]")
        return

    # Try catalog
    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError:
        info = None

    if info:
        console.print(
            f"\n[bold cyan]{info.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("author"):
            console.print(f"  Author:      {info['author']}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        console.print("  [yellow]Not installed[/yellow]")
        console.print(
            f"\n  Install with: [cyan]specify workflow step add {step_id}[/cyan]"
        )
    else:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found")
        raise typer.Exit(1)


@workflow_step_catalog_app.command("list")
def workflow_step_catalog_list():
    """List configured step catalog sources."""
    from .workflows.catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()
    catalog = StepCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Step Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = (
            "[green]install allowed[/green]"
            if cfg["install_allowed"]
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_step_catalog_app.command("add")
def workflow_step_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a step catalog source."""
    from .workflows.catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source added: {url}")


@workflow_step_catalog_app.command("remove")
def workflow_step_catalog_remove(
    index: int = typer.Argument(
        ..., help="Catalog index to remove (from 'step catalog list')"
    ),
):
    """Remove a step catalog source by index."""
    from .workflows.catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source '{removed_name}' removed")


def main():
    # On Windows the default stdout/stderr code page (e.g. cp1252) cannot encode
    # the Rich banner and box-drawing glyphs, so the CLI crashes with
    # UnicodeEncodeError whenever output is not a UTF-8 TTY (piped, redirected to
    # a file, or running under a legacy code page). Force UTF-8 with graceful
    # replacement so output degrades instead of aborting. No-op on POSIX.
    if sys.platform == "win32":
        for _stream in (sys.stdout, sys.stderr):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, OSError):
                pass
    app()

if __name__ == "__main__":
    main()
