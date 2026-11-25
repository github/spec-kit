"""Regression tests for a feature.json pointer whose directory no longer exists (#5566)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.parity_helpers import clean_env, install_scripts


def _find_bash() -> str | None:
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if Path(candidate).is_file():
                return candidate
    return shutil.which("bash")


BASH_EXE = _find_bash()
requires_local_bash = pytest.mark.skipif(not BASH_EXE, reason="no bash available")

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (
    shutil.which("powershell.exe") or shutil.which("powershell")
) if os.name == "nt" else None
HAS_POWERSHELL = HAS_PWSH or _WINDOWS_POWERSHELL is not None

STALE_POINTER = "specs/001-gone"
LIVE_POINTER = "specs/002-live"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".specify").mkdir()
    install_scripts(repo, "check-prerequisites")
    return repo


def _write_pointer(repo: Path, value: str) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": value}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = clean_env()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            del env[key]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, env=env)


def _python_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "python" / "check_prerequisites.py"
    return [sys.executable, str(script), "--json", "--paths-only"]


def _bash_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    return [BASH_EXE or "bash", str(script), "--json", "--paths-only"]


def _powershell_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return [exe, "-NoProfile", "-File", str(script), "-Json", "-PathsOnly"]


def _assert_stale_pointer_rejected(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 1, result.stderr
    assert result.stdout == ""
    assert "Feature directory not found" in result.stderr
    assert STALE_POINTER not in result.stderr


def _assert_live_pointer_resolved(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    feature_dir = Path(payload["FEATURE_DIR"])
    assert feature_dir.name == Path(LIVE_POINTER).name
    assert str(feature_dir).replace("\\", "/").endswith(LIVE_POINTER)


def test_python_rejects_stale_feature_json_pointer(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_python_cmd(project), project))


def test_python_accepts_existing_feature_json_pointer(project: Path) -> None:
    (project / LIVE_POINTER).mkdir(parents=True)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_python_cmd(project), project))


@requires_local_bash
def test_bash_rejects_stale_feature_json_pointer(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_bash_cmd(project), project))


@requires_local_bash
def test_bash_accepts_existing_feature_json_pointer(project: Path) -> None:
    (project / LIVE_POINTER).mkdir(parents=True)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_bash_cmd(project), project))


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_rejects_stale_feature_json_pointer(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_powershell_cmd(project), project))


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_accepts_existing_feature_json_pointer(project: Path) -> None:
    (project / LIVE_POINTER).mkdir(parents=True)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_powershell_cmd(project), project))
