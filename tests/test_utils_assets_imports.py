"""Regression guard: utility and asset symbols importable from specify_cli."""
import importlib.metadata
import tomllib
from pathlib import Path

from specify_cli import (
    check_tool, merge_json_files,
    get_speckit_version,
    CLAUDE_LOCAL_PATH, CLAUDE_NPM_LOCAL_PATH,
)

def test_utils_symbols_importable():
    assert callable(check_tool)
    assert callable(merge_json_files)

def test_get_speckit_version_returns_string():
    version = get_speckit_version()
    assert isinstance(version, str) and len(version) > 0

def test_get_speckit_version_prefers_checked_out_pyproject(monkeypatch):
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.0.0")

    with open(Path(__file__).resolve().parents[1] / "pyproject.toml", "rb") as f:
        expected_version = tomllib.load(f)["project"]["version"]

    assert get_speckit_version() == expected_version

def test_claude_paths_are_paths():
    assert isinstance(CLAUDE_LOCAL_PATH, Path)
    assert isinstance(CLAUDE_NPM_LOCAL_PATH, Path)
