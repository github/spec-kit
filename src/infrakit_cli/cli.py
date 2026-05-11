"""Typer-based CLI definition for ``infrakit``.

This module defines the :data:`app` instance and the four user-facing
commands (``init``, ``check``, ``mcp``, ``version``). The actual work for
each command is delegated to the focused helper modules
(:mod:`bootstrap`, :mod:`mcp`, :mod:`skills`, :mod:`git_utils`, etc.) — this
file is just argument parsing and orchestration.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from datetime import datetime
from pathlib import Path

import typer
import yaml
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .agent_config import AGENT_CONFIG
from .banner import BannerGroup, show_banner
from .bootstrap import initialize_iac_config
from .console import console
from .git_utils import init_git_repo, is_git_repo
from .github_api import _github_auth_headers, client
from .iac_config import IAC_CONFIG, get_iac_choices
from .interactive import select_with_arrows
from .mcp import (
    _build_mcp_markdown_block,
    _build_mcp_server_entry,
    _read_mcp_json,
    _update_mcp_use_table,
)
from .mcp_config import MCP_RECIPES
from .skills import ensure_project_context_from_template, install_ai_skills
from .tools import SCRIPT_TYPE_CHOICES, check_tool, find_project_root
from .tracker import StepTracker

app = typer.Typer(
    name="infrakit",
    help="InfraKit — spec-kit for IaC, with a multi-persona pipeline.",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show the banner when no subcommand is provided."""
    from rich.align import Align

    if (
        ctx.invoked_subcommand is None
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        show_banner()
        console.print(
            Align.center("[dim]Run 'infrakit --help' for usage information[/dim]")
        )
        console.print()


@app.command()
def init(
    project_name: str = typer.Argument(
        None,
        help="Name for your new project directory (optional if using --here, or use '.' for current directory)",
    ),
    ai_assistant: str = typer.Option(
        None,
        "--ai",
        help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, shai, q, agy, bob, qodercli, roo, or generic (requires --ai-commands-dir)",
    ),
    ai_commands_dir: str = typer.Option(
        None,
        "--ai-commands-dir",
        help="Directory for agent command files (required with --ai generic, e.g. .myagent/commands/)",
    ),
    iac_tool: str = typer.Option(
        None, "--iac", help="IaC tool to use: crossplane or terraform"
    ),
    script_type: str = typer.Option(
        None, "--script", help="Script type to use: sh or ps"
    ),
    ignore_agent_tools: bool = typer.Option(
        False,
        "--ignore-agent-tools",
        help="Skip checks for AI agent tools like Claude Code",
    ),
    no_git: bool = typer.Option(
        False, "--no-git", help="Skip git repository initialization"
    ),
    here: bool = typer.Option(
        False,
        "--here",
        help="Initialize project in the current directory instead of creating a new one",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force merge/overwrite when using --here (skip confirmation)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show verbose diagnostic output for initialization failures",
    ),
    ai_skills: bool = typer.Option(
        False,
        "--ai-skills",
        help="Install Prompt.MD templates as agent skills (requires --ai)",
    ),
):
    """Initialize a new InfraKit project.

    Templates ship inside the CLI package — ``infrakit init`` runs entirely
    offline and renders the per-agent layout (Claude, Gemini, Copilot, etc.)
    from the bundled prompts.

    This command will:

    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant and IaC tool
    3. Render commands + personas for the selected agent into the project
    4. Initialize a fresh git repository (if not ``--no-git`` and no existing repo)

    Examples::

        infrakit init my-project --ai claude --iac crossplane
        infrakit init my-project --ai claude --iac crossplane --no-git
        infrakit init --here --ai claude --iac crossplane
        infrakit init . --ai claude --iac crossplane
        infrakit init my-project --ai claude --iac terraform
        infrakit init --here --ai claude --iac terraform
        infrakit init my-project --ai generic --ai-commands-dir .myagent/commands/
    """

    show_banner()

    # Catch the parameter-ordering mistake where the next flag's name gets
    # consumed as the previous flag's value.
    if ai_assistant and ai_assistant.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai: '{ai_assistant}'")
        console.print(
            "[yellow]Hint:[/yellow] Did you forget to provide a value for --ai?"
        )
        console.print("[yellow]Example:[/yellow] infrakit init --ai claude --here")
        console.print(
            f"[yellow]Available agents:[/yellow] {', '.join(AGENT_CONFIG.keys())}"
        )
        raise typer.Exit(1)

    if ai_commands_dir and ai_commands_dir.startswith("--"):
        console.print(
            f"[red]Error:[/red] Invalid value for --ai-commands-dir: '{ai_commands_dir}'"
        )
        console.print(
            "[yellow]Hint:[/yellow] Did you forget to provide a value for --ai-commands-dir?"
        )
        console.print(
            "[yellow]Example:[/yellow] infrakit init --ai generic --ai-commands-dir .myagent/commands/"
        )
        raise typer.Exit(1)

    if project_name == ".":
        here = True
        project_name = None  # Clear so existing --here validation logic applies

    if here and project_name:
        console.print(
            "[red]Error:[/red] Cannot specify both project name and --here flag"
        )
        raise typer.Exit(1)

    if not here and not project_name:
        console.print(
            "[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag"
        )
        raise typer.Exit(1)

    if ai_skills and not ai_assistant:
        console.print("[red]Error:[/red] --ai-skills requires --ai to be specified")
        console.print(
            "[yellow]Usage:[/yellow] infrakit init <project> --ai <agent> --ai-skills"
        )
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(
                f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)"
            )
            console.print(
                "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
            )
            if force:
                console.print(
                    "[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]"
                )
            else:
                response = typer.confirm("Do you want to continue?")
                if not response:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        if project_path.exists():
            error_panel = Panel(
                f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                "Please choose a different project name or remove the existing directory.",
                title="[red]Directory Conflict[/red]",
                border_style="red",
                padding=(1, 2),
            )
            console.print()
            console.print(error_panel)
            raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        "[cyan]InfraKit Project Setup[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")
        if not should_init_git:
            console.print(
                "[yellow]Git not found - will skip repository initialization[/yellow]"
            )

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(
                f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}"
            )
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices, "Choose your AI assistant:", "copilot"
        )

    # Validate --ai-commands-dir usage.
    if selected_ai == "generic":
        if not ai_commands_dir:
            console.print(
                "[red]Error:[/red] --ai-commands-dir is required when using --ai generic"
            )
            console.print(
                "[dim]Example: infrakit init my-project --ai generic --ai-commands-dir .myagent/commands/[/dim]"
            )
            raise typer.Exit(1)
    elif ai_commands_dir:
        console.print(
            f"[red]Error:[/red] --ai-commands-dir can only be used with --ai generic (not '{selected_ai}')"
        )
        raise typer.Exit(1)

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(
                f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}"
            )
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(
                SCRIPT_TYPE_CHOICES,
                "Choose script type (or press Enter)",
                default_script,
            )
        else:
            selected_script = default_script

    if iac_tool:
        if iac_tool not in IAC_CONFIG:
            console.print(
                f"[red]Error:[/red] Invalid IaC tool '{iac_tool}'. Choose from: {', '.join(IAC_CONFIG.keys())}"
            )
            raise typer.Exit(1)
        selected_iac = iac_tool
    else:
        iac_choices = get_iac_choices()
        if sys.stdin.isatty():
            selected_iac = select_with_arrows(
                iac_choices, "Choose your IaC tool:", "crossplane"
            )
        else:
            selected_iac = "crossplane"

    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected IaC tool:[/cyan] {selected_iac}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

    tracker = StepTracker("Initialize InfraKit Project")

    sys._infrakit_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("iac-select", "Select IaC tool")
    tracker.complete("iac-select", f"{selected_iac}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    for key, label in [
        ("project_context", "Project Context setup"),
        ("iac-config", "IaC configuration"),
        ("iac-commands", "Render commands & personas"),
    ]:
        tracker.add(key, label)
    if ai_skills:
        tracker.add("ai-skills", "Install agent skills")
    for key, label in [
        ("git", "Initialize git repository"),
        ("final", "Finalize"),
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it survives the redraw.
    git_error_message = None

    with Live(
        tracker.render(), console=console, refresh_per_second=8, transient=True
    ) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            # Templates ship inside the package; no network calls.
            if not here:
                project_path.mkdir(parents=True, exist_ok=True)

            ensure_project_context_from_template(project_path, tracker=tracker)

            # Materialise .infrakit/, .infrakit_tracks/, commands, personas.
            initialize_iac_config(
                project_path, selected_iac, selected_ai, tracker=tracker
            )

            # For the generic agent, rename the rendered .infrakit/commands/
            # to the user-specified path so they can place commands wherever
            # they want.
            if selected_ai == "generic" and ai_commands_dir:
                placeholder_dir = project_path / ".infrakit" / "commands"
                target_dir = project_path / ai_commands_dir
                if placeholder_dir.is_dir() and placeholder_dir != target_dir:
                    target_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(placeholder_dir), str(target_dir))

            if ai_skills:
                skills_ok = install_ai_skills(
                    project_path, selected_ai, tracker=tracker
                )

                # When --ai-skills is used on a NEW project and skills were
                # successfully installed, remove the command files that the
                # template renderer just created. Skills replace commands;
                # keeping both would be confusing. For --here on an existing
                # repo we leave pre-existing commands untouched. We only
                # delete AFTER skills succeed so the project always has at
                # least one of {commands, skills}.
                if skills_ok and not here:
                    agent_cfg = AGENT_CONFIG.get(selected_ai, {})
                    agent_folder = agent_cfg.get("folder", "")
                    if agent_folder:
                        cmds_dir = project_path / agent_folder.rstrip("/") / "commands"
                        if cmds_dir.exists():
                            try:
                                shutil.rmtree(cmds_dir)
                            except OSError:
                                # Best-effort cleanup: skills are installed,
                                # so leaving stale commands is non-fatal.
                                console.print(
                                    "[yellow]Warning: could not remove extracted commands directory[/yellow]"
                                )

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            console.print(
                Panel(
                    f"Initialization failed: {e}", title="Failure", border_style="red"
                )
            )
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [
                    f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]"
                    for k, v in _env_pairs
                ]
                console.print(
                    Panel(
                        "\n".join(env_lines),
                        title="Debug Environment",
                        border_style="magenta",
                    )
                )
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")

    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f'[cyan]git commit -m "Initial commit"[/cyan]',
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(git_error_panel)

    # Agent folder security notice.
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = (
            ai_commands_dir if selected_ai == "generic" else agent_config["folder"]
        )
        if agent_folder:
            security_notice = Panel(
                f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
                f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
                title="[yellow]Agent Folder Security[/yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
            console.print()
            console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(
            f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]"
        )
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # Codex-specific setup step.
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:
            cmd = f"export CODEX_HOME={quoted_path}"

        steps_lines.append(
            f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]"
        )
        step_num += 1

    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    steps_lines.append(
        "   2.1 [cyan]/infrakit:project_context[/] - Establish infrastructure principles"
    )
    steps_lines.append(
        "   2.2 [cyan]/infrakit:new_composition[/] - Create a new resource with multi-agent workflow"
    )
    steps_lines.append(
        "   2.3 [cyan]/infrakit:update_composition[/] - Update an existing resource"
    )
    steps_lines.append(
        "   2.4 [cyan]/infrakit:status[/] - Track progress of all tracks"
    )
    steps_lines.append(
        "   2.5 [cyan]/infrakit:review_composition[/] - Review against best practices"
    )
    steps_lines.append(
        "   2.6 [cyan]/infrakit:validate_composition[/] - Validate generated YAML"
    )

    steps_panel = Panel(
        "\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1, 2)
    )
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "Enhancement commands [bright_black](improve quality & confidence)[/bright_black]",
        "",
        "○ [cyan]/infrakit:clarify[/] [bright_black](optional)[/bright_black] - Clarify ambiguous requirements",
        "○ [cyan]/infrakit:analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency report",
        "○ [cyan]/infrakit:checklist[/] [bright_black](optional)[/bright_black] - Quality validation checklist",
    ]
    enhancements_panel = Panel(
        "\n".join(enhancement_lines),
        title="Enhancement Commands",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print()
    console.print(enhancements_panel)


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
            # IDE-based agent — skip CLI check and mark as optional.
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False

    # VS Code variants are not in agent config; check them separately.
    tracker.add("code", "Visual Studio Code")
    check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]InfraKit CLI is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")


@app.command()
def mcp():
    """Install a pre-defined MCP server recipe into your agent's MCP config."""

    show_banner()

    project_root = find_project_root()
    if project_root is None:
        console.print(
            Panel(
                "No InfraKit project found.\n\n"
                "Run [cyan]infrakit init[/cyan] first, or navigate to an existing project directory.",
                title="[red]Not in an InfraKit Project[/red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        raise typer.Exit(1)

    config_path = project_root / ".infrakit" / "config.yaml"
    try:
        project_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, Exception) as e:
        console.print(f"[red]Error reading .infrakit/config.yaml:[/red] {e}")
        raise typer.Exit(1)

    ai_assistant = project_config.get("ai_assistant")
    if not ai_assistant:
        console.print(
            "[red]Error:[/red] 'ai_assistant' not found in .infrakit/config.yaml"
        )
        raise typer.Exit(1)

    agent_cfg = AGENT_CONFIG.get(ai_assistant, {})
    agent_name = agent_cfg.get("name", ai_assistant)

    console.print(f"[cyan]Agent:[/cyan] {agent_name} [dim]({ai_assistant})[/dim]")
    console.print(f"[cyan]Project:[/cyan] [dim]{project_root}[/dim]\n")

    recipe_choices = {k: v["display_name"] for k, v in MCP_RECIPES.items()}
    selected_key = select_with_arrows(
        recipe_choices, "Choose an MCP recipe to install:"
    )

    mcp_install_path = agent_cfg.get("mcp_install_path")

    tracker = StepTracker(f"Install MCP: {selected_key}")
    tracker.add("resolve", "Resolve config path")
    tracker.add("merge", "Merge MCP entry")
    tracker.add("write", "Write config file")
    tracker.add("index", "Update mcp-use.md index")

    newly_installed = False

    with Live(
        tracker.render(), console=console, refresh_per_second=8, transient=True
    ) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))

        if mcp_install_path:
            # Path A: native JSON config (Claude, Cursor).
            mcp_json_path = project_root / mcp_install_path
            tracker.complete("resolve", str(mcp_json_path.relative_to(project_root)))

            tracker.start("merge")
            existing = _read_mcp_json(mcp_json_path)
            if selected_key in existing["mcpServers"]:
                tracker.skip("merge", f"{selected_key} already installed")
                tracker.skip("write", "no changes needed")
                tracker.skip("index", "no changes needed")
            else:
                existing["mcpServers"][selected_key] = _build_mcp_server_entry(
                    selected_key
                )
                tracker.complete("merge", f"added {selected_key}")

                tracker.start("write")
                try:
                    mcp_json_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(mcp_json_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)
                        f.write("\n")
                    tracker.complete(
                        "write", str(mcp_json_path.relative_to(project_root))
                    )
                    newly_installed = True
                except OSError as e:
                    tracker.error("write", str(e))
                    raise typer.Exit(1)

        else:
            # Path B: markdown fallback (all other agents).
            md_path = project_root / ".infrakit" / "mcp-servers.md"
            tracker.complete("resolve", str(md_path.relative_to(project_root)))

            tracker.start("merge")
            existing_content = (
                md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            )
            if selected_key in existing_content:
                tracker.skip("merge", f"{selected_key} already documented")
                tracker.skip("write", "no changes needed")
                tracker.skip("index", "no changes needed")
            else:
                tracker.complete("merge", "building markdown entry")
                tracker.start("write")
                try:
                    md_block = _build_mcp_markdown_block(
                        selected_key, MCP_RECIPES[selected_key], agent_name
                    )
                    if not md_path.exists():
                        header = (
                            "# MCP Server Setup\n\n"
                            f"> **{agent_name}** does not support a per-project MCP config file.\n"
                            "> Configure these MCP servers manually in your agent's global settings.\n\n"
                        )
                        md_path.write_text(header + md_block, encoding="utf-8")
                    else:
                        with open(md_path, "a", encoding="utf-8") as f:
                            f.write("\n" + md_block)
                    tracker.complete("write", str(md_path.relative_to(project_root)))
                    newly_installed = True
                except OSError as e:
                    tracker.error("write", str(e))
                    raise typer.Exit(1)

        if newly_installed:
            tracker.start("index")
            try:
                _update_mcp_use_table(project_root, selected_key)
                tracker.complete("index", ".infrakit/mcp-use.md")
            except OSError as e:
                tracker.error("index", str(e))

    console.print(tracker.render())

    if newly_installed:
        console.print(
            f"\n[bold green]MCP recipe installed:[/bold green] {selected_key}"
        )
    else:
        console.print(
            f"\n[dim]{selected_key} was already configured — nothing changed.[/dim]"
        )


@app.command()
def version():
    """Display version and system information."""
    import importlib.metadata
    import platform

    show_banner()

    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("infrakit-cli")
    except Exception:
        # Fallback: read from pyproject.toml when running from source.
        try:
            import tomllib

            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    cli_version = data.get("project", {}).get("version", "unknown")
        except Exception:
            pass

    repo_owner = "github"
    repo_name = "infrakit"
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    template_version = "unknown"
    release_date = "unknown"

    try:
        response = client.get(
            api_url,
            timeout=10,
            follow_redirects=True,
            headers=_github_auth_headers(),
        )
        if response.status_code == 200:
            release_data = response.json()
            template_version = release_data.get("tag_name", "unknown")
            if template_version.startswith("v"):
                template_version = template_version[1:]
            release_date = release_data.get("published_at", "unknown")
            if release_date != "unknown":
                try:
                    dt = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
                    release_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
    except Exception:
        pass

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("CLI Version", cli_version)
    info_table.add_row("Template Version", template_version)
    info_table.add_row("Released", release_date)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]InfraKit CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(panel)
    console.print()


def main():
    """Entry point exposed via ``project.scripts`` in pyproject.toml."""
    app()


if __name__ == "__main__":
    main()
