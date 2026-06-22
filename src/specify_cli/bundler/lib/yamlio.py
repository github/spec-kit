"""YAML/JSON read-write helpers with path confinement (Constitution Principles IV & V).

All reads/writes go through these functions so that:
- IO failures degrade into actionable :class:`~specify_cli.bundler.BundlerError`s
  rather than raw tracebacks, and
- every path can be confined to an allowed root via :func:`ensure_within`.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .. import BundlerError


def ensure_within(root: Path, candidate: Path) -> Path:
    """Resolve *candidate* and guarantee it stays within *root*.

    Refuses path-traversal payloads and symlink escapes. Returns the resolved,
    confined path. Raises :class:`BundlerError` if the path escapes *root*.
    """
    root_resolved = Path(root).resolve()
    # Resolve symlinks so a symlinked component cannot point outside the root.
    candidate_resolved = Path(candidate).resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise BundlerError(
            f"Refusing path '{candidate}' — it escapes the allowed root '{root}'."
        ) from exc
    return candidate_resolved


def load_yaml(path: Path) -> Any:
    """Parse a YAML file, returning ``{}`` for an empty document."""
    path = Path(path)
    if not path.exists():
        raise BundlerError(f"File not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise BundlerError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise BundlerError(f"Could not read {path}: {exc}") from exc


def dump_yaml(path: Path, data: Any, *, within: Path | None = None) -> Path:
    """Write *data* as YAML to *path* (optionally confined to *within*)."""
    path = Path(path)
    if within is not None:
        path = ensure_within(within, path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False, default_flow_style=False)
    except OSError as exc:
        raise BundlerError(f"Could not write {path}: {exc}") from exc
    return path


def load_json(path: Path) -> Any:
    """Parse a JSON file."""
    path = Path(path)
    if not path.exists():
        raise BundlerError(f"File not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise BundlerError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise BundlerError(f"Could not read {path}: {exc}") from exc


def loads_json(text: str, *, origin: str = "<string>") -> Any:
    """Parse JSON from a string (used for catalog payloads fetched as text)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BundlerError(f"Invalid JSON from {origin}: {exc}") from exc


def dump_json(path: Path, data: Any, *, within: Path | None = None) -> Path:
    """Write *data* as pretty JSON to *path* (optionally confined to *within*)."""
    path = Path(path)
    if within is not None:
        path = ensure_within(within, path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=False)
            handle.write("\n")
    except OSError as exc:
        raise BundlerError(f"Could not write {path}: {exc}") from exc
    return path


def is_safe_relpath(rel: str) -> bool:
    """Return True if *rel* is a project-relative path with no traversal/absolute parts.

    Platform-independent: a POSIX-absolute path (``/abs``) or a Windows
    drive-absolute path (``C:\\x``) is rejected on every OS, since these strings
    can appear in untrusted catalog/manifest data regardless of the host.
    """
    if not rel:
        return False
    normalized = rel.replace("\\", "/")
    if os.path.isabs(rel) or normalized.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", normalized):  # Windows drive-absolute (C:/...)
        return False
    parts = PurePosixPath(normalized).parts
    return ".." not in parts
