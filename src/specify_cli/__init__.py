#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
Specify CLI - Setup tool for Specify projects
"""

import importlib.metadata
import os
import platform
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Import from refactored modules
from .cli import BannerGroup, show_banner
from .core import (
    _format_rate_limit_error,
    _github_auth_headers,
    init_git_repo,
    is_git_repo,
)
from .core.github import ssl_context
from .utils import (
    AGENT_CONFIG,
    BANNER,
    CLAUDE_LOCAL_PATH,
    SCRIPT_TYPE_CHOICES,
    TAGLINE,
    StepTracker,
    check_tool,
    download_and_extract_template,
    ensure_executable_scripts,
    get_key,
    run_command,
    select_with_arrows,
)

console = Console()

# Create global httpx client
client = httpx.Client(verify=ssl_context)

# Create the main Typer app
app = typer.Typer(
    name="specify",
    help="Setup tool for Specify spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        from rich.align import Align

        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
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
        help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, shai, q, bob, or qoder ",
    ),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    github_token: str = typer.Option(
        None,
        "--github-token",
        help="GitHub token to use for API requests (or set GH_TOKEN or GITHUB_TOKEN environment variable)",
    ),
):
    """
    Initialize a new Specify project from the latest template.

    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant
    3. Download the appropriate template from GitHub
    4. Extract the template to a new project directory or current directory
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    6. Optionally set up AI assistant commands

    Examples:
        specify init my-project
        specify init my-project --ai claude
        specify init my-project --ai copilot --no-git
        specify init --ignore-agent-tools my-project
        specify init . --ai claude         # Initialize in current directory
        specify init .                     # Initialize in current directory (interactive AI selection)
        specify init --here --ai claude    # Alternative syntax for current directory
        specify init --here --ai codex
        specify init --here --ai codebuddy
        specify init --here
        specify init --here --force  # Skip confirmation when current directory not empty
    """

    show_banner()

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag")
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

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

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(ai_choices, "Choose your AI assistant:", "copilot")

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
            console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            selected_script = default_script

    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

    tracker = StepTracker("Initialize Specify Project")

    sys._specify_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize"),
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(
                project_path,
                selected_ai,
                selected_script,
                here,
                verbose=False,
                tracker=tracker,
                client=local_client,
                debug=debug,
                github_token=github_token,
            )

            ensure_executable_scripts(project_path, tracker=tracker)

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
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")

    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f"[cyan]git commit -m \"Initial commit\"[/cyan]",
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        security_notice = Panel(
            f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
            title="[yellow]Agent Folder Security[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print()
        console.print(security_notice)

    import shlex

    steps_lines = []
    if not here:
        steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"

        steps_lines.append(f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]")
        step_num += 1

    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    steps_lines.append("   2.1 [cyan]/speckit.constitution[/] - Establish project principles")
    steps_lines.append("   2.2 [cyan]/speckit.specify[/] - Create baseline specification")
    steps_lines.append("   2.3 [cyan]/speckit.plan[/] - Create implementation plan")
    steps_lines.append("   2.4 [cyan]/speckit.tasks[/] - Generate actionable tasks")
    steps_lines.append("   2.5 [cyan]/speckit.implement[/] - Execute implementation")

    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]",
        "",
        f"○ [cyan]/speckit.clarify[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]/speckit.plan[/] if used)",
        f"○ [cyan]/speckit.analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]/speckit.tasks[/], before [cyan]/speckit.implement[/])",
        f"○ [cyan]/speckit.checklist[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]/speckit.plan[/])",
    ]
    enhancements_panel = Panel("\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(enhancements_panel)


@app.command()
def check():
    """Check that required tools are installed."""
    show_banner()

    tracker = StepTracker("Tool Verification")

    tools_to_check = ["git"] + list(AGENT_CONFIG.keys())

    for tool in tools_to_check:
        label = AGENT_CONFIG.get(tool, {}).get("name", tool)
        tracker.add(tool, label)

    with Live(tracker.render(), console=console, refresh_per_second=4, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))

        for tool in tools_to_check:
            check_tool(tool, tracker)

    console.print(tracker.render())
    console.print()

    # Summary
    available_tools = [tool for tool in tools_to_check if check_tool(tool)]
    unavailable_tools = [tool for tool in tools_to_check if not check_tool(tool)]

    summary_lines = [f"Available: {len(available_tools)}/{len(tools_to_check)}", ""]

    if available_tools:
        summary_lines.append("[green]Available:[/green]")
        for tool in available_tools:
            label = AGENT_CONFIG.get(tool, {}).get("name", tool)
            summary_lines.append(f"  [green]●[/green] {label}")

    if unavailable_tools:
        summary_lines.append("")
        summary_lines.append("[yellow]Not Available:[/yellow]")
        for tool in unavailable_tools:
            label = AGENT_CONFIG.get(tool, {}).get("name", tool)
            config = AGENT_CONFIG.get(tool, {})
            install_info = ""
            if config.get("install_url"):
                install_info = f" - Install: {config['install_url']}"
            summary_lines.append(f"  [yellow]○[/yellow] {label}{install_info}")

    summary_panel = Panel("\n".join(summary_lines), title="Tool Check Summary", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(summary_panel)


# =============================================================================
# Process Mining Commands
# =============================================================================

pm_app = typer.Typer(
    name="pm",
    help="Process mining commands using pm4py",
    add_completion=False,
)
app.add_typer(pm_app, name="pm")


def _load_event_log(file_path: Path, case_id: str = "case:concept:name", activity: str = "concept:name", timestamp: str = "time:timestamp"):
    """Load event log from CSV/XES file."""
    try:
        import pm4py

        if file_path.suffix.lower() == ".xes":
            return pm4py.read_xes(str(file_path))
        elif file_path.suffix.lower() == ".csv":
            df = pm4py.read_csv(str(file_path))
            return pm4py.convert_to_event_log(df, case_id=case_id, activity_key=activity, timestamp_key=timestamp)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    except ImportError:
        raise RuntimeError("pm4py is not installed. Install it with: pip install pm4py")


def _save_model(model, output_path: Path, model_type: str = "petri"):
    """Save a model to file."""
    try:
        import pm4py

        if model_type == "petri" and hasattr(model, "__iter__") and len(model) == 3:
            net, im, fm = model
            pm4py.write_petri_net(net, str(output_path), im, fm)
        elif model_type == "process_tree":
            pm4py.write_process_tree(model, str(output_path))
        elif hasattr(model, "to_file"):
            model.to_file(str(output_path))
        else:
            raise ValueError(f"Cannot save model of type {type(model)}")
    except ImportError:
        raise RuntimeError("pm4py is not installed. Install it with: pip install pm4py")


@pm_app.command("discover")
def pm_discover(
    input_file: Path = typer.Argument(..., help="Input event log file (CSV or XES)"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output file for discovered model (default: input_name_model.pnml)"),
    model_type: str = typer.Option("petri", "--type", "-t", help="Model type: petri or tree"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Discover a process model from an event log using the Inductive Miner."""
    try:
        import pm4py

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading event log from:[/cyan] {input_file}")
        event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)

        console.print(f"[cyan]Event log loaded:[/cyan] {len(event_log)} cases, {len(event_log.get_events())} events")

        tracker = StepTracker("Process Discovery")
        tracker.add("discover", "Discover model using Inductive Miner")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            tracker.start("discover")

            if model_type == "tree":
                model = pm4py.discover_process_tree_inductive(event_log)
            else:
                model = pm4py.discover_petri_net_inductive(event_log)

            tracker.complete("discover", f"{model_type} net discovered")

            if output_file is None:
                output_file = input_file.parent / f"{input_file.stem}_model.pnml"

            tracker.add("save", "Save model to file")
            tracker.start("save")

            _save_model(model, output_file, model_type)
            tracker.complete("save", str(output_file))

        console.print(tracker.render())
        console.print(f"\n[bold green]Model discovered and saved to:[/bold green] [cyan]{output_file}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("conform")
def pm_conform(
    input_file: Path = typer.Argument(..., help="Input event log file (CSV or XES)"),
    model_file: Path = typer.Argument(..., help="Process model file (PNML)"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Check log conformance against a process model."""
    try:
        import pm4py

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        if not model_file.exists():
            console.print(f"[red]Error:[/red] Model file not found: {model_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading event log:[/cyan] {input_file}")
        event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)

        console.print(f"[cyan]Loading model:[/cyan] {model_file}")
        net, im, fm = pm4py.read_petri_net(str(model_file))

        tracker = StepTracker("Conformance Checking")
        tracker.add("conformance", "Check conformance")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            tracker.start("conformance")

            fitness = pm4py.fitness_petri_net_token_based_replay(event_log, net, im, fm)
            precision = pm4py.precision_petri_net(event_log, net, im, fm)

            tracker.complete("conformance", f"fitness={fitness:.2%}, precision={precision:.2%}")

        console.print(tracker.render())
        console.print()

        # Show results
        result_table = Table(title="Conformance Results", show_header=True, header_style="bold cyan")
        result_table.add_column("Metric", style="cyan")
        result_table.add_column("Value", style="white")

        result_table.add_row("Fitness", f"{fitness:.2%}")
        result_table.add_row("Precision", f"{precision:.2%}")

        console.print(result_table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("stats")
def pm_stats(
    input_file: Path = typer.Argument(..., help="Input event log file (CSV or XES)"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Analyze event log statistics."""
    try:
        import pm4py
        import statistics

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading event log:[/cyan] {input_file}")
        event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)

        tracker = StepTracker("Event Log Analysis")
        tracker.add("stats", "Calculate statistics")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            tracker.start("stats")

            # Compute stats
            cases_count = len(event_log)
            events_count = sum(len(case) for case in event_log)

            trace_lengths = [len(case) for case in event_log]
            min_trace = min(trace_lengths)
            max_trace = max(trace_lengths)
            avg_trace = statistics.mean(trace_lengths)

            activities = set()
            for case in event_log:
                for event in case:
                    if activity in event:
                        activities.add(event[activity])

            tracker.complete("stats", f"{cases_count} cases, {events_count} events")

        console.print(tracker.render())
        console.print()

        # Show results
        stats_table = Table(title="Event Log Statistics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Total Cases", str(cases_count))
        stats_table.add_row("Total Events", str(events_count))
        stats_table.add_row("Unique Activities", str(len(activities)))
        stats_table.add_row("Min Trace Length", str(min_trace))
        stats_table.add_row("Max Trace Length", str(max_trace))
        stats_table.add_row("Avg Trace Length", f"{avg_trace:.2f}")

        console.print(stats_table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("convert")
def pm_convert(
    input_file: Path = typer.Argument(..., help="Input file (CSV, XES, or PNML)"),
    output_file: Path = typer.Argument(..., help="Output file (CSV, XES, or PNML)"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Convert between event log and model formats."""
    try:
        import pm4py

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading:[/cyan] {input_file}")

        tracker = StepTracker("Format Conversion")
        tracker.add("load", "Load file")
        tracker.add("convert", "Convert format")
        tracker.add("save", "Save file")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))

            tracker.start("load")
            if input_file.suffix.lower() == ".pnml":
                net, im, fm = pm4py.read_petri_net(str(input_file))
                tracker.complete("load", "Petri net")
            else:
                event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)
                tracker.complete("load", f"Event log ({input_file.suffix})")

            tracker.start("convert")
            out_suffix = output_file.suffix.lower()

            if out_suffix == ".pnml":
                if input_file.suffix.lower() != ".pnml":
                    net, im, fm = pm4py.discover_petri_net_inductive(event_log)
                    tracker.complete("convert", "Petri net model")
            elif out_suffix in [".csv", ".xes"]:
                if input_file.suffix.lower() == ".pnml":
                    tracker.error("convert", "cannot convert model to log")
                    raise RuntimeError("Cannot convert Petri net model to event log")
                tracker.complete("convert", out_suffix)
            else:
                tracker.error("convert", f"unsupported format: {out_suffix}")
                raise typer.Exit(1)

            tracker.start("save")
            if out_suffix == ".csv" and "event_log" in locals():
                pm4py.write_csv(event_log, str(output_file))
            elif out_suffix == ".xes" and "event_log" in locals():
                pm4py.write_xes(event_log, str(output_file))
            elif out_suffix == ".pnml" and "net" in locals():
                pm4py.write_petri_net(net, str(output_file), im, fm)
            else:
                tracker.error("save", f"unsupported format: {out_suffix}")
                raise typer.Exit(1)
            tracker.complete("save", output_file.name)

        console.print(tracker.render())
        console.print(f"\n[bold green]Conversion complete.[/bold green]")
        console.print(f"Output: [cyan]{output_file}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("visualize")
def pm_visualize(
    input_file: Path = typer.Argument(..., help="Input file (event log CSV/XES or model PNML)"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output image file (PNG, SVG, etc.)"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Visualize a process model or event log."""
    try:
        import pm4py

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading:[/cyan] {input_file}")

        tracker = StepTracker("Visualization")
        tracker.add("load", "Load file")
        tracker.add("visualize", "Generate visualization")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))

            tracker.start("load")
            if input_file.suffix.lower() == ".pnml":
                net, im, fm = pm4py.read_petri_net(str(input_file))
                tracker.complete("load", "Petri net")

                tracker.start("visualize")
                gviz = pm4py.vis_petri_net(net, im, fm)
                tracker.complete("visualize", "Petri net diagram")
            else:
                event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)
                tracker.complete("load", f"Event log ({input_file.suffix})")

                tracker.start("visualize")
                process_tree = pm4py.discover_process_tree_inductive(event_log)
                gviz = pm4py.vis_process_tree(process_tree)
                tracker.complete("visualize", "Process tree diagram")

            if output_file is None:
                output_file = input_file.parent / f"{input_file.stem}_viz"

            gviz.render(str(output_file), format="png", cleanup=True)

        console.print(tracker.render())
        console.print(f"\n[bold green]Visualization saved:[/bold green] [cyan]{output_file}.png[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("filter")
def pm_filter(
    input_file: Path = typer.Argument(..., help="Input event log file (CSV or XES)"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output file (default: input_name_filtered.csv)"),
    min_support: float = typer.Option(0.1, "--min-support", "-s", help="Minimum support threshold (0.0-1.0)"),
    max_duration: int = typer.Option(None, "--max-duration", "-d", help="Maximum trace duration in seconds"),
    case_id: str = typer.Option("case:concept:name", "--case-id", help="Column name for case ID"),
    activity: str = typer.Option("concept:name", "--activity", help="Column name for activity"),
    timestamp: str = typer.Option("time:timestamp", "--timestamp", help="Column name for timestamp"),
):
    """Filter an event log by support and other criteria."""
    try:
        import pm4py

        if not input_file.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading event log:[/cyan] {input_file}")
        event_log = _load_event_log(input_file, case_id=case_id, activity=activity, timestamp=timestamp)

        tracker = StepTracker("Event Log Filtering")
        tracker.add("filter", "Filter event log")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))

            tracker.start("filter")

            # Apply filtering
            if min_support > 0:
                filtered_log = pm4py.filter_log_events_percentage(event_log, min_support)
            else:
                filtered_log = event_log

            original_size = len(event_log)
            filtered_size = len(filtered_log)

            tracker.complete("filter", f"reduced to {filtered_size}/{original_size} cases")

            if output_file is None:
                output_file = input_file.parent / f"{input_file.stem}_filtered.csv"

            tracker.add("save", "Save filtered log")
            tracker.start("save")

            pm4py.write_csv(filtered_log, str(output_file))
            tracker.complete("save", output_file.name)

        console.print(tracker.render())
        console.print(f"\n[bold green]Filtering complete.[/bold green]")
        console.print(f"Original cases: {original_size}, Filtered cases: {filtered_size}")
        console.print(f"Output: [cyan]{output_file}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@pm_app.command("sample")
def pm_sample(
    output_file: Path = typer.Argument(..., help="Output event log file (CSV or XES)"),
    cases: int = typer.Option(100, "--cases", "-c", help="Number of cases to generate"),
    activities: int = typer.Option(5, "--activities", "-a", help="Number of activities"),
    min_trace_length: int = typer.Option(3, "--min-trace", help="Minimum events per trace"),
    max_trace_length: int = typer.Option(10, "--max-trace", help="Maximum events per trace"),
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducibility"),
):
    """Generate a sample event log for testing."""
    try:
        import pm4py
        import random
        from datetime import datetime, timedelta

        if output_file.exists():
            console.print(f"[yellow]Warning:[/yellow] Output file exists, will overwrite: {output_file}")

        tracker = StepTracker("Sample Log Generation")
        tracker.add("generate", "Generate sample log")
        tracker.add("save", "Save to file")

        with Live(tracker.render(), console=console, refresh_per_second=2, transient=True) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))

            tracker.start("generate")

            if seed is not None:
                random.seed(seed)

            event_log = []
            activity_names = [f"Activity_{i+1}" for i in range(activities)]
            start_date = datetime(2024, 1, 1)

            total_events = 0
            for case_id in range(cases):
                trace_length = random.randint(min_trace_length, max_trace_length)
                current_time = start_date + timedelta(days=case_id)

                for event_idx in range(trace_length):
                    event = {
                        "case:concept:name": f"Case_{case_id+1:05d}",
                        "concept:name": random.choice(activity_names),
                        "time:timestamp": current_time.isoformat(),
                    }
                    event_log.append(event)
                    current_time += timedelta(hours=random.randint(1, 8))
                    total_events += 1

            tracker.complete("generate", f"generated {total_events} events")

            tracker.add("save", "Save to file")
            tracker.start("save")

            out_suffix = output_file.suffix.lower()
            if out_suffix == ".csv":
                import csv

                with open(output_file, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["case:concept:name", "concept:name", "time:timestamp"])
                    writer.writeheader()
                    writer.writerows(event_log)
            elif out_suffix == ".xes":
                # For XES, we need to create a proper log object
                import pandas as pd

                df = pd.DataFrame(event_log)
                xes_log = pm4py.convert_to_event_log(df)
                pm4py.write_xes(xes_log, str(output_file))
            else:
                tracker.error("save", f"unsupported format: {out_suffix}")
                raise typer.Exit(1)
            tracker.complete("save", output_file.name)

        console.print(tracker.render())
        console.print(f"\n[bold green]Sample log generated.[/bold green]")
        console.print(f"Output: [cyan]{output_file}[/cyan]")

        # Show summary
        summary_table = Table(title="Generated Log Summary", show_header=True, header_style="bold cyan")
        summary_table.add_column("Parameter", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Cases", str(cases))
        summary_table.add_row("Events", str(total_events))
        summary_table.add_row("Activities", str(activities))
        summary_table.add_row("Trace Length", f"{min_trace_length}-{max_trace_length}")
        if seed is not None:
            summary_table.add_row("Seed", str(seed))

        console.print()
        console.print(summary_table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# End Process Mining Commands
# =============================================================================


@app.command()
def version():
    """Display version and system information."""
    show_banner()

    # Get CLI version from package metadata
    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("specify-cli")
    except Exception:
        # Fallback: try reading from pyproject.toml if running from source
        try:
            import tomllib

            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    cli_version = data.get("project", {}).get("version", "unknown")
        except Exception:
            pass

    # Fetch latest template release version
    repo_owner = "github"
    repo_name = "spec-kit"
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
            # Remove 'v' prefix if present
            if template_version.startswith("v"):
                template_version = template_version[1:]
            release_date = release_data.get("published_at", "unknown")
            if release_date != "unknown":
                # Format the date nicely
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
        title="[bold cyan]Specify CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(panel)
    console.print()


def main():
    app()


if __name__ == "__main__":
    main()
