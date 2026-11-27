"""Regression tests for a feature.json pointer whose directory no longer exists (#5566)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.parity_helpers import PROJECT_ROOT, install_scripts


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
STALE_KINDS = ("missing_dir", "regular_file", "dangling_symlink")
LIVE_KINDS = ("directory", "symlink")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".specify" / "templates").mkdir(parents=True)
    shutil.copy(
        PROJECT_ROOT / "templates" / "plan-template.md",
        repo / ".specify" / "templates" / "plan-template.md",
    )
    install_scripts(repo, "check-prerequisites")
    install_scripts(repo, "setup-plan")
    return repo


def _write_pointer(repo: Path, value: str) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": value}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _prepare_stale_target(repo: Path, kind: str) -> None:
    target = repo / STALE_POINTER
    if kind == "missing_dir":
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "regular_file":
        target.write_text("not a directory\n", encoding="utf-8")
        return
    if kind == "dangling_symlink":
        try:
            target.symlink_to(repo / "specs" / "001-deleted-target", target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable in this environment: {exc}")
        return
    raise ValueError(f"Unknown stale target kind: {kind}")


def _prepare_live_target(repo: Path, kind: str) -> None:
    live = repo / LIVE_POINTER
    live.parent.mkdir(parents=True, exist_ok=True)
    if kind == "directory":
        live.mkdir()
        return
    real = repo / "specs" / "002-real"
    real.mkdir(parents=True, exist_ok=True)
    try:
        live.symlink_to(real, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this environment: {exc}")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
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


def _python_setup_plan_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "python" / "setup_plan.py"
    return [sys.executable, str(script), "--json"]


def _bash_setup_plan_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    return [BASH_EXE or "bash", str(script), "--json"]


def _powershell_setup_plan_cmd(repo: Path) -> list[str]:
    script = repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return [exe, "-NoProfile", "-File", str(script), "-Json"]


def _assert_stale_pointer_rejected(
    result: subprocess.CompletedProcess[str], repo: Path
) -> None:
    assert result.returncode == 1, result.stderr
    assert result.stdout == ""
    assert "Feature directory not found:" in result.stderr
    normalized_stderr = result.stderr.replace("\\", "/")
    assert f"/{repo.name}/{STALE_POINTER}" in normalized_stderr, result.stderr


def _assert_live_pointer_resolved(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    feature_dir = Path(payload["FEATURE_DIR"])
    assert feature_dir.name == Path(LIVE_POINTER).name
    assert str(feature_dir).replace("\\", "/").endswith(LIVE_POINTER)


@pytest.mark.parametrize("kind", STALE_KINDS)
def test_python_rejects_stale_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_stale_target(project, kind)
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_python_cmd(project), project), project)


@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_python_accepts_existing_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_live_target(project, kind)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_python_cmd(project), project))


def test_python_setup_plan_does_not_recreate_deleted_feature_dir(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_python_setup_plan_cmd(project), project), project)
    assert not (project / STALE_POINTER).exists()


@requires_local_bash
@pytest.mark.parametrize("kind", STALE_KINDS)
def test_bash_rejects_stale_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_stale_target(project, kind)
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_bash_cmd(project), project), project)


@requires_local_bash
@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_bash_accepts_existing_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_live_target(project, kind)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_bash_cmd(project), project))


@requires_local_bash
def test_bash_setup_plan_does_not_recreate_deleted_feature_dir(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_bash_setup_plan_cmd(project), project), project)
    assert not (project / STALE_POINTER).exists()


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("kind", STALE_KINDS)
def test_powershell_rejects_stale_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_stale_target(project, kind)
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_powershell_cmd(project), project), project)


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_powershell_accepts_existing_feature_json_pointer(project: Path, kind: str) -> None:
    _prepare_live_target(project, kind)
    _write_pointer(project, LIVE_POINTER)

    _assert_live_pointer_resolved(_run(_powershell_cmd(project), project))


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_setup_plan_does_not_recreate_deleted_feature_dir(project: Path) -> None:
    _write_pointer(project, STALE_POINTER)

    _assert_stale_pointer_rejected(_run(_powershell_setup_plan_cmd(project), project), project)
    assert not (project / STALE_POINTER).exists()
