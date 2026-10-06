"""MCP adapter for the shared ``version`` operation."""

from __future__ import annotations

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict, ValidationError

from ._operation_version import VersionResult, collect_version_result

TOOL_NAME = "specify_version"
_INVALID_RESULT_MESSAGE = "The version operation returned an invalid result."
_INTERNAL_ERROR_MESSAGE = "Unable to collect version information."


class VersionRuntimeResult(BaseModel):
    """Runtime portion of the MCP version result."""

    model_config = ConfigDict(extra="forbid")

    python: str
    openssl: str | None


class VersionSystemResult(BaseModel):
    """System portion of the MCP version result."""

    model_config = ConfigDict(extra="forbid")

    platform: str
    architecture: str
    os_version: str


class VersionToolResult(BaseModel):
    """Typed structured result returned by ``specify_version``."""

    model_config = ConfigDict(extra="forbid")

    cli_version: str
    runtime: VersionRuntimeResult
    system: VersionSystemResult
    features: dict[str, bool]


class _InvalidOperationResult(Exception):
    """The shared operation returned an incomplete or invalid typed result."""


def _tool_error(code: str, message: str) -> CallToolResult:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": {},
        }
    }
    return CallToolResult(
        content=[TextContent(type="text", text=f"{code}: {message}")],
        structuredContent=payload,
        isError=True,
    )


def _convert_result(result: VersionResult) -> VersionToolResult:
    if result.runtime is None or result.system is None:
        raise _InvalidOperationResult

    try:
        return VersionToolResult.model_validate(
            {
                "cli_version": result.cli_version,
                "runtime": {
                    "python": result.runtime.python,
                    "openssl": result.runtime.openssl,
                },
                "system": {
                    "platform": result.system.platform,
                    "architecture": result.system.architecture,
                    "os_version": result.system.os_version,
                },
                "features": result.features,
            },
            strict=True,
        )
    except ValidationError as exc:
        raise _InvalidOperationResult from exc


def specify_version() -> VersionToolResult:
    """Return installed CLI, runtime, system, and feature information."""
    try:
        return _convert_result(collect_version_result())
    except _InvalidOperationResult:
        return _tool_error("invalid_operation_result", _INVALID_RESULT_MESSAGE)
    except Exception:  # noqa: BLE001
        return _tool_error("internal_error", _INTERNAL_ERROR_MESSAGE)


def _forbid_unexpected_arguments(server: MCPServer) -> None:
    tool = server._tool_manager.get_tool(TOOL_NAME)
    if tool is None:  # pragma: no cover - registration immediately precedes this
        raise RuntimeError(f"Tool registration failed: {TOOL_NAME}")

    # MCP SDK argument models ignore extras by default, despite publishing an
    # empty schema for a no-argument callable.
    argument_model = tool.fn_metadata.arg_model
    argument_model.model_config["extra"] = "forbid"
    argument_model.model_rebuild(force=True)
    tool.parameters = argument_model.model_json_schema(by_alias=True)


def register(server: MCPServer) -> None:
    """Register the first-class ``specify_version`` MCP tool exactly once."""
    if server._tool_manager.get_tool(TOOL_NAME) is not None:
        raise ValueError(f"MCP tool name collision: {TOOL_NAME}")

    server.add_tool(
        specify_version,
        name=TOOL_NAME,
        description=(
            "Return the installed Spec Kit CLI version, runtime, system, and "
            "feature capabilities."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    _forbid_unexpected_arguments(server)
