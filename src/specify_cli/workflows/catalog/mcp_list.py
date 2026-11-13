"""Strict MCP projection of the shared workflow catalog list operation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit, urlunsplit

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from ..mcp_list import _lookup_registered_tool, _tool_error, _wire_response_size
from . import _operation_list as operation

logger = logging.getLogger(__name__)
_MAX_WIRE_RESPONSE_BYTES = 1024 * 1024
WorkflowCatalogListLimit = Annotated[
    int, Field(strict=True, ge=1, le=operation.WORKFLOW_CATALOG_LIST_MAX_LIMIT)
]
WorkflowCatalogProjectDirectory = Annotated[str, Field(strict=True)]


class WorkflowCatalogListToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    project_directory: WorkflowCatalogProjectDirectory | None = None
    limit: WorkflowCatalogListLimit = 100


class WorkflowCatalogSourceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str
    url: str
    priority: int
    install_allowed: bool
    description: str | None


class WorkflowCatalogListToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    items: list[WorkflowCatalogSourceResult] = Field(
        max_length=operation.WORKFLOW_CATALOG_LIST_MAX_LIMIT
    )
    truncated: bool


WorkflowCatalogListCallResult = Annotated[CallToolResult, WorkflowCatalogListToolResult]
WorkflowCatalogListTool = Callable[[str | None, int], CallToolResult]


class _InvalidOperationResult(Exception):
    """The shared outcome does not match the declared result contract."""


def _disclosable_url(url: str) -> str:
    """Drop the URL parts that can carry credentials before leaving the process."""
    parts = urlsplit(url)
    host = parts.netloc.rpartition("@")[2]
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def _convert_result(
    result: operation.WorkflowCatalogListResult,
    *,
    requested_limit: int,
) -> WorkflowCatalogListToolResult:
    try:
        if not isinstance(result, operation.WorkflowCatalogListResult):
            raise TypeError("Expected WorkflowCatalogListResult")
        if len(result.items) > requested_limit:
            raise ValueError("Operation exceeded requested limit")
        if result.truncated and len(result.items) != requested_limit:
            raise ValueError("Truncated result must fill the requested limit")
        return WorkflowCatalogListToolResult.model_validate(
            {
                "items": [
                    {
                        "name": item.name,
                        "url": _disclosable_url(item.url),
                        "priority": item.priority,
                        "install_allowed": item.install_allowed,
                        "description": item.description,
                    }
                    for item in result.items
                ],
                "truncated": result.truncated,
            },
            strict=True,
        )
    except (TypeError, ValueError, AttributeError) as exc:
        raise _InvalidOperationResult from exc


def _response_too_large() -> CallToolResult:
    return _tool_error(
        "response_too_large",
        "Workflow catalog list response exceeds the byte limit; retry with a smaller limit.",
        retryable=True,
    )


def create_workflow_catalog_list_tool(
    *,
    launch_directory: Path,
    max_wire_response_bytes: int = _MAX_WIRE_RESPONSE_BYTES,
) -> WorkflowCatalogListTool:
    """Bind the default project once; never change process cwd for requests."""
    launch_directory = Path(launch_directory)
    if not launch_directory.is_absolute():
        raise ValueError("MCP server launch directory must be absolute")
    if _wire_response_size(_response_too_large()) > max_wire_response_bytes:
        raise ValueError(
            "MCP response-size limit cannot hold the bounded error response"
        )

    def specify_workflow_catalog_list(
        project_directory: WorkflowCatalogProjectDirectory | None = None,
        limit: WorkflowCatalogListLimit = 100,
    ) -> WorkflowCatalogListCallResult:
        """List active workflow catalog sources in priority order."""
        tool_input = WorkflowCatalogListToolInput.model_validate(
            {"project_directory": project_directory, "limit": limit}, strict=True
        )
        try:
            result = operation.list_catalog_sources(
                operation.WorkflowCatalogListRequest(
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
        except operation.WorkflowCatalogListError as exc:
            # Shared messages can name local paths, so MCP sends fixed text only.
            messages = {
                "invalid_project_directory": "project_directory must be an absolute path.",
                "not_a_spec_kit_project": "The selected directory is not a Spec Kit project.",
                "unsafe_workflow_storage": "The selected workflow storage is unsafe or unreadable.",
                "invalid_catalog_config": "The workflow catalog configuration is invalid.",
                "invalid_limit": "The workflow catalog list limit is invalid.",
            }
            response = _tool_error(
                exc.code, messages.get(exc.code, "Unable to list workflow catalogs.")
            )
        except _InvalidOperationResult:
            response = _tool_error(
                "invalid_operation_result",
                "The workflow catalog list result is invalid.",
            )
        except Exception:
            logger.exception(
                "Unexpected failure in the workflow catalog list MCP adapter."
            )
            response = _tool_error(
                "internal_error", "Unable to list workflow catalogs."
            )
        if _wire_response_size(response) > max_wire_response_bytes:
            return _response_too_large()
        return response

    return specify_workflow_catalog_list


def register(
    server: MCPServer,
    *,
    launch_directory: Path,
    tool_name: str = "specify_workflow_catalog_list",
) -> None:
    """Register once, closing SDK argument validation as well as discovery."""
    if _lookup_registered_tool(server, tool_name) is not None:
        raise ValueError(f"MCP tool name collision: {tool_name}")
    server.add_tool(
        create_workflow_catalog_list_tool(launch_directory=launch_directory),
        name=tool_name,
        description=(
            "List active workflow catalog sources in priority order without fetching them. "
            "URLs omit userinfo, query strings and fragments. "
            "limit bounds the sources returned; truncated reports omitted sources."
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
            "MCP SDK compatibility error while closing workflow catalog list arguments"
        ) from exc
