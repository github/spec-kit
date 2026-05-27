"""Shared test helpers for the Spec Kit test suite."""

import os
import re
import shutil
import subprocess
import sys

import pytest

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _has_working_bash() -> bool:
    """Check whether a functional native bash is available.

    On Windows, ``subprocess.run(["bash", ...])`` uses CreateProcess,
    which searches System32 *before* PATH — so it may find the WSL
    launcher even when Git-for-Windows bash appears first in PATH via
    ``shutil.which``.  We therefore probe with bare ``"bash"`` (the
    same way test helpers invoke it) to get an accurate result.

    On Windows, only Git-for-Windows bash (MSYS2/MINGW) is accepted.
    The WSL launcher is rejected because it runs in a separate Linux
    filesystem and cannot handle native Windows paths used by the
    test fixtures.

    Set SPECKIT_TEST_BASH=1 to force-enable bash tests regardless.
    """
    if os.environ.get("SPECKIT_TEST_BASH") == "1":
        return True
    if shutil.which("bash") is None:
        return False
    # Probe with bare "bash" — same as the test helpers — so that
    # Windows CreateProcess resolution order is respected.
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    # On Windows, verify we have MSYS/MINGW bash (Git for Windows),
    # not the WSL launcher which can't handle native paths.
    if sys.platform == "win32":
        try:
            u = subprocess.run(
                ["bash", "-c", "uname -s"],
                capture_output=True, text=True, timeout=5,
            )
            kernel = u.stdout.strip().upper()
            if not any(k in kernel for k in ("MSYS", "MINGW", "CYGWIN")):
                return False
        except (OSError, subprocess.TimeoutExpired):
            return False
    return True


requires_bash = pytest.mark.skipif(
    not _has_working_bash(), reason="working bash not available"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)


# ---------------------------------------------------------------------------
# Auth config isolation — prevents tests from reading ~/.specify/auth.json
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_auth_config(monkeypatch):
    """Ensure no test reads the real ~/.specify/auth.json."""
    from specify_cli.authentication import http as _auth_http
    monkeypatch.setattr(_auth_http, "_config_override", [])
    # Also clear the per-process cache so tests that unset _config_override
    # won't see a previously cached real-file result.
    monkeypatch.setattr(_auth_http, "_config_cache", None)


@pytest.fixture
def clean_environ(monkeypatch):
    """Strip any real GH_TOKEN / GITHUB_TOKEN from the test environment."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def _fake_self_upgrade_argv0(monkeypatch, tmp_path, env_name, path_parts):
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
    """Point sys.argv[0] at a simulated `uv tool` install path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("uv", "tools", "specify-cli", "bin")
        )
    return _fake_self_upgrade_argv0(
        monkeypatch,
        tmp_path,
        "HOME",
        (".local", "share", "uv", "tools", "specify-cli", "bin"),
    )


@pytest.fixture
def pipx_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated pipx install path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("pipx", "venvs", "specify-cli", "bin")
        )
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", (".local", "pipx", "venvs", "specify-cli", "bin")
    )


@pytest.fixture
def uvx_ephemeral_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated uvx ephemeral-cache path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch,
            tmp_path,
            "LOCALAPPDATA",
            ("uv", "cache", "archive-v0", "abc123", "bin"),
        )
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", (".cache", "uv", "archive-v0", "abc123", "bin")
    )


@pytest.fixture
def unsupported_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a path that does not match any installer prefix."""
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", ("random", "location", "bin")
    )
