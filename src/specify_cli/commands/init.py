"""specify init command."""
import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

import typer
from rich.panel import Panel
from rich.live import Live

from .._console import console
from .._ui import StepTracker, show_banner
from .._fs import save_init_options
from .._git import _git_service as _git_svc
from .._assets import _asset_service as _svc
from .._helpers import (
    run_command,
    check_tool,
    _install_shared_infra,
    ensure_constitution_from_template,
    ensure_executable_scripts,
    get_speckit_version,
    _parse_integration_options,
    AGENT_CONFIG,
    AI_ASSISTANT_ALIASES,
    AI_ASSISTANT_HELP,
    SCRIPT_TYPE_CHOICES,
)

_BRANCH_NUMBERING_CHOICES = {"sequential", "timestamp"}


def _build_integration_equivalent(
    integration_key: str,
    ai_commands_dir: str | None = None,
) -> str:
    """Build the modern --integration equivalent for legacy --ai usage."""
    parts = [f"--integration {integration_key}"]
    if integration_key == "generic" and ai_commands_dir:
        parts.append(
            f'--integration-options="--commands-dir {shlex.quote(ai_commands_dir)}"'
        )
    return " ".join(parts)


def _build_ai_deprecation_warning(
    integration_key: str,
    ai_commands_dir: str | None = None,
) -> str:
    """Build the legacy --ai deprecation warning message."""
    replacement = _build_integration_equivalent(
        integration_key,
        ai_commands_dir=ai_commands_dir,
    )
    return (
        "[bold]--ai[/bold] is deprecated and will no longer be available in version 0.10.0 or later.\n\n"
        f"Use [bold]{replacement}[/bold] instead."
    )


def register(app: typer.Typer) -> None:
    @app.command()
    def init(
        project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"),
        ai_assistant: str = typer.Option(None, "--ai", help=AI_ASSISTANT_HELP),
        ai_commands_dir: str = typer.Option(None, "--ai-commands-dir", help="Directory for agent command files (required with --ai generic, e.g. .myagent/commands/)"),
        script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
        ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for coding agent tools like Claude Code"),
        no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
        here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
        force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
        skip_tls: bool = typer.Option(False, "--skip-tls", help="Deprecated (no-op). Previously: skip SSL/TLS verification.", hidden=True),
        debug: bool = typer.Option(False, "--debug", help="Deprecated (no-op). Previously: show verbose diagnostic output.", hidden=True),
        github_token: str = typer.Option(None, "--github-token", help="Deprecated (no-op). Previously: GitHub token for API requests.", hidden=True),
        ai_skills: bool = typer.Option(False, "--ai-skills", help="Install Prompt.MD templates as agent skills (requires --ai)"),
        offline: bool = typer.Option(False, "--offline", help="Deprecated (no-op). All scaffolding now uses bundled assets.", hidden=True),
        preset: str = typer.Option(None, "--preset", help="Install a preset during initialization (by preset ID)"),
        branch_numbering: str = typer.Option(None, "--branch-numbering", help="Branch numbering strategy: 'sequential' (001, 002, …, 1000, … — expands past 999 automatically) or 'timestamp' (YYYYMMDD-HHMMSS)"),
        integration: str = typer.Option(None, "--integration", help="Use the new integration system (e.g. --integration copilot). Mutually exclusive with --ai."),
        integration_options: str = typer.Option(None, "--integration-options", help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")'),
    ):
        """
        Initialize a new Specify project.

        By default, project files are downloaded from the latest GitHub release.
        Use --offline to scaffold from assets bundled inside the specify-cli
        package instead (no internet access required, ideal for air-gapped or
        enterprise environments).

        NOTE: Starting with v0.6.0, bundled assets will be used by default and
        the --offline flag will be removed. The GitHub download path will be
        retired because bundled assets eliminate the need for network access,
        avoid proxy/firewall issues, and guarantee that templates always match
        the installed CLI version.

        This command will:
        1. Check that required tools are installed (git is optional)
        2. Let you choose your coding agent integration
        3. Download template from GitHub (or use bundled assets with --offline)
        4. Initialize a fresh git repository (if not --no-git and no existing repo)
        5. Optionally set up coding agent integration commands

        Examples:
            specify init my-project
            specify init my-project --integration claude
            specify init my-project --integration copilot --no-git
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

        show_banner()
        ai_deprecation_warning: str | None = None

        # Detect when option values are likely misinterpreted flags (parameter ordering issue)
        if ai_assistant and ai_assistant.startswith("--"):
            console.print(f"[red]Error:[/red] Invalid value for --ai: '{ai_assistant}'")
            console.print("[yellow]Hint:[/yellow] Did you forget to provide a value for --ai?")
            console.print("[yellow]Example:[/yellow] specify init --integration claude --here")
            console.print(f"[yellow]Available agents:[/yellow] {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)

        if ai_commands_dir and ai_commands_dir.startswith("--"):
            console.print(f"[red]Error:[/red] Invalid value for --ai-commands-dir: '{ai_commands_dir}'")
            console.print("[yellow]Hint:[/yellow] Did you forget to provide a value for --ai-commands-dir?")
            console.print("[yellow]Example:[/yellow] specify init --integration generic --integration-options=\"--commands-dir .myagent/commands/\"")
            raise typer.Exit(1)

        if ai_assistant:
            ai_assistant = AI_ASSISTANT_ALIASES.get(ai_assistant, ai_assistant)

        # --integration and --ai are mutually exclusive
        if integration and ai_assistant:
            console.print("[red]Error:[/red] --integration and --ai are mutually exclusive")
            raise typer.Exit(1)

        # Resolve the integration — either from --integration or --ai
        from ..integrations import INTEGRATION_REGISTRY, get_integration
        if integration:
            resolved_integration = get_integration(integration)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown integration: '{integration}'")
                available = ", ".join(sorted(INTEGRATION_REGISTRY))
                console.print(f"[yellow]Available integrations:[/yellow] {available}")
                raise typer.Exit(1)
            ai_assistant = integration
        elif ai_assistant:
            resolved_integration = get_integration(ai_assistant)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown agent '{ai_assistant}'. Choose from: {', '.join(sorted(INTEGRATION_REGISTRY))}")
                raise typer.Exit(1)
            ai_deprecation_warning = _build_ai_deprecation_warning(
                resolved_integration.key,
                ai_commands_dir=ai_commands_dir,
            )

        # Deprecation warnings for --ai-skills and --ai-commands-dir (only when
        # an integration has been resolved from --ai or --integration)
        if ai_assistant or integration:
            if ai_skills:
                from ..integrations.base import SkillsIntegration as _SkillsCheck
                if isinstance(resolved_integration, _SkillsCheck):
                    console.print(
                        "[dim]Note: --ai-skills is not needed; "
                        "skills are the default for this integration.[/dim]"
                    )
                else:
                    console.print(
                        "[dim]Note: --ai-skills has no effect with "
                        f"{resolved_integration.key}; this integration uses commands, not skills.[/dim]"
                    )
            if ai_commands_dir and resolved_integration.key != "generic":
                console.print(
                    "[dim]Note: --ai-commands-dir is deprecated; "
                    'use [bold]--integration generic --integration-options="--commands-dir <dir>"[/bold] instead.[/dim]'
                )

        if no_git:
            console.print(
                "[yellow]⚠️  --no-git is deprecated and will be removed in v0.10.0.[/yellow]\n"
                "[yellow]The git extension will no longer be enabled by default "
                "— use the [bold]specify extension[/bold] commands to install or enable the git extension if needed.[/yellow]"
            )

        if project_name == ".":
            here = True
            project_name = None  # Clear project_name to use existing validation logic

        if here and project_name:
            console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
            raise typer.Exit(1)

        if not here and not project_name:
            console.print("[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag")
            raise typer.Exit(1)

        if ai_skills and not ai_assistant:
            console.print("[red]Error:[/red] --ai-skills requires --ai to be specified")
            console.print("[yellow]Usage:[/yellow] specify init <project> --ai <agent> --ai-skills")
            raise typer.Exit(1)

        if branch_numbering and branch_numbering not in _BRANCH_NUMBERING_CHOICES:
            console.print(f"[red]Error:[/red] Invalid --branch-numbering value '{branch_numbering}'. Choose from: {', '.join(sorted(_BRANCH_NUMBERING_CHOICES))}")
            raise typer.Exit(1)

        dir_existed_before = False
        if here:
            project_name = Path.cwd().name
            project_path = Path.cwd()
            dir_existed_before = True

            existing_items = list(project_path.iterdir())
            if existing_items:
                console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
                console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
                if force:
                    console.print("[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]")
                else:
                    response = typer.confirm("Do you want to continue?")
                    if not response:
                        console.print("[yellow]Operation cancelled[/yellow]")
                        raise typer.Exit(0)
        else:
            project_path = Path(project_name).resolve()
            dir_existed_before = project_path.exists()
            if project_path.exists():
                if not project_path.is_dir():
                    console.print(f"[red]Error:[/red] '{project_name}' exists but is not a directory.")
                    raise typer.Exit(1)
                existing_items = list(project_path.iterdir())
                if force:
                    if existing_items:
                        console.print(f"[yellow]Warning:[/yellow] Directory '{project_name}' is not empty ({len(existing_items)} items)")
                        console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
                    console.print(f"[cyan]--force supplied: merging into existing directory '[cyan]{project_name}[/cyan]'[/cyan]")
                else:
                    error_panel = Panel(
                        f"Directory already exists: '[cyan]{project_name}[/cyan]'\n"
                        "Please choose a different project name or remove the existing directory.\n"
                        "Use [bold]--force[/bold] to merge into the existing directory.",
                        title="[red]Directory Conflict[/red]",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print()
                    console.print(error_panel)
                    raise typer.Exit(1)

        if ai_assistant:
            if ai_assistant not in AGENT_CONFIG:
                console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
                raise typer.Exit(1)
            selected_ai = ai_assistant
        else:
            # Create options dict for selection (agent_key: display_name)
            ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
            # Access via sys.modules so mock patches on specify_cli.select_with_arrows work.
            import sys as _sys
            _specify_cli = _sys.modules.get("specify_cli")
            _select_fn = getattr(_specify_cli, "select_with_arrows", None) if _specify_cli else None
            if _select_fn is None:
                from .._ui import select_with_arrows as _select_fn
            selected_ai = _select_fn(
                ai_choices,
                "Choose your coding agent integration:",
                "copilot"
            )

        # Auto-promote interactively selected agents to the integration path
        if not ai_assistant:
            resolved_integration = get_integration(selected_ai)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown agent '{selected_ai}'")
                raise typer.Exit(1)

        # Validate --ai-commands-dir usage.
        # Skip validation when --integration-options is provided — the integration
        # will validate its own options in setup().
        if selected_ai == "generic" and not integration_options:
            if not ai_commands_dir:
                console.print("[red]Error:[/red] --ai-commands-dir is required when using --ai generic or --integration generic")
                console.print('[dim]Example: specify init my-project --integration generic --integration-options="--commands-dir .myagent/commands/"[/dim]')
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

        console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

        should_init_git = False
        if not no_git:
            should_init_git = check_tool("git")
            if not should_init_git:
                console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

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
                        padding=(1, 2)
                    )
                    console.print()
                    console.print(error_panel)
                    raise typer.Exit(1)

        if script_type:
            if script_type not in SCRIPT_TYPE_CHOICES:
                console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
                raise typer.Exit(1)
            selected_script = script_type
        else:
            default_script = "ps" if os.name == "nt" else "sh"

            if sys.stdin.isatty():
                from .._ui import select_with_arrows as _select_script_fn
                selected_script = _select_script_fn(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
            else:
                selected_script = default_script

        console.print(f"[cyan]Selected coding agent integration:[/cyan] {selected_ai}")
        console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

        tracker = StepTracker("Initialize Specify Project")

        sys._specify_tracker_active = True

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
            ("git", "Install git extension"),
            ("workflow", "Install bundled workflow"),
            ("final", "Finalize"),
        ]:
            tracker.add(key, label)

        with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            try:
                # Integration-based scaffolding
                from ..integrations.manifest import IntegrationManifest
                tracker.start("integration")
                manifest = IntegrationManifest(
                    resolved_integration.key, project_path, version=get_speckit_version()
                )

                # Forward all legacy CLI flags to the integration as parsed_options.
                # Integrations receive every option and decide what to use;
                # irrelevant keys are simply ignored by the integration's setup().
                integration_parsed_options: dict[str, Any] = {}
                if ai_commands_dir:
                    integration_parsed_options["commands_dir"] = ai_commands_dir
                if ai_skills:
                    integration_parsed_options["skills"] = True
                # Parse --integration-options and merge into parsed_options so
                # flags like --skills reach the integration's setup().
                if integration_options:
                    extra = _parse_integration_options(resolved_integration, integration_options)
                    if extra:
                        integration_parsed_options.update(extra)

                resolved_integration.setup(
                    project_path, manifest,
                    parsed_options=integration_parsed_options or None,
                    script_type=selected_script,
                    raw_options=integration_options,
                )
                manifest.save()

                # Write .specify/integration.json
                integration_json = project_path / ".specify" / "integration.json"
                integration_json.parent.mkdir(parents=True, exist_ok=True)
                integration_json.write_text(json.dumps({
                    "integration": resolved_integration.key,
                    "version": get_speckit_version(),
                }, indent=2) + "\n", encoding="utf-8")

                tracker.complete("integration", resolved_integration.config.get("name", resolved_integration.key))

                # Install shared infrastructure (scripts, templates)
                tracker.start("shared-infra")
                _install_shared_infra(project_path, selected_script, tracker=tracker, force=force, invoke_separator=resolved_integration.effective_invoke_separator(integration_parsed_options))
                tracker.complete("shared-infra", f"scripts ({selected_script}) + templates")

                ensure_constitution_from_template(project_path, tracker=tracker)

                if not no_git:
                    tracker.start("git")
                    git_messages = []
                    git_has_error = False
                    # Step 1: Initialize git repo if needed
                    if _git_svc.is_repo(project_path):
                        git_messages.append("existing repo detected")
                    elif should_init_git:
                        success, error_msg = _git_svc.init_repo(project_path)
                        if success:
                            git_messages.append("initialized")
                        else:
                            git_has_error = True
                            # Sanitize multi-line error_msg to single line for tracker
                            if error_msg:
                                sanitized = error_msg.replace('\n', ' ').strip()
                                git_messages.append(f"init failed: {sanitized[:120]}")
                            else:
                                git_messages.append("init failed")
                    else:
                        git_messages.append("git not available")
                    # Step 2: Install bundled git extension
                    try:
                        from ..extensions import ExtensionManager
                        bundled_path = _svc.locate_bundled_extension("git")
                        if bundled_path:
                            manager = ExtensionManager(project_path)
                            if manager.registry.is_installed("git"):
                                git_messages.append("extension already installed")
                            else:
                                manager.install_from_directory(
                                    bundled_path, get_speckit_version()
                                )
                                git_messages.append("extension installed")
                        else:
                            git_has_error = True
                            git_messages.append("bundled extension not found")
                    except Exception as ext_err:
                        git_has_error = True
                        sanitized_ext = str(ext_err).replace('\n', ' ').strip()
                        git_messages.append(
                            f"extension install failed: {sanitized_ext[:120]}"
                        )
                    summary = "; ".join(git_messages)
                    if git_has_error:
                        tracker.error("git", summary)
                    else:
                        tracker.complete("git", summary)
                else:
                    tracker.skip("git", "--no-git flag")

                # Install bundled speckit workflow
                try:
                    bundled_wf = _svc.locate_bundled_workflow("speckit")
                    if bundled_wf:
                        from ..workflows.catalog import WorkflowRegistry
                        from ..workflows.engine import WorkflowDefinition
                        wf_registry = WorkflowRegistry(project_path)
                        if wf_registry.is_installed("speckit"):
                            tracker.complete("workflow", "already installed")
                        else:
                            dest_wf = project_path / ".specify" / "workflows" / "speckit"
                            dest_wf.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(
                                bundled_wf / "workflow.yml",
                                dest_wf / "workflow.yml",
                            )
                            definition = WorkflowDefinition.from_yaml(dest_wf / "workflow.yml")
                            wf_registry.add("speckit", {
                                "name": definition.name,
                                "version": definition.version,
                                "description": definition.description,
                                "source": "bundled",
                            })
                            tracker.complete("workflow", "speckit installed")
                    else:
                        tracker.skip("workflow", "bundled workflow not found")
                except Exception as wf_err:
                    sanitized_wf = str(wf_err).replace('\n', ' ').strip()
                    tracker.error("workflow", f"install failed: {sanitized_wf[:120]}")

                # Fix permissions after all installs (scripts + extensions)
                ensure_executable_scripts(project_path, tracker=tracker)

                # Persist the CLI options so later operations (e.g. preset add)
                # can adapt their behaviour without re-scanning the filesystem.
                # Must be saved BEFORE preset install so _get_skills_dir() works.
                init_opts = {
                    "ai": selected_ai,
                    "integration": resolved_integration.key,
                    "branch_numbering": branch_numbering or "sequential",
                    "context_file": resolved_integration.context_file,
                    "here": here,
                    "script": selected_script,
                    "speckit_version": get_speckit_version(),
                }
                # Ensure ai_skills is set for SkillsIntegration so downstream
                # tools (extensions, presets) emit SKILL.md overrides correctly.
                # Also set for integrations running in skills mode (e.g. Copilot
                # with --skills).
                from ..integrations.base import SkillsIntegration as _SkillsPersist
                if isinstance(resolved_integration, _SkillsPersist) or getattr(resolved_integration, "_skills_mode", False):
                    init_opts["ai_skills"] = True
                save_init_options(project_path, init_opts)

                # Install preset if specified
                if preset:
                    try:
                        from ..presets import PresetManager, PresetCatalog, PresetError
                        preset_manager = PresetManager(project_path)
                        speckit_ver = get_speckit_version()

                        # Try local directory first, then bundled, then catalog
                        local_path = Path(preset).resolve()
                        if local_path.is_dir() and (local_path / "preset.yml").exists():
                            preset_manager.install_from_directory(local_path, speckit_ver)
                        else:
                            bundled_path = _svc.locate_bundled_preset(preset)
                            if bundled_path:
                                preset_manager.install_from_directory(bundled_path, speckit_ver)
                            else:
                                preset_catalog = PresetCatalog(project_path)
                                pack_info = preset_catalog.get_pack_info(preset)
                                if not pack_info:
                                    console.print(f"[yellow]Warning:[/yellow] Preset '{preset}' not found in catalog. Skipping.")
                                elif pack_info.get("bundled") and not pack_info.get("download_url"):
                                    from ..extensions import REINSTALL_COMMAND
                                    console.print(
                                        f"[yellow]Warning:[/yellow] Preset '{preset}' is bundled with spec-kit "
                                        f"but could not be found in the installed package."
                                    )
                                    console.print(
                                        "This usually means the spec-kit installation is incomplete or corrupted."
                                    )
                                    console.print(f"Try reinstalling: {REINSTALL_COMMAND}")
                                else:
                                    zip_path = None
                                    try:
                                        zip_path = preset_catalog.download_pack(preset)
                                        preset_manager.install_from_zip(zip_path, speckit_ver)
                                    except PresetError as preset_err:
                                        console.print(f"[yellow]Warning:[/yellow] Failed to install preset '{preset}': {preset_err}")
                                    finally:
                                        if zip_path is not None:
                                            # Clean up downloaded ZIP to avoid cache accumulation
                                            try:
                                                zip_path.unlink(missing_ok=True)
                                            except OSError:
                                                # Best-effort cleanup; failure to delete is non-fatal
                                                pass
                    except Exception as preset_err:
                        console.print(f"[yellow]Warning:[/yellow] Failed to install preset: {preset_err}")

                tracker.complete("final", "project ready")
            except (typer.Exit, SystemExit):
                raise
            except Exception as e:
                tracker.error("final", str(e))
                console.print(Panel(f"Initialization failed: {e}", title="Failure", border_style="red"))
                if debug:
                    _env_pairs = [
                        ("Python", sys.version.split()[0]),
                        ("Platform", sys.platform),
                        ("CWD", str(Path.cwd())),
                    ]
                    _label_width = max(len(k) for k, _ in _env_pairs)
                    env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                    console.print(Panel("\n".join(env_lines), title="Debug Environment", border_style="magenta"))
                if not here and project_path.exists() and not dir_existed_before:
                    shutil.rmtree(project_path)
                raise typer.Exit(1)

        console.print(tracker.render())
        console.print("\n[bold green]Project ready.[/bold green]")

        # Agent folder security notice
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config:
            agent_folder = ai_commands_dir if selected_ai == "generic" else agent_config["folder"]
            if agent_folder:
                security_notice = Panel(
                    f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
                    f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
                    title="[yellow]Agent Folder Security[/yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                )
                console.print()
                console.print(security_notice)

        if ai_deprecation_warning:
            deprecation_notice = Panel(
                ai_deprecation_warning,
                title="[bold red]Deprecation Warning[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
            console.print()
            console.print(deprecation_notice)

        steps_lines = []
        if not here:
            steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
            step_num = 2
        else:
            steps_lines.append("1. You're already in the project directory!")
            step_num = 2

        # Determine skill display mode for the next-steps panel.
        # Skills integrations (codex, kimi, agy, trae, cursor-agent) should show skill invocation syntax.
        from ..integrations.base import SkillsIntegration as _SkillsInt
        _is_skills_integration = isinstance(resolved_integration, _SkillsInt) or getattr(resolved_integration, "_skills_mode", False)

        codex_skill_mode = selected_ai == "codex" and (ai_skills or _is_skills_integration)
        claude_skill_mode = selected_ai == "claude" and (ai_skills or _is_skills_integration)
        kimi_skill_mode = selected_ai == "kimi"
        agy_skill_mode = selected_ai == "agy" and _is_skills_integration
        trae_skill_mode = selected_ai == "trae"
        cursor_agent_skill_mode = selected_ai == "cursor-agent" and (ai_skills or _is_skills_integration)
        copilot_skill_mode = selected_ai == "copilot" and _is_skills_integration
        native_skill_mode = codex_skill_mode or claude_skill_mode or kimi_skill_mode or agy_skill_mode or trae_skill_mode or cursor_agent_skill_mode or copilot_skill_mode

        if codex_skill_mode and not ai_skills:
            # Integration path installed skills; show the helpful notice
            steps_lines.append(f"{step_num}. Start Codex in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]")
            step_num += 1
        if claude_skill_mode and not ai_skills:
            steps_lines.append(f"{step_num}. Start Claude in this project directory; spec-kit skills were installed to [cyan].claude/skills[/cyan]")
            step_num += 1
        if cursor_agent_skill_mode and not ai_skills:
            steps_lines.append(f"{step_num}. Start Cursor Agent in this project directory; spec-kit skills were installed to [cyan].cursor/skills[/cyan]")
            step_num += 1
        usage_label = "skills" if native_skill_mode else "slash commands"

        def _display_cmd(name: str) -> str:
            if codex_skill_mode or agy_skill_mode or trae_skill_mode:
                return f"$speckit-{name}"
            if claude_skill_mode:
                return f"/speckit-{name}"
            if kimi_skill_mode:
                return f"/skill:speckit-{name}"
            if cursor_agent_skill_mode or copilot_skill_mode:
                return f"/speckit-{name}"
            return f"/speckit.{name}"

        steps_lines.append(f"{step_num}. Start using {usage_label} with your coding agent:")

        steps_lines.append(f"   {step_num}.1 [cyan]{_display_cmd('constitution')}[/] - Establish project principles")
        steps_lines.append(f"   {step_num}.2 [cyan]{_display_cmd('specify')}[/] - Create baseline specification")
        steps_lines.append(f"   {step_num}.3 [cyan]{_display_cmd('plan')}[/] - Create implementation plan")
        steps_lines.append(f"   {step_num}.4 [cyan]{_display_cmd('tasks')}[/] - Generate actionable tasks")
        steps_lines.append(f"   {step_num}.5 [cyan]{_display_cmd('implement')}[/] - Execute implementation")

        steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1,2))
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
            f"○ [cyan]{_display_cmd('checklist')}[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]{_display_cmd('plan')}[/])"
        ]
        enhancements_title = "Enhancement Skills" if native_skill_mode else "Enhancement Commands"
        enhancements_panel = Panel("\n".join(enhancement_lines), title=enhancements_title, border_style="cyan", padding=(1,2))
        console.print()
        console.print(enhancements_panel)
