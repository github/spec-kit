"""
specify_cli.core.shell - Shell Output and Rich Utilities
=========================================================

Utility helpers that wrap Rich for beautiful terminal output.

This module provides utilities for colored text, JSON formatting, markdown
rendering, progress bars, and timing decorators.

Key Features
-----------
• **Rich Integration**: Beautiful terminal output with syntax highlighting
• **Colored Output**: Easy color-coded text and error messages
• **JSON Formatting**: Pretty-printed JSON with syntax highlighting
• **Markdown Rendering**: Rich markdown display with formatting
• **Progress Tracking**: Context-manager progress bars
• **Timing Decorators**: Function timing with automatic display

Examples
--------
    >>> from specify_cli.core.shell import colour, dump_json, timed
    >>>
    >>> # Colored output
    >>> colour("Success!", "green")
    >>>
    >>> # JSON formatting
    >>> data = {"name": "specify", "version": "0.0.23"}
    >>> dump_json(data)
    >>>
    >>> # Timing decorator
    >>> @timed
    >>> def build_spec():
    >>>     pass
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from typing import Any

from rich.console import Console
from rich.json import JSON as RichJSON
from rich.markdown import Markdown
from rich.progress import Progress
from rich.table import Table
from rich.traceback import install as _install_tb

__all__ = [
    "colour",
    "colour_stderr",
    "dump_json",
    "install_rich",
    "markdown",
    "progress_bar",
    "rich_table",
    "timed",
]

# One global console instance – reuse it everywhere
_console = Console(highlight=False)
# Console for stderr output
_console_stderr = Console(highlight=False, file=sys.stderr)


# --------------------------------------------------------------------------- #
# Core helpers
# --------------------------------------------------------------------------- #
def install_rich(show_locals: bool = False) -> None:
    """Activate Rich tracebacks (call once, idempotent)."""
    _install_tb(show_locals=show_locals)


def colour(text: str, style: str = "green", *, nl: bool = True) -> None:
    """Print *text* in *style* colour (defaults to green)."""
    _console.print(text, style=style, end="\n" if nl else "")


def colour_stderr(text: str, style: str = "green", *, nl: bool = True) -> None:
    """Print *text* in *style* colour to stderr."""
    _console_stderr.print(text, style=style, end="\n" if nl else "")


def dump_json(obj: Any) -> None:
    """Pretty-print a Python object as syntax-highlighted JSON."""
    try:
        json_str = json.dumps(obj, default=str, indent=2)
        _console.print(RichJSON(json_str))
    except Exception as e:
        colour(f"Error formatting JSON: {e}", "red")
        raise


def markdown(md: str) -> None:
    """Render Markdown *md* via Rich (headings, lists, code blocks…)."""
    _console.print(Markdown(md))


def timed(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator: run *fn*, then print "✔ fn_name 1.23s" in green.

    Usage
    -----
    @timed
    def build():
        ...
    """

    @wraps(fn)
    def _wrap(*a, **kw):
        t0 = time.perf_counter()
        exception_occurred = False

        try:
            result = fn(*a, **kw)
            return result
        except Exception as e:
            exception_occurred = True
            raise
        finally:
            duration = time.perf_counter() - t0

            # Original display behavior
            if not exception_occurred:
                colour(f"✔ {fn.__name__} {duration:.2f}s", "green")
            else:
                colour(f"✗ {fn.__name__} {duration:.2f}s (failed)", "red")

    return _wrap


# --------------------------------------------------------------------------- #
# Rich convenience wrappers
# --------------------------------------------------------------------------- #
def rich_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    """Quickly render a table given *headers* and an iterable of *rows*."""
    t = Table(*headers, header_style="bold magenta")
    for r in rows:
        t.add_row(*map(str, r))
    _console.print(t)


def progress_bar(total: int):
    """
    Context-manager yielding a callable *advance()* that increments the bar.

    Example
    -------
    with progress_bar(10) as advance:
        for _ in range(10):
            work()
            advance()
    """

    class _Ctx:
        def __enter__(self):
            self._p = Progress()
            self._p.__enter__()
            self._task = self._p.add_task("work", total=total)
            self._advances = 0
            self._start_time = time.time()

            def advance(inc=1):
                self._advances += inc
                return self._p.update(self._task, advance=inc)

            return advance

        def __exit__(self, exc_type, exc, tb):
            return self._p.__exit__(exc_type, exc, tb)

    return _Ctx()
