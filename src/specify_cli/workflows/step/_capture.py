"""Shared ``capture`` contract for the ``command`` and ``prompt`` steps.

Both steps stream the integration CLI's output to the terminal by default.
``capture: true`` retains stdout and stderr in the step output instead, capped
per stream by ``capture_max_bytes``. This module holds the parts of that
contract the two steps must agree on: validation, the output fields, and the
failure summary.
"""

from __future__ import annotations

import math
from typing import Any

from specify_cli.integrations._capture import (
    DEFAULT_CAPTURE_MAX_BYTES,
    capture_max_bytes_is_valid,
)


def capture_errors(config: dict[str, Any], label: str) -> list[str]:
    """Return errors for the ``capture``/``capture_max_bytes`` fields.

    Shared by execute() and validate() so both paths reject the same values
    with the same message. *label* names the step kind (``"Command"``).
    """
    step_id = config.get("id", "?")
    errors: list[str] = []
    capture = config.get("capture", False)
    if "capture" in config and not isinstance(capture, bool):
        errors.append(
            f"{label} step {step_id!r}: 'capture' must be true or false, "
            f"got {capture!r}."
        )
    if "capture_max_bytes" in config:
        max_bytes = config["capture_max_bytes"]
        if not capture_max_bytes_is_valid(max_bytes):
            errors.append(
                f"{label} step {step_id!r}: 'capture_max_bytes' must be a "
                f"positive integer or -1 (no limit), got {max_bytes!r}."
            )
        elif capture is not True:
            # A limit on a step that streams would silently do nothing.
            errors.append(
                f"{label} step {step_id!r}: 'capture_max_bytes' requires "
                f"'capture: true'."
            )
    return errors


def capture_limit(config: dict[str, Any]) -> int | None:
    """Return the per-stream byte limit, or ``None`` when the step streams.

    Call only after :func:`capture_errors` returned no errors.
    """
    if config.get("capture", False) is not True:
        return None
    return config.get("capture_max_bytes", DEFAULT_CAPTURE_MAX_BYTES)


def timeout_error(config: dict[str, Any], label: str) -> str | None:
    """Return an error message if ``config['timeout']`` is invalid, else None.

    Mirrors the shell and prompt steps: bool is rejected although it is an int
    subclass, and non-finite or oversized numbers are rejected because they
    would raise inside the subprocess wait.
    """
    if "timeout" not in config:
        return None
    timeout = config["timeout"]
    try:
        valid = (
            not isinstance(timeout, bool)
            and isinstance(timeout, (int, float))
            and math.isfinite(timeout)
            and timeout > 0
        )
    except OverflowError:
        valid = False
    if valid:
        return None
    return (
        f"{label} step {config.get('id', '?')!r}: 'timeout' must be a "
        f"positive number of seconds, got {timeout!r}."
    )


def record_capture(output: dict[str, Any], dispatch_result: dict[str, Any]) -> None:
    """Add the capture-only completeness fields to a step's *output*.

    ``*_truncated`` report the byte limit only; ``timed_out`` and
    ``interrupted`` report a stopped process, whose output is partial even
    without a limit.
    """
    for field in ("stdout_truncated", "stderr_truncated", "timed_out", "interrupted"):
        output[field] = bool(dispatch_result.get(field, False))


def capture_failure(
    dispatch_result: dict[str, Any],
    *,
    subject: str,
    timeout: float,
) -> str:
    """Return the error summary for a failed captured dispatch.

    The step error is written to ``log.jsonl`` and printed, so it never
    carries captured stderr; that text stays in ``output.stderr``.
    """
    if dispatch_result.get("interrupted"):
        return "Interrupted by user"
    if dispatch_result.get("timed_out"):
        return f"{subject} timed out after {timeout} seconds."
    return f"{subject} exited with code {dispatch_result['exit_code']}"
