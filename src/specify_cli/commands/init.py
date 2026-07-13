"""specify init command."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

import typer
from rich.live import Live
from rich.panel import Panel

from .._agent_config import (
    AGENT_CONFIG,
    DEFAULT_INIT_INTEGRATION,
    SCRIPT_TYPE_CHOICES,
)
from .._assets import (
    _locate_bundled_preset,
    _locate_bundled_workflow,
    get_speckit_version,
)
from .._console import StepTracker, console, select_with_arrows, show_banner
from .._utils import check_tool


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


def ensure_constitution_from_template(
    project_path: Path, tracker: StepTracker | None = None
) -> None:
    """Copy constitution template to memory if it doesn't exist."""
    memory_constitution = project_path / ".specify" / "memory" / "constitution.md"
    template_constitution = (
        project_path / ".specify" / "templates" / "constitution-template.md"
    )

    if memory_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.skip("constitution", "existing file preserved")
        return

    if not template_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", "template not found")
        return

    try:
        memory_constitution.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_constitution, memory_constitution)
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.complete("constitution", "copied from template")
        else:
            console.print("[cyan]Initialized constitution from template[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", str(e))
        else:
            console.print(
                f"[yellow]Warning: Could not initialize constitution: {e}[/yellow]"
            )


def register(app: typer.Typer) -> None:
    @app.command()
    def init(
        project_name: str = typer.Argument(
            None,
            help="Name for your new project directory (optional if using --here, or use '.' for current directory)",
        ),
        script_type: str = typer.Option(
            None, "--script", help="Script type to use: sh or ps"
        ),
        ignore_agent_tools: bool = typer.Option(
            False,
            "--ignore-agent-tools",
            help="Skip checks for coding agent tools like Claude Code",
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
        skip_tls: bool = typer.Option(
            False,
            "--skip-tls",
            help="Deprecated (no-op). Previously: skip SSL/TLS verification.",
            hidden=True,
        ),
        debug: bool = typer.Option(
            False,
            "--debug",
            help="Deprecated. Previously: show verbose diagnostic output; currently only prints additional diagnostic details on failure.",
            hidden=True,
        ),
        github_token: str = typer.Option(
            None,
            "--github-token",
            help="Deprecated (no-op). Previously: GitHub token for API requests.",
            hidden=True,
        ),
        offline: bool = typer.Option(
            False,
            "--offline",
            help="Deprecated (no-op). All scaffolding now uses bundled assets.",
            hidden=True,
        ),
        preset: str = typer.Option(
            None,
            "--preset",
            help="Install a preset during initialization (by preset ID)",
        ),
        integration: str = typer.Option(
            None,
            "--integration",
            help="AI coding agent integration to use (e.g. --integration copilot). See 'specify check' for available integrations.",
        ),
        integration_options: str = typer.Option(
            None,
            "--integration-options",
            help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")',
        ),
    ):
        """
        Initialize a new Specify project.

        Project files are scaffolded from assets bundled inside the specify-cli
        package, so initialization does not need network access and templates
        match the installed CLI version.

        This command will:
        1. Check that required tools are installed
        2. Let you choose your coding agent integration, or default to Copilot
           in non-interactive sessions
        3. Install bundled Spec Kit templates, scripts, workflow, and shared
           project infrastructure
        4. Set up coding agent integration commands and optional presets

        Examples:
            specify init my-project
            specify init my-project --integration claude
            specify init --ignore-agent-tools my-project
            specify init . --integration claude         # Initialize in current directory
            specify init .                     # Initialize in current directory (interactive integration selection)
            specify init --here --integration claude    # Alternative syntax for current directory
            specify init --here --integration codex --integration-options="--skills"
            specify init --here --integration codebuddy
            specify init --here --integration vibe      # Initialize with Mistral Vibe support
            specify init --here
            specify init --here --force  # Skip confirmation when current directory not empty
            specify init my-project --integration claude   # Claude installs skills by default
            specify init --here --integration gemini
            specify init my-project --integration generic --integration-options="--commands-dir .myagent/commands/"  # Bring your own agent; requires --commands-dir
            specify init my-project --integration claude --preset healthcare-compliance  # With preset
        """
        # Lazy imports to avoid circular dependency — __init__.py imports this module
        from .. import (
            _install_shared_infra_or_exit,
            _print_cli_warning,
            ensure_executable_scripts,
            save_init_options,
        )
        from ..integration_runtime import (
            with_integration_setting as _with_integration_setting,
        )
        from ..integrations._commands import (
            _parse_integration_options,
            _write_integration_json,
        )

        show_banner()

        from ..integrations import INTEGRATION_REGISTRY, get_integration

        if integration:
            resolved_integration = get_integration(integration)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown integration: '{integration}'")
                available = ", ".join(sorted(INTEGRATION_REGISTRY))
                console.print(f"[yellow]Available integrations:[/yellow] {available}")
                raise typer.Exit(1)

        if project_name == ".":
            here = True
            project_name = None

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

        dir_existed_before = False
        if here:
            project_name = Path.cwd().name
            project_path = Path.cwd()
            dir_existed_before = True

            existing_items = list(project_path.iterdir())
            if existing_items:
                console.print(
                    f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)"
                )
                if force:
                    # Proceeding: the merge/overwrite warning is accurate here.
                    console.print(
                        "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
                    )
                    console.print(
                        "[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]"
                    )
                else:
                    # Fold the merge risk into the confirmation prompt rather than
                    # printing it unconditionally first: on the EOF/no-input path
                    # below the command exits without changing anything, so a
                    # standalone "will be merged" line would mislead. Interactive
                    # users still see the risk as part of the question.
                    #
                    # Call typer.confirm normally so piped y/n is honored — e.g.
                    # `echo y | specify init --here` keeps reaching the
                    # non-destructive preserve-merge path.
                    try:
                        proceed = typer.confirm(
                            "Template files will be merged with existing content "
                            "and may overwrite existing files. Do you want to continue?"
                        )
                    except (typer.Abort, EOFError):
                        # typer.confirm raises Abort for BOTH an interactive Ctrl+C
                        # and an EOF on closed/empty stdin. Distinguish them: a real
                        # TTY cancellation is a normal exit (0, "cancelled"), while a
                        # missing-input EOF (non-interactive) becomes an actionable
                        # error pointing at --force.
                        if _stdin_is_interactive():
                            console.print("[yellow]Operation cancelled[/yellow]")
                            raise typer.Exit(0) from None
                        console.print(
                            "[red]Error:[/red] Current directory is not empty and no "
                            "confirmation input is available. Re-run with "
                            "[bold]--force[/bold] to merge into it."
                        )
                        raise typer.Exit(1) from None
                    if not proceed:
                        console.print("[yellow]Operation cancelled[/yellow]")
                        raise typer.Exit(0)
        else:
            project_path = Path(project_name).resolve()
            dir_existed_before = project_path.exists()
            if project_path.exists():
                if not project_path.is_dir():
                    console.print(
                        f"[red]Error:[/red] '{project_name}' exists but is not a directory."
                    )
                    raise typer.Exit(1)
                existing_items = list(project_path.iterdir())
                if force:
                    if existing_items:
                        console.print(
                            f"[yellow]Warning:[/yellow] Directory '{project_name}' is not empty ({len(existing_items)} items)"
                        )
                        console.print(
                            "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
                        )
                    console.print(
                        f"[cyan]--force supplied: merging into existing directory '[cyan]{project_name}[/cyan]'[/cyan]"
                    )
                else:
                    error_panel = Panel(
                        f"Directory already exists: '[cyan]{project_name}[/cyan]'\n"
                        "Please choose a different project name or remove the existing directory.\n"
                        "Use [bold]--force[/bold] to merge into the existing directory.",
                        title="[red]Directory Conflict[/red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                    console.print()
                    console.print(error_panel)
                    raise typer.Exit(1)

        if integration:
            if integration not in AGENT_CONFIG:
                console.print(
                    f"[red]Error:[/red] Invalid integration '{integration}'. Choose from: {', '.join(AGENT_CONFIG.keys())}"
                )
                raise typer.Exit(1)
            selected_ai = integration
        elif not _stdin_is_interactive():
            console.print(
                f"[dim]Non-interactive session detected: defaulting to '{DEFAULT_INIT_INTEGRATION}'. "
                "Use --integration to choose a different agent.[/dim]"
            )
            selected_ai = DEFAULT_INIT_INTEGRATION
        else:
            ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
            selected_ai = select_with_arrows(
                ai_choices,
                "Choose your coding agent integration:",
                DEFAULT_INIT_INTEGRATION,
            )

        if not integration:
            resolved_integration = get_integration(selected_ai)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown agent '{selected_ai}'")
                raise typer.Exit(1)

        if selected_ai == "generic" and not integration_options:
            console.print(
                "[red]Error:[/red] --integration generic requires --integration-options with --commands-dir"
            )
            console.print(
                '[dim]Example: specify init my-project --integration generic --integration-options="--commands-dir .myagent/commands/"[/dim]'
            )
            raise typer.Exit(1)

        current_dir = Path.cwd()

        setup_lines = [
            "[cyan]Specify Project Setup[/cyan]",
            "",
            f"{'Project':<15} [green]{project_path.name}[/green]",
            f"{'Working Path':<15} [dim]{current_dir}[/dim]",
        ]

        if not here:
            setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

        console.print(
            Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2))
        )

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

            if _stdin_is_interactive():
                selected_script = select_with_arrows(
                    SCRIPT_TYPE_CHOICES,
                    "Choose script type (or press Enter)",
                    default_script,
                )
            else:
                selected_script = default_script

        console.print(f"[cyan]Selected coding agent integration:[/cyan] {selected_ai}")
        console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

        tracker = StepTracker("Initialize Specify Project")

        tracker.add("precheck", "Check required tools")
        tracker.complete("precheck", "ok")
        tracker.add("ai-select", "Select coding agent integration")
        tracker.complete("ai-select", f"{selected_ai}")
        tracker.add("script-select", "Select script type")
        tracker.complete("script-select", selected_script)

        tracker.add("integration", "Install integration")
        tracker.add("shared-infra", "Install shared infrastructure")

        for key, label in [
            ("chmod", "Ensure scripts executable"),
            ("constitution", "Constitution setup"),
            ("workflow", "Install bundled workflow"),
            ("final", "Finalize"),
        ]:
            tracker.add(key, label)

        # Disable transient mode on Windows: PowerShell 5.1's legacy console
        # hangs when Rich tries to restore cursor state via VT escape sequences.
        _transient = sys.platform != "win32"

        with Live(
            tracker.render(), console=console, refresh_per_second=8, transient=_transient
        ) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            try:
                from ..integrations.manifest import IntegrationManifest

                tracker.start("integration")
                manifest = IntegrationManifest(
                    resolved_integration.key,
                    project_path,
                    version=get_speckit_version(),
                )

                integration_parsed_options: dict[str, Any] = {}
                if integration_options:
                    extra = _parse_integration_options(
                        resolved_integration, integration_options
                    )
                    if extra:
                        integration_parsed_options.update(extra)

                resolved_integration.setup(
                    project_path,
                    manifest,
                    parsed_options=integration_parsed_options or None,
                    script_type=selected_script,
                    raw_options=integration_options,
                )
                manifest.save()

                integration_settings = _with_integration_setting(
                    {},
                    resolved_integration.key,
                    resolved_integration,
                    script_type=selected_script,
                    raw_options=integration_options,
                    parsed_options=integration_parsed_options or None,
                )
                _write_integration_json(
                    project_path,
                    resolved_integration.key,
                    [resolved_integration.key],
                    integration_settings,
                )

                tracker.complete(
                    "integration",
                    resolved_integration.config.get("name", resolved_integration.key),
                )

                tracker.start("shared-infra")
                _install_shared_infra_or_exit(
                    project_path,
                    selected_script,
                    tracker=tracker,
                    force=force,
                    invoke_separator=resolved_integration.effective_invoke_separator(
                        integration_parsed_options
                    ),
                )
                tracker.complete(
                    "shared-infra", f"scripts ({selected_script}) + templates"
                )

                ensure_constitution_from_template(project_path, tracker=tracker)

                try:
                    bundled_wf = _locate_bundled_workflow("speckit")
                    if bundled_wf:
                        from ..workflows.catalog import WorkflowRegistry
                        from ..workflows.engine import WorkflowDefinition

                        wf_registry = WorkflowRegistry(project_path)
                        if wf_registry.is_installed("speckit"):
                            tracker.complete("workflow", "already installed")
                        else:
                            import shutil as _shutil

                            dest_wf = (
                                project_path / ".specify" / "workflows" / "speckit"
                            )
                            dest_wf.mkdir(parents=True, exist_ok=True)
                            _shutil.copy2(
                                bundled_wf / "workflow.yml",
                                dest_wf / "workflow.yml",
                            )
                            definition = WorkflowDefinition.from_yaml(
                                dest_wf / "workflow.yml"
                            )
                            wf_registry.add(
                                "speckit",
                                {
                                    "name": definition.name,
                                    "version": definition.version,
                                    "description": definition.description,
                                    "source": "bundled",
                                },
                            )
                            tracker.complete("workflow", "speckit installed")
                    else:
                        tracker.skip("workflow", "bundled workflow not found")
                except Exception as wf_err:
                    sanitized_wf = str(wf_err).replace("\n", " ").strip()
                    tracker.error("workflow", f"install failed: {sanitized_wf[:120]}")

                init_opts = {
                    "ai": selected_ai,
                    "integration": resolved_integration.key,
                    "here": here,
                    "script": selected_script,
                    "feature_numbering": "sequential",
                    "speckit_version": get_speckit_version(),
                }
                from ..integrations.base import SkillsIntegration as _SkillsPersist

                if isinstance(resolved_integration, _SkillsPersist) or getattr(
                    resolved_integration, "_skills_mode", False
                ):
                    init_opts["ai_skills"] = True
                save_init_options(project_path, init_opts)

                ensure_executable_scripts(project_path, tracker=tracker)

                if preset:
                    try:
                        from ..presets import PresetCatalog, PresetError, PresetManager

                        preset_manager = PresetManager(project_path)
                        speckit_ver = get_speckit_version()

                        local_path = Path(preset).resolve()
                        if local_path.is_dir() and (local_path / "preset.yml").exists():
                            preset_manager.install_from_directory(
                                local_path, speckit_ver
                            )
                        else:
                            bundled_path = _locate_bundled_preset(preset)
                            if bundled_path:
                                preset_manager.install_from_directory(
                                    bundled_path, speckit_ver
                                )
                            else:
                                preset_catalog = PresetCatalog(project_path)
                                pack_info = preset_catalog.get_pack_info(preset)
                                if not pack_info:
                                    console.print(
                                        f"[yellow]Warning:[/yellow] Preset '{preset}' not found in catalog. Skipping."
                                    )
                                elif pack_info.get("bundled") and not pack_info.get(
                                    "download_url"
                                ):
                                    from ..extensions import REINSTALL_COMMAND

                                    console.print(
                                        f"[yellow]Warning:[/yellow] Preset '{preset}' is bundled with spec-kit "
                                        f"but could not be found in the installed package."
                                    )
                                    console.print(
                                        "This usually means the spec-kit installation is incomplete or corrupted."
                                    )
                                    console.print(
                                        f"Try reinstalling: {REINSTALL_COMMAND}"
                                    )
                                else:
                                    zip_path = None
                                    try:
                                        zip_path = preset_catalog.download_pack(preset)
                                        preset_manager.install_from_zip(
                                            zip_path, speckit_ver
                                        )
                                    except PresetError as preset_err:
                                        _print_cli_warning(
                                            "install",
                                            "preset",
                                            preset,
                                            preset_err,
                                            continuing="Continuing without the optional preset.",
                                        )
                                    finally:
                                        if zip_path is not None:
                                            try:
                                                zip_path.unlink(missing_ok=True)
                                            except OSError:
                                                pass
                    except Exception as preset_err:
                        _print_cli_warning(
                            "install",
                            "preset",
                            preset,
                            preset_err,
                            continuing="Continuing without the optional preset.",
                        )

                tracker.complete("final", "project ready")
            except (typer.Exit, SystemExit):
                raise
            except Exception as e:
                tracker.error("final", str(e))
                console.print(
                    Panel(
                        f"Initialization failed: {e}",
                        title="Failure",
                        border_style="red",
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
                if not here and project_path.exists() and not dir_existed_before:
                    shutil.rmtree(project_path)
                raise typer.Exit(1)
            finally:
                pass

        if _transient:
            console.print(tracker.render())
        console.print("\n[bold green]Project ready.[/bold green]")

        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config:
            agent_folder = agent_config["folder"] or integration_parsed_options.get(
                "commands_dir"
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

        from ..integrations.base import SkillsIntegration as _SkillsInt

        _is_skills_integration = isinstance(
            resolved_integration, _SkillsInt
        ) or getattr(resolved_integration, "_skills_mode", False)

        codex_skill_mode = selected_ai == "codex" and _is_skills_integration
        zcode_skill_mode = selected_ai == "zcode" and _is_skills_integration
        claude_skill_mode = selected_ai == "claude" and _is_skills_integration
        kimi_skill_mode = selected_ai == "kimi"
        agy_skill_mode = selected_ai == "agy" and _is_skills_integration
        trae_skill_mode = selected_ai == "trae"
        cursor_agent_skill_mode = (
            selected_ai == "cursor-agent" and _is_skills_integration
        )
        copilot_skill_mode = selected_ai == "copilot" and _is_skills_integration
        devin_skill_mode = selected_ai == "devin"
        zed_skill_mode = selected_ai == "zed" and _is_skills_integration
        cline_skill_mode = selected_ai == "cline"
        native_skill_mode = (
            codex_skill_mode
            or zcode_skill_mode
            or claude_skill_mode
            or kimi_skill_mode
            or agy_skill_mode
            or trae_skill_mode
            or cursor_agent_skill_mode
            or copilot_skill_mode
            or devin_skill_mode
            or zed_skill_mode
        )

        if codex_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Codex in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]"
            )
            step_num += 1
        if zcode_skill_mode:
            steps_lines.append(
                f"{step_num}. Start ZCode in this project directory; spec-kit skills were installed to [cyan].zcode/skills[/cyan]"
            )
            step_num += 1
        if claude_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Claude in this project directory; spec-kit skills were installed to [cyan].claude/skills[/cyan]"
            )
            step_num += 1
        if cursor_agent_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Cursor Agent in this project directory; spec-kit skills were installed to [cyan].cursor/skills[/cyan]"
            )
            step_num += 1
        if devin_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Devin in this project directory; spec-kit skills were installed to [cyan].devin/skills[/cyan]"
            )
            step_num += 1
        if zed_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Zed in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]"
            )
            step_num += 1
        usage_label = "skills" if native_skill_mode else "slash commands"

        from .._invocation_style import (
            is_dollar_skills_agent as _is_dollar_skills_agent,
            is_slash_skills_agent as _is_slash_skills_agent,
        )

        # `_is_skills_integration` means the integration is installed in
        # skills mode, which is the semantic equivalent of `ai_skills_enabled`
        # used by `is_slash_skills_agent()`.
        _ai_skills_enabled = _is_skills_integration

        def _display_cmd(name: str) -> str:
            if _is_dollar_skills_agent(selected_ai, _ai_skills_enabled):
                return f"$speckit-{name}"
            if kimi_skill_mode:
                return f"/skill:speckit-{name}"
            if (
                _is_slash_skills_agent(selected_ai, _ai_skills_enabled)
                or cline_skill_mode
            ):
                return f"/speckit-{name}"
            return f"/speckit.{name}"

        steps_lines.append(
            f"{step_num}. Start using {usage_label} with your coding agent:"
        )

        steps_lines.append(
            f"   {step_num}.1 [cyan]{_display_cmd('constitution')}[/] - Establish project principles"
        )
        steps_lines.append(
            f"   {step_num}.2 [cyan]{_display_cmd('specify')}[/] - Create baseline specification"
        )
        steps_lines.append(
            f"   {step_num}.3 [cyan]{_display_cmd('plan')}[/] - Create implementation plan"
        )
        steps_lines.append(
            f"   {step_num}.4 [cyan]{_display_cmd('tasks')}[/] - Generate actionable tasks"
        )
        steps_lines.append(
            f"   {step_num}.5 [cyan]{_display_cmd('implement')}[/] - Execute implementation"
        )
        steps_lines.append(
            f"   {step_num}.6 [cyan]{_display_cmd('converge')}[/] - Assess the codebase and append remaining work as tasks"
        )

        steps_panel = Panel(
            "\n".join(steps_lines),
            title="Next Steps",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print()
        console.print(steps_panel)

        enhancement_intro = (
            "Optional skills that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]"
            if native_skill_mode
            else "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]"
        )
        enhancement_lines = [
            enhancement_intro,
            "",
            f"○ [cyan]{_display_cmd('clarify')}[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]{_display_cmd('plan')}[/] if used)",
            f"○ [cyan]{_display_cmd('analyze')}[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]{_display_cmd('tasks')}[/], before [cyan]{_display_cmd('implement')}[/])",
            f"○ [cyan]{_display_cmd('checklist')}[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]{_display_cmd('plan')}[/])",
        ]
        enhancements_title = (
            "Enhancement Skills" if native_skill_mode else "Enhancement Commands"
        )
        enhancements_panel = Panel(
            "\n".join(enhancement_lines),
            title=enhancements_title,
            border_style="cyan",
            padding=(1, 2),
        )
        console.print()
        console.print(enhancements_panel)
