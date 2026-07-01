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

import os
import sys
import json
from pathlib import Path

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
    _locate_bundled_extension as _locate_bundled_extension,
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
# Skills directory helpers
# ---------------------------------------------------------------------------

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

# Moved to extensions/_commands.py — registered here to preserve CLI surface.
from .extensions._commands import register as _register_extension_cmds  # noqa: E402
_register_extension_cmds(app)


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


# ===== Bundle Commands =====

# Bundler subcommand group (specify bundle ...) — see commands/bundle/.
from .commands.bundle import register as _register_bundle_cmds  # noqa: E402
_register_bundle_cmds(app)


# ===== Workflow Commands =====

# Moved to workflows/_commands.py — registered here to preserve CLI surface.
from .workflows._commands import register as _register_workflow_cmds  # noqa: E402
_register_workflow_cmds(app)

# Re-exported at the package root because bundler primitives import these
# handlers via ``from specify_cli import workflow_*`` (and tests monkeypatch
# ``specify_cli.workflow_add``). Keep these names resolvable from the root.
from .workflows._commands import (  # noqa: E402,F401
    workflow_add,
    workflow_remove,
    workflow_step_add,
    workflow_step_remove,
)

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
