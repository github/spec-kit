"""check-prerequisites honors feature.json the same way setup-plan/-tasks do.

Regression guard for the inconsistency where setup-plan.sh / setup-tasks.sh
skipped the feature-branch check when .specify/feature.json pinned an existing
feature directory, but check-prerequisites.{sh,ps1} did not — so half the
spec-kit commands succeeded and half failed on the same branch.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
CHECK_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
CHECK_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, d / "common.sh")
    shutil.copy(CHECK_SH, d / "check-prerequisites.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, d / "common.ps1")
    shutil.copy(CHECK_PS, d / "check-prerequisites.ps1")


def _clean_env() -> dict[str, str]:
    """Strip SPECIFY_* vars so each case relies purely on branch + feature.json."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True)


def _populate_feature(repo: Path, *, with_tasks: bool = False) -> Path:
    feat = repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    if with_tasks:
        (feat / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    return feat


def _pin_feature_json(repo: Path, feature_directory: str = "specs/001-tiny-notes-app") -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}),
        encoding="utf-8",
    )


@pytest.fixture
def prereq_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir(exist_ok=True)
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "chore/not-a-feature-branch"], cwd=repo, check=True
    )
    return repo


def _run_bash(repo: Path, *args: str) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


def _run_ps(repo: Path, *args: str) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    return subprocess.run(
        [exe, "-NoProfile", "-File", str(script), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


@requires_bash
def test_bash_json_passes_custom_branch_when_feature_json_valid(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo)
    _pin_feature_json(prereq_repo)
    result = _run_bash(prereq_repo, "--json")
    assert result.returncode == 0, result.stderr + result.stdout


@requires_bash
def test_bash_require_tasks_passes_when_feature_json_valid(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo, with_tasks=True)
    _pin_feature_json(prereq_repo)
    result = _run_bash(prereq_repo, "--json", "--require-tasks", "--include-tasks")
    assert result.returncode == 0, result.stderr + result.stdout


@requires_bash
def test_bash_json_fails_custom_branch_without_feature_json(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo)
    result = _run_bash(prereq_repo, "--json")
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


@requires_bash
def test_bash_json_enforces_branch_when_feature_json_pins_missing_dir(prereq_repo: Path) -> None:
    # The bypass must only trigger when feature.json matches an EXISTING dir.
    # A bogus pin must NOT bypass the branch check.
    _populate_feature(prereq_repo)
    _pin_feature_json(prereq_repo, feature_directory="specs/999-does-not-exist")
    result = _run_bash(prereq_repo, "--json")
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


@requires_bash
def test_bash_json_enforces_branch_when_feature_json_malformed(prereq_repo: Path) -> None:
    # Malformed feature.json must fail safe (enforce the branch check), not bypass it.
    _populate_feature(prereq_repo)
    (prereq_repo / ".specify" / "feature.json").write_text("{ not json", encoding="utf-8")
    result = _run_bash(prereq_repo, "--json")
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


@requires_bash
def test_bash_paths_only_always_succeeds(prereq_repo: Path) -> None:
    # --paths-only performs no validation and must succeed regardless of branch.
    result = _run_bash(prereq_repo, "--json", "--paths-only")
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_json_passes_custom_branch_when_feature_json_valid(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo)
    _pin_feature_json(prereq_repo)
    result = _run_ps(prereq_repo, "-Json")
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_json_fails_custom_branch_without_feature_json(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo)
    result = _run_ps(prereq_repo, "-Json")
    assert result.returncode != 0
    # Assert the branch check is the failure cause — not the later "feature dir
    # not found" check, which would also exit 1 and mask a broken guard.
    assert "Not on a feature branch" in result.stderr


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_ps_json_enforces_branch_when_feature_json_pins_missing_dir(prereq_repo: Path) -> None:
    _populate_feature(prereq_repo)
    _pin_feature_json(prereq_repo, feature_directory="specs/999-does-not-exist")
    result = _run_ps(prereq_repo, "-Json")
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr
