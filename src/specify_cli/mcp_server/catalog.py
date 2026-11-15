"""Explicit command inventory for the experimental MCP server."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class CommandArgument(BaseModel):
    """One named argument accepted by an MCP-exposed CLI command."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    required: bool
    description: str


class CommandDescription(BaseModel):
    """Stable description of one MCP-exposed CLI command."""

    model_config = ConfigDict(extra="forbid")

    command: Literal["version"]
    description: str
    arguments: list[CommandArgument]
    read_only: Literal[True]
    json_output: Literal[True]


class CommandList(BaseModel):
    """List of commands currently exposed through MCP."""

    model_config = ConfigDict(extra="forbid")

    commands: list[CommandDescription]


class RuntimeInfo(BaseModel):
    """Runtime portion of the stable version JSON result."""

    model_config = ConfigDict(extra="forbid")

    python: str
    openssl: str | None


class SystemInfo(BaseModel):
    """System portion of the stable version JSON result."""

    model_config = ConfigDict(extra="forbid")

    platform: str
    architecture: str
    os_version: str


class VersionResult(BaseModel):
    """Direct success payload returned by ``specify version --json``."""

    model_config = ConfigDict(extra="forbid")

    cli_version: str
    runtime: RuntimeInfo
    system: SystemInfo
    features: dict[str, bool]


class CommandAdapterError(Exception):
    """Sanitized command error suitable for conversion to an MCP tool error."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def payload(self) -> dict[str, object]:
        """Return the stable structured tool-error payload."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


_VERSION_DESCRIPTION = CommandDescription(
    command="version",
    description=(
        "Return the installed Spec Kit CLI version, runtime, system, and "
        "feature capabilities."
    ),
    arguments=[],
    read_only=True,
    json_output=True,
)
_SUPPORTED_COMMANDS = {"version": _VERSION_DESCRIPTION}


def list_commands() -> CommandList:
    """Return the deliberately minimal supported command inventory."""
    return CommandList(commands=list(_SUPPORTED_COMMANDS.values()))


def describe_command(command: str) -> CommandDescription:
    """Return one supported command description or an unavailable error."""
    description = _SUPPORTED_COMMANDS.get(command)
    if description is None:
        raise unavailable_command(command)
    return description


def unavailable_command(command: str) -> CommandAdapterError:
    """Build a stable error for a command outside the explicit inventory."""
    return CommandAdapterError(
        code="unavailable_command",
        message=(
            f"Command '{command}' is not available through the experimental "
            "Spec Kit MCP server."
        ),
        details={
            "command": command,
            "available_commands": list(_SUPPORTED_COMMANDS),
        },
    )
