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
InfraKit CLI - Setup tool for InfraKit projects

Usage:
    uvx infrakit-cli.py init <project-name>
    uvx infrakit-cli.py init .
    uvx infrakit-cli.py init --here

Or install globally:
    uv tool install --from infrakit-cli.py infrakit-cli
    infrakit init <project-name>
    infrakit init .
    infrakit init --here
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
import json
import yaml
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

# For cross-platform keyboard input
import readchar
import ssl
import truststore
from datetime import datetime, timezone

from .agent_config import AGENT_CONFIG
from .iac_config import IAC_CONFIG, get_iac_choices, get_iac_commands
from .mcp_config import MCP_RECIPES

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)

def _github_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitHub token (cli arg takes precedence) or None."""
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None

def _github_auth_headers(cli_token: str | None = None) -> dict:
    """Return Authorization header dict only when a non-empty token exists."""
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}

def _parse_rate_limit_headers(headers: httpx.Headers) -> dict:
    """Extract and parse GitHub rate-limit headers."""
    info = {}
    
    # Standard GitHub rate-limit headers
    if "X-RateLimit-Limit" in headers:
        info["limit"] = headers.get("X-RateLimit-Limit")
    if "X-RateLimit-Remaining" in headers:
        info["remaining"] = headers.get("X-RateLimit-Remaining")
    if "X-RateLimit-Reset" in headers:
        reset_epoch = int(headers.get("X-RateLimit-Reset", "0"))
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
            info["reset_epoch"] = reset_epoch
            info["reset_time"] = reset_time
            info["reset_local"] = reset_time.astimezone()
    
    # Retry-After header (seconds or HTTP-date)
    if "Retry-After" in headers:
        retry_after = headers.get("Retry-After")
        try:
            info["retry_after_seconds"] = int(retry_after)
        except ValueError:
            # HTTP-date format - not implemented, just store as string
            info["retry_after"] = retry_after
    
    return info

def _format_rate_limit_error(status_code: int, headers: httpx.Headers, url: str) -> str:
    """Format a user-friendly error message with rate-limit information."""
    rate_info = _parse_rate_limit_headers(headers)
    
    lines = [f"GitHub API returned status {status_code} for {url}"]
    lines.append("")
    
    if rate_info:
        lines.append("[bold]Rate Limit Information:[/bold]")
        if "limit" in rate_info:
            lines.append(f"  • Rate Limit: {rate_info['limit']} requests/hour")
        if "remaining" in rate_info:
            lines.append(f"  • Remaining: {rate_info['remaining']}")
        if "reset_local" in rate_info:
            reset_str = rate_info["reset_local"].strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"  • Resets at: {reset_str}")
        if "retry_after_seconds" in rate_info:
            lines.append(f"  • Retry after: {rate_info['retry_after_seconds']} seconds")
        lines.append("")
    
    # Add troubleshooting guidance
    lines.append("[bold]Troubleshooting Tips:[/bold]")
    lines.append("  • If you're on a shared CI or corporate environment, you may be rate-limited.")
    lines.append("  • Consider using a GitHub token via --github-token or the GH_TOKEN/GITHUB_TOKEN")
    lines.append("    environment variable to increase rate limits.")
    lines.append("  • Authenticated requests have a limit of 5,000/hour vs 60/hour for unauthenticated.")
    
    return "\n".join(lines)

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

BANNER = """
██╗███╗   ██╗███████╗██████╗  █████╗ ██╗  ██╗██╗████████╗
██║████╗  ██║██╔════╝██╔══██╗██╔══██╗██║ ██╔╝██║╚══██╔══╝
██║██╔██╗ ██║█████╗  ██████╔╝███████║█████╔╝ ██║   ██║   
██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██╔═██╗ ██║   ██║   
██║██║ ╚████║██║     ██║  ██║██║  ██║██║  ██╗██║   ██║   
╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝   
"""

TAGLINE = "InfraKit - Infrastructure-First Constraint-Driven Development"
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

        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

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

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()

    if key == readchar.key.UP or key == readchar.key.CTRL_P:
        return 'up'
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N:
        return 'down'

    if key == readchar.key.ENTER:
        return 'enter'

    if key == readchar.key.ESC:
        return 'escape'

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
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")

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

    return selected_key

console = Console()

class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="infrakit",
    help="Setup tool for InfraKit infrastructure-first constraint-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
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
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'infrakit --help' for usage information[/dim]"))
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

def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.
    
    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results
        
    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/infrakit/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True
    
    found = shutil.which(tool) is not None
    
    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")
    
    return found

def find_project_root(start: Path = None) -> Optional[Path]:
    """Walk up from start (default: cwd) to find a directory containing .infrakit/config.yaml."""
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".infrakit" / "config.yaml").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent

def _read_mcp_json(path: Path) -> dict:
    """Read existing mcp.json, returning {'mcpServers': {}} on missing/invalid file."""
    if not path.exists():
        return {"mcpServers": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"mcpServers": {}}
        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {"mcpServers": {}}

def _build_mcp_server_entry(recipe_key: str) -> dict:
    """Convert a recipe dict into the mcpServers entry format."""
    recipe = MCP_RECIPES[recipe_key]
    entry = {"type": recipe["type"]}
    if recipe["type"] == "stdio":
        entry["command"] = recipe["command"]
        entry["args"] = recipe["args"]
    elif recipe["type"] == "sse":
        entry["url"] = recipe["url"]
    return entry

def _build_mcp_markdown_block(recipe_key: str, recipe: dict, agent_name: str) -> str:
    """Build a markdown block with JSON config example for agents without native MCP file support."""
    lines = [
        f"## {recipe_key}",
        "",
        f"**{recipe['display_name']}**",
        "",
        recipe["description"],
        "",
        f"Configure in your {agent_name} global MCP settings:",
        "",
    ]
    if recipe["type"] == "stdio":
        lines += [
            "```json",
            f'"{recipe_key}": {{',
            f'  "type": "stdio",',
            f'  "command": "{recipe["command"]}",',
            f'  "args": {json.dumps(recipe["args"])}',
            "}",
            "```",
            "",
        ]
    elif recipe["type"] == "sse":
        lines += [
            "```json",
            f'"{recipe_key}": {{',
            f'  "type": "sse",',
            f'  "url": "{recipe["url"]}"',
            "}",
            "```",
            "",
        ]
    return "\n".join(lines)

def _update_mcp_use_table(project_root: Path, recipe_key: str) -> None:
    """Append a row to .infrakit/mcp-use.md if the recipe isn't already listed."""
    md_path = project_root / ".infrakit" / "mcp-use.md"
    recipe = MCP_RECIPES[recipe_key]

    existing = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if f"| {recipe_key} |" in existing:
        return

    tools_str = ", ".join(f"`{t}`" for t in recipe.get("tools", []))
    new_row = f"| {recipe_key} | {recipe['description']} | {tools_str} | {recipe['usage']} |\n"

    if md_path.exists():
        updated = existing.replace("| — | — | — | — |\n", new_row)
        if updated == existing:
            updated = existing + new_row
        md_path.write_text(updated, encoding="utf-8")
    else:
        md_path.write_text(
            "# Installed MCP Servers\n\n"
            "| MCP | Description | Tools | Usage |\n"
            "|-----|-------------|-------|-------|\n"
            + new_row,
            encoding="utf-8",
        )

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

def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path.
    
    Args:
        project_path: Path to initialize git repository in
        quiet: if True suppress console output (tracker handles status)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from InfraKit template"], check=True, capture_output=True, text=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"
        
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False, error_msg
    finally:
        os.chdir(original_cwd)

def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """Handle merging or copying of .vscode/settings.json files."""
    def log(message, color="green"):
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)
                f.write('\n')
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")

    except Exception as e:
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)

def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged

def download_template_from_github(ai_assistant: str, download_dir: Path, *, iac_tool: str = "crossplane", script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Tuple[Path, dict]:
    repo_owner = "neelneelpurk"
    repo_name = "infrakit"
    if client is None:
        client = httpx.Client(verify=ssl_context)

    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = client.get(
            api_url,
            timeout=30,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        )
        status = response.status_code
        if status != 200:
            # Format detailed error message with rate-limit info
            error_msg = _format_rate_limit_error(status, response.headers, api_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
            raise RuntimeError(error_msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        console.print("[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)

    assets = release_data.get("assets", [])
    pattern = f"infrakit-template-{ai_assistant}-{iac_tool}-{script_type}"
    matching_assets = [
        asset for asset in assets
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        console.print(f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] (expected pattern: [bold]{pattern}[/bold])")
        asset_names = [a.get('name', '?') for a in assets]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        raise typer.Exit(1)

    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print("[cyan]Downloading template...[/cyan]")

    try:
        with client.stream(
            "GET",
            download_url,
            timeout=60,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        ) as response:
            if response.status_code != 200:
                # Handle rate-limiting on download as well
                error_msg = _format_rate_limit_error(response.status_code, response.headers, download_url)
                if debug:
                    error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{response.text[:400]}"
                raise RuntimeError(error_msg)
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
        console.print("[red]Error downloading template[/red]")
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

def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, iac_tool: str = "crossplane", verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            iac_tool=iac_tool,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token
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
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print("[cyan]Found nested directory structure[/cyan]")

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # Special handling for .vscode/settings.json - merge instead of overwrite
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print("[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print("[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .infrakit/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".infrakit" / "scripts"
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

def ensure_project_context_from_template(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Copy project context template to memory if it doesn't exist (preserves existing project context on reinitialization)."""
    memory_context = project_path / ".infrakit" / "memory" / "project-context.md"
    template_context = project_path / ".infrakit" / "templates" / "project-context-template.md"

    # If project context already exists in memory, preserve it
    if memory_context.exists():
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.skip("project_context", "existing file preserved")
        return

    # If template doesn't exist, something went wrong with extraction
    if not template_context.exists():
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.error("project_context", "template not found")
        return

    # Copy template to memory directory
    try:
        memory_context.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_context, memory_context)
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.complete("project_context", "copied from template")
        else:
            console.print("[cyan]Initialized project context from template[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.error("project_context", str(e))
        else:
            console.print(f"[yellow]Warning: Could not initialize project context: {e}[/yellow]")

# Agent-specific skill directory overrides for agents whose skills directory
# doesn't follow the standard <agent_folder>/skills/ pattern
AGENT_SKILLS_DIR_OVERRIDES = {
    "codex": ".agents/skills",  # Codex agent layout override
}

# Default skills directory for agents not in AGENT_CONFIG
DEFAULT_SKILLS_DIR = ".agents/skills"

# Enhanced descriptions for each infrakit command skill
SKILL_DESCRIPTIONS = {
    "specify_composition": "Create or update infrastructure resource specifications from natural language descriptions. Use when starting new Crossplane compositions. Generates a structured spec following constraint-driven development methodology.",
    "plan_composition": "Generate architecture review and implementation plans for Crossplane compositions. Use after creating a spec to define the XRD, Composition, and Claim structure. Produces a detailed plan before any YAML is written.",
    "implement_composition": "Generate XRD, Composition, and example Claim YAML from an approved plan. Use after planning to produce production-ready Crossplane manifests.",
    "review_composition": "Review generated Crossplane YAML against best practices and project coding standards. Checks Pipeline mode usage, patch paths, providerConfigRef patterns, and tagging requirements.",
    "validate_composition": "Run crossplane render validation against generated Composition and Claim manifests. Use to verify the output is syntactically and structurally correct.",
    "tasks": "Break down infrastructure resource plans into actionable task lists. Generates tasks.md with ordered, dependency-aware implementation steps.",
    "analyze": "Perform cross-artifact consistency analysis across spec, plan, and implementation artifacts. Use to identify gaps or inconsistencies before or after implementation.",
    "clarify": "Structured clarification workflow for underspecified infrastructure requirements. Use before planning to resolve ambiguities through targeted questioning.",
    "project_context": "Create or update project context and standards. Use at project start to establish encryption policies, tagging requirements, network topology standards, and compliance rules.",
    "checklist": "Generate quality checklists for validating infrastructure resource completeness and Crossplane best-practice compliance.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues. Use after task breakdown to track work items in GitHub project management.",
    "coding_style": "Specify and update the project coding style standards using the coding-style-template.md.",
    "tagging": "Update project tagging requirements using the tagging-constraint-template.md.",
}


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory for the given AI assistant.

    Uses ``AGENT_SKILLS_DIR_OVERRIDES`` first, then falls back to
    ``AGENT_CONFIG[agent]["folder"] + "skills"``, and finally to
    ``DEFAULT_SKILLS_DIR``.
    """
    if selected_ai in AGENT_SKILLS_DIR_OVERRIDES:
        return project_path / AGENT_SKILLS_DIR_OVERRIDES[selected_ai]

    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"

    return project_path / DEFAULT_SKILLS_DIR


def install_ai_skills(project_path: Path, selected_ai: str, tracker: StepTracker | None = None) -> bool:
    """Install Prompt.MD files from templates/commands/ as agent skills.

    Skills are written to the agent-specific skills directory following the
    `agentskills.io <https://agentskills.io/specification>`_ specification.
    Installation is additive — existing files are never removed and prompt
    command files in the agent's commands directory are left untouched.

    Args:
        project_path: Target project directory.
        selected_ai: AI assistant key from ``AGENT_CONFIG``.
        tracker: Optional progress tracker.

    Returns:
        ``True`` if at least one skill was installed or all skills were
        already present (idempotent re-run), ``False`` otherwise.
    """
    # Locate command templates in the agent's extracted commands directory.
    # download_and_extract_template() already placed the .md files here.
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    commands_subdir = agent_config.get("commands_subdir", "commands")
    if agent_folder:
        templates_dir = project_path / agent_folder.rstrip("/") / commands_subdir
    else:
        templates_dir = project_path / commands_subdir

    if not templates_dir.exists() or not any(templates_dir.glob("*.md")):
        # Fallback: try the repo-relative path (for running from source checkout)
        # This also covers agents whose extracted commands are in a different
        # format (e.g. gemini uses .toml, not .md).
        script_dir = Path(__file__).parent.parent.parent  # up from src/infrakit_cli/
        fallback_dir = script_dir / "templates" / "commands"
        if fallback_dir.exists() and any(fallback_dir.glob("*.md")):
            templates_dir = fallback_dir

    if not templates_dir.exists() or not any(templates_dir.glob("*.md")):
        if tracker:
            tracker.error("ai-skills", "command templates not found")
        else:
            console.print("[yellow]Warning: command templates not found, skipping skills installation[/yellow]")
        return False

    command_files = sorted(templates_dir.glob("*.md"))
    if not command_files:
        if tracker:
            tracker.skip("ai-skills", "no command templates found")
        else:
            console.print("[yellow]No command templates found to install[/yellow]")
        return False

    # Resolve the correct skills directory for this agent
    skills_dir = _get_skills_dir(project_path, selected_ai)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if tracker:
        tracker.start("ai-skills")

    installed_count = 0
    skipped_count = 0
    for command_file in command_files:
        try:
            content = command_file.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if not isinstance(frontmatter, dict):
                        frontmatter = {}
                    body = parts[2].strip()
                else:
                    # File starts with --- but has no closing ---
                    console.print(f"[yellow]Warning: {command_file.name} has malformed frontmatter (no closing ---), treating as plain content[/yellow]")
                    frontmatter = {}
                    body = content
            else:
                frontmatter = {}
                body = content

            command_name = command_file.stem
            # Normalize: extracted commands may be named "infrakit:<cmd>.md";
            # strip the "infrakit:" prefix so skill names stay clean and
            # SKILL_DESCRIPTIONS lookups work.
            if command_name.startswith("infrakit:"):
                command_name = command_name[len("infrakit:"):]
            skill_name = f"infrakit-{command_name}"

            # Create skill directory (additive — never removes existing content)
            skill_dir = skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Select the best description available
            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(command_name, original_desc or f"Spec-kit workflow command: {command_name}")

            # Build SKILL.md following agentskills.io spec
            # Use yaml.safe_dump to safely serialise the frontmatter and
            # avoid YAML injection from descriptions containing colons,
            # quotes, or newlines.
            # Normalize source filename for metadata — strip infrakit: prefix
            # so it matches the canonical templates/commands/<cmd>.md path.
            source_name = command_file.name
            if source_name.startswith("infrakit:"):
                source_name = source_name[len("infrakit:"):]

            frontmatter_data = {
                "name": skill_name,
                "description": enhanced_desc,
                "compatibility": "Requires InfraKit project structure with .infrakit/ directory",
                "metadata": {
                    "author": "github-infrakit",
                    "source": f"templates/commands/{source_name}",
                },
            }
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
            skill_content = (
                f"---\n"
                f"{frontmatter_text}\n"
                f"---\n\n"
                f"# InfraKit {command_name.title()} Skill\n\n"
                f"{body}\n"
            )

            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                # Do not overwrite user-customized skills on re-runs
                skipped_count += 1
                continue
            skill_file.write_text(skill_content, encoding="utf-8")
            installed_count += 1

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to install skill {command_file.stem}: {e}[/yellow]")
            continue

    if tracker:
        if installed_count > 0 and skipped_count > 0:
            tracker.complete("ai-skills", f"{installed_count} new + {skipped_count} existing skills in {skills_dir.relative_to(project_path)}")
        elif installed_count > 0:
            tracker.complete("ai-skills", f"{installed_count} skills → {skills_dir.relative_to(project_path)}")
        elif skipped_count > 0:
            tracker.complete("ai-skills", f"{skipped_count} skills already present")
        else:
            tracker.error("ai-skills", "no skills installed")
    else:
        if installed_count > 0:
            console.print(f"[green]✓[/green] Installed {installed_count} agent skills to {skills_dir.relative_to(project_path)}/")
        elif skipped_count > 0:
            console.print(f"[green]✓[/green] {skipped_count} agent skills already present in {skills_dir.relative_to(project_path)}/")
        else:
            console.print("[yellow]No skills were installed[/yellow]")

    return installed_count > 0 or skipped_count > 0


def initialize_iac_config(project_path: Path, iac_tool: str, ai_assistant: str, *, tracker: StepTracker | None = None) -> None:
    """Set up IaC-specific configuration, commands, agents, and documentation.

    Creates:
    - .infrakit/config.yaml — selected IaC tool and AI agent
    - .infrakit/context.md — project context template
    - .infrakit/coding-style.md — default coding standards
    - .infrakit/tracks.md — master resource registry
    - .infrakit/agent_personas/ — IaC-specific agent definitions
    - .infrakit/tracks/ — track directories
    - technical-docs/ — provider and tool documentation
    - IaC-native commands in the agent's commands directory
    """
    iac_cfg = IAC_CONFIG.get(iac_tool, {})
    if not iac_cfg:
        if tracker:
            tracker.error("iac-config", f"unknown IaC tool: {iac_tool}")
        return

    # Locate the templates/iac/<tool>/ directory
    # Try the repo-relative path first (running from source checkout)
    script_dir = Path(__file__).parent.parent.parent  # up from src/infrakit_cli/
    iac_templates_dir = script_dir / "templates" / "iac" / iac_tool

    if not iac_templates_dir.is_dir():
        # When installed via pip, templates are not included in the package.
        # This is expected because the GitHub release ZIP already contains the extracted templates.
        # We only log a debug message and continue so configuration like config.yaml is generated.
        if tracker:
            tracker.add("iac-config-assets", "Check IaC templates")
            tracker.skip("iac-config-assets", f"No local template dir, rely on downloaded ZIP")

    # --- 1. Create .infrakit/ configuration directory ---
    if tracker:
        tracker.start("iac-config")

    infrakit_dir = project_path / ".infrakit"
    infrakit_dir.mkdir(parents=True, exist_ok=True)

    # config.yaml
    config_data = {
        "iac_tool": iac_tool,
        "iac_name": iac_cfg.get("name", iac_tool),
        "ai_assistant": ai_assistant,
        "resource_term": iac_cfg.get("resource_term", "composition"),
    }
    config_file = infrakit_dir / "config.yaml"
    if not config_file.exists():
        config_file.write_text(yaml.dump(config_data, sort_keys=False), encoding="utf-8")

    # Copy assets (context.md, coding-style.md) from templates
    assets_dir = iac_templates_dir / "assets"
    if assets_dir.is_dir():
        for asset_file in assets_dir.iterdir():
            if asset_file.is_file():
                dest = infrakit_dir / asset_file.name.replace("context_template", "context").replace("default_coding_style", "coding-style")
                if not dest.exists():
                    shutil.copy2(asset_file, dest)

    # tracks.md — master resource registry
    tracks_md = infrakit_dir / "tracks.md"
    if not tracks_md.exists():
        tracks_md.write_text(
            "# Infrastructure Resource Registry\n\n"
            "Track all infrastructure compositions and their current status.\n\n"
            "## Status Reference\n\n"
            "| Symbol | Meaning |\n"
            "|--------|---------|\n"
            "| 🔵 `initializing` | Track created, spec in progress |\n"
            "| 📝 `spec-generated` | Spec confirmed, ready for plan |\n"
            "| 📋 `planned` | Plan generated, ready for implementation |\n"
            "| ⚙️ `in-progress` | Implementation underway |\n"
            "| ✅ `done` | Implementation complete and reviewed |\n"
            "| ❌ `blocked` | Blocked, needs attention |\n\n"
            "---\n\n"
            "## Tracks\n\n"
            "| Track | Type | Directory | Status | Created |\n"
            "|-------|------|-----------|--------|---------|\n"
            "| (none yet) | — | — | — | — |\n",
            encoding="utf-8",
        )

    # tagging.md — tagging constraints (populated by /infrakit:setup)
    tagging_md = infrakit_dir / "tagging.md"
    if not tagging_md.exists():
        tagging_md.write_text(
            "# Tagging Constraints\n\n"
            "> Run `/infrakit:setup` to configure your tagging requirements.\n",
            encoding="utf-8",
        )

    # mcp-use.md — installed MCP server index
    mcp_use_md = infrakit_dir / "mcp-use.md"
    if not mcp_use_md.exists():
        mcp_use_md.write_text(
            "# Installed MCP Servers\n\n"
            "MCP servers configured for this project.\n"
            "Run `infrakit mcp` to add more.\n\n"
            "| MCP | Description | Tools | Usage |\n"
            "|-----|-------------|-------|-------|\n"
            "| — | — | — | — |\n",
            encoding="utf-8",
        )

    # memory directory (for project context)
    (infrakit_dir / "memory").mkdir(parents=True, exist_ok=True)

    # .infrakit/tracks/ — track working directories
    tracks_dir = infrakit_dir / "tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)

    # Copy IaC-specific agents
    agents_src = iac_templates_dir / "agent_personas"
    agents_dest = infrakit_dir / "agent_personas"
    if agents_src.is_dir():
        agents_dest.mkdir(parents=True, exist_ok=True)
        for agent_file in agents_src.iterdir():
            if agent_file.is_file():
                dest = agents_dest / agent_file.name
                if not dest.exists():
                    shutil.copy2(agent_file, dest)

    # Copy generic agents
    generic_agents_src = script_dir / "templates" / "agent_personas"
    if generic_agents_src.is_dir():
        agents_dest.mkdir(parents=True, exist_ok=True)
        for agent_file in generic_agents_src.iterdir():
            if agent_file.is_file():
                dest = agents_dest / agent_file.name
                if not dest.exists():
                    shutil.copy2(agent_file, dest)


    if tracker:
        tracker.complete("iac-config", f"{iac_tool} ({iac_cfg.get('name', '')})")

    # --- 2. Generate IaC-native commands ---
    if tracker:
        tracker.start("iac-commands")

    agent_config = AGENT_CONFIG.get(ai_assistant, {})
    agent_folder = agent_config.get("folder", "")
    commands_subdir = agent_config.get("commands_subdir", "commands")
    command_ext = agent_config.get("command_extension", ".md")

    if agent_folder:
        cmds_dest = project_path / agent_folder.rstrip("/") / commands_subdir
    else:
        cmds_dest = project_path / commands_subdir

    cmds_dest.mkdir(parents=True, exist_ok=True)

    # Copy generic commands from templates/commands/ (filtered by iac_config generic_commands list)
    generic_commands_dir = script_dir / "templates" / "commands"
    allowed_generic = set(iac_cfg.get("generic_commands", []))
    generic_count = 0
    if generic_commands_dir.is_dir():
        for cmd_file in generic_commands_dir.iterdir():
            if cmd_file.is_file() and cmd_file.suffix == ".md" and cmd_file.stem in allowed_generic:
                dest_name = f"infrakit:{cmd_file.stem}{command_ext}"
                dest = cmds_dest / dest_name
                if not dest.exists():
                    shutil.copy2(cmd_file, dest)
                    generic_count += 1

    # Copy IaC-native commands from templates/iac/<tool>/commands/ (filtered by iac_config iac_commands list)
    iac_commands_dir = iac_templates_dir / "commands"
    allowed_iac = set(iac_cfg.get("iac_commands", []))
    iac_count = 0
    if iac_commands_dir.is_dir():
        for cmd_file in iac_commands_dir.iterdir():
            if cmd_file.is_file() and cmd_file.suffix == ".md" and cmd_file.stem in allowed_iac:
                dest_name = f"infrakit:{cmd_file.stem}{command_ext}"
                dest = cmds_dest / dest_name
                if not dest.exists():
                    shutil.copy2(cmd_file, dest)
                    iac_count += 1

    if tracker:
        tracker.complete("iac-commands", f"{generic_count} generic + {iac_count} IaC commands → {cmds_dest.relative_to(project_path)}")

    # --- 3. Copy technical documentation ---
    if tracker:
        tracker.start("iac-docs")

    docs_src = iac_templates_dir / "docs"
    docs_dest = project_path / "technical-docs"
    doc_count = 0
    if docs_src.is_dir():
        docs_dest.mkdir(parents=True, exist_ok=True)
        for doc_file in docs_src.iterdir():
            if doc_file.is_file():
                dest = docs_dest / doc_file.name
                if not dest.exists():
                    shutil.copy2(doc_file, dest)
                    doc_count += 1

    if tracker:
        tracker.complete("iac-docs", f"{doc_count} docs → technical-docs/")


@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, shai, q, agy, bob, qodercli, or generic (requires --ai-commands-dir)"),
    ai_commands_dir: str = typer.Option(None, "--ai-commands-dir", help="Directory for agent command files (required with --ai generic, e.g. .myagent/commands/)"),
    iac_tool: str = typer.Option(None, "--iac", help="IaC tool to use: crossplane"),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token to use for API requests (or set GH_TOKEN or GITHUB_TOKEN environment variable)"),
    ai_skills: bool = typer.Option(False, "--ai-skills", help="Install Prompt.MD templates as agent skills (requires --ai)"),
):
    """
    Initialize a new InfraKit project from the latest template.
    
    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant and IaC tool
    3. Download the appropriate template from GitHub
    4. Extract the template and set up IaC-native commands
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    
    Examples:
        infrakit init my-project --ai claude --iac crossplane
        infrakit init my-project --ai claude --iac crossplane --no-git
        infrakit init --here --ai claude --iac crossplane
        infrakit init . --ai claude --iac crossplane
        infrakit init my-project --ai generic --ai-commands-dir .myagent/commands/  # Unsupported agent
    """

    show_banner()

    # Detect when option values are likely misinterpreted flags (parameter ordering issue)
    if ai_assistant and ai_assistant.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai: '{ai_assistant}'")
        console.print("[yellow]Hint:[/yellow] Did you forget to provide a value for --ai?")
        console.print("[yellow]Example:[/yellow] infrakit init --ai claude --here")
        console.print(f"[yellow]Available agents:[/yellow] {', '.join(AGENT_CONFIG.keys())}")
        raise typer.Exit(1)
    
    if ai_commands_dir and ai_commands_dir.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai-commands-dir: '{ai_commands_dir}'")
        console.print("[yellow]Hint:[/yellow] Did you forget to provide a value for --ai-commands-dir?")
        console.print("[yellow]Example:[/yellow] infrakit init --ai generic --ai-commands-dir .myagent/commands/")
        raise typer.Exit(1)

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
        console.print("[yellow]Usage:[/yellow] infrakit init <project> --ai <agent> --ai-skills")
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
                padding=(1, 2)
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
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices, 
            "Choose your AI assistant:", 
            "copilot"
        )

    # Validate --ai-commands-dir usage
    if selected_ai == "generic":
        if not ai_commands_dir:
            console.print("[red]Error:[/red] --ai-commands-dir is required when using --ai generic")
            console.print("[dim]Example: infrakit init my-project --ai generic --ai-commands-dir .myagent/commands/[/dim]")
            raise typer.Exit(1)
    elif ai_commands_dir:
        console.print(f"[red]Error:[/red] --ai-commands-dir can only be used with --ai generic (not '{selected_ai}')")
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
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            selected_script = default_script

    # IaC tool selection
    if iac_tool:
        if iac_tool not in IAC_CONFIG:
            console.print(f"[red]Error:[/red] Invalid IaC tool '{iac_tool}'. Choose from: {', '.join(IAC_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_iac = iac_tool
    else:
        iac_choices = get_iac_choices()
        if sys.stdin.isatty():
            selected_iac = select_with_arrows(
                iac_choices,
                "Choose your IaC tool:",
                "crossplane"
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
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("project_context", "Project Context setup"),
        ("iac-config", "IaC configuration"),
        ("iac-commands", "IaC-native commands"),
        ("iac-docs", "Technical documentation"),
    ]:
        tracker.add(key, label)
    if ai_skills:
        tracker.add("ai-skills", "Install agent skills")
    for key, label in [
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize")
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

            download_and_extract_template(project_path, selected_ai, selected_script, here, iac_tool=selected_iac, verbose=False, tracker=tracker, client=local_client, debug=debug, github_token=github_token)

            # For generic agent, rename placeholder directory to user-specified path
            if selected_ai == "generic" and ai_commands_dir:
                placeholder_dir = project_path / ".infrakit" / "commands"
                target_dir = project_path / ai_commands_dir
                if placeholder_dir.is_dir():
                    target_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(placeholder_dir), str(target_dir))
                    # Clean up empty .infrakit dir if it's now empty
                    infrakit_dir = project_path / ".infrakit"
                    if infrakit_dir.is_dir() and not any(infrakit_dir.iterdir()):
                        infrakit_dir.rmdir()

            ensure_executable_scripts(project_path, tracker=tracker)

            ensure_project_context_from_template(project_path, tracker=tracker)

            # IaC-specific setup
            initialize_iac_config(project_path, selected_iac, selected_ai, tracker=tracker)

            if ai_skills:
                skills_ok = install_ai_skills(project_path, selected_ai, tracker=tracker)

                # When --ai-skills is used on a NEW project and skills were
                # successfully installed, remove the command files that the
                # template archive just created.  Skills replace commands, so
                # keeping both would be confusing.  For --here on an existing
                # repo we leave pre-existing commands untouched to avoid a
                # breaking change.  We only delete AFTER skills succeed so the
                # project always has at least one of {commands, skills}.
                if skills_ok and not here:
                    agent_cfg = AGENT_CONFIG.get(selected_ai, {})
                    agent_folder = agent_cfg.get("folder", "")
                    if agent_folder:
                        cmds_dir = project_path / agent_folder.rstrip("/") / "commands"
                        if cmds_dir.exists():
                            try:
                                shutil.rmtree(cmds_dir)
                            except OSError:
                                # Best-effort cleanup: skills are already installed,
                                # so leaving stale commands is non-fatal.
                                console.print("[yellow]Warning: could not remove extracted commands directory[/yellow]")

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
            padding=(1, 2)
        )
        console.print(git_error_panel)

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

    iac_cfg = IAC_CONFIG.get(selected_iac, {})
    resource_term = iac_cfg.get("resource_term", "composition")

    steps_lines.append(f"   2.1 [cyan]/infrakit:project_context[/] - Establish infrastructure principles")
    steps_lines.append(f"   2.2 [cyan]/infrakit:new_composition[/] - Create a new resource with multi-agent workflow")
    steps_lines.append(f"   2.3 [cyan]/infrakit:update_composition[/] - Update an existing resource")
    steps_lines.append(f"   2.4 [cyan]/infrakit:status[/] - Track progress of all tracks")
    steps_lines.append(f"   2.5 [cyan]/infrakit:review_composition[/] - Review against best practices")
    steps_lines.append(f"   2.6 [cyan]/infrakit:validate_composition[/] - Validate generated YAML")

    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "Enhancement commands [bright_black](improve quality & confidence)[/bright_black]",
        "",
        "○ [cyan]/infrakit:clarify[/] [bright_black](optional)[/bright_black] - Clarify ambiguous requirements",
        "○ [cyan]/infrakit:analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency report",
        "○ [cyan]/infrakit:checklist[/] [bright_black](optional)[/bright_black] - Quality validation checklist",
    ]
    enhancements_panel = Panel("\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1,2))
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
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
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

    # 1. Find project root
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

    # 2. Read config
    config_path = project_root / ".infrakit" / "config.yaml"
    try:
        project_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, Exception) as e:
        console.print(f"[red]Error reading .infrakit/config.yaml:[/red] {e}")
        raise typer.Exit(1)

    ai_assistant = project_config.get("ai_assistant")
    if not ai_assistant:
        console.print("[red]Error:[/red] 'ai_assistant' not found in .infrakit/config.yaml")
        raise typer.Exit(1)

    agent_cfg = AGENT_CONFIG.get(ai_assistant, {})
    agent_name = agent_cfg.get("name", ai_assistant)

    console.print(f"[cyan]Agent:[/cyan] {agent_name} [dim]({ai_assistant})[/dim]")
    console.print(f"[cyan]Project:[/cyan] [dim]{project_root}[/dim]\n")

    # 3. Interactive MCP recipe selection
    recipe_choices = {k: v["display_name"] for k, v in MCP_RECIPES.items()}
    selected_key = select_with_arrows(recipe_choices, "Choose an MCP recipe to install:")

    # 4. Install
    mcp_config_file = agent_cfg.get("mcp_config_file")
    agent_folder = agent_cfg.get("folder")

    tracker = StepTracker(f"Install MCP: {selected_key}")
    tracker.add("resolve", "Resolve config path")
    tracker.add("merge", "Merge MCP entry")
    tracker.add("write", "Write config file")
    tracker.add("index", "Update mcp-use.md index")

    newly_installed = False

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))

        if mcp_config_file and agent_folder:
            # Path A: native JSON config (Claude, Cursor)
            mcp_json_path = project_root / agent_folder.rstrip("/") / mcp_config_file
            tracker.complete("resolve", str(mcp_json_path.relative_to(project_root)))

            tracker.start("merge")
            existing = _read_mcp_json(mcp_json_path)
            if selected_key in existing["mcpServers"]:
                tracker.skip("merge", f"{selected_key} already installed")
                tracker.skip("write", "no changes needed")
                tracker.skip("index", "no changes needed")
            else:
                existing["mcpServers"][selected_key] = _build_mcp_server_entry(selected_key)
                tracker.complete("merge", f"added {selected_key}")

                tracker.start("write")
                try:
                    mcp_json_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(mcp_json_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)
                        f.write("\n")
                    tracker.complete("write", str(mcp_json_path.relative_to(project_root)))
                    newly_installed = True
                except OSError as e:
                    tracker.error("write", str(e))
                    raise typer.Exit(1)

        else:
            # Path B: markdown fallback (all other agents)
            md_path = project_root / ".infrakit" / "mcp-servers.md"
            tracker.complete("resolve", str(md_path.relative_to(project_root)))

            tracker.start("merge")
            existing_content = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            if selected_key in existing_content:
                tracker.skip("merge", f"{selected_key} already documented")
                tracker.skip("write", "no changes needed")
                tracker.skip("index", "no changes needed")
            else:
                tracker.complete("merge", "building markdown entry")
                tracker.start("write")
                try:
                    md_block = _build_mcp_markdown_block(selected_key, MCP_RECIPES[selected_key], agent_name)
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

        # Update mcp-use.md index
        if newly_installed:
            tracker.start("index")
            try:
                _update_mcp_use_table(project_root, selected_key)
                tracker.complete("index", ".infrakit/mcp-use.md")
            except OSError as e:
                tracker.error("index", str(e))

    console.print(tracker.render())

    if newly_installed:
        console.print(f"\n[bold green]MCP recipe installed:[/bold green] {selected_key}")
    else:
        console.print(f"\n[dim]{selected_key} was already configured — nothing changed.[/dim]")

@app.command()
def version():
    """Display version and system information."""
    import platform
    import importlib.metadata
    
    show_banner()
    
    # Get CLI version from package metadata
    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("infrakit-cli")
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
            # Remove 'v' prefix if present
            if template_version.startswith("v"):
                template_version = template_version[1:]
            release_date = release_data.get("published_at", "unknown")
            if release_date != "unknown":
                # Format the date nicely
                try:
                    dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
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
        padding=(1, 2)
    )

    console.print(panel)
    console.print()




def main():
    app()

if __name__ == "__main__":
    main()

