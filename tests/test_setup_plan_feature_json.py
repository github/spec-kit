"""Tests for setup-plan bypassing branch-pattern checks when feature.json is valid."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
SETUP_PLAN_SH = PROJECT_ROOT / "scripts" / "bash" / "setup-plan.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
SETUP_PLAN_PS = PROJECT_ROOT / "scripts" / "powershell" / "setup-plan.ps1"
PLAN_TEMPLATE = PROJECT_ROOT / "templates" / "plan-template.md"

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, d / "common.sh")
    shutil.copy(SETUP_PLAN_SH, d / "setup-plan.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, d / "common.ps1")
    shutil.copy(SETUP_PLAN_PS, d / "setup-plan.ps1")


def _minimal_templates(repo: Path) -> None:
    tdir = repo / ".specify" / "templates"
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(PLAN_TEMPLATE, tdir / "plan-template.md")


def _write_feature_json(repo: Path, feature_directory: str) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}),
        encoding="utf-8",
    )


def _clean_env() -> dict[str, str]:
    """Return a copy of the current environment with any SPECIFY_* vars removed.

    setup-plan.{sh,ps1} honors SPECIFY_FEATURE, SPECIFY_FEATURE_DIRECTORY, etc.,
    which would otherwise leak from a developer shell or CI runner and make these
    tests flaky. Stripping them forces every case to rely purely on git branch +
    .specify/feature.json state set up by the fixture.
    """
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
def plan_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _minimal_templates(repo)
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    return repo


@requires_bash
def test_setup_plan_passes_custom_branch_when_feature_json_valid(plan_repo: Path) -> None:
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(plan_repo, "specs/001-tiny-notes-app")
    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (feat / "plan.md").is_file()


@requires_bash
def test_setup_plan_errors_without_feature_context(plan_repo: Path) -> None:
    """Without feature.json or SPECIFY_FEATURE_DIRECTORY, setup-plan must error."""
    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "Feature directory not found" in result.stderr


@requires_bash
def test_setup_plan_numbered_branch_works_with_feature_json(
    plan_repo: Path,
) -> None:
    """A numbered branch still works when feature.json explicitly pins the spec dir."""
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-tiny-notes-app"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(plan_repo, "specs/001-tiny-notes-app")
    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (feat / "plan.md").is_file()


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_plan_ps_passes_custom_branch_when_feature_json_valid(plan_repo: Path) -> None:
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(plan_repo, "specs/001-tiny-notes-app")
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (feat / "plan.md").is_file()


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_plan_ps_errors_without_feature_context(
    plan_repo: Path,
) -> None:
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    combined = result.stderr + result.stdout
    assert result.returncode != 0
    assert "Feature directory not found" in combined
