"""Singleton Rich :class:`~rich.console.Console` used by every CLI module.

A shared instance keeps colour state, terminal width detection, and output
buffering consistent across the whole CLI. Modules should import the symbol
``console`` from this module rather than constructing their own.
"""

from rich.console import Console

console = Console()
