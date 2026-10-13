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


def test_unrelated_exception_from_version_lookup_propagates(monkeypatch):
    """A TypeError from importlib.metadata.version() must NOT be swallowed.

    With the old bare ``except Exception`` this was silently caught and
    the function returned "unknown". After the narrowing to
    (PackageNotFoundError, InvalidMetadataError) an unrelated exception
    must propagate. This test fails against the previous implementation.
    """
    def _boom(name):
        raise TypeError("unexpected internal error")

    monkeypatch.setattr(importlib.metadata, "version", _boom)

    try:
        get_speckit_version()
    except TypeError:
        pass  # narrowed: TypeError propagates
    else:
        raise AssertionError("TypeError was swallowed by the fallback")


def test_unrelated_exception_from_pyproject_propagates(monkeypatch, tmp_path):
    """A RuntimeError from pyproject parsing must NOT be swallowed.

    With the old bare ``except Exception`` in the inner fallback this
    was silently caught. After narrowing to (OSError, KeyError,
    ValueError) an unrelated exception must propagate. This test fails
    against the previous implementation.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.0"\n', encoding="utf-8"
    )
    monkeypatch.setattr(_assets, "_repo_root", lambda: tmp_path)

    def _not_found(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _not_found)

    import tomllib

    def _boom_load(f):
        raise RuntimeError("corrupt tomllib")

    monkeypatch.setattr(tomllib, "load", _boom_load)

    try:
        get_speckit_version()
    except RuntimeError:
        pass  # narrowed: RuntimeError propagates
    else:
        raise AssertionError("RuntimeError was swallowed by the pyproject fallback")


def test_pyproject_io_error_returns_unknown(monkeypatch, tmp_path):
    """An OSError reading pyproject.toml must return "unknown", not propagate.

    This exercises the intended pyproject I/O failure path: the narrowing
    keeps OSError in the caught tuple so a missing/unreadable pyproject
    still falls through to "unknown".
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.0"\n', encoding="utf-8"
    )
    monkeypatch.setattr(_assets, "_repo_root", lambda: tmp_path)

    def _not_found(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _not_found)

    import builtins
    real_open = builtins.open

    def _deny_read(path, *args, **kwargs):
        if "pyproject" in str(path):
            raise OSError("permission denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _deny_read)

    assert get_speckit_version() == "unknown"
