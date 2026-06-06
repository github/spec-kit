"""Shared shell-path normalization helpers for cross-platform tests."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path


def normalize_path_text(path_value: str) -> str:
    """Normalize slashes and repeated separators for string checks."""
    normalized = path_value.replace("\\", "/")
    if path_value.startswith("\\\\") or (normalized.startswith("//") and not normalized.startswith("///")):
        unc_tail = normalized.lstrip("/")
        return "//" + re.sub(r"/{2,}", "/", unc_tail)
    return re.sub(r"/{2,}", "/", normalized)


def normalized_parts(path_value: str) -> list[str]:
    """Return normalized path components, ignoring Windows drive prefixes."""
    normalized = normalize_path_text(path_value.strip().strip("'\""))
    normalized = re.sub(r"^[A-Za-z]:", "", normalized)
    return [p for p in normalized.split("/") if p]


def assert_normalized_path_equal(actual: str, expected: Path | str) -> None:
    """Assert paths are equivalent after cross-platform shell normalization."""
    actual_raw = actual.strip().strip("'\"")
    expected_raw = str(expected).strip().strip("'\"")
    if os.name == "nt":
        actual_raw = str(path_from_bash_output(actual_raw))
        expected_raw = str(path_from_bash_output(expected_raw))
    if actual_raw == expected_raw:
        return
    if normalized_parts(actual_raw) == normalized_parts(expected_raw):
        return
    raise AssertionError(f"Path mismatch. actual={actual_raw!r} expected={expected_raw!r}")


def assert_shell_path_matches(actual: str, expected: Path) -> None:
    """Assert shell-emitted path matches expected path with Windows-only relaxations."""
    actual_raw = actual.strip().strip("'\"")
    expected_raw = str(expected)
    if os.name == "nt":
        nested_drive = re.search(r"[\\/][A-Za-z]:[\\/]", actual_raw)
        if nested_drive:
            actual_raw = actual_raw[nested_drive.start() + 1:]
        actual_raw = str(path_from_bash_output(actual_raw))
        expected_raw = str(path_from_bash_output(expected_raw))

    if actual_raw == expected_raw:
        return

    actual_parts = normalized_parts(actual_raw)
    expected_parts = normalized_parts(expected_raw)

    def trim_to_pytest(parts: list[str]) -> list[str]:
        for idx, part in enumerate(parts):
            if part.startswith("pytest-"):
                return parts[idx:]
        return parts

    if os.name == "nt" and trim_to_pytest(actual_parts) == trim_to_pytest(expected_parts):
        return

    raise AssertionError(f"Path mismatch. actual={actual_raw!r} expected={expected_raw!r}")


def path_from_bash_output(path_value: str) -> Path:
    """Normalize bash-emitted paths for assertions on Windows/Git Bash."""
    path_value = path_value.strip().strip("'\"")
    if os.name == "nt":
        if path_value.startswith("/tmp/"):
            return Path(tempfile.gettempdir()) / path_value[len("/tmp/"):]
        match = re.match(r"^/([a-zA-Z])/(.*)$", path_value)
        if match:
            return Path(f"{match.group(1).upper()}:/{match.group(2)}")
    return Path(path_value)
