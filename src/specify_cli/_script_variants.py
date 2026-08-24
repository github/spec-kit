"""Canonical names and paths for the core script runtime variants."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

_SCRIPT_VARIANTS = (
    ("bash", ".sh", False),
    ("powershell", ".ps1", False),
    ("python", ".py", True),
)


def canonical_script_name(path: Path) -> str | None:
    """Return the logical name shared by a core script's runtime variants."""
    for runtime, suffix, uses_underscores in _SCRIPT_VARIANTS:
        if path.parent.name == runtime and path.suffix == suffix:
            return path.stem.replace("_", "-") if uses_underscores else path.stem
    return None


def script_variant_paths(scripts_dir: Path, name: str) -> Iterator[Path]:
    """Yield runtime-specific paths for the logical script *name*."""
    for runtime, suffix, uses_underscores in _SCRIPT_VARIANTS:
        stem = name.replace("-", "_") if uses_underscores else name
        yield scripts_dir / runtime / f"{stem}{suffix}"
