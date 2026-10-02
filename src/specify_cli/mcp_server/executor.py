"""Subprocess adapter for stable CLI JSON commands exposed through MCP."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from .catalog import CommandAdapterError, VersionResult, unavailable_command

_INVALID_OUTPUT_MESSAGE = (
    "The Specify CLI returned invalid machine-readable output."
)


class _CliError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, object]


class _CliFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: _CliError


def _adapter_failure(reason: str) -> CommandAdapterError:
    return CommandAdapterError(
        code="adapter_internal_error",
        message=_INVALID_OUTPUT_MESSAGE,
        details={"command": "version", "reason": reason},
    )


def _run_cli_process(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        check=False,
        capture_output=True,
    )


def _decode_streams(
    completed: subprocess.CompletedProcess[bytes],
) -> tuple[str, str]:
    try:
        return (
            completed.stdout.decode("utf-8"),
            completed.stderr.decode("utf-8"),
        )
    except UnicodeDecodeError as exc:
        raise _adapter_failure("invalid_utf8") from exc


def _parse_object(raw: str, *, reason: str) -> dict[str, Any]:
    if not raw.strip():
        raise _adapter_failure(reason)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _adapter_failure(reason) from exc
    if not isinstance(payload, dict):
        raise _adapter_failure(reason)
    return payload


def _run_version() -> VersionResult:
    argv = [
        sys.executable,
        "-m",
        "specify_cli.mcp_server._worker",
        "version",
        "--json",
    ]
    try:
        completed = _run_cli_process(argv)
    except OSError as exc:
        raise _adapter_failure("process_launch_failed") from exc

    stdout, stderr = _decode_streams(completed)
    if completed.returncode == 0:
        if stderr.strip():
            raise _adapter_failure("mixed_success_output")
        payload = _parse_object(stdout, reason="invalid_success_output")
        try:
            return VersionResult.model_validate(payload)
        except ValidationError as exc:
            raise _adapter_failure("invalid_success_payload") from exc

    if stdout.strip():
        raise _adapter_failure("mixed_failure_output")
    payload = _parse_object(stderr, reason="invalid_failure_output")
    try:
        failure = _CliFailure.model_validate(payload)
    except ValidationError as exc:
        raise _adapter_failure("invalid_failure_payload") from exc
    raise CommandAdapterError(
        code=failure.error.code,
        message=failure.error.message,
        details=failure.error.details,
    )


def run_command(command: str) -> VersionResult:
    """Run one supported dotted CLI command through the real CLI process."""
    if command != "version":
        raise unavailable_command(command)
    return _run_version()
