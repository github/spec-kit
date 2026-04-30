"""Tests for setup-tasks.{sh,ps1} template resolution and branch validation."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
SETUP_TASKS_SH = PROJECT_ROOT / "scripts" / "bash" / "setup-tasks.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
SETUP_TASKS_PS = PROJECT_ROOT / "scripts" / "powershell" / "setup-tasks.ps1"
TASKS_TEMPLATE = PROJECT_ROOT / "templates" / "tasks-template.md"

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, d / "common.sh")
    shutil.copy(SETUP_TASKS_SH, d / "setup-tasks.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, d / "common.ps1")
    shutil.copy(SETUP_TASKS_PS, d / "setup-tasks.ps1")


def _install_core_tasks_template(repo: Path) -> None:
    """Copy the real tasks-template.md into the core template location."""
    tdir = repo / ".specify" / "templates"
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(TASKS_TEMPLATE, tdir / "tasks-template.md")


def _minimal_feature(repo: Path) -> Path:
    """
    Create a numbered branch-style feature directory with spec.md and plan.md
    so all prerequisite checks in setup-tasks pass.
    Returns the feature directory path.
    """
    feat = repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    return feat


def _clean_env() -> dict[str, str]:
    """
    Return os.environ with all SPECIFY_* variables stripped so the scripts
    rely purely on git branch + feature.json state set up by each fixture.
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


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def tasks_repo(tmp_path: Path) -> Path:
    """
    A minimal repo with:
      - git initialised on a numbered branch (001-my-feature)
      - core tasks-template.md in place
      - both bash and PowerShell scripts installed
    """
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)

    # Switch to a numbered branch so branch validation passes without feature.json
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-my-feature"],
        cwd=repo,
        check=True,
    )

    (repo / ".specify").mkdir()
    _install_core_tasks_template(repo)
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    return repo


# ===========================================================================
# BASH TESTS
# ===========================================================================

@requires_bash
def test_setup_tasks_bash_core_template_resolved(tasks_repo: Path) -> None:
    """
    When the core tasks-template.md is present and all prerequisites are met,
    setup-tasks.sh --json should exit 0 and return an absolute, existing
    TASKS_TEMPLATE path pointing to the core template.
    """
    feat = _minimal_feature(tasks_repo)
    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout

    data = json.loads(result.stdout)
    tasks_tmpl = Path(data["TASKS_TEMPLATE"])
    assert tasks_tmpl.is_absolute(), "TASKS_TEMPLATE must be an absolute path"
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    assert tasks_tmpl.name == "tasks-template.md"


@requires_bash
def test_setup_tasks_bash_override_wins(tasks_repo: Path) -> None:
    """
    When an override exists at .specify/templates/overrides/tasks-template.md,
    setup-tasks.sh --json must return the override path, not the core path.
    """
    feat = _minimal_feature(tasks_repo)

    # Create the override
    overrides_dir = tasks_repo / ".specify" / "templates" / "overrides"
    overrides_dir.mkdir(parents=True, exist_ok=True)
    override_file = overrides_dir / "tasks-template.md"
    override_file.write_text("# override tasks template\n", encoding="utf-8")

    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout

    data = json.loads(result.stdout)
    tasks_tmpl = Path(data["TASKS_TEMPLATE"])
    assert tasks_tmpl.is_absolute(), "TASKS_TEMPLATE must be an absolute path"
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    # The resolved path must be inside the overrides directory
    assert "overrides" in tasks_tmpl.parts, (
        f"Expected override path but got: {tasks_tmpl}"
    )


@requires_bash
def test_setup_tasks_bash_missing_template_errors(tasks_repo: Path) -> None:
    """
    When tasks-template.md is absent from all locations, setup-tasks.sh must
    exit non-zero and print a helpful ERROR message to stderr.
    """
    feat = _minimal_feature(tasks_repo)

    # Remove the core template so no template exists anywhere
    core = tasks_repo / ".specify" / "templates" / "tasks-template.md"
    core.unlink()

    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode != 0
    assert "ERROR" in result.stderr
    assert "tasks-template" in result.stderr


@requires_bash
def test_setup_tasks_bash_passes_custom_branch_when_feature_json_valid(
    tasks_repo: Path,
) -> None:
    """
    On a non-standard branch, setup-tasks.sh must succeed when feature.json
    pins a valid FEATURE_DIR (branch validation should be skipped).
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/custom-branch"],
        cwd=tasks_repo,
        check=True,
    )

    feat = tasks_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")

    (tasks_repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-my-feature"}),
        encoding="utf-8",
    )

    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout


@requires_bash
def test_setup_tasks_bash_fails_custom_branch_without_feature_json(
    tasks_repo: Path,
) -> None:
    """
    On a non-standard branch with no feature.json, setup-tasks.sh must fail
    and report that we are not on a feature branch.
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/custom-branch"],
        cwd=tasks_repo,
        check=True,
    )

    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


# ===========================================================================
# POWERSHELL TESTS
# ===========================================================================

@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_core_template_resolved(tasks_repo: Path) -> None:
    """
    When the core tasks-template.md is present and all prerequisites are met,
    setup-tasks.ps1 -Json should exit 0 and return an absolute, existing
    TASKS_TEMPLATE path.
    """
    feat = _minimal_feature(tasks_repo)
    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout

    data = json.loads(result.stdout)
    tasks_tmpl = Path(data["TASKS_TEMPLATE"])
    assert tasks_tmpl.is_absolute(), "TASKS_TEMPLATE must be an absolute path"
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    assert tasks_tmpl.name == "tasks-template.md"


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_override_wins(tasks_repo: Path) -> None:
    """
    When an override exists at .specify/templates/overrides/tasks-template.md,
    setup-tasks.ps1 -Json must return the override path, not the core path.
    """
    feat = _minimal_feature(tasks_repo)

    overrides_dir = tasks_repo / ".specify" / "templates" / "overrides"
    overrides_dir.mkdir(parents=True, exist_ok=True)
    override_file = overrides_dir / "tasks-template.md"
    override_file.write_text("# override tasks template\n", encoding="utf-8")

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout

    data = json.loads(result.stdout)
    tasks_tmpl = Path(data["TASKS_TEMPLATE"])
    assert tasks_tmpl.is_absolute(), "TASKS_TEMPLATE must be an absolute path"
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    assert "overrides" in tasks_tmpl.parts, (
        f"Expected override path but got: {tasks_tmpl}"
    )


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_missing_template_errors(tasks_repo: Path) -> None:
    """
    When tasks-template.md is absent from all locations, setup-tasks.ps1 must
    exit non-zero and write a helpful error to stderr.
    """
    feat = _minimal_feature(tasks_repo)

    core = tasks_repo / ".specify" / "templates" / "tasks-template.md"
    core.unlink()

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode != 0
    assert "tasks-template" in result.stderr.lower() or "tasks-template" in result.stdout.lower()


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_passes_custom_branch_when_feature_json_valid(
    tasks_repo: Path,
) -> None:
    """
    On a non-standard branch, setup-tasks.ps1 must succeed when feature.json
    pins a valid FEATURE_DIR (branch validation should be skipped).
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/custom-branch"],
        cwd=tasks_repo,
        check=True,
    )

    feat = tasks_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")

    (tasks_repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-my-feature"}),
        encoding="utf-8",
    )

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_fails_custom_branch_without_feature_json(
    tasks_repo: Path,
) -> None:
    """
    On a non-standard branch with no feature.json, setup-tasks.ps1 must fail
    and report that we are not on a feature branch.
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/custom-branch"],
        cwd=tasks_repo,
        check=True,
    )

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr