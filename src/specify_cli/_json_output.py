"""Small internal helpers for versioned CLI JSON envelopes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def success_envelope(
    command: str,
    result: Mapping[str, Any],
    *,
    warnings: Sequence[Mapping[str, Any] | str] = (),
) -> dict[str, Any]:
    """Build a successful version 1.0 CLI JSON envelope."""
    return {
        "schema_version": "1.0",
        "command": command,
        "ok": True,
        "result": dict(result),
        "warnings": list(warnings),
    }


def failure_envelope(
    command: str,
    *,
    code: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a failed version 1.0 CLI JSON envelope."""
    return {
        "schema_version": "1.0",
        "command": command,
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        },
    }
