#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich>=13.0.0",
#     "platformdirs",
#     "readchar",
#     "httpx",
#     "click>=8.0.0",
#     "colorama>=0.4.6",
#     "pyyaml>=6.0.0",
#     "requests>=2.28.0",
#     "python-frontmatter>=1.0.0",
#     "tomli>=1.2.0; python_version<'3.11'",
#     "toml>=0.10.2",
#     "rich-click>=1.7.0",
#     "watchdog>=3.0.0",
#     "GitPython>=3.1.0",
# ]
# ///
"""
Specify CLI - Setup tool for Specify projects

Usage:
    uvx specify-cli.py init <project-name>
    uvx specify-cli.py init --here

Or install globally:
    uv tool install --from specify-cli.py specify-cli
    specify init <project-name>
    specify init --here
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# APM imports
from apm_cli.cli import init as apm_init, install as apm_install, compile as apm_compile, prune as apm_prune, uninstall as apm_uninstall
from apm_cli.commands.deps import deps as apm_deps
import click
from click.testing import CliRunner

# For cross-platform keyboard input
import readchar
import ssl
import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)

# Constants
AI_CHOICES = {
    "copilot": "GitHub Copilot",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "cursor": "Cursor"
}
# Add script type choices
SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

# Claude CLI local installation path after migrate-installer
CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

# ASCII Art Banner
BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝  
███████║██║     ███████╗╚██████╗██║██║        ██║   
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝   
"""

TAGLINE = "Spec-Driven Development Toolkit"
class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return
        # If not present, add it
        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[bold cyan]{self.title}[/bold cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            # Circles (unchanged styling)
            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree



MINI_BANNER = """
╔═╗╔═╗╔═╗╔═╗╦╔═╗╦ ╦
╚═╗╠═╝║╣ ║  ║╠╣ ╚╦╝
╚═╝╩  ╚═╝╚═╝╩╚   ╩ 
"""

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()
    
    # Arrow keys
    if key == readchar.key.UP:
        return 'up'
    if key == readchar.key.DOWN:
        return 'down'
    
    # Enter/Return
    if key == readchar.key.ENTER:
        return 'enter'
    
    # Escape
    if key == readchar.key.ESC:
        return 'escape'
        
    # Ctrl+C
    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key



def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.
    
    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with
        
    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0
    
    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")
        
        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[bright_cyan]{key}: {options[key]}[/bright_cyan]")
            else:
                table.add_row(" ", f"[white]{key}: {options[key]}[/white]")
        
        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")
        
        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)
                    
                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    # Suppress explicit selection print; tracker / later logic will report consolidated status
    return selected_key



console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""
    
    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="specify",
    help="Setup tool for Specify spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

@click.group()
def apm_click():
    """APM - Agent Package Manager commands"""
    pass

# Add APM commands to the Click group
apm_click.add_command(apm_init, name="init")
apm_click.add_command(apm_install, name="install") 
apm_click.add_command(apm_uninstall, name="uninstall")
apm_click.add_command(apm_compile, name="compile")
apm_click.add_command(apm_prune, name="prune")
apm_click.add_command(apm_deps, name="deps")


# Create APM subcommands as Typer commands
apm_app = typer.Typer(
    name="apm",
    help="APM - Agent Package Manager commands for context management.",
    add_completion=False,
)

@apm_app.command("init", context_settings={"allow_extra_args": True, "allow_interspersed_args": False})
def apm_init_wrapper(
    ctx: typer.Context,
    project_name: str = typer.Argument(None, help="Project name"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing files without confirmation"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip interactive questionnaire and use defaults"),
):
    """Initialize a new APM project"""
    args = []
    if project_name:
        args.append(project_name)
    if force:
        args.append("--force")
    if yes:
        args.append("--yes")
    if ctx.args:
        args.extend(ctx.args)
    
    _run_apm_command(["init"] + args)

@apm_app.command("install", context_settings={"allow_extra_args": True, "allow_interspersed_args": False}) 
def apm_install_wrapper(
    ctx: typer.Context,
    packages: list[str] = typer.Argument(None, help="APM packages to add and install (owner/repo format)"),
    runtime: str = typer.Option(None, "--runtime", help="Target specific runtime only (codex, vscode)"),
    exclude: str = typer.Option(None, "--exclude", help="Exclude specific runtime from installation"),
    only: str = typer.Option(None, "--only", help="Install only specific dependency type (apm or mcp)"),
    update: bool = typer.Option(False, "--update", help="Update dependencies to latest Git references"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be installed without installing"),
):
    """Install APM and MCP dependencies from apm.yml. 
    
    Examples:
        specify apm install                             # Install existing deps from apm.yml
        specify apm install github/design-guidelines   # Add package and install
        specify apm install org/pkg1 org/pkg2          # Add multiple packages and install
    """
    args = []
    
    # Add package arguments first
    if packages:
        args.extend(packages)
    
    if runtime:
        args.extend(["--runtime", runtime])
    if exclude:
        args.extend(["--exclude", exclude])
    if only:
        args.extend(["--only", only])
    if update:
        args.append("--update")
    if dry_run:
        args.append("--dry-run")
    if ctx.args:
        args.extend(ctx.args)
    
    _run_apm_command(["install"] + args)

@apm_app.command("compile", context_settings={"allow_extra_args": True, "allow_interspersed_args": False})
def apm_compile_wrapper(
    ctx: typer.Context,
    output: str = typer.Option(None, "-o", "--output", help="Output file path (for single-file mode)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="🔍 Preview compilation without writing files (shows placement decisions)"),
    no_links: bool = typer.Option(False, "--no-links", help="Skip markdown link resolution"),
    chatmode: str = typer.Option(None, "--chatmode", help="Chatmode to prepend to AGENTS.md files"),
    watch: bool = typer.Option(False, "--watch", help="Auto-regenerate on changes"),
    validate: bool = typer.Option(False, "--validate", help="Validate primitives without compiling"),
    with_constitution: bool = typer.Option(True, "--with-constitution/--no-constitution", help="Include Spec Kit constitution block at top if memory/constitution.md present"),
    single_agents: bool = typer.Option(False, "--single-agents", help="📄 Force single-file compilation (legacy mode)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="🔍 Show detailed source attribution and optimizer analysis"),
    local_only: bool = typer.Option(False, "--local-only", help="🏠 Ignore dependencies, compile only local primitives"),
    clean: bool = typer.Option(False, "--clean", help="🧹 Remove orphaned AGENTS.md files that are no longer generated"),
):
    """Generate AGENTS.md from APM context"""
    # Build arguments for the Click command
    args = []
    if output:
        args.extend(["-o", output])
    if dry_run:
        args.append("--dry-run")
    if no_links:
        args.append("--no-links")
    if chatmode:
        args.extend(["--chatmode", chatmode])
    if watch:
        args.append("--watch")
    if validate:
        args.append("--validate")
    if not with_constitution:
        args.append("--no-constitution")
    if single_agents:
        args.append("--single-agents")
    if verbose:
        args.append("--verbose")
    if local_only:
        args.append("--local-only")
    if clean:
        args.append("--clean")
    
    # Add any extra arguments
    if ctx.args:
        args.extend(ctx.args)
    
    _run_apm_command(["compile"] + args)

@apm_app.command("prune", context_settings={"allow_extra_args": True, "allow_interspersed_args": False})
def apm_prune_wrapper(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed without removing"),
):
    """Remove APM packages not listed in apm.yml.
    
    This command cleans up the apm_modules/ directory by removing packages that
    were previously installed but are no longer declared as dependencies in apm.yml.
    
    Examples:
        specify apm prune           # Remove orphaned packages
        specify apm prune --dry-run # Show what would be removed
    """
    args = []
    if dry_run:
        args.append("--dry-run")
    
    # Add any extra arguments
    if ctx.args:
        args.extend(ctx.args)
    
    _run_apm_command(["prune"] + args)

@apm_app.command("uninstall", context_settings={"allow_extra_args": True, "allow_interspersed_args": False})
def apm_uninstall_wrapper(
    ctx: typer.Context,
    packages: list[str] = typer.Argument(..., help="APM packages to remove (owner/repo format)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed without removing"),
):
    """Remove APM packages from apm.yml and apm_modules.
    
    This command removes packages from both the apm.yml dependencies list
    and the apm_modules/ directory. It's the opposite of 'specify apm install <package>'.
    
    Examples:
        specify apm uninstall github/design-guidelines    # Remove one package
        specify apm uninstall org/pkg1 org/pkg2           # Remove multiple packages
        specify apm uninstall github/pkg --dry-run        # Show what would be removed
    """
    args = []
    
    # Add package arguments first
    if packages:
        args.extend(packages)
    
    if dry_run:
        args.append("--dry-run")
    
    # Add any extra arguments
    if ctx.args:
        args.extend(ctx.args)
    
    _run_apm_command(["uninstall"] + args)

# Create deps subcommands as Typer sub-application
deps_app = typer.Typer(
    name="deps",
    help="🔗 Manage APM package dependencies",
    add_completion=False,
)

@deps_app.command("clean")
def apm_deps_clean_wrapper(ctx: typer.Context):
    """Remove all APM dependencies"""
    _run_apm_command(["deps", "clean"] + (ctx.args or []))

@deps_app.command("info") 
def apm_deps_info_wrapper(ctx: typer.Context):
    """Show detailed package information"""
    _run_apm_command(["deps", "info"] + (ctx.args or []))

@deps_app.command("list")
def apm_deps_list_wrapper(ctx: typer.Context):
    """List installed APM dependencies"""
    _run_apm_command(["deps", "list"] + (ctx.args or []))

@deps_app.command("tree")
def apm_deps_tree_wrapper(ctx: typer.Context):
    """Show dependency tree structure"""
    _run_apm_command(["deps", "tree"] + (ctx.args or []))

@deps_app.command("update")
def apm_deps_update_wrapper(ctx: typer.Context):
    """Update APM dependencies"""
    _run_apm_command(["deps", "update"] + (ctx.args or []))

# Add the deps sub-application to the APM app
apm_app.add_typer(deps_app, name="deps")

def _run_apm_command(args: list[str]):
    """Helper to run APM Click commands"""
    original_argv = sys.argv.copy()
    try:
        sys.argv = ["apm"] + args
        try:
            apm_click.main(args, standalone_mode=False)
        except SystemExit as e:
            if e.code != 0:
                raise typer.Exit(e.code)
    finally:
        sys.argv = original_argv

# Add the APM subcommand app to the main app
app.add_typer(apm_app, name="apm")

# Remove the old apm_command since we're using the Typer subcommand app now


def show_banner():
    """Display the ASCII art banner."""
    # Create gradient effect with different colors
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]
    
    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)
    
    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    # Show banner only when no subcommand and no help flag
    # (help is handled by BannerGroup)
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
        console.print()


def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool_for_tracker(tool: str, install_hint: str, tracker: StepTracker) -> bool:
    """Check if a tool is installed and update tracker."""
    if shutil.which(tool):
        tracker.complete(tool, "available")
        return True
    else:
        tracker.error(tool, f"not found - {install_hint}")
        return False


def check_tool(tool: str, install_hint: str) -> bool:
    """Check if a tool is installed."""
    
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/spec-kit/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            return True
    
    if shutil.which(tool):
        return True
    else:
        console.print(f"[yellow]⚠️  {tool} not found[/yellow]")
        console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
        return False


def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def init_git_repo(project_path: Path, quiet: bool = False) -> bool:
    """Initialize a git repository in the specified path.
    quiet: if True suppress console output (tracker handles status)
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Specify template"], check=True, capture_output=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True
        
    except subprocess.CalledProcessError as e:
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False
    finally:
        os.chdir(original_cwd)


def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False) -> Tuple[Path, dict]:
    repo_owner = "github"
    repo_name = "spec-kit"
    if client is None:
        client = httpx.Client(verify=ssl_context)
    
    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    
    try:
        response = client.get(api_url, timeout=30, follow_redirects=True)
        status = response.status_code
        if status != 200:
            msg = f"GitHub API returned {status} for {api_url}"
            if debug:
                msg += f"\nResponse headers: {response.headers}\nBody (truncated 500): {response.text[:500]}"
            raise RuntimeError(msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        console.print(f"[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)
    
    # Find the template asset for the specified AI assistant
    pattern = f"spec-kit-template-{ai_assistant}-{script_type}"
    matching_assets = [
        asset for asset in release_data.get("assets", [])
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]
    
    if not matching_assets:
        console.print(f"[red]No matching release asset found[/red] for pattern: [bold]{pattern}[/bold]")
        asset_names = [a.get('name','?') for a in release_data.get('assets', [])]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        raise typer.Exit(1)
    
    # Use the first matching asset
    asset = matching_assets[0]
    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]
    
    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")
    
    # Download the file
    zip_path = download_dir / filename
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")
    
    try:
        with client.stream("GET", download_url, timeout=60, follow_redirects=True) as response:
            if response.status_code != 200:
                body_sample = response.text[:400]
                raise RuntimeError(f"Download failed with {response.status_code}\nHeaders: {response.headers}\nBody (truncated): {body_sample}")
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except Exception as e:
        console.print(f"[red]Error downloading template[/red]")
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="Download Error", border_style="red"))
        raise typer.Exit(1)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    return zip_path, metadata


def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()
    
    # Step: fetch + download combined
    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug
        )
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error downloading template:[/red] {e}")
        raise
    
    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")
    
    try:
        # Create project directory only if not using current directory
        if not is_current_dir:
            project_path.mkdir(parents=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the ZIP for debugging
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")
            
            # For current directory, extract to a temp location first
            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)
                    
                    # Check what was extracted
                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")
                    
                    # Handle GitHub-style ZIP with a single root directory
                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(f"[cyan]Found nested directory structure[/cyan]")
                    
                    # Copy contents to current directory
                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                # Recursively copy directory contents
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print(f"[cyan]Template files merged into current directory[/cyan]")
            else:
                # Extract directly to project directory (original behavior)
                zip_ref.extractall(project_path)
                
                # Check what was extracted
                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
                
                # Handle GitHub-style ZIP with a single root directory
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    # Move contents up one level
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"
                    # Move the nested directory contents to temp location
                    shutil.move(str(nested_dir), str(temp_move_dir))
                    # Remove the now-empty project directory
                    project_path.rmdir()
                    # Rename temp directory to project directory
                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")
                    
    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))
        # Clean up project directory if created and not current directory
        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")
        # Clean up downloaded ZIP file
        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")
    
    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".specify" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
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
            st = script.stat(); mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400: new_mode |= 0o100
            if mode & 0o040: new_mode |= 0o010
            if mode & 0o004: new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
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


def _create_apm_structure(project_path: Path, project_name: str, ai_assistant: str = "copilot") -> None:
    """Create APM structure in the project directory."""
    # Copy APM template files
    template_source = Path(__file__).parent.parent.parent / "templates" / "apm" / "hello-world"
    
    if not template_source.exists():
        raise FileNotFoundError(f"APM template not found at {template_source}")
    
    # Copy APM files to project root
    files_to_copy = [
        "apm.yml",
        "hello-world.prompt.md", 
        "feature-implementation.prompt.md",
        "README.md"
    ]
    
    for file_name in files_to_copy:
        src_file = template_source / file_name
        if src_file.exists():
            shutil.copy2(src_file, project_path / file_name)
    
    # Copy .apm directory
    apm_src = template_source / ".apm"
    apm_dst = project_path / ".apm"
    if apm_src.exists():
        shutil.copytree(apm_src, apm_dst, dirs_exist_ok=True)
    
    # Update apm.yml with proper template variable replacement
    apm_yml = project_path / "apm.yml"
    if apm_yml.exists():
        content = apm_yml.read_text()
        
        # Replace template variables with actual values
        replacements = {
            "{{project_name}}": project_name,
            "{{version}}": "1.0.0",
            "{{description}}": f"AI-native project powered by {ai_assistant}",
            "{{author}}": "Developer",
            "hello-world": project_name  # Also replace any hello-world references
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        apm_yml.write_text(content)


@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, or cursor"),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    use_apm: bool = typer.Option(False, "--use-apm", help="Include APM (Agent Package Manager) structure for context management"),
):
    """
    Initialize a new Specify project from the latest template.
    
    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant (Claude Code, Gemini CLI, GitHub Copilot, or Cursor)
    3. Download the appropriate template from GitHub
    4. Extract the template to a new project directory or current directory
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    6. Optionally set up AI assistant commands
    7. Optionally include APM support (with --use-apm flag)
    
    Examples:
        specify init my-project
        specify init my-project --ai claude
        specify init my-project --ai gemini --use-apm
        specify init my-project --ai copilot --no-git
        specify init my-project --ai cursor --use-apm
        specify init --ignore-agent-tools my-project
        specify init --here --ai claude
        specify init --here --use-apm
    """
    # Show banner first
    show_banner()
    
    # Validate arguments
    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)
    
    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name or use --here flag")
        raise typer.Exit(1)
    
    # Determine project directory
    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()
        
        # Check if current directory has any files
        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
            
            # Ask for confirmation
            response = typer.confirm("Do you want to continue?")
            if not response:
                console.print("[yellow]Operation cancelled[/yellow]")
                raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        # Check if project directory already exists
        if project_path.exists():
            console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
            raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold cyan]Specify Project Setup[/bold cyan]\n"
        f"{'Initializing in current directory:' if here else 'Creating new project:'} [green]{project_path.name}[/green]"
        + (f"\n[dim]Path: {project_path}[/dim]" if here else ""),
        border_style="cyan"
    ))
    
    # Check git only if we might need it (not --no-git)
    git_available = True
    if not no_git:
        git_available = check_tool("git", "https://git-scm.com/downloads")
        if not git_available:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    # AI assistant selection
    if ai_assistant:
        if ai_assistant not in AI_CHOICES:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AI_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Use arrow-key selection interface
        selected_ai = select_with_arrows(
            AI_CHOICES, 
            "Choose your AI assistant:", 
            "copilot"
        )
    
    # Check agent tools unless ignored
    if not ignore_agent_tools:
        agent_tool_missing = False
        if selected_ai == "claude":
            if not check_tool("claude", "Install from: https://docs.anthropic.com/en/docs/claude-code/setup"):
                console.print("[red]Error:[/red] Claude CLI is required for Claude Code projects")
                agent_tool_missing = True
        elif selected_ai == "gemini":
            if not check_tool("gemini", "Install from: https://github.com/google-gemini/gemini-cli"):
                console.print("[red]Error:[/red] Gemini CLI is required for Gemini projects")
                agent_tool_missing = True

        if agent_tool_missing:
            console.print("\n[red]Required AI tool is missing![/red]")
            console.print("[yellow]Tip:[/yellow] Use --ignore-agent-tools to skip this check")
            raise typer.Exit(1)
    
    # Determine script type (explicit, interactive, or OS default)
    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        # Auto-detect default
        default_script = "ps" if os.name == "nt" else "sh"
        # Provide interactive selection similar to AI if stdin is a TTY
        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            selected_script = default_script
    
    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")
    
    # Download and set up project
    # New tree-based progress (no emojis); include earlier substeps
    tracker = StepTracker("Initialize Specify Project")
    # Flag to allow suppressing legacy headings
    sys._specify_tracker_active = True
    # Pre steps recorded as completed before live rendering
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
        ("apm", "Create APM structure"),
        ("chmod", "Ensure scripts executable"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize")
    ]:
        tracker.add(key, label)

    # Use transient so live tree is replaced by the final static render (avoids duplicate output)
    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            # Create a httpx client with verify based on skip_tls
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug)

            # APM structure creation (conditional)
            if use_apm:
                tracker.start("apm", "setting up APM structure")
                try:
                    _create_apm_structure(project_path, project_path.name, selected_ai)
                    tracker.complete("apm", "APM structure created")
                except Exception as e:
                    tracker.error("apm", f"APM setup failed: {str(e)}")
            else:
                tracker.skip("apm", "APM not requested")

            # Ensure scripts are executable (POSIX)
            ensure_executable_scripts(project_path, tracker=tracker)

            # Git step
            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif git_available:
                    if init_git_repo(project_path, quiet=True):
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
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
            # Force final render
            pass

    # Final static tree (ensures finished state visible after Live context ends)
    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")
    
    # Boxed "Next steps" section
    steps_lines = []
    if not here:
        steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    if selected_ai == "claude":
        steps_lines.append(f"{step_num}. Open in Visual Studio Code and start using / commands with Claude Code")
        steps_lines.append("   - Type / in any file to see available commands")
        steps_lines.append("   - Use /specify to create specifications")
        steps_lines.append("   - Use /plan to create implementation plans")
        steps_lines.append("   - Use /tasks to generate tasks")
    elif selected_ai == "gemini":
        steps_lines.append(f"{step_num}. Use / commands with Gemini CLI")
        steps_lines.append("   - Run gemini /specify to create specifications")
        steps_lines.append("   - Run gemini /plan to create implementation plans")
        steps_lines.append("   - Run gemini /tasks to generate tasks")
        steps_lines.append("   - See GEMINI.md for all available commands")
    elif selected_ai == "copilot":
        steps_lines.append(f"{step_num}. Open in Visual Studio Code and use [bold cyan]/specify[/], [bold cyan]/plan[/], [bold cyan]/tasks[/] commands with GitHub Copilot")

    # Removed script variant step (scripts are transparent to users)
    step_num += 1
    steps_lines.append(f"{step_num}. Update [bold magenta]CONSTITUTION.md[/bold magenta] with your project's non-negotiable principles")
    
    # Add APM-specific next steps if APM was enabled
    if use_apm:
        step_num += 1
        steps_lines.append(f"{step_num}. Use APM commands to manage your project context:")
        steps_lines.append("   - [bold cyan]specify apm compile[/bold cyan] - Generate AGENTS.md from APM instructions and packages")
        steps_lines.append("   - [bold cyan]specify apm install[/bold cyan] - Install APM packages")
        steps_lines.append("   - [bold cyan]specify apm deps list[/bold cyan] - List installed APM packages")

    steps_panel = Panel("\n".join(steps_lines), title="Next steps", border_style="cyan", padding=(1,2))
    console.print()  # blank line
    console.print(steps_panel)
    
    # Removed farewell line per user request


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    # Create tracker for checking tools
    tracker = StepTracker("Check Available Tools")
    
    # Add all tools we want to check
    tracker.add("git", "Git version control")
    tracker.add("claude", "Claude Code CLI")
    tracker.add("gemini", "Gemini CLI")
    tracker.add("code", "VS Code (for GitHub Copilot)")
    tracker.add("cursor-agent", "Cursor IDE agent (optional)")
    
    # Check each tool
    git_ok = check_tool_for_tracker("git", "https://git-scm.com/downloads", tracker)
    claude_ok = check_tool_for_tracker("claude", "https://docs.anthropic.com/en/docs/claude-code/setup", tracker)  
    gemini_ok = check_tool_for_tracker("gemini", "https://github.com/google-gemini/gemini-cli", tracker)
    # Check for VS Code (code or code-insiders)
    code_ok = check_tool_for_tracker("code", "https://code.visualstudio.com/", tracker)
    if not code_ok:
        code_ok = check_tool_for_tracker("code-insiders", "https://code.visualstudio.com/insiders/", tracker)
    cursor_ok = check_tool_for_tracker("cursor-agent", "https://cursor.sh/", tracker)
    
    # Render the final tree
    console.print(tracker.render())
    
    # Summary
    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")
    
    # Recommendations
    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")
    if not (claude_ok or gemini_ok):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")


def main():
    app()


if __name__ == "__main__":
    main()
