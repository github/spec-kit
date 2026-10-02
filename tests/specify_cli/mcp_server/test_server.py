"""In-memory tests for MCP tool registration and dispatch."""

import asyncio
import json

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from specify_cli.mcp_server.catalog import CommandAdapterError, VersionResult
from specify_cli.mcp_server.server import create_server

VERSION_PAYLOAD = {
    "cli_version": "1.2.3",
    "runtime": {"python": "3.13.1", "openssl": None},
    "system": {
        "platform": "ExampleOS",
        "architecture": "example64",
        "os_version": "ExampleOS 4.5",
    },
    "features": {"workflow_catalog": True},
}


def _run(coro):
    return asyncio.run(coro)


def _error_payload(exc: ToolError) -> dict[str, object]:
    text = str(exc)
    return json.loads(text[text.index("{") :])


def test_tool_discovery_exposes_only_generic_surface_with_typed_inputs():
    tools = _run(create_server().list_tools())

    assert [tool.name for tool in tools] == [
        "specify_list_commands",
        "specify_describe_command",
        "specify_run_command",
    ]
    schemas = {tool.name: tool.input_schema for tool in tools}
    assert schemas["specify_list_commands"]["properties"] == {}
    for name in ("specify_describe_command", "specify_run_command"):
        assert schemas[name]["required"] == ["command"]
        assert schemas[name]["properties"]["command"]["type"] == "string"


def test_list_and_describe_tools_return_version_inventory():
    server = create_server()

    listed = _run(server.call_tool("specify_list_commands", {}))
    described = _run(
        server.call_tool("specify_describe_command", {"command": "version"})
    )

    assert listed.structured_content["commands"][0]["command"] == "version"
    assert described.structured_content["command"] == "version"


def test_run_tool_returns_direct_version_payload():
    server = create_server(
        command_runner=lambda command: VersionResult.model_validate(VERSION_PAYLOAD)
    )

    result = _run(server.call_tool("specify_run_command", {"command": "version"}))

    assert result.structured_content == VERSION_PAYLOAD
    assert "ok" not in result.structured_content
    assert "result" not in result.structured_content
    assert "schema_version" not in result.structured_content


@pytest.mark.parametrize(
    ("tool", "command"),
    [
        ("specify_describe_command", "artifact.list"),
        ("specify_run_command", "check"),
    ],
)
def test_tools_reject_unavailable_commands_with_structured_error(tool, command):
    def unavailable(_: str) -> VersionResult:
        raise CommandAdapterError(
            "unavailable_command",
            "Unavailable.",
            {"command": command, "available_commands": ["version"]},
        )

    server = create_server(command_runner=unavailable)
    with pytest.raises(ToolError) as captured:
        _run(server.call_tool(tool, {"command": command}))

    payload = _error_payload(captured.value)
    assert payload["error"]["code"] == "unavailable_command"
    assert payload["error"]["details"]["command"] == command
