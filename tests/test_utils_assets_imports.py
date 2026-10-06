"""Regression guard: utility and asset symbols importable from specify_cli."""
import importlib.metadata

from specify_cli import (
    check_tool, merge_json_files,
    get_speckit_version,
    CLAUDE_LOCAL_PATH, CLAUDE_NPM_LOCAL_PATH,
)
from specify_cli import _assets
from pathlib import Path

def test_utils_symbols_importable():
    assert callable(check_tool)
    assert callable(merge_json_files)

def test_get_speckit_version_returns_string():
    version = get_speckit_version()
    assert isinstance(version, str) and len(version) > 0

def test_claude_paths_are_paths():
    assert isinstance(CLAUDE_LOCAL_PATH, Path)
    assert isinstance(CLAUDE_NPM_LOCAL_PATH, Path)


def test_get_speckit_version_survives_invalid_metadata(monkeypatch):
    """A corrupt installed distribution must fall back, not raise.

    ``InvalidMetadataError`` is not a ``PackageNotFoundError``, so catching
    only the latter lets it escape the version fallback (the same guard
    _version._get_installed_version() already applies). The class is looked up
    dynamically and was removed from the stdlib in 3.14, so install a stand-in
    to exercise the guard on every supported interpreter.
    """

    class _InvalidMetadataError(Exception):
        pass

    monkeypatch.setattr(
        importlib.metadata, "InvalidMetadataError", _InvalidMetadataError, raising=False
    )

    def _corrupt(name):
        raise _InvalidMetadataError("corrupt metadata")

    monkeypatch.setattr(importlib.metadata, "version", _corrupt)

    assert isinstance(get_speckit_version(), str)


def test_get_speckit_version_survives_non_mapping_project(monkeypatch, tmp_path):
    """A present but non-mapping ``project`` value must not raise.

    The narrowed pyproject branch previously called ``.get`` on whatever the
    ``project`` key held, so ``project = 5`` turned the fallback into an
    AttributeError.
    """
    (tmp_path / "pyproject.toml").write_text("project = 5\n", encoding="utf-8")
    monkeypatch.setattr(_assets, "_repo_root", lambda: tmp_path)

    def _not_found(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _not_found)

    assert get_speckit_version() == "unknown"


def test_get_speckit_version_reads_pyproject_fallback(monkeypatch, tmp_path):
    """When the distribution is missing, a valid pyproject.toml is the source."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "9.9.9"\n', encoding="utf-8"
    )
    monkeypatch.setattr(_assets, "_repo_root", lambda: tmp_path)

    def _not_found(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _not_found)

    assert get_speckit_version() == "9.9.9"
