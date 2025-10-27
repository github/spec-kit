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

Usage:
    uvx specify-cli.py init <project-name>
    uvx specify-cli.py init --here

Or install globally:
    uv tool install --from specify-cli.py specify-cli
    specify init <project-name>
    specify init --here
"""

import os
import re
import subprocess
import sys
import zipfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple
from importlib.resources import files

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


def download_from_branch(ai_assistant: str, download_dir: Path, repo_owner: str, repo_name: str, repo_branch: str, script_type: str, verbose: bool, show_progress: bool, client: httpx.Client, debug: bool) -> Tuple[Path, dict]:
    """Download template directly from a branch as an archive."""
    download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/{repo_branch}.zip"
    filename = f"{repo_name}-{repo_branch}.zip"
    zip_path = download_dir / filename

    if verbose:
        console.print(f"[cyan]Downloading from branch:[/cyan] {repo_branch}")
        console.print(f"[cyan]URL:[/cyan] {download_url}")

    try:
        with client.stream("GET", download_url, timeout=60, follow_redirects=True) as response:
            if response.status_code != 200:
                # Read response content for error message
                error_content = b"".join(response.iter_bytes(chunk_size=1024))
                body_sample = error_content.decode('utf-8', errors='ignore')[:400]
                raise RuntimeError(f"Branch download failed with {response.status_code}\nHeaders: {response.headers}\nBody (truncated): {body_sample}")

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
        console.print(f"[red]Error downloading template from branch[/red]")
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="Download Error", border_style="red"))
        raise typer.Exit(1)

    if verbose:
        console.print(f"Downloaded: {filename}")

    metadata = {
        "filename": filename,
        "size": zip_path.stat().st_size,
        "release": f"branch-{repo_branch}",
        "asset_url": download_url
    }
    return zip_path, metadata


def detect_uvx_repo_info() -> tuple[str | None, str | None, str | None]:
    """Detect if we're running from uvx --from and extract repo info.

    Returns: (repo_owner, repo_name, repo_branch) or (None, None, None) if not detected
    """
    # Check command line args for uvx patterns
    cmdline = " ".join(sys.argv)
    git_url_match = re.search(r'git\+https://github\.com/([^/]+)/([^/.@\s]+)(?:\.git)?(?:@([^/\s]+))?', cmdline)

    if git_url_match:
        owner, repo, branch = git_url_match.groups()
        return owner, repo, branch or None

    # Check environment variables that uvx might set
    for env_var in os.environ:
        if "github.com" in os.environ[env_var]:
            git_match = re.search(r'github\.com/([^/]+)/([^/.]+)(?:\.git)?(?:/tree/([^/\s]+))?', os.environ[env_var])
            if git_match:
                owner, repo, branch = git_match.groups()
                return owner, repo, branch

    return None, None, None


def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, repo_owner: str = None, repo_name: str = None, repo_branch: str = None) -> Tuple[Path, dict]:
    # Auto-detect repo info if running from uvx --from
    detected_owner, detected_name, detected_branch = detect_uvx_repo_info()

    # Get repo settings from parameters, environment variables, uvx detection, or defaults
    repo_owner = repo_owner or os.getenv("SPECIFY_REPO_OWNER") or detected_owner or "github"
    repo_name = repo_name or os.getenv("SPECIFY_REPO_NAME") or detected_name or "spec-kit"
    repo_branch = repo_branch or os.getenv("SPECIFY_REPO_BRANCH") or detected_branch

    if verbose and (detected_owner or detected_name or detected_branch):
        console.print(f"[dim]Auto-detected from uvx: {detected_owner}/{detected_name}@{detected_branch or 'main'}[/dim]")

    if client is None:
        client = httpx.Client(verify=ssl_context)
    
    if repo_branch:
        if verbose:
            console.print(f"[cyan]Downloading template from branch {repo_branch}...[/cyan]")
        # Use direct branch archive download
        return download_from_branch(ai_assistant, download_dir, repo_owner, repo_name, repo_branch, script_type, verbose, show_progress, client, debug)

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


def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, repo_owner: str = None, repo_name: str = None, repo_branch: str = None, force: bool = False) -> Path:
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
            debug=debug,
            repo_owner=repo_owner,
            repo_name=repo_name,
            repo_branch=repo_branch
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

                        # Skip specs folder if it already exists to preserve user documentation (unless force)
                        if item.name == "specs" and dest_path.exists() and not force:
                            if verbose and not tracker:
                                console.print(f"[cyan]Preserving existing specs folder[/cyan]")
                            continue

                        if item.is_dir():
                            if dest_path.exists():
                                if force:
                                    if verbose and not tracker:
                                        console.print(f"[yellow]Force overwriting directory:[/yellow] {item.name}")
                                    shutil.rmtree(dest_path)
                                    shutil.copytree(item, dest_path)
                                else:
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
                            if dest_path.exists():
                                if force:
                                    if verbose and not tracker:
                                        console.print(f"[yellow]Force overwriting file:[/yellow] {item.name}")
                                    shutil.copy2(item, dest_path)
                                elif verbose and not tracker:
                                    console.print(f"[dim]Skipping existing file:[/dim] {item.name}")
                            else:
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

    # Transform branch structure if needed (detect if this was a branch download)
    try:
        transform_branch_structure(project_path, ai_assistant, script_type, tracker)
    except Exception as e:
        if verbose and not tracker:
            console.print(f"[yellow]Warning: Could not transform branch structure: {e}[/yellow]")

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


def move_claude_commands(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Move Claude commands to the spec-kit subfolder if needed."""
    claude_dir = project_path / ".claude" / "commands"
    target_dir = claude_dir / "spec-kit"

    # Check if commands already in correct location
    if target_dir.exists() and list(target_dir.glob("*.md")):
        if tracker:
            cmd_count = len(list(target_dir.glob("*.md")))
            tracker.complete("claude-cmds", f"{cmd_count} commands already in place")
        return

    # Check if commands are in parent directory
    if claude_dir.exists() and list(claude_dir.glob("*.md")):
        try:
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Move .md files to spec-kit subfolder
            moved_files = []
            for cmd_file in claude_dir.glob("*.md"):
                target_file = target_dir / cmd_file.name
                shutil.move(str(cmd_file), str(target_file))
                moved_files.append(cmd_file.name)

            if tracker:
                detail = f"moved {len(moved_files)} commands to spec-kit folder"
                tracker.complete("claude-cmds", detail)
            else:
                console.print(f"[cyan]Moved {len(moved_files)} Claude commands to .claude/commands/spec-kit[/cyan]")
        except Exception as e:
            if tracker:
                tracker.error("claude-cmds", str(e))
            else:
                console.print(f"[red]Error moving Claude commands:[/red] {e}")
    else:
        if tracker:
            tracker.skip("claude-cmds", "no commands found in template")


def transform_branch_structure(project_path: Path, ai_assistant: str, script_type: str, tracker: StepTracker | None = None) -> None:
    """Transform raw branch download structure to match release package structure."""
    if tracker:
        tracker.add("transform", "Transform branch structure")
        tracker.start("transform")

    # Check if this is a raw branch download (has memory/, scripts/, templates/ at root)
    has_raw_structure = any((project_path / dirname).exists() for dirname in ["memory", "scripts", "templates"])
    if not has_raw_structure:
        if tracker:
            tracker.skip("transform", "already packaged")
        return

    try:
        # Create .specify directory
        specify_dir = project_path / ".specify"
        specify_dir.mkdir(exist_ok=True)

        # Move directories to .specify/
        for dirname in ["memory", "scripts", "templates"]:
            src_dir = project_path / dirname
            if src_dir.exists():
                dest_dir = specify_dir / dirname
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                src_dir.rename(dest_dir)

        # Filter scripts by variant and restructure
        scripts_dir = specify_dir / "scripts"
        if scripts_dir.exists():
            # Keep only the relevant script variant
            if script_type == "sh":
                # Keep bash subdirectory, remove powershell
                bash_dir = scripts_dir / "bash"
                powershell_dir = scripts_dir / "powershell"
                if powershell_dir.exists():
                    shutil.rmtree(powershell_dir)
            else:  # ps
                # Keep powershell subdirectory, remove bash
                bash_dir = scripts_dir / "bash"
                powershell_dir = scripts_dir / "powershell"
                if bash_dir.exists():
                    shutil.rmtree(bash_dir)

        # Generate AI-specific commands from templates
        templates_dir = specify_dir / "templates"
        commands_dir = templates_dir / "commands" if templates_dir.exists() else None

        if commands_dir and commands_dir.exists() and list(commands_dir.glob("*.md")):
            generate_ai_commands(project_path, ai_assistant, script_type, commands_dir)

        if tracker:
            tracker.complete("transform", f"restructured for {ai_assistant}")

    except Exception as e:
        if tracker:
            tracker.error("transform", str(e))
        else:
            console.print(f"[red]Error transforming branch structure:[/red] {e}")
        raise


def generate_ai_commands(project_path: Path, ai_assistant: str, script_type: str, commands_dir: Path) -> None:
    """Generate AI-specific commands from templates/commands/*.md files."""

    def rewrite_paths(content: str) -> str:
        """Rewrite paths to use .specify/ prefix."""
        content = re.sub(r'(/?)memory/', r'.specify/memory/', content)
        content = re.sub(r'(/?)scripts/', r'.specify/scripts/', content)
        content = re.sub(r'(/?)templates/', r'.specify/templates/', content)
        return content

    def extract_yaml_field(content: str, field: str) -> str:
        """Extract a field from YAML frontmatter."""
        pattern = rf'^{field}:\s*(.+)$'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def extract_script_command(content: str, script_variant: str) -> str:
        """Extract script command for specific variant from YAML frontmatter."""
        pattern = rf'^\s*{script_variant}:\s*(.+)$'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else f"(Missing script command for {script_variant})"

    def clean_yaml_frontmatter(content: str) -> str:
        """Remove scripts section from YAML frontmatter."""
        lines = content.split('\n')
        result = []
        in_frontmatter = False
        skip_scripts = False
        dash_count = 0

        for line in lines:
            if line == '---':
                dash_count += 1
                if dash_count == 1:
                    in_frontmatter = True
                elif dash_count == 2:
                    in_frontmatter = False
                result.append(line)
                continue

            if in_frontmatter and line == 'scripts:':
                skip_scripts = True
                continue

            if in_frontmatter and skip_scripts and re.match(r'^[a-zA-Z].*:', line):
                skip_scripts = False

            if in_frontmatter and skip_scripts and re.match(r'^\s+', line):
                continue

            result.append(line)

        return '\n'.join(result)

    # Create appropriate directory structure for each AI assistant
    if ai_assistant == "claude":
        target_dir = project_path / ".claude" / "commands" / "spec-kit"
        target_dir.mkdir(parents=True, exist_ok=True)
        arg_format = "$ARGUMENTS"
        ext = "md"
    elif ai_assistant == "gemini":
        target_dir = project_path / ".gemini" / "commands"
        target_dir.mkdir(parents=True, exist_ok=True)
        arg_format = "{{args}}"
        ext = "toml"
        # Copy GEMINI.md if it exists
        gemini_md = project_path / ".specify" / "agent_templates" / "gemini" / "GEMINI.md"
        if gemini_md.exists():
            shutil.copy2(gemini_md, project_path / "GEMINI.md")
    elif ai_assistant == "copilot":
        target_dir = project_path / ".github" / "prompts"
        target_dir.mkdir(parents=True, exist_ok=True)
        arg_format = "$ARGUMENTS"
        ext = "prompt.md"
    elif ai_assistant == "cursor":
        target_dir = project_path / ".cursor" / "commands"
        target_dir.mkdir(parents=True, exist_ok=True)
        arg_format = "$ARGUMENTS"
        ext = "md"
    else:
        return

    # Process each command template
    for template_file in commands_dir.glob("*.md"):
        try:
            content = template_file.read_text(encoding='utf-8')
            name = template_file.stem

            # Extract metadata
            description = extract_yaml_field(content, 'description')
            script_command = extract_script_command(content, script_type)

            # Apply substitutions
            content = content.replace('{SCRIPT}', script_command)
            content = content.replace('{ARGS}', arg_format)
            content = content.replace('__AGENT__', ai_assistant)
            content = rewrite_paths(content)
            content = clean_yaml_frontmatter(content)

            # Write command file in appropriate format
            output_file = target_dir / f"{name}.{ext}"
            if ext == "toml":
                # TOML format for Gemini
                toml_content = f'description = "{description}"\n\nprompt = """\n{content}\n"""'
                output_file.write_text(toml_content, encoding='utf-8')
            else:
                # Markdown format for others
                output_file.write_text(content, encoding='utf-8')

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to process command template {template_file.name}: {e}[/yellow]")
            continue


@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here or --workspace)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, or cursor"),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    workspace: bool = typer.Option(False, "--workspace", help="Initialize a multi-repo workspace (discovers git repos and creates workspace config)"),
    auto_init: bool = typer.Option(False, "--auto-init", help="Automatically initialize .specify/ in all discovered repos (workspace mode only)"),
    force: bool = typer.Option(False, "--force", help="Force overwrite existing files when using --here or --workspace"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    repo_owner: str = typer.Option(None, "--repo-owner", help="GitHub repository owner (default: 'github')"),
    repo_name: str = typer.Option(None, "--repo-name", help="GitHub repository name (default: 'spec-kit')"),
    repo_branch: str = typer.Option(None, "--repo-branch", help="GitHub repository branch to download from (uses releases by default)"),
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

    Workspace mode (--workspace):
    1. Discover all git repositories in the workspace directory
    2. Generate .specify/workspace.yml with auto-detected configuration
    3. Create workspace-level specs/ directory
    4. Optionally initialize .specify/ in each repo (with --auto-init)

    Examples:
        specify init my-project
        specify init my-project --ai claude
        specify init --here --ai claude
        specify init --workspace --auto-init  # Initialize multi-repo workspace
        specify init --workspace ~/git/my-workspace --force
    """
    # Show banner first
    show_banner()

    # Workspace mode: delegate to init-workspace.sh
    if workspace:
        workspace_dir = project_name if project_name else str(Path.cwd())
        workspace_path = Path(workspace_dir).resolve()

        console.print(Panel.fit(
            "[bold cyan]Multi-Repo Workspace Initialization[/bold cyan]\n"
            f"Workspace directory: [green]{workspace_path}[/green]",
            border_style="cyan"
        ))

        # Find init-workspace.sh script from package resources
        script_resource = files("specify_cli").joinpath("scripts", "bash", "init-workspace.sh")
        if not script_resource.is_file():
            console.print(f"[red]Error:[/red] init-workspace.sh not found in package resources")
            raise typer.Exit(1)
        script_path = Path(str(script_resource))

        # Build command
        cmd = ["bash", str(script_path), str(workspace_path)]
        if force:
            cmd.append("--force")
        if auto_init:
            cmd.append("--auto-init")

        # Execute workspace initialization
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                console.print("\n[green]✅ Workspace initialization complete![/green]")
            raise typer.Exit(result.returncode)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error:[/red] Workspace initialization failed: {e}")
            raise typer.Exit(1)

    # Validate arguments for single-repo mode
    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name or use --here flag")
        raise typer.Exit(1)

    if force and not here:
        console.print("[red]Error:[/red] --force can only be used with --here flag")
        raise typer.Exit(1)

    if auto_init and not workspace:
        console.print("[red]Error:[/red] --auto-init can only be used with --workspace flag")
        raise typer.Exit(1)
    
    # Determine project directory
    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()
        
        # Check if current directory has any files
        existing_items = list(project_path.iterdir())
        if existing_items:
            if force:
                console.print(f"[red]Warning:[/red] --force will overwrite existing template files ({len(existing_items)} items)")
                console.print("[red]This will replace .specify/, .claude/, and other template files with fresh versions[/red]")
                console.print("[yellow]Tip: specs/ folder will be preserved unless it doesn't exist in the template[/yellow]")
            else:
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
        ("chmod", "Ensure scripts executable"),
        ("claude-cmds", "Organize Claude commands"),
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

            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug, repo_owner=repo_owner, repo_name=repo_name, repo_branch=repo_branch, force=force)

            # Ensure scripts are executable (POSIX)
            ensure_executable_scripts(project_path, tracker=tracker)

            # Move Claude commands if Claude is selected
            if selected_ai == "claude":
                tracker.start("claude-cmds")
                move_claude_commands(project_path, tracker=tracker)
            else:
                tracker.skip("claude-cmds", f"not using Claude (using {selected_ai})")

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
        steps_lines.append("   - Claude commands installed to .claude/commands/spec-kit")
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
