"""
Spec-Kit MCP Server

Model Context Protocol server for Spec-Driven Development toolkit.
"""

__version__ = "0.0.2"
__all__ = ["server_main", "cli_main"]

def server_main():
    """Entry point for MCP server."""
    from .server import main
    main()

def cli_main():
    """Entry point for CLI."""
    from .cli import main
    main()