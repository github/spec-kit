"""Tests for the first-class ``specify_artifact_info`` MCP adapter."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import anyio
import pytest
from mcp import ClientSession
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.memory import create_client_server_memory_streams
from mcp.types import CallToolResult
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import (
    _commands,
    _mcp,
    _operation_info,
    command_info,
    mcp_info,
)
from specify_cli.artifacts._operation_info import (
    ARTIFACT_INFO_OPERATION,
    ArtifactInfoAmbiguousError,
    ArtifactInfoError,
    ArtifactInfoHookArtifact,
    ArtifactInfoHookNotFoundError,
    ArtifactInfoIdentifierError,
    ArtifactInfoInvalidResultError,
    ArtifactInfoKindError,
    ArtifactInfoNamedArtifact,
    ArtifactInfoNotFoundError,
    ArtifactInfoProjectDirectoryError,
    ArtifactInfoProjectError,
    ArtifactInfoRequest,
    ArtifactInfoResolutionError,
    ArtifactInfoResult,
)
from specify_cli.artifacts.mcp_info import (
    ArtifactInfoHookResult,
    ArtifactInfoNamedResult,
    ArtifactInfoToolResult,
    create_artifact_info_tool,
)
from specify_cli.artifacts.models import HookStackEntry, StackLayer
from specify_cli.mcp_server.server import create_server
from specify_cli.presets import PresetError
from tests.specify_cli.artifacts.helpers import install_extension_with_hooks

TOOL_NAME = "specify_artifact_info"
TOOL_DESCRIPTION = (
    "Return one artifact and its complete composition stack for a project. "
    "Accepts bare or kind:name identifiers; responses are bounded by the MCP "
    "response-size limit."
)


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


def _named_result(
    *,
    description: str = "Réview ✓",
    source_path: str = ".specify/extensions/quality/templates/réview.md",
) -> ArtifactInfoResult:
    return ArtifactInfoResult(
        artifact=ArtifactInfoNamedArtifact(
            id="template:réview",
            name="réview",
            kind="template",
            description=description,
            stack=(
                StackLayer(
                    id="template:réview",
                    layer="preset",
                    sourceId="compliance",
                    presetId="compliance",
                    presetName="Compliance",
                    strategy="prepend",
                    active=True,
                    hidden=False,
                    manifestPath=".specify/presets/compliance/preset.yml",
                    lookupId="preset:compliance:template:réview",
                    sourcePath=".specify/presets/compliance/templates/réview.md",
                ),
                StackLayer(
                    id="template:réview",
                    layer="extension",
                    sourceId="quality",
                    presetId=None,
                    presetName=None,
                    strategy="append",
                    active=True,
                    hidden=False,
                    manifestPath=".specify/extensions/quality/extension.yml",
                    lookupId="extension:quality:template:réview",
                    sourcePath=source_path,
                ),
            ),
        )
    )


def test_artifact_info_dispatches_directly_to_shared_operation(
    spec_kit_project: Path,
):
    command_runner = Mock(side_effect=AssertionError("subprocess executor reached"))

    with (
        patch(
            "specify_cli.artifacts.mcp_info.get_artifact_info",
            return_value=_named_result(),
        ) as operation,
        patch(
            "specify_cli.mcp_server.executor._run_cli_process",
            side_effect=AssertionError("subprocess executor reached"),
        ) as run_cli_process,
        patch(
            "specify_cli.artifacts.command_info.artifact_info",
            side_effect=AssertionError("CLI adapter reached"),
        ) as cli_adapter,
    ):
        server = create_server(
            command_runner=command_runner,
            launch_directory=spec_kit_project,
        )
        result = _run(
            server.call_tool(
                TOOL_NAME,
                {"identifier": "réview", "kind": "template"},
            )
        )

    assert result.is_error is False
    assert result.structured_content["id"] == "template:réview"
    assert operation.call_args.args[0] == ArtifactInfoRequest(
        project_directory=spec_kit_project,
        identifier="réview",
        kind="template",
    )
    command_runner.assert_not_called()
    run_cli_process.assert_not_called()
    cli_adapter.assert_not_called()


def test_artifact_info_cli_mcp_success_parity(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    expected = _named_result()
    operation = Mock(return_value=expected)
    request = ArtifactInfoRequest(
        project_directory=spec_kit_project,
        identifier="réview",
        kind="template",
    )
    monkeypatch.chdir(spec_kit_project)

    with (
        patch.object(command_info, "get_artifact_info", operation),
        patch.object(mcp_info, "get_artifact_info", operation),
    ):
        cli_result = CliRunner().invoke(
            app,
            [
                "artifact",
                "info",
                "réview",
                "--json",
                "--kind",
                "template",
            ],
        )
        mcp_result = create_artifact_info_tool(launch_directory=spec_kit_project)(
            "réview", "template"
        )

    assert cli_result.exit_code == 0, cli_result.stderr
    assert cli_result.stderr == ""
    assert mcp_result.is_error is False
    assert json.loads(cli_result.stdout) == mcp_result.structured_content
    assert [item.args[0] for item in operation.call_args_list] == [request, request]


def test_artifact_info_cli_mcp_expected_error_parity(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def fail(request: ArtifactInfoRequest) -> ArtifactInfoResult:
        raise ArtifactInfoNotFoundError(request.identifier)

    operation = Mock(side_effect=fail)
    request = ArtifactInfoRequest(
        project_directory=spec_kit_project,
        identifier="missing",
        kind=None,
    )
    monkeypatch.chdir(spec_kit_project)

    with (
        patch.object(command_info, "get_artifact_info", operation),
        patch.object(mcp_info, "get_artifact_info", operation),
    ):
        cli_result = CliRunner().invoke(
            app,
            ["artifact", "info", "missing", "--json"],
        )
        mcp_result = create_artifact_info_tool(launch_directory=spec_kit_project)(
            "missing"
        )

    assert cli_result.exit_code == 1
    assert cli_result.stdout == ""
    assert mcp_result.is_error is True
    assert mcp_result.structured_content == _expected_error(
        "unknown_artifact",
        "unknown artifact missing",
        details={"identifier": "missing"},
    )
    assert json.loads(cli_result.stderr) == {
        "error": mcp_result.structured_content["error"]["message"]
    }
    assert [item.args[0] for item in operation.call_args_list] == [request, request]


def test_artifact_info_preserves_complete_unicode_layered_result(
    spec_kit_project: Path,
):
    tool = create_artifact_info_tool(launch_directory=spec_kit_project)
    with patch(
        "specify_cli.artifacts.mcp_info.get_artifact_info",
        return_value=_named_result(),
    ):
        result = tool("template:réview")

    expected = _named_result().to_json_dict()
    assert result.is_error is False
    assert result.structured_content == expected
    assert json.loads(result.content[0].text) == expected
    typed = ArtifactInfoToolResult.model_validate(
        result.structured_content,
        strict=True,
    ).root
    assert isinstance(typed, ArtifactInfoNamedResult)
    assert typed.name == "réview"
    assert typed.description == "Réview ✓"
    assert [entry.sourceId for entry in typed.stack] == ["compliance", "quality"]
    assert typed.stack[0].presetName == "Compliance"
    assert typed.stack[0].lookupId == "preset:compliance:template:réview"
    assert typed.stack[1].sourcePath.endswith("réview.md")


def test_artifact_info_bare_and_public_identifiers_are_semantically_equal(
    spec_kit_project: Path,
):
    server = create_server(launch_directory=spec_kit_project)

    by_name = _run(server.call_tool(TOOL_NAME, {"identifier": "speckit.plan"}))
    by_id = _run(server.call_tool(TOOL_NAME, {"identifier": "command:speckit.plan"}))

    assert by_name.is_error is False
    assert by_id.is_error is False
    assert by_name.structured_content == by_id.structured_content


@pytest.mark.parametrize(
    ("identifier", "kind"),
    [
        ("speckit.constitution", "command"),
        ("spec-template", "template"),
        ("setup-plan", "script"),
    ],
)
def test_artifact_info_accepts_each_explicit_named_kind(
    spec_kit_project: Path,
    identifier: str,
    kind: str,
):
    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": identifier, "kind": kind},
        )
    )

    assert result.is_error is False
    assert result.structured_content["kind"] == kind


def test_artifact_info_preserves_hook_identity_and_stack(
    spec_kit_project: Path,
):
    install_extension_with_hooks(
        spec_kit_project,
        "quality",
        hooks={
            "custom:after": [
                {
                    "command": "/skill:speckit-quality",
                    "description": "Réview hook",
                    "priority": 4,
                    "optional": False,
                }
            ]
        },
    )
    identifier = "hook:custom%3Aafter:%2Fskill%3Aspeckit-quality"

    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": identifier},
        )
    )

    assert result.is_error is False
    typed = ArtifactInfoToolResult.model_validate(
        result.structured_content,
        strict=True,
    ).root
    assert isinstance(typed, ArtifactInfoHookResult)
    assert typed.id == identifier
    assert typed.name == "custom%3Aafter:%2Fskill%3Aspeckit-quality"
    assert typed.eventName == "custom:after"
    assert typed.targetCommand == "/skill:speckit-quality"
    assert typed.description == "Réview hook"
    assert typed.stack[0].lookupId == (
        "extension:quality:hook:custom%3Aafter:%2Fskill%3Aspeckit-quality"
    )
    assert typed.stack[0].priority == 4
    assert typed.stack[0].optional is False


def test_artifact_info_is_deterministic_across_repeated_calls(
    spec_kit_project: Path,
):
    server = create_server(launch_directory=spec_kit_project)

    first = _run(server.call_tool(TOOL_NAME, {"identifier": "speckit.plan"}))
    second = _run(server.call_tool(TOOL_NAME, {"identifier": "speckit.plan"}))

    assert first == second


def test_artifact_info_callable_declares_call_tool_result_contract(
    spec_kit_project: Path,
):
    tool = create_artifact_info_tool(launch_directory=spec_kit_project)

    assert tool.__annotations__["return"] == "ArtifactInfoCallResult"
    assert mcp_info.ArtifactInfoCallResult.__origin__ is CallToolResult


def test_artifact_info_uses_server_launch_directory_by_default(
    spec_kit_project: Path,
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(spec_kit_project)
    server = create_server()
    monkeypatch.chdir(non_project)
    operation = Mock(return_value=_named_result())
    with patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation):
        result = _run(server.call_tool(TOOL_NAME, {"identifier": "réview"}))

    assert result.is_error is False
    assert operation.call_args.args[0].project_directory == spec_kit_project


def test_artifact_info_accepts_explicit_absolute_project_directory(
    spec_kit_project: Path,
    non_project: Path,
):
    operation = Mock(return_value=_named_result())
    with patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation):
        result = _run(
            create_server(launch_directory=non_project).call_tool(
                TOOL_NAME,
                {
                    "identifier": "réview",
                    "project_directory": str(spec_kit_project),
                },
            )
        )

    assert result.is_error is False
    assert operation.call_args.args[0].project_directory == spec_kit_project


def test_artifact_info_isolates_sequential_project_contexts(
    spec_kit_project: Path,
    non_project: Path,
):
    invocation_cwd = Path.cwd()

    def operation(request: ArtifactInfoRequest) -> ArtifactInfoResult:
        return ArtifactInfoResult(
            artifact=ArtifactInfoNamedArtifact(
                id=f"template:{request.project_directory.name}",
                name=request.project_directory.name,
                kind="template",
                description=request.project_directory.name,
                stack=(
                    StackLayer(
                        id=f"template:{request.project_directory.name}",
                        layer=None,
                        sourceId=None,
                        presetId=None,
                        presetName=None,
                        strategy="replace",
                        active=True,
                        hidden=False,
                        manifestPath=None,
                        lookupId=None,
                        sourcePath=None,
                    ),
                ),
            )
        )

    with patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation):
        server = create_server(launch_directory=spec_kit_project)
        first = _run(
            server.call_tool(
                TOOL_NAME,
                {
                    "identifier": "first",
                    "project_directory": str(spec_kit_project),
                },
            )
        )
        second = _run(
            server.call_tool(
                TOOL_NAME,
                {
                    "identifier": "second",
                    "project_directory": str(non_project),
                },
            )
        )

    assert first.structured_content["name"] == spec_kit_project.name
    assert second.structured_content["name"] == non_project.name
    assert Path.cwd() == invocation_cwd


def test_artifact_info_discovery_has_exact_contract(
    spec_kit_project: Path,
):
    tools = _run(create_server(launch_directory=spec_kit_project).list_tools())
    tool = next(tool for tool in tools if tool.name == TOOL_NAME)

    assert tool.name == TOOL_NAME
    assert tool.description == TOOL_DESCRIPTION
    assert tool.input_schema == {
        "additionalProperties": False,
        "properties": {
            "identifier": {"title": "Identifier", "type": "string"},
            "kind": {
                "anyOf": [
                    {
                        "enum": ["command", "template", "script", "hook"],
                        "type": "string",
                    },
                    {"type": "null"},
                ],
                "default": None,
                "title": "Kind",
            },
            "project_directory": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "title": "Project Directory",
            },
        },
        "required": ["identifier"],
        "title": "specify_artifact_infoArguments",
        "type": "object",
    }
    assert tool.output_schema == ArtifactInfoToolResult.model_json_schema()
    assert tool.output_schema["discriminator"] == {
        "mapping": {
            "command": "#/$defs/ArtifactInfoNamedResult",
            "hook": "#/$defs/ArtifactInfoHookResult",
            "script": "#/$defs/ArtifactInfoNamedResult",
            "template": "#/$defs/ArtifactInfoNamedResult",
        },
        "propertyName": "kind",
    }
    assert (
        tool.output_schema["$defs"]["ArtifactInfoNamedResult"]["additionalProperties"]
        is False
    )
    assert (
        tool.output_schema["$defs"]["ArtifactInfoHookResult"]["additionalProperties"]
        is False
    )
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is None
    assert tool.annotations.idempotent_hint is True
    assert tool.annotations.open_world_hint is False


def test_artifact_info_rejects_unknown_arguments_before_dispatch(
    spec_kit_project: Path,
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation),
        pytest.raises(ToolError, match="Extra inputs are not permitted"),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan", "unexpected": True},
            )
        )

    operation.assert_not_called()


@pytest.mark.parametrize(
    "arguments",
    [
        {"identifier": 1},
        {"identifier": True},
        {"identifier": "speckit.plan", "kind": 1},
        {"identifier": "speckit.plan", "kind": True},
        {"identifier": "speckit.plan", "project_directory": 1},
        {"identifier": "speckit.plan", "project_directory": True},
    ],
)
def test_artifact_info_rejects_type_coercion_before_dispatch(
    spec_kit_project: Path,
    arguments: dict[str, object],
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation),
        pytest.raises(ToolError),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                arguments,
            )
        )

    operation.assert_not_called()


def test_artifact_info_rejects_invalid_kind_before_dispatch(
    spec_kit_project: Path,
):
    operation = Mock(side_effect=AssertionError("operation reached"))
    with (
        patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation),
        pytest.raises(ToolError),
    ):
        _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan", "kind": "invalid"},
            )
        )

    operation.assert_not_called()


def test_artifact_info_maps_relative_project_directory(
    spec_kit_project: Path,
):
    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {
                "identifier": "speckit.plan",
                "project_directory": "relative-project",
            },
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "invalid_project_directory",
        "project_directory must be an absolute path",
        details={"project_directory": "relative-project"},
    )


def test_artifact_info_maps_non_project_error(non_project: Path):
    result = _run(
        create_server(launch_directory=non_project).call_tool(
            TOOL_NAME,
            {"identifier": "speckit.plan"},
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "not_a_spec_kit_project",
        "not a Spec Kit project: no .specify/ directory found",
        details={"project_directory": str(non_project)},
    )


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "unknown-prefix:name",
        "command:bad:name",
        "hook:event",
        "hook:event:bad%escape",
        "hook:event:%FF",
    ],
)
def test_artifact_info_maps_malformed_identifiers(
    spec_kit_project: Path,
    identifier: str,
):
    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": identifier},
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "invalid_artifact_identifier",
        f"unknown artifact {identifier}",
        details={"identifier": identifier},
    )


@pytest.mark.parametrize(
    ("identifier", "code"),
    [
        ("missing", "unknown_artifact"),
        ("command:missing", "unknown_artifact"),
        ("hook:nope:missing.cmd", "unknown_hook"),
    ],
)
def test_artifact_info_maps_unknown_artifacts(
    spec_kit_project: Path,
    identifier: str,
    code: str,
):
    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": identifier},
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        code,
        f"unknown artifact {identifier}",
        details={"identifier": identifier},
    )


def test_artifact_info_maps_ambiguous_artifact(spec_kit_project: Path):
    overrides = spec_kit_project / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "shared.md").write_text("body", encoding="utf-8")

    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": "shared"},
        )
    )

    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "ambiguous_artifact"
    assert result.structured_content["error"]["message"].startswith(
        "ambiguous artifact shared:"
    )
    assert result.structured_content["error"]["details"] == {"identifier": "shared"}


def test_artifact_info_maps_corrupt_registry_error(spec_kit_project: Path):
    registry = spec_kit_project / ".specify" / "extensions" / ".registry"
    registry.write_text("{invalid", encoding="utf-8")

    result = _run(
        create_server(launch_directory=spec_kit_project).call_tool(
            TOOL_NAME,
            {"identifier": "speckit.plan"},
        )
    )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "artifact_resolution_failed",
        "artifact resolution failed",
        details={
            "project_directory": str(spec_kit_project),
            "identifier": "speckit.plan",
        },
    )


@pytest.mark.parametrize(
    "failure",
    [
        PresetError("broken preset"),
        OSError("unreadable"),
    ],
)
def test_artifact_info_preserves_operation_owned_resolution_mapping(
    spec_kit_project: Path,
    failure: Exception,
):
    catalog = Mock()
    catalog.get_artifact_info.side_effect = failure
    with patch.object(
        _operation_info,
        "ArtifactCatalog",
        Mock(return_value=catalog),
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan"},
            )
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "artifact_resolution_failed",
        "artifact resolution failed",
        details={
            "project_directory": str(spec_kit_project),
            "identifier": "speckit.plan",
        },
    )


@pytest.mark.parametrize(
    "operation_error",
    [
        ArtifactInfoProjectDirectoryError(Path("relative")),
        ArtifactInfoProjectError(Path("/missing")),
        ArtifactInfoKindError("invalid"),
        ArtifactInfoIdentifierError("bad"),
        ArtifactInfoNotFoundError("missing"),
        ArtifactInfoHookNotFoundError("hook:missing:command"),
        ArtifactInfoAmbiguousError("shared", "ambiguous artifact shared"),
        ArtifactInfoResolutionError(Path("/project"), "speckit.plan"),
        ArtifactInfoInvalidResultError(Path("/project"), "speckit.plan"),
        ArtifactInfoError(
            code="temporary_failure",
            message="try again",
            details={"attempt": 1},
            retryable=True,
        ),
    ],
)
def test_artifact_info_preserves_expected_operation_error_contract(
    spec_kit_project: Path,
    operation_error: ArtifactInfoError,
):
    with patch(
        "specify_cli.artifacts.mcp_info.get_artifact_info",
        side_effect=operation_error,
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan"},
            )
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        operation_error.code,
        operation_error.message,
        details=operation_error.details,
        retryable=operation_error.retryable,
    )


@pytest.mark.parametrize(
    "operation_result",
    [
        None,
        object(),
        ArtifactInfoResult(artifact=None),  # type: ignore[arg-type]
        ArtifactInfoResult(
            artifact=ArtifactInfoNamedArtifact(
                id="template:wrong",
                name="réview",
                kind="template",
                description="Broken",
                stack=(),
            )
        ),
        ArtifactInfoResult(
            artifact=ArtifactInfoHookArtifact(
                id="hook:event:command",
                name="event:command",
                kind="hook",
                description="Broken",
                eventName="event",
                targetCommand="command",
                registered=True,
                stack=(
                    HookStackEntry(
                        id="hook:event:command",
                        layer="extension",
                        sourceId="quality",
                        presetId=None,
                        presetName=None,
                        strategy="additive",
                        active=True,
                        hidden=False,
                        manifestPath=".specify/extensions/quality/extension.yml",
                        lookupId="extension:quality:hook:event:command",
                        sourcePath=None,
                        priority=True,  # type: ignore[arg-type]
                        optional=False,
                    ),
                ),
            )
        ),
    ],
)
def test_artifact_info_rejects_invalid_operation_results(
    spec_kit_project: Path,
    operation_result: object,
):
    with patch(
        "specify_cli.artifacts.mcp_info.get_artifact_info",
        return_value=operation_result,
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan"},
            )
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "invalid_operation_result",
        "The artifact info operation returned an invalid result.",
    )


def test_artifact_info_sanitizes_and_logs_unexpected_failure(
    spec_kit_project: Path,
    caplog: pytest.LogCaptureFixture,
):
    unsafe = "SECRET_TOKEN=do-not-print /Users/example/private/project"
    with (
        patch(
            "specify_cli.artifacts.mcp_info.get_artifact_info",
            side_effect=RuntimeError(unsafe),
        ),
        caplog.at_level(logging.ERROR, logger="specify_cli.artifacts.mcp_info"),
    ):
        result = _run(
            create_server(launch_directory=spec_kit_project).call_tool(
                TOOL_NAME,
                {"identifier": "speckit.plan"},
            )
        )

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "internal_error",
        "Unable to inspect the Spec Kit artifact.",
    )
    rendered = result.model_dump_json(by_alias=True)
    assert unsafe not in rendered
    assert "RuntimeError" not in rendered
    assert "Traceback" not in rendered
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "Unexpected failure in the artifact info MCP adapter."
    )
    assert caplog.records[0].exc_info is not None


def test_artifact_info_rejects_oversized_success(spec_kit_project: Path):
    tool = create_artifact_info_tool(
        launch_directory=spec_kit_project,
        max_wire_response_bytes=4096,
    )
    with patch(
        "specify_cli.artifacts.mcp_info.get_artifact_info",
        return_value=_named_result(description="x" * 8192),
    ):
        result = tool("template:réview")

    assert result.is_error is True
    assert result.structured_content == _expected_error(
        "response_too_large",
        "The artifact info result exceeds the MCP response-size limit.",
        details={"max_bytes": 4096},
        retryable=True,
    )
    assert "x" * 1024 not in result.model_dump_json(by_alias=True)


def test_artifact_info_bounds_oversized_expected_error(spec_kit_project: Path):
    oversized = "private-" * 1024
    tool = create_artifact_info_tool(
        launch_directory=spec_kit_project,
        max_wire_response_bytes=4096,
    )
    with patch(
        "specify_cli.artifacts.mcp_info.get_artifact_info",
        side_effect=ArtifactInfoError(
            code="artifact_resolution_failed",
            message="artifact resolution failed",
            details={"path": oversized},
        ),
    ):
        result = tool("template:réview")

    assert result.structured_content == _expected_error(
        "response_too_large",
        "The artifact info result exceeds the MCP response-size limit.",
        details={"max_bytes": 4096},
        retryable=True,
    )
    assert oversized not in result.model_dump_json(by_alias=True)


@pytest.mark.parametrize(
    ("operation_result", "constant_name"),
    [
        (None, "_INVALID_RESULT_MESSAGE"),
        (RuntimeError("unsafe"), "_INTERNAL_ERROR_MESSAGE"),
    ],
)
def test_artifact_info_bounds_oversized_adapter_errors(
    spec_kit_project: Path,
    operation_result: object,
    constant_name: str,
):
    tool = create_artifact_info_tool(
        launch_directory=spec_kit_project,
        max_wire_response_bytes=4096,
    )
    patcher = (
        patch(
            "specify_cli.artifacts.mcp_info.get_artifact_info",
            side_effect=operation_result,
        )
        if isinstance(operation_result, Exception)
        else patch(
            "specify_cli.artifacts.mcp_info.get_artifact_info",
            return_value=operation_result,
        )
    )
    with (
        patcher,
        patch.object(mcp_info, constant_name, "x" * 8192),
    ):
        result = tool("template:réview")

    assert result.structured_content == _expected_error(
        "response_too_large",
        "The artifact info result exceeds the MCP response-size limit.",
        details={"max_bytes": 4096},
        retryable=True,
    )
    assert "x" * 1024 not in result.model_dump_json(by_alias=True)


def test_artifact_info_inventory_matches_operation_and_registration(
    spec_kit_project: Path,
):
    cli_operation_ids = {
        f"artifact.{command.name}"
        for command in _commands.artifact_app.registered_commands
    }
    inventory_operation_ids = [item.operation_id for item in _mcp.ARTIFACT_TOOLS]
    inventory_tool_names = [item.mcp_tool_name for item in _mcp.ARTIFACT_TOOLS]
    registered_tool_names = [
        tool.name
        for tool in _run(create_server(launch_directory=spec_kit_project).list_tools())
    ]

    assert set(inventory_operation_ids) == cli_operation_ids
    assert len(inventory_operation_ids) == len(set(inventory_operation_ids))
    assert len(inventory_tool_names) == len(set(inventory_tool_names))
    info_tool = next(
        item
        for item in _mcp.ARTIFACT_TOOLS
        if item.operation_id == ARTIFACT_INFO_OPERATION.operation_id
    )
    assert info_tool.contract_version == ARTIFACT_INFO_OPERATION.contract_version
    assert info_tool.disposition == "available"
    assert info_tool.disposition_reason is None
    assert info_tool.capabilities == ARTIFACT_INFO_OPERATION.capabilities
    assert info_tool.network_access == ARTIFACT_INFO_OPERATION.network_access
    assert registered_tool_names.count(info_tool.mcp_tool_name) == 1

    lookup_tool = next(
        item for item in _mcp.ARTIFACT_TOOLS if item.operation_id == "artifact.lookup"
    )
    assert lookup_tool.disposition == "unavailable"
    assert lookup_tool.disposition_reason == (
        "The artifact.lookup CLI leaf does not yet have a shared typed operation."
    )
    assert lookup_tool.mcp_tool_name not in registered_tool_names


def test_artifact_info_registration_adds_one_tool_and_rejects_collision(
    spec_kit_project: Path,
):
    server = MCPServer(name="test")

    mcp_info.register(server, launch_directory=spec_kit_project)

    assert [tool.name for tool in _run(server.list_tools())] == [TOOL_NAME]
    with pytest.raises(ValueError, match=f"MCP tool name collision: {TOOL_NAME}"):
        mcp_info.register(server, launch_directory=spec_kit_project)
    assert [tool.name for tool in _run(server.list_tools())] == [TOOL_NAME]


def test_artifact_info_sdk_tool_lookup_failure_is_descriptive():
    with pytest.raises(
        RuntimeError,
        match="MCP SDK compatibility error: registered tool lookup is unavailable",
    ):
        mcp_info._lookup_registered_tool(object(), TOOL_NAME)


def test_artifact_info_sdk_tool_lookup_wraps_manager_failure():
    server = Mock()
    server._tool_manager.get_tool.side_effect = RuntimeError("SDK changed")

    with pytest.raises(
        RuntimeError,
        match="MCP SDK compatibility error: registered tool lookup is unavailable",
    ):
        mcp_info._lookup_registered_tool(server, TOOL_NAME)


def test_artifact_info_closed_arguments_require_retained_registration():
    server = Mock()
    server._tool_manager.get_tool.return_value = None

    with pytest.raises(
        RuntimeError,
        match=f"MCP tool registration was not retained: {TOOL_NAME}",
    ):
        mcp_info._configure_closed_arguments(server, TOOL_NAME)


def test_artifact_info_closed_arguments_wrap_incompatible_metadata():
    server = Mock()
    server._tool_manager.get_tool.return_value = object()

    with pytest.raises(
        RuntimeError,
        match=f"MCP SDK compatibility error while closing arguments for {TOOL_NAME}",
    ):
        mcp_info._configure_closed_arguments(server, TOOL_NAME)


def test_artifact_info_tool_requires_absolute_server_launch_directory():
    with pytest.raises(
        ValueError,
        match="MCP server launch directory must be absolute",
    ):
        create_artifact_info_tool(launch_directory=Path("relative"))


def test_artifact_info_tool_requires_room_for_bounded_error_response(
    spec_kit_project: Path,
):
    with pytest.raises(
        ValueError,
        match="MCP response-size limit cannot hold the bounded error response",
    ):
        create_artifact_info_tool(
            launch_directory=spec_kit_project,
            max_wire_response_bytes=1024,
        )


def test_in_memory_artifact_info_protocol_enforces_near_boundary_wire_size(
    spec_kit_project: Path,
):
    max_wire_response_bytes = 4096
    within_limit: ArtifactInfoResult | None = None
    oversized: ArtifactInfoResult | None = None

    for description_length in range(max_wire_response_bytes):
        candidate = _named_result(description="x" * description_length)
        converted = mcp_info._convert_result(candidate)
        wire_size = mcp_info._wire_response_size(
            mcp_info._build_success_result(converted)
        )
        if wire_size <= max_wire_response_bytes:
            within_limit = candidate
            continue
        oversized = candidate
        assert (
            len(converted.model_dump_json().encode("utf-8")) < max_wire_response_bytes
        )
        break

    assert within_limit is not None
    assert oversized is not None

    async def exercise():
        server = MCPServer(name="test")
        mcp_info.register(
            server,
            launch_directory=spec_kit_project,
            max_wire_response_bytes=max_wire_response_bytes,
        )
        operation = Mock(side_effect=[within_limit, oversized])
        with patch("specify_cli.artifacts.mcp_info.get_artifact_info", operation):
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
                    success = await session.call_tool(
                        TOOL_NAME,
                        {"identifier": "template:réview"},
                    )
                    failure = await session.call_tool(
                        TOOL_NAME,
                        {"identifier": "template:réview"},
                    )
                task_group.cancel_scope.cancel()
        return success, failure

    success, failure = _run(exercise())

    assert success.is_error is False
    assert mcp_info._wire_response_size(success) <= max_wire_response_bytes
    assert failure.is_error is True
    assert failure.structured_content == _expected_error(
        "response_too_large",
        "The artifact info result exceeds the MCP response-size limit.",
        details={"max_bytes": max_wire_response_bytes},
        retryable=True,
    )
    assert mcp_info._wire_response_size(failure) <= max_wire_response_bytes


def test_in_memory_client_preserves_artifact_info_wire_shapes(
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
                success = await session.call_tool(
                    TOOL_NAME,
                    {"identifier": "speckit.plan"},
                )
                failure = await session.call_tool(
                    TOOL_NAME,
                    {"identifier": "missing"},
                )
                schema_failure = await session.call_tool(
                    TOOL_NAME,
                    {"identifier": "speckit.plan", "unexpected": True},
                )
            task_group.cancel_scope.cancel()
        return tools, success, failure, schema_failure

    tools, success, failure, schema_failure = _run(exercise())

    discovered = next(tool for tool in tools.tools if tool.name == TOOL_NAME)
    assert discovered.input_schema["additionalProperties"] is False
    assert success.is_error is False
    assert success.structured_content["id"] == "command:speckit.plan"
    assert failure.is_error is True
    assert failure.structured_content["error"]["code"] == "unknown_artifact"
    assert schema_failure.is_error is True
    assert schema_failure.structured_content is None
    assert "Extra inputs are not permitted" in schema_failure.content[0].text
