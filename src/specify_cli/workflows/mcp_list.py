"""Strict MCP projection of the shared installed-workflow list operation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from . import _operation_list as operation

logger = logging.getLogger(__name__)
_MAX_WIRE_RESPONSE_BYTES = 1024 * 1024
_WIRE_ENVELOPE_RESERVE_BYTES = 1024
WorkflowListLimit = Annotated[
    int, Field(strict=True, ge=1, le=operation.WORKFLOW_LIST_MAX_LIMIT)
]
WorkflowProjectDirectory = Annotated[str, Field(strict=True)]


class WorkflowListToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    project_directory: WorkflowProjectDirectory | None = None
    limit: WorkflowListLimit = 100


class WorkflowEntryResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["workflow"]
    id: str
    name: str
    version: str
    description: str | None
    enabled: bool


class WorkflowWarningResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["warning"]
    code: Literal["invalid_registry_entry"]
    workflow_id: str
    message: str


class WorkflowListToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    items: list[
        Annotated[
            WorkflowEntryResult | WorkflowWarningResult, Field(discriminator="kind")
        ]
    ] = Field(max_length=operation.WORKFLOW_LIST_MAX_LIMIT)
    truncated: bool


WorkflowListCallResult = Annotated[CallToolResult, WorkflowListToolResult]
WorkflowListTool = Callable[[str | None, int], CallToolResult]


class _InvalidOperationResult(Exception):
    """The shared outcome does not match the declared result contract."""


def _convert_result(
    result: operation.WorkflowListResult,
    *,
    requested_limit: int,
) -> WorkflowListToolResult:
    try:
        if not isinstance(result, operation.WorkflowListResult):
            raise TypeError("Expected WorkflowListResult")
        if len(result.items) > requested_limit:
            raise ValueError("Operation exceeded requested limit")
        if result.truncated and len(result.items) != requested_limit:
            raise ValueError("Truncated result must fill the requested limit")
        return WorkflowListToolResult.model_validate(
            {
                "items": [asdict(item) for item in result.items],
                "truncated": result.truncated,
            },
            strict=True,
        )
    except (TypeError, ValueError, AttributeError) as exc:
        raise _InvalidOperationResult from exc


def _tool_error(code: str, message: str, *, retryable: bool = False) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=f"{code}: {message}")],
        structured_content={
            "error": {
                "code": code,
                "message": message,
                "details": {},
                "retryable": retryable,
            }
        },
        is_error=True,
    )


def _wire_response_size(result: CallToolResult) -> int:
    return (
        len(result.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8"))
        + _WIRE_ENVELOPE_RESERVE_BYTES
    )


def _response_too_large() -> CallToolResult:
    return _tool_error(
        "response_too_large",
        "Workflow list response exceeds the byte limit; retry with a smaller limit.",
        retryable=True,
    )


def create_workflow_list_tool(
    *,
    launch_directory: Path,
    max_wire_response_bytes: int = _MAX_WIRE_RESPONSE_BYTES,
) -> WorkflowListTool:
    """Bind the default project once; never change process cwd for requests."""
    launch_directory = Path(launch_directory)
    if not launch_directory.is_absolute():
        raise ValueError("MCP server launch directory must be absolute")
    if _wire_response_size(_response_too_large()) > max_wire_response_bytes:
        raise ValueError(
            "MCP response-size limit cannot hold the bounded error response"
        )

    def specify_workflow_list(
        project_directory: WorkflowProjectDirectory | None = None,
        limit: WorkflowListLimit = 100,
    ) -> WorkflowListCallResult:
        """List installed workflows and skipped-entry warnings in registry order."""
        tool_input = WorkflowListToolInput.model_validate(
            {"project_directory": project_directory, "limit": limit}, strict=True
        )
        try:
            result = operation.list_workflows(
                operation.WorkflowListRequest(
                    project_directory=(
                        launch_directory
                        if tool_input.project_directory is None
                        else Path(tool_input.project_directory)
                    ),
                    limit=tool_input.limit,
                )
            )
            payload = _convert_result(result, requested_limit=tool_input.limit)
            response = CallToolResult(
                content=[
                    TextContent(type="text", text=payload.model_dump_json(indent=2))
                ],
                structured_content=payload.model_dump(mode="json"),
                is_error=False,
            )
        except operation.WorkflowListError as exc:
            # Registry/OS exception strings can contain paths or untrusted data.
            # CLI retains its established diagnostics; MCP never exposes them.
            messages = {
                "invalid_project_directory": "project_directory must be an absolute path.",
                "not_a_spec_kit_project": "The selected directory is not a Spec Kit project.",
                "unsafe_workflow_storage": "The selected workflow storage is unsafe or unreadable.",
                "workflow_registry_read_failed": "Unable to read the workflow registry.",
                "invalid_limit": "The workflow list limit is invalid.",
            }
            response = _tool_error(
                exc.code, messages.get(exc.code, "Unable to list workflows.")
            )
        except _InvalidOperationResult:
            response = _tool_error(
                "invalid_operation_result", "The workflow list result is invalid."
            )
        except Exception:
            logger.exception("Unexpected failure in the workflow list MCP adapter.")
            response = _tool_error(
                "internal_error", "Unable to list installed workflows."
            )
        if _wire_response_size(response) > max_wire_response_bytes:
            return _response_too_large()
        return response

    return specify_workflow_list


def _lookup_registered_tool(server: MCPServer, name: str) -> Any:
    try:
        return server._tool_manager.get_tool(name)
    except Exception as exc:
        raise RuntimeError(
            "MCP SDK compatibility error: registered tool lookup failed"
        ) from exc


def register(
    server: MCPServer,
    *,
    launch_directory: Path,
    tool_name: str = "specify_workflow_list",
) -> None:
    """Register once, closing SDK argument validation as well as discovery."""
    if _lookup_registered_tool(server, tool_name) is not None:
        raise ValueError(f"MCP tool name collision: {tool_name}")
    server.add_tool(
        create_workflow_list_tool(launch_directory=launch_directory),
        name=tool_name,
        description=(
            "List installed workflows and warnings without execution or network access. "
            "limit bounds registry entries, including warnings; truncated reports omitted entries."
        ),
        annotations=ToolAnnotations(
            read_only_hint=True, idempotent_hint=True, open_world_hint=False
        ),
        structured_output=True,
    )
    try:
        tool = _lookup_registered_tool(server, tool_name)
        argument_model = tool.fn_metadata.arg_model
        argument_model.model_config["extra"] = "forbid"
        argument_model.model_rebuild(force=True)
        tool.parameters = argument_model.model_json_schema(by_alias=True)
    except Exception as exc:
        raise RuntimeError(
            "MCP SDK compatibility error while closing workflow list arguments"
        ) from exc
