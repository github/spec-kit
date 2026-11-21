"""Strict schemas, dispatch, URL disclosure and bounds for workflow.catalog.list."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
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
from specify_cli.workflows.catalog import _operation_list as operation
from specify_cli.workflows.catalog import mcp_list

TOOL = "specify_workflow_catalog_list"


@pytest.fixture(autouse=True)
def isolated_layers(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)


def _run(coro):
    return asyncio.run(coro)


def _project(root, config=None):
    (root / ".specify").mkdir(parents=True)
    if config is not None:
        (root / ".specify" / "workflow-catalogs.yml").write_text(
            config, encoding="utf-8"
        )
    return root


def _source(name="n", url="https://e.example/c.json", priority=1):
    return operation.WorkflowCatalogSource(name, url, priority, True, None)


def _call(root, arguments=None):
    server = create_server(launch_directory=root)
    return _run(server.call_tool(TOOL, arguments or {}))


def test_actual_discovery_schema_annotations_and_collision(tmp_path):
    server = MCPServer(name="test")
    mcp_list.register(server, launch_directory=tmp_path)
    tools = _run(server.list_tools())
    assert [tool.name for tool in tools] == [TOOL]
    tool = tools[0]
    assert (
        tool.input_schema["properties"]
        == mcp_list.WorkflowCatalogListToolInput.model_json_schema()["properties"]
    )
    assert tool.input_schema["additionalProperties"] is False
    assert set(tool.input_schema["properties"]) == {"project_directory", "limit"}
    assert tool.output_schema == mcp_list.WorkflowCatalogListToolResult.model_json_schema()
    assert set(tool.output_schema["required"]) == {"items", "truncated"}
    assert set(
        tool.output_schema["$defs"]["WorkflowCatalogSourceResult"]["properties"]
    ) == {"name", "url", "priority", "install_allowed", "description"}
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.idempotent_hint is True
    assert tool.annotations.open_world_hint is False
    with pytest.raises(ValueError, match="collision"):
        mcp_list.register(server, launch_directory=tmp_path)
    assert len(_run(server.list_tools())) == 1


def test_shared_operation_used_by_both_adapters(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path))
    requests = []
    result = operation.WorkflowCatalogListResult((_source("Shared"),))

    def collect(request):
        requests.append(request)
        return result

    monkeypatch.setattr(operation, "list_catalog_sources", collect)
    cli = CliRunner().invoke(app, ["workflow", "catalog", "list"])
    assert cli.exit_code == 0, cli.output
    assert "Shared" in cli.output
    response = _call(tmp_path)
    assert response.is_error is False
    assert response.structured_content["items"][0]["name"] == "Shared"
    assert requests == [
        operation.WorkflowCatalogListRequest(tmp_path),
        operation.WorkflowCatalogListRequest(tmp_path, 100),
    ]


def test_adapters_agree_on_real_sources_and_order(tmp_path, monkeypatch):
    _project(
        tmp_path,
        "catalogs:\n"
        "  - name: second\n    url: https://s.example/c.json\n    priority: 2\n"
        "  - name: first\n    url: https://f.example/c.json\n    priority: 1\n",
    )
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path))
    cli = CliRunner().invoke(app, ["workflow", "catalog", "list"])
    assert cli.exit_code == 0, cli.output
    names = [item["name"] for item in _call(tmp_path).structured_content["items"]]
    assert names == ["first", "second"]
    assert cli.output.index("first") < cli.output.index("second")


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
        operation, "list_catalog_sources", lambda *a: pytest.fail("Unexpected dispatch")
    )
    with pytest.raises(ToolError):
        _call(tmp_path, arguments)


@pytest.mark.parametrize(
    "configured,disclosed",
    [
        ("https://e.example/c.json", "https://e.example/c.json"),
        ("https://e.example:8443/a/c.json", "https://e.example:8443/a/c.json"),
        ("https://user:s3cret@e.example/c.json", "https://e.example/c.json"),
        ("https://s3cret@e.example:8443/c.json", "https://e.example:8443/c.json"),
        ("https://e.example/c.json?token=s3cret", "https://e.example/c.json"),
        ("https://e.example/c.json#s3cret", "https://e.example/c.json"),
        ("https://u:s3cret@e.example/c.json?k=s3cret#s3cret", "https://e.example/c.json"),
        ("http://user:s3cret@localhost:9/c.json", "http://localhost:9/c.json"),
        ("https://user:s3cret@[::1]:9/c.json", "https://[::1]:9/c.json"),
    ],
)
def test_credential_bearing_url_parts_never_reach_the_client(
    tmp_path, configured, disclosed
):
    _project(tmp_path, f'catalogs:\n  - name: c\n    url: "{configured}"\n')
    response = _call(tmp_path)
    assert response.is_error is False
    assert response.structured_content["items"][0]["url"] == disclosed
    assert "s3cret" not in response.model_dump_json()
    assert json.loads(response.content[0].text) == response.structured_content


def test_environment_override_url_is_also_stripped(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.setenv(
        "SPECKIT_WORKFLOW_CATALOG_URL", "https://user:s3cret@e.example/c.json"
    )
    response = _call(tmp_path)
    assert response.structured_content["items"][0]["url"] == "https://e.example/c.json"
    assert "s3cret" not in response.model_dump_json()


@pytest.mark.parametrize(
    "config",
    [
        'catalogs:\n  - name: c\n    url: "https://user:s3cret@[::1"\n',
        'catalogs:\n  - name: c\n    url: "ftp://user:s3cret@e.example/c.json"\n',
        'catalogs:\n  - name: s3cret\n    url: https://e.example/c\n    priority: high\n',
    ],
)
def test_config_errors_do_not_quote_configured_values(tmp_path, config):
    _project(tmp_path, config)
    response = _call(tmp_path)
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "invalid_catalog_config"
    assert "s3cret" not in response.model_dump_json()
    assert str(tmp_path) not in response.model_dump_json()


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_invalid_project_roots_return_not_a_project(tmp_path, kind):
    root = tmp_path / "not-a-project"
    if kind == "file":
        root.write_text("not a directory", encoding="utf-8")
    response = _call(tmp_path, {"project_directory": str(root)})
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "not_a_spec_kit_project"
    assert str(root) not in response.model_dump_json()


@pytest.mark.parametrize("kind", ["policy", "storage"])
def test_unsafe_project_storage_keeps_structured_error(tmp_path, kind):
    root = _project(tmp_path / "project")
    if kind == "policy":
        path = root / ".specify" / "init-options.json"
        path.write_text('{"allow_symlinks": "yes"}', encoding="utf-8")
    else:
        (root / ".specify" / "workflows").write_text("not a dir", encoding="utf-8")
    response = _call(tmp_path, {"project_directory": str(root)})
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "unsafe_workflow_storage"
    assert str(root) not in response.model_dump_json()


def test_launch_directory_captured_and_explicit_projects_are_independent(
    tmp_path, monkeypatch
):
    def config(name):
        return f"catalogs:\n  - name: {name}\n    url: https://{name}.example/c.json\n"

    first = _project(tmp_path / "first", config("one"))
    second = _project(tmp_path / "second", config("two"))
    tool = mcp_list.create_workflow_catalog_list_tool(launch_directory=first)
    monkeypatch.chdir(second)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(second))
    assert tool().structured_content["items"][0]["name"] == "one"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda root: tool(str(root), 100), [first, second]))
    assert [r.structured_content["items"][0]["name"] for r in results] == ["one", "two"]
    assert Path.cwd() == second
    relative = tool("relative", 100)
    assert relative.structured_content["error"]["code"] == "invalid_project_directory"


@pytest.mark.parametrize(
    "error,code",
    [
        (
            operation.WorkflowCatalogListError(
                "invalid_catalog_config", "s3cret /private/path"
            ),
            "invalid_catalog_config",
        ),
        (RuntimeError("s3cret /private/path"), "internal_error"),
        (TypeError("s3cret /private/path"), "internal_error"),
    ],
)
def test_error_mapping_never_exposes_exception_details(
    tmp_path, monkeypatch, error, code
):
    def fail(request):
        raise error

    monkeypatch.setattr(operation, "list_catalog_sources", fail)
    response = mcp_list.create_workflow_catalog_list_tool(launch_directory=tmp_path)()
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == code
    assert "s3cret" not in response.model_dump_json()
    assert "/private/path" not in response.model_dump_json()


@pytest.mark.parametrize(
    "result",
    [
        None,
        {"items": []},
        operation.WorkflowCatalogListResult(("bad",)),
        operation.WorkflowCatalogListResult((_source(priority="1"),)),
        operation.WorkflowCatalogListResult((_source(url="https://[::1"),)),
    ],
)
def test_invalid_operation_outcomes_are_rejected(tmp_path, monkeypatch, result):
    monkeypatch.setattr(operation, "list_catalog_sources", lambda request: result)
    response = mcp_list.create_workflow_catalog_list_tool(launch_directory=tmp_path)()
    assert response.is_error is True
    assert response.structured_content["error"]["code"] == "invalid_operation_result"


@pytest.mark.parametrize(
    "limit,count,truncated",
    [(1, 2, False), (100, 101, True), (100, 0, True), (100, 99, True)],
)
def test_operation_result_must_obey_requested_limit_and_truncation(
    tmp_path, monkeypatch, limit, count, truncated
):
    items = tuple(_source(str(i)) for i in range(count))
    monkeypatch.setattr(
        operation,
        "list_catalog_sources",
        lambda request: operation.WorkflowCatalogListResult(items, truncated),
    )
    response = mcp_list.create_workflow_catalog_list_tool(launch_directory=tmp_path)(
        None, limit
    )
    assert response.structured_content["error"]["code"] == "invalid_operation_result"


def test_real_limit_reports_omitted_sources(tmp_path):
    entries = "".join(
        f"  - name: c{i}\n    url: https://c{i}.example/c.json\n    priority: {i}\n"
        for i in range(3)
    )
    _project(tmp_path, f"catalogs:\n{entries}")
    response = _call(tmp_path, {"limit": 2})
    assert [i["name"] for i in response.structured_content["items"]] == ["c0", "c1"]
    assert response.structured_content["truncated"] is True


def test_output_schema_enforces_ceiling_and_rejects_extras():
    row = {
        "name": "n",
        "url": "https://e.example/c.json",
        "priority": 1,
        "install_allowed": True,
        "description": None,
    }
    schema = mcp_list.WorkflowCatalogListToolResult.model_json_schema()
    assert schema["properties"]["items"]["maxItems"] == 1000
    with pytest.raises(ValidationError):
        mcp_list.WorkflowCatalogListToolResult.model_validate(
            {"items": [row] * 1001, "truncated": False}
        )
    with pytest.raises(ValidationError):
        mcp_list.WorkflowCatalogListToolResult.model_validate(
            {"items": [], "truncated": False, "extra": 1}
        )


def test_response_byte_budget_and_constructor_bounds(tmp_path, monkeypatch):
    result = operation.WorkflowCatalogListResult((_source("é" * 2000),))
    monkeypatch.setattr(operation, "list_catalog_sources", lambda request: result)
    tool = mcp_list.create_workflow_catalog_list_tool(
        launch_directory=tmp_path, max_wire_response_bytes=2000
    )
    response = tool()
    assert response.structured_content["error"]["code"] == "response_too_large"
    assert response.structured_content["error"]["retryable"] is True
    assert mcp_list._wire_response_size(response) <= 2000
    with pytest.raises(ValueError, match="bounded error response"):
        mcp_list.create_workflow_catalog_list_tool(
            launch_directory=tmp_path, max_wire_response_bytes=10
        )
    with pytest.raises(ValueError, match="absolute"):
        mcp_list.create_workflow_catalog_list_tool(launch_directory=Path("relative"))


def test_in_memory_protocol_success_expected_error_and_schema_error(tmp_path):
    _project(
        tmp_path,
        "catalogs:\n  - name: c\n    url: https://user:s3cret@e.example/c.json\n",
    )

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
                success = await session.call_tool(TOOL, {})
                error = await session.call_tool(
                    TOOL, {"project_directory": "relative"}
                )
                invalid = await session.call_tool(TOOL, {"unexpected": True})
            tasks.cancel_scope.cancel()
        return success, error, invalid

    success, error, invalid = _run(exercise())
    assert success.is_error is False
    assert success.structured_content["items"][0]["url"] == "https://e.example/c.json"
    assert "s3cret" not in success.model_dump_json()
    assert error.is_error is True
    assert error.structured_content["error"]["code"] == "invalid_project_directory"
    assert invalid.is_error is True
    assert invalid.structured_content is None
