"""
MCP (Model Context Protocol) server for spec-kit.

This module provides an MCP server that exposes spec-kit functionality
to AI assistants like Claude Desktop.

Usage:
    python -m speckit.mcp

Or via CLI:
    speckit mcp serve
"""

from speckit.mcp.server import MCP_AVAILABLE, create_server, run_server

__all__ = [
    "MCP_AVAILABLE",
    "create_server",
    "run_server",
]
