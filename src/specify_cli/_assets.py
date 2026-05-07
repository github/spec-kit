from __future__ import annotations
import importlib.metadata
import re
from pathlib import Path


def _locate_core_pack() -> Path | None:
    """Return the filesystem path to the bundled core_pack directory, or None.

    Only present in wheel installs: hatchling's force-include copies
    templates/, scripts/ etc. into specify_cli/core_pack/ at build time.

    Source-checkout and editable installs do NOT have this directory.
    Callers that need to work in both environments must check the repo-root
    trees (templates/, scripts/) as a fallback when this returns None.
    """
    # Wheel install: core_pack is a sibling directory of this file
    candidate = Path(__file__).parent / "core_pack"
    if candidate.is_dir():
        return candidate
    return None


def _repo_root() -> Path:
    """Return the source checkout root used for editable installs."""
    return Path(__file__).parent.parent.parent


def _locate_bundled_extension(extension_id: str) -> Path | None:
    """Return the path to a bundled extension, or None.

    Checks the wheel's core_pack first, then falls back to the
    source-checkout ``extensions/<id>/`` directory.
    """
    if not re.match(r'^[a-z0-9-]+$', extension_id):
        return None

    core = _locate_core_pack()
    if core is not None:
        candidate = core / "extensions" / extension_id
        if (candidate / "extension.yml").is_file():
            return candidate

    # Source-checkout / editable install: look relative to repo root
    candidate = _repo_root() / "extensions" / extension_id
    if (candidate / "extension.yml").is_file():
        return candidate

    return None


def _locate_bundled_workflow(workflow_id: str) -> Path | None:
    """Return the path to a bundled workflow directory, or None.

    Checks the wheel's core_pack first, then falls back to the
    source-checkout ``workflows/<id>/`` directory.
    """
    if not re.match(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$', workflow_id):
        return None

    core = _locate_core_pack()
    if core is not None:
        candidate = core / "workflows" / workflow_id
        if (candidate / "workflow.yml").is_file():
            return candidate

    # Source-checkout / editable install: look relative to repo root
    candidate = _repo_root() / "workflows" / workflow_id
    if (candidate / "workflow.yml").is_file():
        return candidate

    return None


def _locate_bundled_preset(preset_id: str) -> Path | None:
    """Return the path to a bundled preset, or None.

    Checks the wheel's core_pack first, then falls back to the
    source-checkout ``presets/<id>/`` directory.
    """
    if not re.match(r'^[a-z0-9-]+$', preset_id):
        return None

    core = _locate_core_pack()
    if core is not None:
        candidate = core / "presets" / preset_id
        if (candidate / "preset.yml").is_file():
            return candidate

    # Source-checkout / editable install: look relative to repo root
    candidate = _repo_root() / "presets" / preset_id
    if (candidate / "preset.yml").is_file():
        return candidate

    return None


def get_speckit_version() -> str:
    """Get current spec-kit version."""
    try:
        return importlib.metadata.version("specify-cli")
    except Exception:
        # Fallback: try reading from pyproject.toml
        try:
            import tomllib
            pyproject_path = _repo_root() / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "unknown")
        except Exception:
            # Intentionally ignore any errors while reading/parsing pyproject.toml.
            # If this lookup fails for any reason, we fall back to returning "unknown" below.
            pass
    return "unknown"
