"""Tests for the first-class ``specify_version`` MCP adapter."""

from __future__ import annotations

import asyncio
from unittest.mock import Mock, patch

import anyio
import pytest
from mcp import ClientSession
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.memory import create_client_server_memory_streams

from specify_cli._operation_version import (
    VersionResult,
    VersionRuntime,
    VersionSystem,
)
from specify_cli.mcp_server.server import create_server
from specify_cli.mcp_version import (
    TOOL_NAME,
    VersionToolResult,
    register,
    specify_version,
)

VERSION_RESULT = VersionResult(
    cli_version="1.2.3",
    runtime=VersionRuntime(
        python="3.13.1",
        openssl="OpenSSL 3.4.0",
    ),
    system=VersionSystem(
        platform="ExampleOS",
        architecture="example64",
        os_version="ExampleOS 4.5",
    ),
    features={"workflow_catalog": True},
)
VERSION_PAYLOAD = {
    "cli_version": "1.2.3",
    "runtime": {
        "python": "3.13.1",
        "openssl": "OpenSSL 3.4.0",
    },
    "system": {
        "platform": "ExampleOS",
        "architecture": "example64",
        "os_version": "ExampleOS 4.5",
    },
    "features": {"workflow_catalog": True},
}


def _run(coro):
    return asyncio.run(coro)


def test_specify_version_dispatches_directly_to_shared_operation():
    command_runner = Mock(side_effect=AssertionError("subprocess executor reached"))

    with (
        patch(
            "specify_cli.mcp_version.collect_version_result",
            return_value=VERSION_RESULT,
        ) as collect,
        patch(
            "specify_cli.mcp_server.executor._run_cli_process",
            side_effect=AssertionError("subprocess executor reached"),
        ) as run_cli_process,
        patch(
            "specify_cli.command_version.version",
            side_effect=AssertionError("CLI adapter reached"),
        ) as cli_adapter,
    ):
        server = create_server(command_runner=command_runner)
        result = _run(server.call_tool(TOOL_NAME, {}))

    assert result.structured_content == VERSION_PAYLOAD
    collect.assert_called_once_with()
    command_runner.assert_not_called()
    run_cli_process.assert_not_called()
    cli_adapter.assert_not_called()


def test_specify_version_matches_shared_operation_and_cli_json_semantics():
    with patch(
        "specify_cli.mcp_version.collect_version_result",
        return_value=VERSION_RESULT,
    ):
        result = specify_version()

    assert isinstance(result, VersionToolResult)
    assert result.model_dump() == VERSION_PAYLOAD
    assert isinstance(result.cli_version, str)
    assert isinstance(result.runtime.python, str)
    assert isinstance(result.runtime.openssl, str)
    assert isinstance(result.system.platform, str)
    assert isinstance(result.system.architecture, str)
    assert isinstance(result.system.os_version, str)
    assert all(isinstance(value, bool) for value in result.features.values())


def test_specify_version_preserves_unavailable_openssl_as_none():
    operation_result = VersionResult(
        cli_version=VERSION_RESULT.cli_version,
        runtime=VersionRuntime(
            python=VERSION_RESULT.runtime.python,
            openssl=None,
        ),
        system=VERSION_RESULT.system,
        features=VERSION_RESULT.features,
    )
    with patch(
        "specify_cli.mcp_version.collect_version_result",
        return_value=operation_result,
    ):
        result = specify_version()

    assert isinstance(result, VersionToolResult)
    assert result.runtime.openssl is None


@pytest.mark.parametrize(
    "operation_result",
    [
        VersionResult(
            cli_version="1.2.3",
            runtime=None,
            system=VERSION_RESULT.system,
            features=VERSION_RESULT.features,
        ),
        VersionResult(
            cli_version="1.2.3",
            runtime=VERSION_RESULT.runtime,
            system=None,
            features=VERSION_RESULT.features,
        ),
        VersionResult(
            cli_version="1.2.3",
            runtime=VERSION_RESULT.runtime,
            system=VERSION_RESULT.system,
            features={"workflow_catalog": "yes"},
        ),
    ],
)
def test_specify_version_rejects_invalid_operation_results(operation_result):
    with patch(
        "specify_cli.mcp_version.collect_version_result",
        return_value=operation_result,
    ):
        result = specify_version()

    assert result.is_error is True
    assert result.structured_content == {
        "error": {
            "code": "invalid_operation_result",
            "message": "The version operation returned an invalid result.",
            "details": {},
        }
    }
    assert result.content[0].text == (
        "invalid_operation_result: The version operation returned an invalid result."
    )


def test_specify_version_sanitizes_unexpected_operation_failure():
    unsafe = "SECRET_TOKEN=do-not-print /Users/example/private/project"
    with patch(
        "specify_cli.mcp_version.collect_version_result",
        side_effect=RuntimeError(unsafe),
    ):
        result = specify_version()

    assert result.is_error is True
    assert result.structured_content == {
        "error": {
            "code": "internal_error",
            "message": "Unable to collect version information.",
            "details": {},
        }
    }
    rendered = result.model_dump_json(by_alias=True)
    assert unsafe not in rendered
    assert "RuntimeError" not in rendered
    assert "Traceback" not in rendered


def test_specify_version_discovery_has_no_argument_schema_and_typed_output():
    tools = _run(create_server().list_tools())
    tool = next(tool for tool in tools if tool.name == TOOL_NAME)

    assert tool.input_schema == {
        "additionalProperties": False,
        "properties": {},
        "title": "specify_versionArguments",
        "type": "object",
    }
    assert set(tool.output_schema["properties"]) == {
        "cli_version",
        "runtime",
        "system",
        "features",
    }
    assert tool.output_schema["required"] == [
        "cli_version",
        "runtime",
        "system",
        "features",
    ]
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is False
    assert tool.annotations.idempotent_hint is True
    assert tool.annotations.open_world_hint is False


def test_specify_version_rejects_unexpected_arguments_before_dispatch():
    collect = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.mcp_version.collect_version_result", collect),
        pytest.raises(ToolError, match="Extra inputs are not permitted"),
    ):
        _run(create_server().call_tool(TOOL_NAME, {"unexpected": True}))

    collect.assert_not_called()


def test_register_adds_one_tool_and_rejects_name_collision():
    server = MCPServer(name="test")

    register(server)
    tools = _run(server.list_tools())

    assert [tool.name for tool in tools] == [TOOL_NAME]
    with pytest.raises(ValueError, match=f"MCP tool name collision: {TOOL_NAME}"):
        register(server)
    assert [tool.name for tool in _run(server.list_tools())] == [TOOL_NAME]


def test_in_memory_client_preserves_success_and_failure_wire_shapes():
    async def exercise():
        server = create_server()
        async with (
            create_client_server_memory_streams() as (
                client_streams,
                server_streams,
            ),
            anyio.create_task_group() as task_group,
        ):
            task_group.start_soon(
                server._lowlevel_server.run,
                server_streams[0],
                server_streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client_streams) as session:
                await session.initialize()
                with patch(
                    "specify_cli.mcp_version.collect_version_result",
                    return_value=VERSION_RESULT,
                ):
                    success = await session.call_tool(TOOL_NAME, {})
                with patch(
                    "specify_cli.mcp_version.collect_version_result",
                    return_value=VersionResult(
                        cli_version="1.2.3",
                        runtime=None,
                        system=None,
                        features={},
                    ),
                ):
                    failure = await session.call_tool(TOOL_NAME, {})
                schema_failure = await session.call_tool(
                    TOOL_NAME,
                    {"unexpected": True},
                )
            task_group.cancel_scope.cancel()
        return success, failure, schema_failure

    success, failure, schema_failure = _run(exercise())

    assert success.is_error is False
    assert success.structured_content == VERSION_PAYLOAD
    assert failure.is_error is True
    assert failure.structured_content["error"]["code"] == "invalid_operation_result"
    assert schema_failure.is_error is True
    assert schema_failure.structured_content is None
    assert "Extra inputs are not permitted" in schema_failure.content[0].text
