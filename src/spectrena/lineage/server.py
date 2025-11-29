#!/usr/bin/env python3
"""
Standalone MCP server entry point.

This gets installed as `spectrena-mcp` for easy MCP client configuration.
"""

import sys


def main():
    """Entry point for spectrena-mcp command."""
    try:
        from spectrena.lineage.db import create_mcp_server
    except ImportError:
        print("Error: Lineage dependencies not installed.", file=sys.stderr)
        print("Run: uv pip install spectrena[lineage-surreal]", file=sys.stderr)
        sys.exit(1)

    server = create_mcp_server()
    server.run()


if __name__ == "__main__":
    main()
