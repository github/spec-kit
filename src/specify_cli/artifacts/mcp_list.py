"""MCP adapter for the shared ``artifact.list`` operation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ._operation_list import (
    ARTIFACT_LIST_CURSOR_MAX_LENGTH,
    ARTIFACT_LIST_MAX_LIMIT,
    ArtifactListError,
    ArtifactListRequest,
    ArtifactListResult,
    list_artifacts,
)

logger = logging.getLogger(__name__)
_DEFAULT_LIMIT = 100
_MAX_RESPONSE_BYTES = 1024 * 1024
_INVALID_RESULT_MESSAGE = "The artifact list operation returned an invalid result."
_INTERNAL_ERROR_MESSAGE = "Unable to list Spec Kit artifacts."
_RESPONSE_TOO_LARGE_MESSAGE = (
    "The artifact list result exceeds the MCP response-size limit."
)
_TOOL_DESCRIPTION = (
    "List every command, template, script, and hook Spec Kit exposes for a project."
)

ArtifactListLimit = Annotated[
    int,
    Field(ge=1, le=ARTIFACT_LIST_MAX_LIMIT),
]
ArtifactListCursor = Annotated[
    str,
    Field(
        max_length=ARTIFACT_LIST_CURSOR_MAX_LENGTH,
        pattern=r"^(0|[1-9][0-9]*)$",
    ),
]


class ArtifactListToolInput(BaseModel):
    """Typed input accepted by ``specify_artifact_list``."""

    model_config = ConfigDict(extra="forbid")

    project_directory: str | None = None
    limit: ArtifactListLimit = _DEFAULT_LIMIT
    cursor: ArtifactListCursor | None = None


class ArtifactListStackEntryResult(BaseModel):
    """Composition entry for a named artifact."""

    model_config = ConfigDict(extra="forbid")

    id: str
    layer: Literal["project", "preset", "extension"] | None
    sourceId: str | None
    presetId: str | None
    presetName: str | None
    strategy: Literal["replace", "wrap", "prepend", "append"]
    active: bool
    hidden: bool
    manifestPath: str | None
    lookupId: str | None
    sourcePath: str | None


class ArtifactListHookStackEntryResult(BaseModel):
    """Composition entry for a hook artifact."""

    model_config = ConfigDict(extra="forbid")

    id: str
    layer: Literal["preset", "extension"]
    sourceId: str
    presetId: str | None
    presetName: str | None
    strategy: Literal["additive"]
    active: bool
    hidden: bool
    manifestPath: str
    lookupId: str
    sourcePath: None
    priority: int
    optional: bool


class ArtifactListRowResult(BaseModel):
    """One named artifact inventory row."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["command", "template", "script"]
    description: str
    stack: list[ArtifactListStackEntryResult]


class ArtifactListHookRowResult(BaseModel):
    """One hook inventory row."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["hook"]
    description: str
    eventName: str
    targetCommand: str
    registered: bool
    stack: list[ArtifactListHookStackEntryResult]


ArtifactListItemResult = Annotated[
    ArtifactListRowResult | ArtifactListHookRowResult,
    Field(discriminator="kind"),
]


class ArtifactListToolResult(BaseModel):
    """Typed structured result returned by ``specify_artifact_list``."""

    model_config = ConfigDict(extra="forbid")

    rows: list[ArtifactListItemResult]
    next_cursor: ArtifactListCursor | None
    truncated: bool

    @model_validator(mode="after")
    def validate_continuation(self) -> ArtifactListToolResult:
        """Require continuation metadata to agree with truncation state."""
        if self.truncated != (self.next_cursor is not None):
            raise ValueError("inconsistent artifact list continuation metadata")
        return self


class _InvalidOperationResult(Exception):
    """The shared operation returned an incomplete or invalid typed result."""


class _ResponseTooLarge(Exception):
    """The serialized structured result exceeds the MCP response budget."""


ArtifactListTool = Callable[
    [str | None, ArtifactListLimit, ArtifactListCursor | None],
    ArtifactListToolResult | CallToolResult,
]


def _tool_error(
    code: str,
    message: str,
    *,
    details: dict[str, object] | None = None,
    retryable: bool = False,
) -> CallToolResult:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        }
    }
    return CallToolResult(
        content=[TextContent(type="text", text=f"{code}: {message}")],
        structuredContent=payload,
        isError=True,
    )


def _convert_result(result: ArtifactListResult) -> ArtifactListToolResult:
    try:
        rows = result.rows
    except AttributeError as exc:
        raise _InvalidOperationResult from exc

    try:
        return ArtifactListToolResult.model_validate(
            {
                "rows": list(rows),
                "next_cursor": result.next_cursor,
                "truncated": result.truncated,
            },
            strict=True,
        )
    except (TypeError, ValidationError) as exc:
        raise _InvalidOperationResult from exc


def create_artifact_list_tool(
    *,
    launch_directory: Path,
    max_response_bytes: int = _MAX_RESPONSE_BYTES,
) -> ArtifactListTool:
    """Create a tool bound to the immutable MCP server launch directory."""
    launch_directory = Path(launch_directory)
    if not launch_directory.is_absolute():
        raise ValueError("MCP server launch directory must be absolute")
    if max_response_bytes < 1:
        raise ValueError("MCP response-size limit must be positive")

    def specify_artifact_list(
        project_directory: str | None = None,
        limit: ArtifactListLimit = _DEFAULT_LIMIT,
        cursor: ArtifactListCursor | None = None,
    ) -> ArtifactListToolResult:
        """List every artifact exposed by the selected Spec Kit project."""
        tool_input = ArtifactListToolInput.model_validate(
            {
                "project_directory": project_directory,
                "limit": limit,
                "cursor": cursor,
            },
            strict=True,
        )
        selected_directory = (
            launch_directory
            if tool_input.project_directory is None
            else Path(tool_input.project_directory)
        )
        try:
            result = _convert_result(
                list_artifacts(
                    ArtifactListRequest(
                        project_directory=selected_directory,
                        limit=tool_input.limit,
                        cursor=tool_input.cursor,
                    ),
                )
            )
            if len(result.model_dump_json().encode("utf-8")) > max_response_bytes:
                raise _ResponseTooLarge
            return result
        except ArtifactListError as exc:
            return _tool_error(
                exc.code,
                exc.message,
                details=exc.details,
                retryable=exc.retryable,
            )
        except _InvalidOperationResult:
            return _tool_error(
                "invalid_operation_result",
                _INVALID_RESULT_MESSAGE,
            )
        except _ResponseTooLarge:
            return _tool_error(
                "response_too_large",
                _RESPONSE_TOO_LARGE_MESSAGE,
                details={
                    "max_bytes": max_response_bytes,
                    "requested_limit": tool_input.limit,
                },
                retryable=True,
            )
        except Exception:
            logger.exception("Unexpected failure in the artifact list MCP adapter.")
            return _tool_error("internal_error", _INTERNAL_ERROR_MESSAGE)

    return specify_artifact_list


def _forbid_unexpected_arguments(server: MCPServer, tool_name: str) -> None:
    tool = server._tool_manager.get_tool(tool_name)
    if tool is None:  # pragma: no cover - registration immediately precedes this
        raise RuntimeError(f"Tool registration failed: {tool_name}")

    # MCP SDK argument models ignore extras by default even when discovery
    # advertises a closed command-specific schema.
    argument_model = tool.fn_metadata.arg_model
    argument_model.model_config["extra"] = "forbid"
    argument_model.model_rebuild(force=True)
    tool.parameters = argument_model.model_json_schema(by_alias=True)


def register(
    server: MCPServer,
    *,
    launch_directory: Path,
    tool_name: str = "specify_artifact_list",
) -> None:
    """Register the first-class artifact-list MCP tool exactly once."""
    if server._tool_manager.get_tool(tool_name) is not None:
        raise ValueError(f"MCP tool name collision: {tool_name}")

    server.add_tool(
        create_artifact_list_tool(launch_directory=launch_directory),
        name=tool_name,
        description=_TOOL_DESCRIPTION,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    _forbid_unexpected_arguments(server, tool_name)
