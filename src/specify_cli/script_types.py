"""Script type helpers shared by init and integration commands."""

from __future__ import annotations

import os


SCRIPT_TYPE_CHOICES: dict[str, str] = {
    "sh": "POSIX Shell (bash/zsh)",
    "ps": "PowerShell",
    "both": "Both POSIX Shell and PowerShell",
}

def normalize_script_type(script_type: str) -> str:
    """Return a normalized script selection, or raise ``ValueError``."""
    normalized = script_type.strip().lower()
    if normalized not in SCRIPT_TYPE_CHOICES:
        raise ValueError(normalized)
    return normalized


def default_script_type() -> str:
    """Return the OS default primary script type."""
    return "ps" if os.name == "nt" else "sh"


def script_install_variants(script_type: str) -> tuple[str, ...]:
    """Return script variants that should be copied for *script_type*."""
    normalized = normalize_script_type(script_type)
    if normalized == "both":
        return ("sh", "ps")
    return (normalized,)


def script_render_type(script_type: str) -> str:
    """Return the primary script type to embed in generated commands."""
    normalized = normalize_script_type(script_type)
    if normalized == "both":
        return default_script_type()
    return normalized
