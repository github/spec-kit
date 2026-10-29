"""Parity between real workflow CLI registration and its explicit MCP inventory."""

from __future__ import annotations

import asyncio
import io
import json
import os
from collections import Counter
from collections.abc import Sequence
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
from typing import TypedDict

import pytest
from mcp.server import MCPServer
from mcp.types import Tool
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.mcp_server.catalog import (
    CommandAdapterError,
    describe_command,
    list_commands,
)
from specify_cli.mcp_server.server import create_server
from specify_cli.workflows import _commands, _mcp
from specify_cli.workflows._operation_list import WORKFLOW_LIST_OPERATION
from specify_cli.workflows.mcp_list import WorkflowListToolInput, WorkflowListToolResult
from specify_cli.workflows.step import catalog as step_catalog


def _workflow_cli_paths() -> list[str]:
    """Walk the registered CLI, including future nested groups, without dispatch."""
    root = get_command(app)

    def walk(group: TyperGroup, prefix: str) -> list[str]:
        paths = []
        for name, command in group.commands.items():
            path = f"{prefix} {name}"
            if isinstance(command, TyperGroup):
                paths.extend(walk(command, path))
            else:
                paths.append(path)
        return paths

    return walk(root.commands["workflow"], "specify workflow")


def _assert_synthetic_discovery_shape(
    record: _mcp.WorkflowToolInventory, tools: Sequence[Tool]
) -> None:
    """Check discovery cardinality/schema shape, not operation correspondence."""
    matching = [tool for tool in tools if tool.name == record.mcp_tool_name]
    assert len(matching) == 1, (
        f"Expected exactly one registered tool for {record.operation_id}; got {len(matching)}"
    )
    tool = matching[0]
    assert tool.input_schema.get("type") == "object", (
        f"Missing input schema: {tool.name}"
    )
    assert tool.output_schema and tool.output_schema.get("type") == "object", (
        f"Missing output schema: {tool.name}"
    )


def _assert_inventory(
    records: Sequence[_mcp.WorkflowToolInventory],
    cli_paths: Sequence[str],
    tools: Sequence[Tool],
) -> None:
    """Bind the one implemented contract; fail closed for all other operations."""
    for label, values in (
        ("operation IDs", [item.operation_id for item in records]),
        ("CLI paths", [item.cli_path for item in records]),
        ("tool names", [item.mcp_tool_name for item in records]),
    ):
        duplicates = sorted(
            value for value, count in Counter(values).items() if count > 1
        )
        assert not duplicates, f"Duplicate {label}: {duplicates}"

    inventory_paths = {item.cli_path for item in records}
    missing = sorted(set(cli_paths) - inventory_paths)
    stale = sorted(inventory_paths - set(cli_paths))
    assert not missing, f"Missing CLI paths: {missing}"
    assert not stale, f"Stale CLI paths: {stale}"

    for item in records:
        assert item.cli_path.startswith("specify workflow "), item.cli_path
        expected_id = item.cli_path.removeprefix("specify ").replace(" ", ".")
        assert item.operation_id == expected_id, (
            f"Invalid operation ID: {item.operation_id}"
        )
        expected_tool = "specify_" + expected_id.replace(".", "_").replace("-", "_")
        assert item.mcp_tool_name == expected_tool, (
            f"Invalid tool name: {item.mcp_tool_name}"
        )
        assert item.disposition in {"available", "unavailable", "excluded"}, (
            f"Invalid disposition: {item.operation_id}"
        )
        assert isinstance(item.capabilities, frozenset) and item.capabilities, (
            f"Invalid capabilities: {item.operation_id}"
        )
        assert item.capabilities <= {
            "local-read",
            "project-write",
            "execution",
            "self-modifying",
        }, f"Invalid capabilities: {item.operation_id}"
        assert item.network_access in {"none", "optional", "required"}, (
            f"Invalid network access: {item.operation_id}"
        )
        assert item.contract_version is None or (
            isinstance(item.contract_version, str) and item.contract_version.strip()
        ), f"Invalid contract version: {item.operation_id}"

        matching = [tool for tool in tools if tool.name == item.mcp_tool_name]
        if item.disposition == "available":
            assert item.contract_version, f"Missing contract: {item.operation_id}"
            assert item.disposition_reason is None, (
                f"Available reason: {item.operation_id}"
            )
            _assert_synthetic_discovery_shape(item, tools)
            assert item.operation_id == WORKFLOW_LIST_OPERATION.operation_id, (
                f"No workflow operation contract evidence: {item.operation_id}"
            )
            assert item.contract_version == WORKFLOW_LIST_OPERATION.contract_version
            assert item.capabilities == WORKFLOW_LIST_OPERATION.capabilities
            assert item.network_access == WORKFLOW_LIST_OPERATION.network_access
            tool = matching[0]
            expected_input = WorkflowListToolInput.model_json_schema()
            assert tool.input_schema["properties"] == expected_input["properties"]
            assert tool.input_schema["additionalProperties"] is False
            assert tool.output_schema == WorkflowListToolResult.model_json_schema()
        else:
            assert item.contract_version is None, (
                f"Nonavailable tool has contract version: {item.operation_id}"
            )
            assert (
                isinstance(item.disposition_reason, str)
                and item.disposition_reason.strip()
            ), f"Missing disposition reason: {item.operation_id}"
            assert not matching, f"Nonavailable tool registered: {item.operation_id}"

    inventory_names = {item.mcp_tool_name for item in records}
    unexpected = sorted(
        tool.name
        for tool in tools
        if tool.name.startswith("specify_workflow_")
        and tool.name not in inventory_names
    )
    assert not unexpected, f"Uninventoried workflow tools: {unexpected}"


def test_workflow_inventory_matches_actual_cli_and_server(tmp_path):
    server = create_server(launch_directory=tmp_path)
    tools = asyncio.run(server.list_tools())

    _assert_inventory(_mcp.WORKFLOW_TOOLS, _workflow_cli_paths(), tools)


def test_inventory_records_are_immutable():
    with pytest.raises(FrozenInstanceError):
        _mcp.WORKFLOW_TOOLS[0].disposition = "available"


@pytest.mark.parametrize("location", ["root", "nested"])
def test_new_registered_cli_leaf_requires_disposition(monkeypatch, location):
    target = _commands.workflow_app if location == "root" else step_catalog.catalog_app
    # Isolate the registration list before adding a command; monkeypatch restores
    # the original object, including on failure. Do not call register() again.
    monkeypatch.setattr(target, "registered_commands", list(target.registered_commands))

    @target.command("inventory-probe")
    def probe():
        raise AssertionError("CLI traversal must not execute handlers")

    path = (
        "specify workflow inventory-probe"
        if location == "root"
        else "specify workflow step catalog inventory-probe"
    )
    paths = _workflow_cli_paths()
    assert path in paths
    with pytest.raises(AssertionError, match="Missing CLI paths"):
        _assert_inventory(_mcp.WORKFLOW_TOOLS, paths, [])


def test_missing_inventory_entry_is_rejected():
    with pytest.raises(AssertionError, match="Missing CLI paths"):
        _assert_inventory(_mcp.WORKFLOW_TOOLS[1:], _workflow_cli_paths(), [])


def test_stale_inventory_entry_is_rejected():
    stale = replace(
        _mcp.WORKFLOW_TOOLS[0],
        operation_id="workflow.removed",
        cli_path="specify workflow removed",
        mcp_tool_name="specify_workflow_removed",
    )
    with pytest.raises(AssertionError, match="Stale CLI paths"):
        _assert_inventory((*_mcp.WORKFLOW_TOOLS, stale), _workflow_cli_paths(), [])


@pytest.mark.parametrize(
    "field,label",
    [
        ("operation_id", "operation IDs"),
        ("cli_path", "CLI paths"),
        ("mcp_tool_name", "tool names"),
    ],
)
def test_duplicate_inventory_identity_is_rejected(field, label):
    records = list(_mcp.WORKFLOW_TOOLS)
    records[1] = replace(records[1], **{field: getattr(records[0], field)})
    with pytest.raises(AssertionError, match=f"Duplicate {label}"):
        _assert_inventory(records, _workflow_cli_paths(), [])


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"operation_id": "workflow.wrong"}, "Invalid operation ID"),
        ({"mcp_tool_name": "specify_workflow_wrong"}, "Invalid tool name"),
        ({"disposition": "unknown"}, "Invalid disposition"),
        ({"capabilities": frozenset()}, "Invalid capabilities"),
        ({"capabilities": frozenset({"read-only"})}, "Invalid capabilities"),
        ({"capabilities": {"local-read"}}, "Invalid capabilities"),
        ({"network_access": "sometimes"}, "Invalid network access"),
        ({"contract_version": " "}, "Invalid contract version"),
    ],
)
def test_invalid_inventory_metadata_is_rejected(changes, message):
    records = list(_mcp.WORKFLOW_TOOLS)
    records[0] = replace(records[0], **changes)
    with pytest.raises(AssertionError, match=message):
        _assert_inventory(records, _workflow_cli_paths(), [])


@pytest.mark.parametrize("disposition", ["unavailable", "excluded"])
@pytest.mark.parametrize("reason", [None, "", " \n\t"])
def test_nonavailable_disposition_requires_explanation(disposition, reason):
    record = replace(
        _mcp.WORKFLOW_TOOLS[0],
        disposition=disposition,
        disposition_reason=reason,
    )
    with pytest.raises(AssertionError, match="Missing disposition reason"):
        _assert_inventory([record], [record.cli_path], [])


@pytest.mark.parametrize("disposition", ["unavailable", "excluded"])
def test_nonavailable_record_cannot_declare_contract_version(disposition):
    record = replace(
        _mcp.WORKFLOW_TOOLS[0], disposition=disposition, contract_version="1"
    )
    with pytest.raises(AssertionError, match="Nonavailable tool has contract version"):
        _assert_inventory([record], [record.cli_path], [])


class _ProbeResult(TypedDict):
    value: str


class _UnrelatedResult(TypedDict):
    unrelated: int


@pytest.fixture
def available_record_and_tool():
    """Synthetic shape/count probe, not evidence of a workflow.add contract."""
    record = replace(
        _mcp.WORKFLOW_TOOLS[0],
        disposition="available",
        disposition_reason=None,
        contract_version="1",
    )
    server = MCPServer(name="workflow-inventory-test")

    def probe(value: str) -> _ProbeResult:
        return {"value": value}

    server.add_tool(probe, name=record.mcp_tool_name, structured_output=True)
    tools = asyncio.run(server.list_tools())
    assert len(tools) == 1
    return record, tools[0]


@pytest.mark.parametrize("count", [0, 1, 2])
def test_available_record_requires_exactly_one_matching_tool(
    available_record_and_tool, count
):
    record, tool = available_record_and_tool
    tools = (
        [tool] * count
    )  # Duplicate discovery is invalid even if an SDK deduplicates registration.
    if count == 1:
        _assert_synthetic_discovery_shape(record, tools)
    else:
        with pytest.raises(
            AssertionError, match="Expected exactly one registered tool"
        ):
            _assert_synthetic_discovery_shape(record, tools)


@pytest.mark.parametrize("version", ["1", "999-fabricated"])
def test_correctly_named_unrelated_contract_is_rejected(version):
    record = replace(
        _mcp.WORKFLOW_TOOLS[0],
        disposition="available",
        disposition_reason=None,
        contract_version=version,
        capabilities=frozenset({"local-read"}),
        network_access="none",
    )

    def unrelated_operation(unrelated: bool) -> _UnrelatedResult:
        return {"unrelated": int(unrelated)}

    server = MCPServer(name="wrong-workflow-contract")
    server.add_tool(
        unrelated_operation, name=record.mcp_tool_name, structured_output=True
    )
    tools = asyncio.run(server.list_tools())
    assert len(tools) == 1
    assert tools[0].input_schema["type"] == "object"
    assert tools[0].output_schema["type"] == "object"
    with pytest.raises(AssertionError, match="No workflow operation contract evidence"):
        _assert_inventory([record], [record.cli_path], tools)


def test_synthetic_probe_cannot_establish_real_workflow_availability(
    available_record_and_tool,
):
    record, tool = available_record_and_tool
    _assert_synthetic_discovery_shape(record, [tool])
    with pytest.raises(AssertionError, match="No workflow operation contract evidence"):
        _assert_inventory([record], [record.cli_path], [tool])


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"contract_version": None}, "Missing contract"),
        ({"disposition_reason": "not ready"}, "Available reason"),
    ],
)
def test_available_record_requires_contract(
    available_record_and_tool, changes, message
):
    record, tool = available_record_and_tool
    with pytest.raises(AssertionError, match=message):
        _assert_inventory([replace(record, **changes)], [record.cli_path], [tool])


@pytest.mark.parametrize(
    "schema,message",
    [
        ({"input_schema": {}}, "Missing input schema"),
        ({"output_schema": None}, "Missing output schema"),
    ],
)
def test_available_tool_requires_typed_schemas(
    available_record_and_tool, schema, message
):
    record, tool = available_record_and_tool
    with pytest.raises(AssertionError, match=message):
        _assert_synthetic_discovery_shape(record, [tool.model_copy(update=schema)])


@pytest.mark.parametrize("disposition", ["unavailable", "excluded"])
def test_nonavailable_record_cannot_register_tool(
    available_record_and_tool, disposition
):
    record, tool = available_record_and_tool
    record = replace(
        record,
        disposition=disposition,
        disposition_reason="Not offered through MCP.",
        contract_version=None,
    )
    with pytest.raises(AssertionError, match="Nonavailable tool registered"):
        _assert_inventory([record], [record.cli_path], [tool])


def test_matching_registration_cannot_be_replaced_by_different_tool(
    available_record_and_tool,
):
    record, tool = available_record_and_tool
    with pytest.raises(AssertionError, match="Expected exactly one registered tool"):
        _assert_inventory(
            [record], [record.cli_path], [tool.model_copy(update={"name": "other"})]
        )


def test_uninventoried_workflow_tool_is_rejected(available_record_and_tool):
    _, tool = available_record_and_tool
    with pytest.raises(AssertionError, match="Uninventoried workflow tools"):
        _assert_inventory([], [], [tool])


def test_server_adds_only_workflow_list_and_preserves_legacy_catalog(tmp_path):
    tools = asyncio.run(create_server(launch_directory=tmp_path).list_tools())
    assert Counter(tool.name for tool in tools) == Counter(
        {
            "specify_version": 1,
            "specify_artifact_list": 1,
            "specify_artifact_info": 1,
            "specify_workflow_list": 1,
            "specify_list_commands": 1,
            "specify_describe_command": 1,
            "specify_run_command": 1,
        }
    )
    assert [item.command for item in list_commands().commands] == ["version"]
    assert describe_command("version").command == "version"
    with pytest.raises(CommandAdapterError) as exc:
        describe_command("workflow.run")
    assert exc.value.code == "unavailable_command"
    assert [
        item.operation_id
        for item in _mcp.WORKFLOW_TOOLS
        if item.disposition == "available"
    ] == ["workflow.list"]


@pytest.mark.parametrize("operation_id", ["workflow.run", "workflow.resume"])
def test_execution_command_effects_include_persistence_and_optional_network(
    operation_id,
):
    # command_run.workflow_run reads a definition and calls WorkflowEngine.execute;
    # command_resume.workflow_resume reads RunState and calls WorkflowEngine.resume.
    # Both engine paths save checkpoints and dispatch executable steps. Command
    # steps can run offline; prompt steps can invoke networked integrations, so
    # networking is optional rather than required. See step/command and step/prompt.
    record = next(
        item for item in _mcp.WORKFLOW_TOOLS if item.operation_id == operation_id
    )
    assert record.capabilities == frozenset(
        {"local-read", "project-write", "execution"}
    )
    assert record.network_access == "optional"


@pytest.mark.parametrize("step", [False, True], ids=["workflow", "step"])
def test_catalog_discovery_effects_include_cache_and_auth_execution(
    tmp_path, monkeypatch, step
):
    """Follow real CLI -> catalog -> HTTP -> auth paths, mocking only external IO."""
    from specify_cli.authentication import azure_devops, http
    from specify_cli.authentication.config import AuthConfigEntry

    (tmp_path / ".specify").mkdir()
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path))
    executable = tmp_path / "bin" / ("az.cmd" if os.name == "nt" else "az")
    executable.parent.mkdir()
    executable.write_text("test executable", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(executable.parent))
    url = "https://inventory.invalid/catalog.json"
    monkeypatch.setenv(
        "SPECKIT_STEP_CATALOG_URL" if step else "SPECKIT_WORKFLOW_CATALOG_URL", url
    )
    monkeypatch.setattr(
        http,
        "_config_override",
        [
            AuthConfigEntry(
                hosts=("inventory.invalid",), provider="azure-devops", auth="azure-cli"
            ),
        ],
    )
    processes = []
    requests = []

    def run(argv, **kwargs):
        processes.append(argv)
        return SimpleNamespace(
            returncode=0, stdout='{"accessToken": "test-only"}', stderr=""
        )

    class Response(io.BytesIO):
        headers = {}

        def geturl(self):
            return url

    def open_request(request, **kwargs):
        requests.append(request.full_url)
        return Response(json.dumps({"steps" if step else "workflows": {}}).encode())

    monkeypatch.setattr(azure_devops.subprocess, "run", run)
    monkeypatch.setattr(
        http.urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=open_request),
    )
    args = ["workflow", "step", "search"] if step else ["workflow", "search"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert requests == [url]
    assert len(processes) == 1
    assert os.path.normcase(processes[0][0]) == os.path.normcase(str(executable))
    assert processes[0][1:3] == ["account", "get-access-token"]
    cache = tmp_path / ".specify" / "workflows"
    if step:
        cache /= "steps"
    assert len(list((cache / ".cache").glob("*.json"))) == 2

    operation = "workflow.step.search" if step else "workflow.search"
    record = next(
        item for item in _mcp.WORKFLOW_TOOLS if item.operation_id == operation
    )
    assert record.capabilities == frozenset(
        {"local-read", "project-write", "execution"}
    )
    assert record.network_access == "optional"

    # A warm cache needs neither network nor an authentication subprocess:
    # the static declaration is a union, not a claim every invocation uses IO.
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert requests == [url]
    assert len(processes) == 1


@pytest.mark.parametrize(
    "suffix",
    [["list"], ["catalog", "list"], ["step", "list"], ["step", "catalog", "list"]],
)
def test_local_inventory_queries_do_not_load_integrations_or_fetch(
    tmp_path, monkeypatch, suffix
):
    from specify_cli.authentication import http
    from specify_cli.integrations import installer

    (tmp_path / ".specify").mkdir()
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path))
    # Use explicit catalog configuration rather than the operator's home files.
    monkeypatch.setenv(
        "SPECKIT_WORKFLOW_CATALOG_URL", "https://inventory.invalid/workflows.json"
    )
    monkeypatch.setenv(
        "SPECKIT_STEP_CATALOG_URL", "https://inventory.invalid/steps.json"
    )

    def unexpected(*args, **kwargs):
        pytest.fail(
            "A local inventory query must not load integrations or fetch catalogs"
        )

    monkeypatch.setattr(installer, "load_installed_integrations", unexpected)
    monkeypatch.setattr(http, "open_url", unexpected)
    result = CliRunner().invoke(app, ["workflow", *suffix])
    assert result.exit_code == 0, result.output
    record = next(
        item
        for item in _mcp.WORKFLOW_TOOLS
        if item.cli_path == " ".join(["specify", "workflow", *suffix])
    )
    assert record.capabilities == frozenset({"local-read"})
    assert record.network_access == "none"
