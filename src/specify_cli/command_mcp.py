"""CLI adapter for the experimental ``specify mcp`` stdio server."""

from __future__ import annotations

import typer


def mcp() -> None:
    """Run the experimental version-only MCP server over stdio."""
    from .mcp_server import run_stdio_server

    run_stdio_server()


def register(app: typer.Typer) -> None:
    """Register ``specify mcp`` on the root application."""
    app.command()(mcp)
