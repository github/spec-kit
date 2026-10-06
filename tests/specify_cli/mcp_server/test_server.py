"""In-memory tests for MCP tool registration and dispatch."""

import asyncio

import pytest

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


def test_tool_discovery_exposes_first_class_and_transitional_tools():
    tools = _run(create_server().list_tools())

    assert [tool.name for tool in tools] == [
        "specify_list_commands",
        "specify_describe_command",
        "specify_run_command",
        "specify_version",
    ]
    schemas = {tool.name: tool.input_schema for tool in tools}
    assert schemas["specify_list_commands"]["properties"] == {}
    assert schemas["specify_version"]["properties"] == {}
    assert schemas["specify_version"]["additionalProperties"] is False
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
    ("tool", "command", "message"),
    [
        (
            "specify_describe_command",
            "artifact.list",
            (
                "Command 'artifact.list' is not available through the "
                "experimental Spec Kit MCP server."
            ),
        ),
        ("specify_run_command", "check", "Unavailable."),
    ],
)
def test_tools_reject_unavailable_commands_with_structured_error(
    tool,
    command,
    message,
):
    def unavailable(_: str) -> VersionResult:
        raise CommandAdapterError(
            "unavailable_command",
            "Unavailable.",
            {"command": command, "available_commands": ["version"]},
        )

    server = create_server(command_runner=unavailable)
    result = _run(server.call_tool(tool, {"command": command}))

    assert result.is_error is True
    assert result.structured_content == {
        "error": {
            "code": "unavailable_command",
            "message": message,
            "details": {
                "command": command,
                "available_commands": ["version"],
            },
        }
    }
    assert result.content[0].text == f"unavailable_command: {message}"
