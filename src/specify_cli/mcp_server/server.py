"""MCP tool registration and stdio server lifecycle."""

from __future__ import annotations

from collections.abc import Callable

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent

from ..mcp_version import register as register_version
from .catalog import (
    CommandAdapterError,
    CommandDescription,
    CommandList,
    VersionResult,
    describe_command,
    list_commands,
)
from .executor import run_command

CommandRunner = Callable[[str], VersionResult]


def _tool_error(exc: CommandAdapterError) -> CallToolResult:
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"{exc.code}: {exc.message}",
            )
        ],
        structuredContent=exc.payload(),
        isError=True,
    )


def create_server(
    *,
    command_runner: CommandRunner = run_command,
) -> MCPServer:
    """Create the experimental version-only MCP server."""
    server = MCPServer(
        name="specify",
        title="Spec Kit CLI",
        description=(
            "Experimental stdio-only MCP adapter for stable Specify CLI JSON commands."
        ),
        version="experimental",
        log_level="ERROR",
    )

    @server.tool(
        name="specify_list_commands",
        description="List CLI commands supported by the Spec Kit MCP server.",
    )
    def specify_list_commands() -> CommandList:
        return list_commands()

    @server.tool(
        name="specify_describe_command",
        description="Describe one CLI command supported by the Spec Kit MCP server.",
    )
    def specify_describe_command(command: str) -> CommandDescription:
        try:
            return describe_command(command)
        except CommandAdapterError as exc:
            return _tool_error(exc)

    @server.tool(
        name="specify_run_command",
        description=(
            "Run one supported CLI command and return its direct stable JSON payload."
        ),
    )
    def specify_run_command(command: str) -> VersionResult:
        try:
            return command_runner(command)
        except CommandAdapterError as exc:
            return _tool_error(exc)

    register_version(server)

    return server


def run_stdio_server() -> None:
    """Run the MCP server using stdio and no alternate transport."""
    create_server().run(transport="stdio")
