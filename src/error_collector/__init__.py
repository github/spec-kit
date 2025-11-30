#!/usr/bin/env python3
"""
Error Collector CLI - Real-time error collection from multiple sources

Collects errors from:
- Google Chrome DevTools console
- VS Code / Cursor IDE logs
- Any CLI tool's stderr output

Usage:
    error-collector chrome          # Collect Chrome console errors
    error-collector vscode          # Watch VS Code logs
    error-collector cursor          # Watch Cursor logs
    error-collector cli -- <cmd>    # Run command and collect stderr
    error-collector all             # Watch all available sources
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, AsyncIterator
import signal

try:
    import typer
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.layout import Layout
except ImportError:
    print("Missing dependencies. Install with: pip install typer rich")
    sys.exit(1)

# Optional websockets for Chrome DevTools
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


class ErrorLevel(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CollectedError:
    """Represents a collected error from any source"""
    timestamp: datetime
    source: str
    level: ErrorLevel
    message: str
    details: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "level": self.level.value,
            "message": self.message,
            "details": self.details,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "stack_trace": self.stack_trace,
        }


class ErrorStore:
    """Thread-safe storage for collected errors"""

    def __init__(self, max_errors: int = 1000):
        self._errors: deque[CollectedError] = deque(maxlen=max_errors)
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[CollectedError], None]] = []

    def add(self, error: CollectedError):
        with self._lock:
            self._errors.append(error)
        for cb in self._callbacks:
            try:
                cb(error)
            except Exception:
                pass

    def get_all(self) -> list[CollectedError]:
        with self._lock:
            return list(self._errors)

    def get_recent(self, count: int = 50) -> list[CollectedError]:
        with self._lock:
            return list(self._errors)[-count:]

    def clear(self):
        with self._lock:
            self._errors.clear()

    def on_error(self, callback: Callable[[CollectedError], None]):
        self._callbacks.append(callback)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._errors)


# ============================================================================
# Chrome DevTools Protocol Connector
# ============================================================================

class ChromeConnector:
    """Connects to Chrome DevTools Protocol to capture console errors"""

    DEFAULT_PORT = 9222

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.ws_url: Optional[str] = None
        self._running = False

    async def discover_targets(self) -> list[dict]:
        """Discover available Chrome debugging targets"""
        import urllib.request
        try:
            url = f"http://localhost:{self.port}/json"
            with urllib.request.urlopen(url, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Chrome DevTools on port {self.port}. "
                f"Start Chrome with: google-chrome --remote-debugging-port={self.port}\n"
                f"Error: {e}"
            )

    async def collect_errors(self, store: ErrorStore, target_idx: int = 0):
        """Stream console errors from Chrome"""
        if not HAS_WEBSOCKETS:
            raise RuntimeError("websockets package required. Install with: pip install websockets")

        targets = await self.discover_targets()
        if not targets:
            raise ConnectionError("No Chrome targets found")

        # Find a page target
        page_targets = [t for t in targets if t.get("type") == "page"]
        if not page_targets:
            raise ConnectionError("No page targets found in Chrome")

        target = page_targets[min(target_idx, len(page_targets) - 1)]
        ws_url = target.get("webSocketDebuggerUrl")

        if not ws_url:
            raise ConnectionError("No WebSocket URL available for target")

        self._running = True
        msg_id = 1

        async with websockets.connect(ws_url) as ws:
            # Enable Console and Runtime domains
            await ws.send(json.dumps({"id": msg_id, "method": "Console.enable"}))
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.enable"}))
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Log.enable"}))

            while self._running:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(message)

                    # Handle console messages
                    if data.get("method") == "Console.messageAdded":
                        msg = data["params"]["message"]
                        level = self._map_level(msg.get("level", "log"))

                        if level in (ErrorLevel.ERROR, ErrorLevel.WARNING, ErrorLevel.CRITICAL):
                            error = CollectedError(
                                timestamp=datetime.now(),
                                source="chrome",
                                level=level,
                                message=msg.get("text", ""),
                                file_path=msg.get("url"),
                                line_number=msg.get("line"),
                                column=msg.get("column"),
                                stack_trace=msg.get("stackTrace"),
                            )
                            store.add(error)

                    # Handle runtime exceptions
                    elif data.get("method") == "Runtime.exceptionThrown":
                        exc = data["params"]["exceptionDetails"]
                        error = CollectedError(
                            timestamp=datetime.now(),
                            source="chrome",
                            level=ErrorLevel.ERROR,
                            message=exc.get("text", "Runtime exception"),
                            file_path=exc.get("url"),
                            line_number=exc.get("lineNumber"),
                            column=exc.get("columnNumber"),
                            stack_trace=self._format_stack(exc.get("stackTrace")),
                        )
                        store.add(error)

                    # Handle Log domain messages
                    elif data.get("method") == "Log.entryAdded":
                        entry = data["params"]["entry"]
                        level = self._map_level(entry.get("level", "info"))

                        if level in (ErrorLevel.ERROR, ErrorLevel.WARNING, ErrorLevel.CRITICAL):
                            error = CollectedError(
                                timestamp=datetime.now(),
                                source="chrome",
                                level=level,
                                message=entry.get("text", ""),
                                file_path=entry.get("url"),
                                line_number=entry.get("lineNumber"),
                            )
                            store.add(error)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if self._running:
                        store.add(CollectedError(
                            timestamp=datetime.now(),
                            source="chrome-connector",
                            level=ErrorLevel.WARNING,
                            message=f"Connection issue: {e}",
                        ))
                    break

    def stop(self):
        self._running = False

    def _map_level(self, level: str) -> ErrorLevel:
        mapping = {
            "error": ErrorLevel.ERROR,
            "warning": ErrorLevel.WARNING,
            "warn": ErrorLevel.WARNING,
            "info": ErrorLevel.INFO,
            "log": ErrorLevel.INFO,
            "debug": ErrorLevel.DEBUG,
            "verbose": ErrorLevel.DEBUG,
        }
        return mapping.get(level.lower(), ErrorLevel.INFO)

    def _format_stack(self, stack: Optional[dict]) -> Optional[str]:
        if not stack or "callFrames" not in stack:
            return None
        lines = []
        for frame in stack["callFrames"]:
            fn = frame.get("functionName", "<anonymous>")
            url = frame.get("url", "")
            line = frame.get("lineNumber", 0)
            col = frame.get("columnNumber", 0)
            lines.append(f"  at {fn} ({url}:{line}:{col})")
        return "\n".join(lines)


# ============================================================================
# Log File Watcher (VS Code, Cursor, etc.)
# ============================================================================

class LogWatcher:
    """Watches log files for errors"""

    # Common log locations
    LOG_PATHS = {
        "vscode": [
            Path.home() / ".config/Code/logs",
            Path.home() / "Library/Application Support/Code/logs",
            Path.home() / "AppData/Roaming/Code/logs",
        ],
        "vscode-insiders": [
            Path.home() / ".config/Code - Insiders/logs",
            Path.home() / "Library/Application Support/Code - Insiders/logs",
            Path.home() / "AppData/Roaming/Code - Insiders/logs",
        ],
        "cursor": [
            Path.home() / ".config/Cursor/logs",
            Path.home() / "Library/Application Support/Cursor/logs",
            Path.home() / "AppData/Roaming/Cursor/logs",
        ],
    }

    # Error patterns to match
    ERROR_PATTERNS = [
        (re.compile(r"\[error\]", re.I), ErrorLevel.ERROR),
        (re.compile(r"\[warn(?:ing)?\]", re.I), ErrorLevel.WARNING),
        (re.compile(r"error:", re.I), ErrorLevel.ERROR),
        (re.compile(r"exception:", re.I), ErrorLevel.ERROR),
        (re.compile(r"failed:", re.I), ErrorLevel.ERROR),
        (re.compile(r"fatal:", re.I), ErrorLevel.CRITICAL),
        (re.compile(r"traceback", re.I), ErrorLevel.ERROR),
        (re.compile(r"unhandled", re.I), ErrorLevel.ERROR),
    ]

    def __init__(self, source: str):
        self.source = source
        self._running = False
        self._watched_files: dict[Path, int] = {}  # path -> last position

    def find_log_dir(self) -> Optional[Path]:
        """Find the log directory for this source"""
        paths = self.LOG_PATHS.get(self.source, [])
        for path in paths:
            if path.exists():
                return path
        return None

    def watch(self, store: ErrorStore, log_dir: Optional[Path] = None):
        """Watch log files for errors"""
        if log_dir is None:
            log_dir = self.find_log_dir()

        if not log_dir or not log_dir.exists():
            store.add(CollectedError(
                timestamp=datetime.now(),
                source=self.source,
                level=ErrorLevel.WARNING,
                message=f"Log directory not found for {self.source}",
            ))
            return

        self._running = True

        while self._running:
            # Find all log files
            log_files = list(log_dir.rglob("*.log"))

            for log_file in log_files:
                try:
                    self._process_log_file(log_file, store)
                except Exception as e:
                    pass  # Ignore file access errors

            time.sleep(1.0)  # Check every second

    def _process_log_file(self, log_file: Path, store: ErrorStore):
        """Process a single log file for new errors"""
        stat = log_file.stat()
        current_size = stat.st_size
        last_pos = self._watched_files.get(log_file, 0)

        # Skip if file hasn't grown
        if current_size <= last_pos:
            if current_size < last_pos:
                # File was truncated, reset position
                self._watched_files[log_file] = 0
                last_pos = 0
            else:
                return

        # Read new content
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(last_pos)
            new_content = f.read()
            self._watched_files[log_file] = f.tell()

        # Parse for errors
        for line in new_content.splitlines():
            level = self._detect_error_level(line)
            if level:
                error = CollectedError(
                    timestamp=datetime.now(),
                    source=self.source,
                    level=level,
                    message=line.strip()[:500],  # Truncate long lines
                    file_path=str(log_file),
                )
                store.add(error)

    def _detect_error_level(self, line: str) -> Optional[ErrorLevel]:
        """Detect if a line contains an error"""
        for pattern, level in self.ERROR_PATTERNS:
            if pattern.search(line):
                return level
        return None

    def stop(self):
        self._running = False


# ============================================================================
# CLI Process Stderr Collector
# ============================================================================

class CLICollector:
    """Collects stderr from CLI commands"""

    def __init__(self, command: list[str], name: Optional[str] = None):
        self.command = command
        self.name = name or command[0] if command else "cli"
        self._process: Optional[subprocess.Popen] = None
        self._running = False

    def run(self, store: ErrorStore) -> int:
        """Run the command and collect stderr errors"""
        self._running = True

        try:
            self._process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Thread to read stdout (just pass through)
            def read_stdout():
                if self._process and self._process.stdout:
                    for line in self._process.stdout:
                        print(line, end="")

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            # Read stderr and collect errors
            if self._process.stderr:
                for line in self._process.stderr:
                    line = line.rstrip()
                    if line:
                        level = self._detect_level(line)
                        error = CollectedError(
                            timestamp=datetime.now(),
                            source=self.name,
                            level=level,
                            message=line,
                        )
                        store.add(error)
                        # Also print to stderr so user sees it
                        print(line, file=sys.stderr)

            self._process.wait()
            return self._process.returncode or 0

        except FileNotFoundError:
            store.add(CollectedError(
                timestamp=datetime.now(),
                source=self.name,
                level=ErrorLevel.CRITICAL,
                message=f"Command not found: {self.command[0]}",
            ))
            return 127
        except Exception as e:
            store.add(CollectedError(
                timestamp=datetime.now(),
                source=self.name,
                level=ErrorLevel.CRITICAL,
                message=f"Failed to run command: {e}",
            ))
            return 1

    def _detect_level(self, line: str) -> ErrorLevel:
        """Detect error level from stderr line"""
        lower = line.lower()
        if "fatal" in lower or "critical" in lower:
            return ErrorLevel.CRITICAL
        if "error" in lower or "exception" in lower or "failed" in lower:
            return ErrorLevel.ERROR
        if "warn" in lower:
            return ErrorLevel.WARNING
        return ErrorLevel.ERROR  # Default stderr to error

    def stop(self):
        self._running = False
        if self._process:
            self._process.terminate()


# ============================================================================
# Terminal UI
# ============================================================================

class ErrorDisplay:
    """Rich terminal display for errors"""

    LEVEL_STYLES = {
        ErrorLevel.DEBUG: "dim",
        ErrorLevel.INFO: "blue",
        ErrorLevel.WARNING: "yellow",
        ErrorLevel.ERROR: "red",
        ErrorLevel.CRITICAL: "bold red",
    }

    LEVEL_ICONS = {
        ErrorLevel.DEBUG: ".",
        ErrorLevel.INFO: "i",
        ErrorLevel.WARNING: "!",
        ErrorLevel.ERROR: "X",
        ErrorLevel.CRITICAL: "!!!",
    }

    def __init__(self, console: Console, store: ErrorStore):
        self.console = console
        self.store = store
        self._last_count = 0

    def render_table(self, max_rows: int = 30) -> Table:
        """Render errors as a Rich table"""
        table = Table(
            title="Collected Errors",
            show_header=True,
            header_style="bold cyan",
            expand=True,
        )

        table.add_column("Time", style="dim", width=12)
        table.add_column("Lvl", width=4)
        table.add_column("Source", style="cyan", width=12)
        table.add_column("Message", overflow="fold")

        errors = self.store.get_recent(max_rows)

        for error in errors:
            style = self.LEVEL_STYLES.get(error.level, "")
            icon = self.LEVEL_ICONS.get(error.level, "?")

            time_str = error.timestamp.strftime("%H:%M:%S")
            msg = error.message[:200] + "..." if len(error.message) > 200 else error.message

            table.add_row(
                time_str,
                Text(f"[{icon}]", style=style),
                error.source,
                Text(msg, style=style),
            )

        return table

    def render_summary(self) -> Panel:
        """Render a summary panel"""
        errors = self.store.get_all()

        by_source: dict[str, int] = {}
        by_level: dict[ErrorLevel, int] = {}

        for e in errors:
            by_source[e.source] = by_source.get(e.source, 0) + 1
            by_level[e.level] = by_level.get(e.level, 0) + 1

        lines = [
            f"[bold]Total Errors:[/bold] {len(errors)}",
            "",
            "[bold]By Source:[/bold]",
        ]
        for source, count in sorted(by_source.items()):
            lines.append(f"  {source}: {count}")

        lines.append("")
        lines.append("[bold]By Level:[/bold]")
        for level in ErrorLevel:
            count = by_level.get(level, 0)
            if count > 0:
                style = self.LEVEL_STYLES.get(level, "")
                lines.append(f"  [{style}]{level.value}: {count}[/{style}]")

        return Panel("\n".join(lines), title="Summary", border_style="cyan")


# ============================================================================
# CLI Application
# ============================================================================

console = Console()
app = typer.Typer(
    name="error-collector",
    help="Real-time error collection from Chrome, VS Code, Cursor, and CLI tools",
    add_completion=False,
)


def run_with_display(store: ErrorStore, title: str = "Error Collector"):
    """Run the live display loop"""
    display = ErrorDisplay(console, store)

    with Live(display.render_table(), console=console, refresh_per_second=2) as live:
        try:
            while True:
                live.update(display.render_table())
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

    # Show final summary
    console.print()
    console.print(display.render_summary())


@app.command()
def chrome(
    port: int = typer.Option(9222, "--port", "-p", help="Chrome DevTools port"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    Collect console errors from Google Chrome.

    Start Chrome with remote debugging enabled:
        google-chrome --remote-debugging-port=9222

    Or on macOS:
        /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
    """
    if not HAS_WEBSOCKETS:
        console.print("[red]Error:[/red] websockets package required")
        console.print("Install with: pip install websockets")
        raise typer.Exit(1)

    store = ErrorStore()
    connector = ChromeConnector(port=port)

    console.print(f"[cyan]Connecting to Chrome on port {port}...[/cyan]")

    async def run():
        try:
            targets = await connector.discover_targets()
            console.print(f"[green]Connected![/green] Found {len(targets)} target(s)")

            # Start collection in background
            collect_task = asyncio.create_task(connector.collect_errors(store))

            # Run display
            display = ErrorDisplay(console, store)

            try:
                with Live(display.render_table(), console=console, refresh_per_second=2) as live:
                    while True:
                        live.update(display.render_table())
                        await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                connector.stop()
                await collect_task

        except ConnectionError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass

    # Output JSON if requested
    if json_output:
        errors = [e.to_dict() for e in store.get_all()]
        print(json.dumps(errors, indent=2))
    else:
        display = ErrorDisplay(console, store)
        console.print()
        console.print(display.render_summary())


@app.command()
def vscode(
    log_dir: Optional[Path] = typer.Option(None, "--log-dir", "-d", help="Custom log directory"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Watch VS Code logs for errors."""
    store = ErrorStore()
    watcher = LogWatcher("vscode")

    log_path = log_dir or watcher.find_log_dir()
    if not log_path:
        console.print("[red]Error:[/red] VS Code log directory not found")
        console.print("Specify with --log-dir or ensure VS Code is installed")
        raise typer.Exit(1)

    console.print(f"[cyan]Watching VS Code logs:[/cyan] {log_path}")

    # Start watcher in background thread
    thread = threading.Thread(target=watcher.watch, args=(store, log_path), daemon=True)
    thread.start()

    run_with_display(store, "VS Code Errors")
    watcher.stop()

    if json_output:
        errors = [e.to_dict() for e in store.get_all()]
        print(json.dumps(errors, indent=2))


@app.command()
def cursor(
    log_dir: Optional[Path] = typer.Option(None, "--log-dir", "-d", help="Custom log directory"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Watch Cursor IDE logs for errors."""
    store = ErrorStore()
    watcher = LogWatcher("cursor")

    log_path = log_dir or watcher.find_log_dir()
    if not log_path:
        console.print("[red]Error:[/red] Cursor log directory not found")
        console.print("Specify with --log-dir or ensure Cursor is installed")
        raise typer.Exit(1)

    console.print(f"[cyan]Watching Cursor logs:[/cyan] {log_path}")

    thread = threading.Thread(target=watcher.watch, args=(store, log_path), daemon=True)
    thread.start()

    run_with_display(store, "Cursor Errors")
    watcher.stop()

    if json_output:
        errors = [e.to_dict() for e in store.get_all()]
        print(json.dumps(errors, indent=2))


@app.command()
def cli(
    command: list[str] = typer.Argument(None, help="Command to run"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for this source"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    Run a command and collect its stderr errors.

    Example:
        error-collector cli -- npm run build
        error-collector cli -- pytest tests/
        error-collector cli --name myapp -- python app.py
    """
    if not command:
        console.print("[red]Error:[/red] No command specified")
        console.print("Usage: error-collector cli -- <command>")
        raise typer.Exit(1)

    store = ErrorStore()
    collector = CLICollector(command, name)

    console.print(f"[cyan]Running:[/cyan] {' '.join(command)}")
    console.print()

    exit_code = collector.run(store)

    console.print()
    display = ErrorDisplay(console, store)
    console.print(display.render_summary())

    if json_output:
        errors = [e.to_dict() for e in store.get_all()]
        print(json.dumps(errors, indent=2))

    raise typer.Exit(exit_code)


@app.command("all")
def watch_all(
    chrome_port: int = typer.Option(9222, "--chrome-port", help="Chrome DevTools port"),
    no_chrome: bool = typer.Option(False, "--no-chrome", help="Skip Chrome"),
    no_vscode: bool = typer.Option(False, "--no-vscode", help="Skip VS Code"),
    no_cursor: bool = typer.Option(False, "--no-cursor", help="Skip Cursor"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Watch all available error sources simultaneously."""
    store = ErrorStore()
    threads = []
    connectors = []

    # VS Code watcher
    if not no_vscode:
        vscode_watcher = LogWatcher("vscode")
        if vscode_watcher.find_log_dir():
            console.print("[green]Found VS Code logs[/green]")
            t = threading.Thread(target=vscode_watcher.watch, args=(store,), daemon=True)
            t.start()
            threads.append(t)
            connectors.append(vscode_watcher)

    # Cursor watcher
    if not no_cursor:
        cursor_watcher = LogWatcher("cursor")
        if cursor_watcher.find_log_dir():
            console.print("[green]Found Cursor logs[/green]")
            t = threading.Thread(target=cursor_watcher.watch, args=(store,), daemon=True)
            t.start()
            threads.append(t)
            connectors.append(cursor_watcher)

    # Chrome connector
    chrome_task = None
    if not no_chrome and HAS_WEBSOCKETS:
        chrome_connector = ChromeConnector(port=chrome_port)

        async def try_chrome():
            try:
                await chrome_connector.discover_targets()
                console.print(f"[green]Found Chrome on port {chrome_port}[/green]")
                await chrome_connector.collect_errors(store)
            except Exception:
                console.print(f"[yellow]Chrome not available on port {chrome_port}[/yellow]")

        def run_chrome():
            asyncio.run(try_chrome())

        t = threading.Thread(target=run_chrome, daemon=True)
        t.start()
        threads.append(t)
        connectors.append(chrome_connector)

    console.print()
    console.print("[cyan]Watching for errors... Press Ctrl+C to stop[/cyan]")
    console.print()

    run_with_display(store, "All Error Sources")

    # Stop all connectors
    for c in connectors:
        c.stop()

    if json_output:
        errors = [e.to_dict() for e in store.get_all()]
        print(json.dumps(errors, indent=2))


@app.command()
def export(
    output_file: Path = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, csv, txt"),
):
    """Export collected errors to a file (use with pipes)."""
    console.print(f"[cyan]Reading errors from stdin...[/cyan]")

    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        console.print("[red]Error:[/red] Invalid JSON input")
        raise typer.Exit(1)

    if format == "json":
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
    elif format == "csv":
        import csv
        with open(output_file, "w", newline="") as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    elif format == "txt":
        with open(output_file, "w") as f:
            for e in data:
                f.write(f"[{e['timestamp']}] [{e['level']}] {e['source']}: {e['message']}\n")
    else:
        console.print(f"[red]Error:[/red] Unknown format: {format}")
        raise typer.Exit(1)

    console.print(f"[green]Exported {len(data)} errors to {output_file}[/green]")


def main():
    app()


if __name__ == "__main__":
    main()
