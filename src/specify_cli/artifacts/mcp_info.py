"""MCP adapter for the shared ``artifact.info`` operation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetJsonSchemaHandler,
    RootModel,
    ValidationError,
)
from pydantic_core import CoreSchema

from ._operation_info import (
    ArtifactInfoError,
    ArtifactInfoRequest,
    ArtifactInfoResult,
    get_artifact_info,
)

logger = logging.getLogger(__name__)
_MAX_WIRE_RESPONSE_BYTES = 1024 * 1024
_WIRE_ENVELOPE_RESERVE_BYTES = 1024
_INVALID_RESULT_MESSAGE = "The artifact info operation returned an invalid result."
_INTERNAL_ERROR_MESSAGE = "Unable to inspect the Spec Kit artifact."
_RESPONSE_TOO_LARGE_MESSAGE = (
    "The artifact info result exceeds the MCP response-size limit."
)
_SDK_LOOKUP_ERROR = (
    "MCP SDK compatibility error: registered tool lookup is unavailable."
)
_TOOL_DESCRIPTION = (
    "Return one artifact and its complete composition stack for a project. "
    "Accepts bare or kind:name identifiers; responses are bounded by the MCP "
    "response-size limit."
)

ArtifactIdentifier = Annotated[str, Field(strict=True)]
ArtifactKindInput = Literal["command", "template", "script", "hook"]
ArtifactProjectDirectory = Annotated[str, Field(strict=True)]


class ArtifactInfoToolInput(BaseModel):
    """Typed input accepted by ``specify_artifact_info``."""

    model_config = ConfigDict(extra="forbid")

    identifier: ArtifactIdentifier
    kind: ArtifactKindInput | None = None
    project_directory: ArtifactProjectDirectory | None = None


class ArtifactInfoStackEntryResult(BaseModel):
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


class ArtifactInfoHookStackEntryResult(BaseModel):
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


class ArtifactInfoNamedResult(BaseModel):
    """One named artifact and its complete ordered composition stack."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["command", "template", "script"]
    description: str
    stack: Annotated[list[ArtifactInfoStackEntryResult], Field(min_length=1)]


class ArtifactInfoHookResult(BaseModel):
    """One hook artifact and its additive declaration stack."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["hook"]
    description: str
    eventName: str
    targetCommand: str
    registered: bool
    stack: Annotated[list[ArtifactInfoHookStackEntryResult], Field(min_length=1)]


ArtifactInfoItemResult = Annotated[
    ArtifactInfoNamedResult | ArtifactInfoHookResult,
    Field(discriminator="kind"),
]


class ArtifactInfoToolResult(RootModel[ArtifactInfoItemResult]):
    """Typed structured result returned by ``specify_artifact_info``."""

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> dict[str, Any]:
        """Declare the root-union result as the object required by MCP."""
        schema = handler(core_schema)
        schema["type"] = "object"
        return schema


class _InvalidOperationResult(Exception):
    """The shared operation returned an incomplete or invalid typed result."""


ArtifactInfoCallResult = Annotated[CallToolResult, ArtifactInfoToolResult]
ArtifactInfoTool = Callable[
    [
        ArtifactIdentifier,
        ArtifactKindInput | None,
        ArtifactProjectDirectory | None,
    ],
    CallToolResult,
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


def _convert_result(result: ArtifactInfoResult) -> ArtifactInfoToolResult:
    if not isinstance(result, ArtifactInfoResult):
        raise _InvalidOperationResult
    try:
        payload = result.to_json_dict()
        return ArtifactInfoToolResult.model_validate(payload, strict=True)
    except (AttributeError, TypeError, ValidationError) as exc:
        raise _InvalidOperationResult from exc


def _build_success_result(result: ArtifactInfoToolResult) -> CallToolResult:
    """Build the duplicated structured and compatibility content sent by MCP."""
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=result.model_dump_json(indent=2),
            )
        ],
        structuredContent=result.model_dump(mode="json"),
        isError=False,
    )


def _wire_response_size(result: CallToolResult) -> int:
    """Bound the serialized result plus conservative JSON-RPC envelope space."""
    result_bytes = len(
        result.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8")
    )
    return result_bytes + _WIRE_ENVELOPE_RESERVE_BYTES


def _response_too_large_error(
    *,
    max_wire_response_bytes: int,
) -> CallToolResult:
    return _tool_error(
        "response_too_large",
        _RESPONSE_TOO_LARGE_MESSAGE,
        details={"max_bytes": max_wire_response_bytes},
        retryable=True,
    )


def _bound_tool_result(
    result: CallToolResult,
    *,
    max_wire_response_bytes: int,
) -> CallToolResult:
    if _wire_response_size(result) <= max_wire_response_bytes:
        return result
    return _response_too_large_error(
        max_wire_response_bytes=max_wire_response_bytes,
    )


def create_artifact_info_tool(
    *,
    launch_directory: Path,
    max_wire_response_bytes: int = _MAX_WIRE_RESPONSE_BYTES,
) -> ArtifactInfoTool:
    """Create a tool bound to the immutable MCP server launch directory."""
    launch_directory = Path(launch_directory)
    if not launch_directory.is_absolute():
        raise ValueError("MCP server launch directory must be absolute")
    largest_fallback = _response_too_large_error(
        max_wire_response_bytes=max_wire_response_bytes,
    )
    if _wire_response_size(largest_fallback) > max_wire_response_bytes:
        raise ValueError(
            "MCP response-size limit cannot hold the bounded error response"
        )

    def specify_artifact_info(
        identifier: ArtifactIdentifier,
        kind: ArtifactKindInput | None = None,
        project_directory: ArtifactProjectDirectory | None = None,
    ) -> ArtifactInfoCallResult:
        """Return one artifact and its complete composition stack."""
        tool_input = ArtifactInfoToolInput.model_validate(
            {
                "identifier": identifier,
                "kind": kind,
                "project_directory": project_directory,
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
                get_artifact_info(
                    ArtifactInfoRequest(
                        project_directory=selected_directory,
                        identifier=tool_input.identifier,
                        kind=tool_input.kind,
                    ),
                )
            )
            return _bound_tool_result(
                _build_success_result(result),
                max_wire_response_bytes=max_wire_response_bytes,
            )
        except ArtifactInfoError as exc:
            return _bound_tool_result(
                _tool_error(
                    exc.code,
                    exc.message,
                    details=exc.details,
                    retryable=exc.retryable,
                ),
                max_wire_response_bytes=max_wire_response_bytes,
            )
        except _InvalidOperationResult:
            return _bound_tool_result(
                _tool_error(
                    "invalid_operation_result",
                    _INVALID_RESULT_MESSAGE,
                ),
                max_wire_response_bytes=max_wire_response_bytes,
            )
        except Exception:
            logger.exception("Unexpected failure in the artifact info MCP adapter.")
            return _bound_tool_result(
                _tool_error("internal_error", _INTERNAL_ERROR_MESSAGE),
                max_wire_response_bytes=max_wire_response_bytes,
            )

    return specify_artifact_info


def _lookup_registered_tool(server: MCPServer, tool_name: str) -> Any | None:
    try:
        manager = server._tool_manager
        get_tool = manager.get_tool
    except AttributeError as exc:
        raise RuntimeError(_SDK_LOOKUP_ERROR) from exc
    try:
        return get_tool(tool_name)
    except Exception as exc:
        raise RuntimeError(_SDK_LOOKUP_ERROR) from exc


def _configure_closed_arguments(server: MCPServer, tool_name: str) -> None:
    tool = _lookup_registered_tool(server, tool_name)
    if tool is None:
        raise RuntimeError(f"MCP tool registration was not retained: {tool_name}")

    # MCP SDK argument models ignore extras by default even when discovery
    # advertises a closed typed schema. Field-level strictness is declared on
    # the callable; this compatibility shim only closes the generated model.
    try:
        argument_model = tool.fn_metadata.arg_model
        argument_model.model_config["extra"] = "forbid"
        argument_model.model_rebuild(force=True)
        tool.parameters = argument_model.model_json_schema(by_alias=True)
    except Exception as exc:
        raise RuntimeError(
            f"MCP SDK compatibility error while closing arguments for {tool_name}"
        ) from exc


def register(
    server: MCPServer,
    *,
    launch_directory: Path,
    tool_name: str = "specify_artifact_info",
    max_wire_response_bytes: int = _MAX_WIRE_RESPONSE_BYTES,
) -> None:
    """Register the first-class artifact-info MCP tool exactly once."""
    if _lookup_registered_tool(server, tool_name) is not None:
        raise ValueError(f"MCP tool name collision: {tool_name}")

    server.add_tool(
        create_artifact_info_tool(
            launch_directory=launch_directory,
            max_wire_response_bytes=max_wire_response_bytes,
        ),
        name=tool_name,
        description=_TOOL_DESCRIPTION,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    _configure_closed_arguments(server, tool_name)
