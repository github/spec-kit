"""Tests for the first-class ``specify_artifact_list`` MCP adapter."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import anyio
import pytest
from mcp import ClientSession
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.memory import create_client_server_memory_streams

from specify_cli.artifacts import _commands, _mcp, _operation_list
from specify_cli.artifacts._operation_list import (
    ARTIFACT_LIST_OPERATION,
    ArtifactListRequest,
    ArtifactListResult,
)
from specify_cli.artifacts.mcp_list import (
    ArtifactListToolResult,
    create_artifact_list_tool,
)
from specify_cli.mcp_server.server import create_server
from specify_cli.presets import PresetError

TOOL_NAME = "specify_artifact_list"
TOOL_DESCRIPTION = (
    "List every command, template, script, and hook Spec Kit exposes for a project."
)

ARTIFACT_ROWS = (
    {
        "id": "template:réview",
        "name": "réview",
        "kind": "template",
        "description": "Réview checklist",
        "stack": [
            {
                "id": "template:réview",
                "layer": "extension",
                "sourceId": "quality",
                "presetId": None,
                "presetName": None,
                "strategy": "append",
                "active": True,
                "hidden": False,
                "manifestPath": ".specify/extensions/quality/extension.yml",
                "lookupId": "extension:quality:template:réview",
                "sourcePath": (
                    ".specify/extensions/quality/templates/réview-checklist.md"
                ),
            }
        ],
    },
    {
        "id": "hook:before_plan:quality",
        "name": "quality",
        "kind": "hook",
        "description": "Validate quality",
        "eventName": "before_plan",
        "targetCommand": "speckit.plan",
        "registered": True,
        "stack": [
            {
                "id": "hook:before_plan:quality",
                "layer": "extension",
                "sourceId": "quality",
                "presetId": None,
                "presetName": None,
                "strategy": "additive",
                "active": True,
                "hidden": False,
                "manifestPath": ".specify/extensions/quality/extension.yml",
                "lookupId": "extension:quality:hook:before_plan:quality",
                "sourcePath": None,
                "priority": 10,
                "optional": False,
            }
        ],
    },
)

ARTIFACT_PAYLOAD = {
    "rows": list(ARTIFACT_ROWS),
    "next_cursor": None,
    "truncated": False,
}

EXPECTED_OUTPUT_SCHEMA = {
    "$defs": {
        "ArtifactListHookRowResult": {
            "additionalProperties": False,
            "description": "One hook inventory row.",
            "properties": {
                "id": {"title": "Id", "type": "string"},
                "name": {"title": "Name", "type": "string"},
                "kind": {"const": "hook", "title": "Kind", "type": "string"},
                "description": {"title": "Description", "type": "string"},
                "eventName": {"title": "Eventname", "type": "string"},
                "targetCommand": {"title": "Targetcommand", "type": "string"},
                "registered": {"title": "Registered", "type": "boolean"},
                "stack": {
                    "items": {"$ref": "#/$defs/ArtifactListHookStackEntryResult"},
                    "title": "Stack",
                    "type": "array",
                },
            },
            "required": [
                "id",
                "name",
                "kind",
                "description",
                "eventName",
                "targetCommand",
                "registered",
                "stack",
            ],
            "title": "ArtifactListHookRowResult",
            "type": "object",
        },
        "ArtifactListHookStackEntryResult": {
            "additionalProperties": False,
            "description": "Composition entry for a hook artifact.",
            "properties": {
                "id": {"title": "Id", "type": "string"},
                "layer": {
                    "enum": ["preset", "extension"],
                    "title": "Layer",
                    "type": "string",
                },
                "sourceId": {"title": "Sourceid", "type": "string"},
                "presetId": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Presetid",
                },
                "presetName": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Presetname",
                },
                "strategy": {
                    "const": "additive",
                    "title": "Strategy",
                    "type": "string",
                },
                "active": {"title": "Active", "type": "boolean"},
                "hidden": {"title": "Hidden", "type": "boolean"},
                "manifestPath": {"title": "Manifestpath", "type": "string"},
                "lookupId": {"title": "Lookupid", "type": "string"},
                "sourcePath": {"title": "Sourcepath", "type": "null"},
                "priority": {"title": "Priority", "type": "integer"},
                "optional": {"title": "Optional", "type": "boolean"},
            },
            "required": [
                "id",
                "layer",
                "sourceId",
                "presetId",
                "presetName",
                "strategy",
                "active",
                "hidden",
                "manifestPath",
                "lookupId",
                "sourcePath",
                "priority",
                "optional",
            ],
            "title": "ArtifactListHookStackEntryResult",
            "type": "object",
        },
        "ArtifactListRowResult": {
            "additionalProperties": False,
            "description": "One named artifact inventory row.",
            "properties": {
                "id": {"title": "Id", "type": "string"},
                "name": {"title": "Name", "type": "string"},
                "kind": {
                    "enum": ["command", "template", "script"],
                    "title": "Kind",
                    "type": "string",
                },
                "description": {"title": "Description", "type": "string"},
                "stack": {
                    "items": {"$ref": "#/$defs/ArtifactListStackEntryResult"},
                    "title": "Stack",
                    "type": "array",
                },
            },
            "required": ["id", "name", "kind", "description", "stack"],
            "title": "ArtifactListRowResult",
            "type": "object",
        },
        "ArtifactListStackEntryResult": {
            "additionalProperties": False,
            "description": "Composition entry for a named artifact.",
            "properties": {
                "id": {"title": "Id", "type": "string"},
                "layer": {
                    "anyOf": [
                        {
                            "enum": ["project", "preset", "extension"],
                            "type": "string",
                        },
                        {"type": "null"},
                    ],
                    "title": "Layer",
                },
                "sourceId": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Sourceid",
                },
                "presetId": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Presetid",
                },
                "presetName": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Presetname",
                },
                "strategy": {
                    "enum": ["replace", "wrap", "prepend", "append"],
                    "title": "Strategy",
                    "type": "string",
                },
                "active": {"title": "Active", "type": "boolean"},
                "hidden": {"title": "Hidden", "type": "boolean"},
                "manifestPath": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Manifestpath",
                },
                "lookupId": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Lookupid",
                },
                "sourcePath": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Sourcepath",
                },
            },
            "required": [
                "id",
                "layer",
                "sourceId",
                "presetId",
                "presetName",
                "strategy",
                "active",
                "hidden",
                "manifestPath",
                "lookupId",
                "sourcePath",
            ],
            "title": "ArtifactListStackEntryResult",
            "type": "object",
        },
    },
    "additionalProperties": False,
    "description": "Typed structured result returned by ``specify_artifact_list``.",
    "properties": {
        "rows": {
            "items": {
                "discriminator": {
                    "mapping": {
                        "command": "#/$defs/ArtifactListRowResult",
                        "hook": "#/$defs/ArtifactListHookRowResult",
                        "script": "#/$defs/ArtifactListRowResult",
                        "template": "#/$defs/ArtifactListRowResult",
                    },
                    "propertyName": "kind",
                },
                "oneOf": [
                    {"$ref": "#/$defs/ArtifactListRowResult"},
                    {"$ref": "#/$defs/ArtifactListHookRowResult"},
                ],
            },
            "title": "Rows",
            "type": "array",
        },
        "next_cursor": {
            "anyOf": [
                {
                    "maxLength": 20,
                    "pattern": "^(0|[1-9][0-9]*)$",
                    "type": "string",
                },
                {"type": "null"},
            ],
            "title": "Next Cursor",
        },
        "truncated": {
            "title": "Truncated",
            "type": "boolean",
        },
    },
    "required": ["rows", "next_cursor", "truncated"],
    "title": "ArtifactListToolResult",
    "type": "object",
}


def _run(coro):
    return asyncio.run(coro)


def _expected_error(
    code: str,
    message: str,
    *,
    details: dict[str, object] | None = None,
    retryable: bool = False,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        }
    }


def test_artifact_list_dispatches_directly_to_shared_operation(
    spec_kit_project: Path,
):
    command_runner = Mock(side_effect=AssertionError("subprocess executor reached"))

    with (
        patch(
            "specify_cli.artifacts.mcp_list.list_artifacts",
            return_value=ArtifactListResult(rows=ARTIFACT_ROWS),
        ) as operation,
        patch(
            "specify_cli.mcp_server.executor._run_cli_process",
            side_effect=AssertionError("subprocess executor reached"),
        ) as run_cli_process,
        patch(
            "specify_cli.artifacts.command_list.artifact_list",
            side_effect=AssertionError("CLI adapter reached"),
        ) as cli_adapter,
    ):
        server = create_server(
            command_runner=command_runner,
            launch_directory=spec_kit_project,
        )
        result = _run(server.call_tool(TOOL_NAME, {}))

    assert result.structured_content == ARTIFACT_PAYLOAD
    request = operation.call_args.args[0]
    assert request == ArtifactListRequest(
        project_directory=spec_kit_project,
        limit=100,
        cursor=None,
    )
    command_runner.assert_not_called()
    run_cli_process.assert_not_called()
    cli_adapter.assert_not_called()


def test_artifact_list_preserves_complete_typed_rows_unicode_and_order(
    spec_kit_project: Path,
):
    tool = create_artifact_list_tool(launch_directory=spec_kit_project)
    with patch(
        "specify_cli.artifacts.mcp_list.list_artifacts",
        return_value=ArtifactListResult(rows=ARTIFACT_ROWS),
    ):
        result = tool()

    assert isinstance(result, ArtifactListToolResult)
    assert result.model_dump() == ARTIFACT_PAYLOAD
    assert [row.id for row in result.rows] == [
        "template:réview",
        "hook:before_plan:quality",
    ]
    assert result.rows[0].stack[0].sourcePath.endswith("réview-checklist.md")
    assert result.rows[1].stack[0].sourcePath is None


def test_artifact_list_uses_server_launch_directory_by_default(
    spec_kit_project: Path,
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(spec_kit_project)
    server = create_server()
    monkeypatch.chdir(non_project)
    operation = Mock(return_value=ArtifactListResult(rows=()))
    with patch("specify_cli.artifacts.mcp_list.list_artifacts", operation):
        result = _run(server.call_tool(TOOL_NAME, {}))

    assert result.structured_content == {
        "rows": [],
        "next_cursor": None,
        "truncated": False,
    }
    assert operation.call_args.args[0] == ArtifactListRequest(
        project_directory=spec_kit_project,
        limit=100,
        cursor=None,
    )


def test_artifact_list_accepts_explicit_absolute_project_directory(
    spec_kit_project: Path,
    non_project: Path,
):
    operation = Mock(return_value=ArtifactListResult(rows=()))
    with patch("specify_cli.artifacts.mcp_list.list_artifacts", operation):
        result = _run(
            create_server(launch_directory=non_project).call_tool(
                TOOL_NAME,
                {"project_directory": str(spec_kit_project)},
            )
        )

    assert result.structured_content == {
        "rows": [],
        "next_cursor": None,
        "truncated": False,
    }
    assert operation.call_args.args[0] == ArtifactListRequest(
        project_directory=spec_kit_project,
        limit=100,
        cursor=None,
    )


def test_artifact_list_forwards_pagination_and_returns_continuation(
    spec_kit_project: Path,
):
    operation = Mock(
        return_value=ArtifactListResult(
            rows=(ARTIFACT_ROWS[1],),
            next_cursor="7",
            truncated=True,
        )
    )
    with patch("specify_cli.artifacts.mcp_list.list_artifacts", operation):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"limit": 2, "cursor": "5"},
            )
        )

    assert result.structured_content == {
        "rows": [ARTIFACT_ROWS[1]],
        "next_cursor": "7",
        "truncated": True,
    }
    assert operation.call_args.args[0] == ArtifactListRequest(
        project_directory=spec_kit_project,
        limit=2,
        cursor="5",
    )


def test_artifact_list_rejects_oversized_structured_page(
    spec_kit_project: Path,
):
    tool = create_artifact_list_tool(
        launch_directory=spec_kit_project,
        max_response_bytes=64,
    )
    with patch(
        "specify_cli.artifacts.mcp_list.list_artifacts",
        return_value=ArtifactListResult(rows=ARTIFACT_ROWS),
    ):
        result = tool()

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "response_too_large",
        "The artifact list result exceeds the MCP response-size limit.",
        details={"max_bytes": 64, "requested_limit": 100},
        retryable=True,
    )
    assert result.content[0].text == (
        "response_too_large: "
        "The artifact list result exceeds the MCP response-size limit."
    )


def test_artifact_list_isolates_sequential_project_contexts(
    spec_kit_project: Path,
    non_project: Path,
):
    invocation_cwd = Path.cwd()

    def operation(request: ArtifactListRequest) -> ArtifactListResult:
        return ArtifactListResult(
            rows=(
                {
                    **ARTIFACT_ROWS[0],
                    "id": f"template:{request.project_directory.name}",
                    "name": request.project_directory.name,
                },
            )
        )

    with patch("specify_cli.artifacts.mcp_list.list_artifacts", operation):
        server = create_server(launch_directory=spec_kit_project)
        first = _run(
            server.call_tool(
                TOOL_NAME,
                {"project_directory": str(spec_kit_project)},
            )
        )
        second = _run(
            server.call_tool(
                TOOL_NAME,
                {"project_directory": str(non_project)},
            )
        )

    assert first.structured_content["rows"][0]["name"] == spec_kit_project.name
    assert second.structured_content["rows"][0]["name"] == non_project.name
    assert Path.cwd() == invocation_cwd


def test_artifact_list_discovery_has_exact_contract(
    spec_kit_project: Path,
):
    tools = _run(create_server(launch_directory=spec_kit_project).list_tools())
    tool = next(tool for tool in tools if tool.name == TOOL_NAME)

    assert tool.name == TOOL_NAME
    assert tool.description == TOOL_DESCRIPTION
    assert tool.input_schema == {
        "additionalProperties": False,
        "properties": {
            "project_directory": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "title": "Project Directory",
            },
            "limit": {
                "default": 100,
                "maximum": 1000,
                "minimum": 1,
                "title": "Limit",
                "type": "integer",
            },
            "cursor": {
                "anyOf": [
                    {
                        "maxLength": 20,
                        "pattern": "^(0|[1-9][0-9]*)$",
                        "type": "string",
                    },
                    {"type": "null"},
                ],
                "default": None,
                "title": "Cursor",
            },
        },
        "title": "specify_artifact_listArguments",
        "type": "object",
    }
    assert tool.output_schema == EXPECTED_OUTPUT_SCHEMA
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is None
    assert tool.annotations.idempotent_hint is True
    assert tool.annotations.open_world_hint is False


def test_artifact_list_rejects_unknown_arguments_before_dispatch(
    spec_kit_project: Path,
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_list.list_artifacts", operation),
        pytest.raises(ToolError, match="Extra inputs are not permitted"),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"unexpected": True},
            )
        )

    operation.assert_not_called()


def test_artifact_list_rejects_invalid_project_directory_type_before_dispatch(
    spec_kit_project: Path,
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_list.list_artifacts", operation),
        pytest.raises(ToolError, match="Input should be a valid string"),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"project_directory": 123},
            )
        )

    operation.assert_not_called()


@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 0},
        {"limit": 1001},
        {"cursor": "01"},
    ],
)
def test_artifact_list_rejects_invalid_pagination_before_dispatch(
    spec_kit_project: Path,
    arguments: dict[str, object],
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_list.list_artifacts", operation),
        pytest.raises(ToolError),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                arguments,
            )
        )

    operation.assert_not_called()


def test_artifact_list_rejects_relative_project_directory(
    spec_kit_project: Path,
):
    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"project_directory": "relative-project"},
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "not_a_spec_kit_project",
        "not a Spec Kit project: no .specify/ directory found",
        details={"project_directory": "relative-project"},
    )


def test_artifact_list_maps_non_project_error(non_project: Path):
    result = _run(create_server(launch_directory=non_project).call_tool(TOOL_NAME, {}))

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "not_a_spec_kit_project",
        "not a Spec Kit project: no .specify/ directory found",
        details={"project_directory": str(non_project)},
    )
    assert result.content[0].text == (
        "not_a_spec_kit_project: not a Spec Kit project: no .specify/ directory found"
    )


def test_artifact_list_maps_corrupt_registry_error(spec_kit_project: Path):
    registry = spec_kit_project / ".specify" / "extensions" / ".registry"
    registry.write_text("{invalid", encoding="utf-8")

    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(TOOL_NAME, {})
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "artifact_resolution_failed",
        "artifact resolution failed",
        details={"project_directory": str(spec_kit_project)},
    )


@pytest.mark.parametrize(
    "operation_failure",
    [
        OSError("unreadable"),
        PresetError("broken preset"),
    ],
)
def test_artifact_list_preserves_operation_owned_resolution_mapping(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation_failure: Exception,
):
    catalog = Mock()
    catalog.list_artifacts_with_stack.side_effect = operation_failure
    monkeypatch.setattr(
        _operation_list,
        "ArtifactCatalog",
        Mock(return_value=catalog),
    )

    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(TOOL_NAME, {})
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "artifact_resolution_failed",
        "artifact resolution failed",
        details={"project_directory": str(spec_kit_project)},
    )


@pytest.mark.parametrize(
    "operation_result",
    [
        None,
        ArtifactListResult(rows=None),
        ArtifactListResult(
            rows=(
                {
                    "id": "template:incomplete",
                    "name": "incomplete",
                    "kind": "template",
                    "description": "Missing stack",
                },
            )
        ),
        ArtifactListResult(
            rows=(
                {
                    **ARTIFACT_ROWS[0],
                    "unexpected": True,
                },
            )
        ),
        ArtifactListResult(rows=(), next_cursor=1, truncated=True),
        ArtifactListResult(rows=(), next_cursor=None, truncated=True),
        ArtifactListResult(rows=(), next_cursor="1", truncated=False),
    ],
)
def test_artifact_list_rejects_invalid_operation_results(
    spec_kit_project: Path,
    operation_result: object,
):
    with patch(
        "specify_cli.artifacts.mcp_list.list_artifacts",
        return_value=operation_result,
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(TOOL_NAME, {})
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "invalid_operation_result",
        "The artifact list operation returned an invalid result.",
    )


def test_artifact_list_sanitizes_and_logs_unexpected_failure(
    spec_kit_project: Path,
    caplog: pytest.LogCaptureFixture,
):
    unsafe = "SECRET_TOKEN=do-not-print /Users/example/private/project"
    with (
        patch(
            "specify_cli.artifacts.mcp_list.list_artifacts",
            side_effect=RuntimeError(unsafe),
        ),
        caplog.at_level(logging.ERROR, logger="specify_cli.artifacts.mcp_list"),
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(TOOL_NAME, {})
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "internal_error",
        "Unable to list Spec Kit artifacts.",
    )
    rendered = result.model_dump_json(by_alias=True)
    assert unsafe not in rendered
    assert "RuntimeError" not in rendered
    assert "Traceback" not in rendered
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "Unexpected failure in the artifact list MCP adapter."
    )
    assert caplog.records[0].exc_info is not None


def test_artifact_inventory_matches_cli_leaves_and_operation_contract(
    spec_kit_project: Path,
):
    cli_operation_ids = {
        f"artifact.{command.name}"
        for command in _commands.artifact_app.registered_commands
    }
    inventory_operation_ids = [item.operation_id for item in _mcp.ARTIFACT_TOOLS]
    inventory_tool_names = [item.mcp_tool_name for item in _mcp.ARTIFACT_TOOLS]
    registered_tool_names = {
        tool.name
        for tool in _run(create_server(launch_directory=spec_kit_project).list_tools())
    }

    assert set(inventory_operation_ids) == cli_operation_ids
    assert len(inventory_operation_ids) == len(set(inventory_operation_ids))
    assert len(inventory_tool_names) == len(set(inventory_tool_names))
    assert all(
        item.cli_path == f"specify {item.operation_id.replace('.', ' ')}"
        for item in _mcp.ARTIFACT_TOOLS
    )
    assert all(
        item.mcp_tool_name == f"specify_{item.operation_id.replace('.', '_')}"
        for item in _mcp.ARTIFACT_TOOLS
    )

    list_tool = next(
        item
        for item in _mcp.ARTIFACT_TOOLS
        if item.operation_id == ARTIFACT_LIST_OPERATION.operation_id
    )
    assert list_tool.contract_version == ARTIFACT_LIST_OPERATION.contract_version
    assert list_tool.disposition == "available"
    assert list_tool.disposition_reason is None
    assert list_tool.capabilities == ARTIFACT_LIST_OPERATION.capabilities
    assert list_tool.network_access == ARTIFACT_LIST_OPERATION.network_access
    assert list_tool.mcp_tool_name in registered_tool_names

    unavailable = [
        item for item in _mcp.ARTIFACT_TOOLS if item.disposition == "unavailable"
    ]
    assert {item.operation_id for item in unavailable} == {
        "artifact.info",
        "artifact.lookup",
    }
    assert all(item.contract_version is None for item in unavailable)
    assert all(item.disposition_reason for item in unavailable)
    assert all(item.mcp_tool_name not in registered_tool_names for item in unavailable)


def test_artifact_registration_adds_available_tool_once_and_rejects_collision(
    spec_kit_project: Path,
):
    server = MCPServer(name="test")

    _mcp.register(server, launch_directory=spec_kit_project)

    available_names = [
        item.mcp_tool_name
        for item in _mcp.ARTIFACT_TOOLS
        if item.disposition == "available"
    ]
    assert [tool.name for tool in _run(server.list_tools())] == available_names
    with pytest.raises(ValueError, match=f"MCP tool name collision: {TOOL_NAME}"):
        _mcp.register(server, launch_directory=spec_kit_project)
    assert [tool.name for tool in _run(server.list_tools())] == available_names


def test_artifact_tool_requires_absolute_server_launch_directory():
    with pytest.raises(
        ValueError,
        match="MCP server launch directory must be absolute",
    ):
        create_artifact_list_tool(launch_directory=Path("relative"))


def test_artifact_tool_requires_positive_response_size_limit(
    spec_kit_project: Path,
):
    with pytest.raises(
        ValueError,
        match="MCP response-size limit must be positive",
    ):
        create_artifact_list_tool(
            launch_directory=spec_kit_project,
            max_response_bytes=0,
        )


def test_in_memory_client_preserves_artifact_success_and_failure_wire_shapes(
    spec_kit_project: Path,
):
    async def exercise():
        server = create_server(launch_directory=spec_kit_project)
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
                tools = await session.list_tools()
                with patch(
                    "specify_cli.artifacts.mcp_list.list_artifacts",
                    return_value=ArtifactListResult(rows=ARTIFACT_ROWS),
                ):
                    success = await session.call_tool(TOOL_NAME, {})
                with patch(
                    "specify_cli.artifacts.mcp_list.list_artifacts",
                    return_value=None,
                ):
                    failure = await session.call_tool(TOOL_NAME, {})
                schema_failure = await session.call_tool(
                    TOOL_NAME,
                    {"unexpected": True},
                )
            task_group.cancel_scope.cancel()
        return tools, success, failure, schema_failure

    tools, success, failure, schema_failure = _run(exercise())

    discovered = next(tool for tool in tools.tools if tool.name == TOOL_NAME)
    assert discovered.input_schema["additionalProperties"] is False
    assert success.is_error is False
    assert success.structured_content == ARTIFACT_PAYLOAD
    assert failure.is_error is True
    assert failure.structured_content["error"]["code"] == "invalid_operation_result"
    assert schema_failure.is_error is True
    assert schema_failure.structured_content is None
    assert "Extra inputs are not permitted" in schema_failure.content[0].text
