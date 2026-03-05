#!/usr/bin/env python3
"""
Spec-Kit MCP Server

Main FastMCP server implementation for specification-driven development workflow.
Provides tools for feature specification, planning, task breakdown, and domain analysis.
"""

import asyncio
import sys
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Please install with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Import all MCP tools
from .tools import (
    specify_tool,
    plan_tool,
    tasks_tool,
    initialize_tool,
    get_context_tool,
    analyze_domain_tool,
    clarify_tool,
    constitution_tool,
    task_progress_tool,
    validate_compliance_tool,
    analyze_mcp_tools_tool,
    get_mcp_spec_version_tool
)

# Import resources
from .resources import register_resources


def create_server() -> FastMCP:
    """Create and configure the Spec-Kit MCP server."""

    server = FastMCP("spec-kit")

    # Register all tools
    server.add_tool(specify_tool)
    server.add_tool(plan_tool)
    server.add_tool(tasks_tool)
    server.add_tool(initialize_tool)
    server.add_tool(get_context_tool)
    server.add_tool(analyze_domain_tool)
    server.add_tool(clarify_tool)
    server.add_tool(constitution_tool)
    server.add_tool(task_progress_tool)
    server.add_tool(validate_compliance_tool)
    server.add_tool(analyze_mcp_tools_tool)
    server.add_tool(get_mcp_spec_version_tool)

    # Register resources (templates, schemas, sample data)
    register_resources(server)

    return server


async def main():
    """Main entry point for the MCP server."""
    server = create_server()

    # Run the server with stdio transport
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())