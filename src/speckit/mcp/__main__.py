"""
Entry point for running the MCP server.

Usage:
    python -m speckit.mcp
    python -m speckit.mcp /path/to/project
"""

import asyncio
import sys
from pathlib import Path

from speckit.mcp.server import run_server, MCP_AVAILABLE


def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        print("Error: MCP is not installed. Install with: pip install speckit-ai[mcp]")
        sys.exit(1)

    # Get project path from command line if provided
    project_path = None
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])

    # Run the server
    asyncio.run(run_server(project_path))


if __name__ == "__main__":
    main()
