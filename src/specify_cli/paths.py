from __future__ import annotations

import os
import subprocess
from pathlib import Path

def _run_git_toplevel() -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True)
            .strip()
            or None
        )
    except Exception:
        return None


def get_repo_root() -> Path:
    root = _run_git_toplevel()
    if root:
        return Path(root)
    return Path.cwd()


def get_specs_root(override: str | Path | None = None) -> Path:
    if isinstance(override, Path):
        # Treat path overrides as a base directory unless they already point at a
        # '.specs' folder so callers can pass either the project root or the
        # target specs directory explicitly.
        expanded = override.expanduser().resolve()
        root = expanded if expanded.name == ".specs" else (expanded / ".specs").resolve()
    else:
        base = override or os.getenv("SPEC_KIT_DIR")
        if base:
            root = Path(base).expanduser().resolve()
        else:
            root = get_repo_root() / ".specs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def specs_subdir(name: str, base: Path | None = None) -> Path:
    safe = name.strip().strip("/\\")
    if not safe:
        raise ValueError("Subdirectory name must not be empty")
    return ensure_dir(get_specs_root(base) / safe)


def get_specify_root(base: Path | None = None) -> Path:
    return ensure_dir(get_specs_root(base) / ".specify")


def specify_subdir(name: str, base: Path | None = None) -> Path:
    safe = name.strip().strip("/\\")
    if not safe:
        raise ValueError("Subdirectory name must not be empty")
    return ensure_dir(get_specify_root(base) / safe)


def specify_scripts_dir(base: Path | None = None) -> Path:
    return specify_subdir("scripts", base)


def specify_templates_dir(base: Path | None = None) -> Path:
    return specify_subdir("templates", base)


def plan_dir(base: Path | None = None) -> Path:
    return specify_subdir("plan", base)


def spec_dir(base: Path | None = None) -> Path:
    return specify_subdir("spec", base)


def notes_dir(base: Path | None = None) -> Path:
    return specify_subdir("notes", base)


def memory_dir(base: Path | None = None) -> Path:
    return specify_subdir("memory", base)


def scratch_dir(base: Path | None = None) -> Path:
    return specify_subdir("scratch", base)


def docs_dir(base: Path | None = None) -> Path:
    return specify_subdir("docs", base)


def logs_dir(base: Path | None = None) -> Path:
    return specify_subdir("logs", base)


def features_dir(base: Path | None = None) -> Path:
    return specify_subdir("specs", base)


def contracts_dir(feature_path: Path) -> Path:
    return ensure_dir(feature_path / "contracts")
