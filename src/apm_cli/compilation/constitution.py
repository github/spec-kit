"""Utilities for reading Spec Kit style constitution file."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .constants import CONSTITUTION_RELATIVE_PATH


def find_constitution(base_dir: Path) -> Path:
    """Return path to constitution.md if present, else Path that does not exist.

    We keep logic trivial for Phase 0: fixed location under memory/.
    Later phases may support multiple shards / namespacing.
    """
    return base_dir / CONSTITUTION_RELATIVE_PATH


def read_constitution(base_dir: Path) -> Optional[str]:
    """Read full constitution content if file exists.

    Args:
        base_dir: Repository root path.
    Returns:
        Full file text or None if absent.
    """
    path = find_constitution(base_dir)
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
