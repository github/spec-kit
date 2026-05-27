"""Tests for check-prerequisites --paths-only skipping branch validation (#2653)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
CHECK_PREREQS_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
CHECK_PREREQS_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, d / "common.sh")
    shutil.copy(CHECK_PREREQS_SH, d / "check-prerequisites.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, d / "common.ps1")
    shutil.copy(CHECK_PREREQS_PS, d / "check-prerequisites.ps1")


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True
    )


@pytest.fixture
def prereq_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    return repo


# ── Bash tests ────────────────────────────────────────────────────────────


@requires_bash
def test_paths_only_succeeds_on_non_spec_branch(prereq_repo: Path) -> None:
    """--paths-only must return paths without branch validation (main branch)."""
    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    result = subprocess.run(
        ["bash", str(script), "--json", "--paths-only"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "REPO_ROOT" in data
    assert "BRANCH" in data
    assert "FEATURE_DIR" in data


@requires_bash
def test_paths_only_succeeds_on_spec_branch(prereq_repo: Path) -> None:
    """--paths-only must also work on a properly named spec branch."""
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-my-feature"],
        cwd=prereq_repo,
        check=True,
    )
    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    result = subprocess.run(
        ["bash", str(script), "--json", "--paths-only"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "FEATURE_DIR" in data
    assert "001-my-feature" in data.get("BRANCH", "")


@requires_bash
def test_paths_only_text_mode_on_non_spec_branch(prereq_repo: Path) -> None:
    """--paths-only without --json must return text paths on a non-spec branch."""
    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    result = subprocess.run(
        ["bash", str(script), "--paths-only"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "REPO_ROOT:" in result.stdout
    assert "FEATURE_DIR:" in result.stdout


@requires_bash
def test_normal_mode_still_validates_branch(prereq_repo: Path) -> None:
    """Without --paths-only, branch validation must still fail on main."""
    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


# ── PowerShell tests ──────────────────────────────────────────────────────


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_paths_only_succeeds_on_non_spec_branch(prereq_repo: Path) -> None:
    """-PathsOnly must return paths without branch validation (main branch)."""
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json", "-PathsOnly"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "REPO_ROOT" in data
    assert "BRANCH" in data
    assert "FEATURE_DIR" in data


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_paths_only_succeeds_on_spec_branch(prereq_repo: Path) -> None:
    """-PathsOnly must also work on a properly named spec branch."""
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-my-feature"],
        cwd=prereq_repo,
        check=True,
    )
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json", "-PathsOnly"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "FEATURE_DIR" in data


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_normal_mode_still_validates_branch(prereq_repo: Path) -> None:
    """Without -PathsOnly, branch validation must still fail on main."""
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr
