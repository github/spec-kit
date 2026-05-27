"""Fixtures for `specify self upgrade` tests."""

import os

import pytest


@pytest.fixture
def clean_environ(monkeypatch):
    """Strip any real GH_TOKEN / GITHUB_TOKEN from the test environment."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def _fake_argv0(monkeypatch, tmp_path, env_name, path_parts):
    """Create a fake executable under tmp_path and point sys.argv[0] at it."""
    monkeypatch.setenv(env_name, str(tmp_path))
    fake_dir = tmp_path.joinpath(*path_parts)
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / ("specify.exe" if os.name == "nt" else "specify")
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


@pytest.fixture
def uv_tool_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated `uv tool` install path under tmp HOME.

    Sets the platform-specific home/tool root env so _expand_prefix() resolves
    to a path that actually contains the fake binary. This avoids needing a
    `_UV_TOOL_ROOT_OVERRIDE` knob in production code.
    """
    if os.name == "nt":
        return _fake_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("uv", "tools", "specify-cli", "bin")
        )
    return _fake_argv0(
        monkeypatch,
        tmp_path,
        "HOME",
        (".local", "share", "uv", "tools", "specify-cli", "bin"),
    )


@pytest.fixture
def pipx_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated pipx install path under tmp HOME."""
    if os.name == "nt":
        return _fake_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("pipx", "venvs", "specify-cli", "bin")
        )
    return _fake_argv0(
        monkeypatch, tmp_path, "HOME", (".local", "pipx", "venvs", "specify-cli", "bin")
    )


@pytest.fixture
def uvx_ephemeral_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated uvx ephemeral-cache path under tmp HOME."""
    if os.name == "nt":
        return _fake_argv0(
            monkeypatch,
            tmp_path,
            "LOCALAPPDATA",
            ("uv", "cache", "archive-v0", "abc123", "bin"),
        )
    return _fake_argv0(
        monkeypatch, tmp_path, "HOME", (".cache", "uv", "archive-v0", "abc123", "bin")
    )


@pytest.fixture
def unsupported_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a path that does not match any installer prefix."""
    return _fake_argv0(monkeypatch, tmp_path, "HOME", ("random", "location", "bin"))
