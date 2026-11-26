"""Strict schemas, dispatch, bounds and discovery for workflow.step.list."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.memory import create_client_server_memory_streams
from pydantic import ValidationError
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.mcp_server.server import create_server
from specify_cli.workflows import _mcp
from specify_cli.workflows.step import _operation_list as operation
from specify_cli.workflows.step import mcp_list


def _run(coro):
    return asyncio.run(coro)


def _project(root, entries):
    directory = root / ".specify" / "workflows" / "steps"
    directory.mkdir(parents=True)
    (directory / "step-registry.json").write_text(
        json.dumps({"steps": entries}), encoding="utf-8"
    )
    return root


def test_actual_discovery_schema_annotations_and_collision(tmp_path):
    server = MCPServer(name="test")
    _mcp.register(server, launch_directory=tmp_path)
    tools = _run(server.list_tools())
    tool = next(tool for tool in tools if tool.name == "specify_workflow_step_list")
    assert tool.name == "specify_workflow_step_list"
    assert (
        tool.input_schema["properties"]
        == mcp_list.WorkflowStepListToolInput.model_json_schema()["properties"]
    )
    assert tool.input_schema["additionalProperties"] is False
    assert set(tool.input_schema["properties"]) == {"project_directory", "limit"}
    assert tool.input_schema["properties"]["limit"] == {
        "type": "integer",
        "title": "Limit",
        "default": 100,
        "minimum": 1,
        "maximum": 1000,
    }
    assert tool.output_schema == mcp_list.WorkflowStepListToolResult.model_json_schema()
    assert set(tool.output_schema["properties"]) == {"items", "truncated"}
    assert set(tool.output_schema["required"]) == {"items", "truncated"}
    assert set(
        tool.output_schema["$defs"]["WorkflowStepEntryResult"]["properties"]
    ) == {
        "kind",
        "id",
        "name",
        "version",
    }
    assert (
        tool.output_schema["$defs"]["WorkflowStepEntryResult"]["additionalProperties"]
        is False
    )
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.idempotent_hint is True
    assert tool.annotations.open_world_hint is False
    with pytest.raises(ValueError, match="collision"):
        _mcp.register(server, launch_directory=tmp_path)
    assert {tool.name for tool in _run(server.list_tools())} == {
        "specify_workflow_list",
        "specify_workflow_step_list",
    }


def test_shared_operation_used_by_both_adapters(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path))
    requests = []
    result = operation.WorkflowStepListResult(
        (operation.WorkflowStepListEntry("id", "Name", "1", "custom"),)
    )

    def collect(request):
        requests.append(request)
        return result

    monkeypatch.setattr(operation, "list_step_types", collect)
    cli = CliRunner().invoke(app, ["workflow", "step", "list"])
    assert cli.exit_code == 0, cli.output
    assert "Name (id) v1" in cli.output
    server = create_server(launch_directory=tmp_path)
    response = _run(server.call_tool("specify_workflow_step_list", {}))
    assert response.is_error is False
    assert response.structured_content["items"][0]["name"] == "Name"
    assert requests == [
        operation.WorkflowStepListRequest(tmp_path),
        operation.WorkflowStepListRequest(tmp_path, 100),
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        {"extra": True},
        {"limit": 0},
        {"limit": 1001},
        {"limit": True},
        {"limit": "1"},
        {"limit": 1.5},
        {"limit": None},
        {"project_directory": 4},
    ],
)
def test_sdk_rejects_invalid_input_before_operation(tmp_path, monkeypatch, arguments):
    monkeypatch.setattr(
        operation, "list_step_types", lambda *a: pytest.fail("Unexpected dispatch")
    )
    # The SDK's direct server API raises ToolError; the protocol layer converts
    # that into a text-only error response (exercised separately below).
    with pytest.raises(ToolError):
        _run(
            create_server(launch_directory=tmp_path).call_tool(
                "specify_workflow_step_list", arguments
            )
        )


def test_real_registry_result_warnings_and_limit(tmp_path):
    _project(tmp_path, {"z": {"enabled": False}, "bad": [], "a": {}})
    server = create_server(launch_directory=tmp_path)
    response = _run(server.call_tool("specify_workflow_step_list", {"limit": 2}))
    assert response.is_error is False
    data = response.structured_content
    # Built-ins sort first, so limit 2 returns the first two built-ins.
    assert [item["kind"] for item in data["items"]] == ["builtin", "builtin"]
    assert data["truncated"] is True
    assert json.loads(response.content[0].text) == data


def test_real_registry_installed_entries_and_warning(tmp_path):
    _project(tmp_path, {"z": {"name": "Zed", "version": "2"}, "bad": [], "a": {}})
    server = create_server(launch_directory=tmp_path)
    response = _run(server.call_tool("specify_workflow_step_list", {"limit": 1000}))
    assert response.is_error is False
    data = response.structured_content
    installed = [item for item in data["items"] if item["kind"] == "custom"]
    assert [item["id"] for item in installed] == ["a", "z"]
    assert installed[1]["name"] == "Zed"
    assert installed[1]["version"] == "2"
    warning = [item for item in data["items"] if item["kind"] == "warning"]
    assert len(warning) == 1
    assert warning[0]["code"] == "invalid_registry_entry"
    assert warning[0]["step_id"] == "bad"
    assert data["truncated"] is False


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_invalid_project_roots_return_not_a_project(tmp_path, kind):
    root = tmp_path / "not-a-project"
    if kind == "file":
        root.write_text("not a directory", encoding="utf-8")
    server = create_server(launch_directory=tmp_path)
    response = _run(
        server.call_tool("specify_workflow_step_list", {"project_directory": str(root)})
    )
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "not_a_spec_kit_project"
    assert str(root) not in response.model_dump_json()


def test_absolute_project_path_with_embedded_nul_returns_not_a_project(tmp_path):
    root = tmp_path / "invalid\x00project"
    assert root.is_absolute()
    response = _run(
        create_server(launch_directory=tmp_path).call_tool(
            "specify_workflow_step_list", {"project_directory": str(root)}
        )
    )
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "not_a_spec_kit_project"


@pytest.mark.parametrize("kind", ["policy", "storage"])
def test_unsafe_project_storage_keeps_structured_error(tmp_path, kind):
    root = _project(tmp_path / "project", {})
    if kind == "policy":
        path = root / ".specify" / "init-options.json"
        path.write_text('{"allow_symlinks": "yes"}', encoding="utf-8")
    else:
        path = root / ".specify" / "workflows" / "runs"
        path.write_text("not a directory", encoding="utf-8")
    response = _run(
        create_server(launch_directory=tmp_path).call_tool(
            "specify_workflow_step_list", {"project_directory": str(root)}
        )
    )
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "unsafe_workflow_storage"
    assert str(root) not in response.model_dump_json()


def test_launch_directory_captured_and_explicit_projects_are_independent(
    tmp_path, monkeypatch
):
    first = _project(tmp_path / "first", {"one": {}})
    second = _project(tmp_path / "second", {"two": {}})
    tool = mcp_list.create_workflow_step_list_tool(launch_directory=first)
    monkeypatch.chdir(second)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(second))
    assert tool().structured_content["items"][-1]["id"] == "one"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda root: tool(str(root), 100), [first, second]))
    assert [r.structured_content["items"][-1]["id"] for r in results] == [
        "one",
        "two",
    ]
    assert Path.cwd() == second
    relative = tool("relative", 100)
    assert relative.structured_content["error"]["code"] == "invalid_project_directory"


@pytest.mark.parametrize(
    "error",
    [
        operation.WorkflowStepListError(
            "step_registry_read_failed", "secret /private/path"
        ),
        RuntimeError("secret /private/path"),
        TypeError("secret /private/path"),
    ],
)
def test_error_mapping_never_exposes_exception_details(tmp_path, monkeypatch, error):
    def fail(request):
        raise error

    monkeypatch.setattr(operation, "list_step_types", fail)
    response = mcp_list.create_workflow_step_list_tool(launch_directory=tmp_path)()
    assert response.is_error is True
    code = (
        "step_registry_read_failed"
        if isinstance(error, operation.WorkflowStepListError)
        else "internal_error"
    )
    assert response.structured_content["error"]["code"] == code
    assert "secret" not in response.model_dump_json()
    assert "/private/path" not in response.model_dump_json()


@pytest.mark.parametrize(
    "result",
    [
        None,
        {"items": []},
        operation.WorkflowStepListResult(("bad",)),
        operation.WorkflowStepListResult(
            (operation.WorkflowStepListEntry("id", "n", "v", "yes"),)
        ),
    ],
)
def test_invalid_operation_outcomes_are_rejected(tmp_path, monkeypatch, result):
    monkeypatch.setattr(operation, "list_step_types", lambda request: result)
    response = mcp_list.create_workflow_step_list_tool(launch_directory=tmp_path)()
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "invalid_operation_result"


@pytest.mark.parametrize(
    "limit,count,truncated",
    [
        (1, 2, False),
        (100, 101, True),
        (1000, 1001, False),
        (100, 0, True),
        (100, 99, True),
        (1000, 999, True),
    ],
)
def test_operation_result_must_obey_requested_limit_and_truncation(
    tmp_path,
    monkeypatch,
    limit,
    count,
    truncated,
):
    items = tuple(
        operation.WorkflowStepListEntry(str(i), "N", "1", "custom")
        for i in range(count)
    )
    monkeypatch.setattr(
        operation,
        "list_step_types",
        lambda request: operation.WorkflowStepListResult(items, truncated),
    )
    response = mcp_list.create_workflow_step_list_tool(launch_directory=tmp_path)(
        None, limit
    )
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "invalid_operation_result"


@pytest.mark.parametrize("limit", [100, 1000])
@pytest.mark.parametrize("extra", [0, 1])
def test_real_result_boundaries_preserve_order_and_warnings(tmp_path, limit, extra):
    entries = {str(i): (None if i == 1 else {}) for i in range(limit + extra)}
    _project(tmp_path, entries)
    tool = mcp_list.create_workflow_step_list_tool(launch_directory=tmp_path)
    response = tool() if limit == 100 else tool(None, limit)
    assert response.is_error is False
    payload = response.structured_content
    assert len(payload["items"]) == limit
    # Built-ins (sorted) first, then installed entries sorted by id as strings.
    assert [item["id"] for item in payload["items"][:14]] == sorted(
        (
            "command",
            "do-while",
            "fan-in",
            "fan-out",
            "gate",
            "github",
            "if",
            "init",
            "prompt",
            "shell",
            "slot",
            "switch",
            "while",
            "workflow",
        )
    )
    assert payload["items"][14]["id"] == "0"
    assert payload["items"][15]["kind"] == "warning"
    # Built-ins plus installed entries always exceed the limit in this
    # fixture, so truncation is true with or without the extra entry.
    assert payload["truncated"] is True


def test_output_schema_enforces_static_entry_ceiling():
    schema = mcp_list.WorkflowStepListToolResult.model_json_schema()
    assert schema["properties"]["items"]["maxItems"] == 1000
    row = {
        "kind": "custom",
        "id": "id",
        "name": "N",
        "version": "1",
    }
    with pytest.raises(ValidationError):
        mcp_list.WorkflowStepListToolResult.model_validate(
            {"items": [row] * 1001, "truncated": False}
        )


def test_response_byte_budget_and_constructor_bounds(tmp_path, monkeypatch):
    result = operation.WorkflowStepListResult(
        (operation.WorkflowStepListEntry("id", "é" * 2000, "v", "custom"),)
    )
    monkeypatch.setattr(operation, "list_step_types", lambda request: result)
    tool = mcp_list.create_workflow_step_list_tool(
        launch_directory=tmp_path, max_wire_response_bytes=2000
    )
    response = tool()
    assert response.structured_content["error"]["code"] == "response_too_large"
    assert mcp_list._wire_response_size(response) <= 2000
    assert response.structured_content["error"]["retryable"] is True
    with pytest.raises(ValueError, match="bounded error response"):
        mcp_list.create_workflow_step_list_tool(
            launch_directory=tmp_path, max_wire_response_bytes=10
        )
    with pytest.raises(ValueError, match="absolute"):
        mcp_list.create_workflow_step_list_tool(launch_directory=Path("relative"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract_version", "999-fabricated"),
        ("network_access", "optional"),
        ("capabilities", frozenset({"execution"})),
    ],
)
def test_real_available_inventory_must_match_descriptor(tmp_path, field, value):
    from tests.specify_cli.workflows.test_mcp import (
        _assert_inventory,
        _workflow_cli_paths,
    )

    records = [
        replace(r, **{field: value}) if r.operation_id == "workflow.step.list" else r
        for r in _mcp.WORKFLOW_TOOLS
    ]
    tools = _run(create_server(launch_directory=tmp_path).list_tools())
    with pytest.raises(AssertionError):
        _assert_inventory(records, _workflow_cli_paths(), tools)


def test_output_schema_rejects_extra_fields_and_wrong_types():
    with pytest.raises(ValidationError):
        mcp_list.WorkflowStepListToolResult.model_validate(
            {"items": [], "truncated": "no"}
        )
    with pytest.raises(ValidationError):
        mcp_list.WorkflowStepListToolResult.model_validate(
            {"items": [], "truncated": False, "extra": 1}
        )


@pytest.mark.parametrize("field", ["input_schema", "output_schema"])
def test_correct_tool_name_with_unrelated_schema_fails_parity(tmp_path, field):
    from tests.specify_cli.workflows.test_mcp import (
        _assert_inventory,
        _workflow_cli_paths,
    )

    tools = _run(create_server(launch_directory=tmp_path).list_tools())
    tools = [
        tool.model_copy(
            update={
                field: {
                    "type": "object",
                    "properties": {"unrelated": {"type": "string"}},
                }
            }
        )
        if tool.name == "specify_workflow_step_list"
        else tool
        for tool in tools
    ]
    with pytest.raises(AssertionError):
        _assert_inventory(_mcp.WORKFLOW_TOOLS, _workflow_cli_paths(), tools)


def test_in_memory_protocol_success_expected_error_and_schema_error(tmp_path):
    _project(tmp_path, {"installed": {}})

    async def exercise():
        server = create_server(launch_directory=tmp_path)
        async with (
            create_client_server_memory_streams() as (client, streams),
            anyio.create_task_group() as tasks,
        ):
            tasks.start_soon(
                server._lowlevel_server.run,
                streams[0],
                streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert "specify_workflow_step_list" in [
                    tool.name for tool in tools.tools
                ]
                success = await session.call_tool(
                    "specify_workflow_step_list",
                    {"project_directory": str(tmp_path)},
                )
                error = await session.call_tool(
                    "specify_workflow_step_list",
                    {"project_directory": "relative"},
                )
                invalid = await session.call_tool(
                    "specify_workflow_step_list", {"unexpected": True}
                )
            tasks.cancel_scope.cancel()
        return success, error, invalid

    success, error, invalid = _run(exercise())
    assert success.is_error is False
    installed = [
        item for item in success.structured_content["items"] if item["kind"] == "custom"
    ]
    assert [item["id"] for item in installed] == ["installed"]
    assert error.is_error is True
    assert error.structured_content["error"]["code"] == "invalid_project_directory"
    assert invalid.is_error is True
    assert invalid.structured_content is None
