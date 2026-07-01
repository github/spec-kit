"""Tests for setup-plan preserving existing plan.md (#2653)."""

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
_WINDOWS_POWERSHELL = (shutil.which("powershell.exe") or shutil.which("powershell")) if os.name == "nt" else None


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


def _write_feature_json(
    repo: Path, feature_directory: str = "specs/001-my-feature"
) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}),
        encoding="utf-8",
    )


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
def plan_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-my-feature"],
        cwd=repo,
        check=True,
    )
    (repo / ".specify").mkdir()
    _minimal_templates(repo)
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    _write_feature_json(repo)
    return repo


# ── Bash tests ────────────────────────────────────────────────────────────


@requires_bash
def test_setup_plan_creates_plan_when_missing(plan_repo: Path) -> None:
    """First run must create plan.md from the template."""
    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    plan_path = Path(data["IMPL_PLAN"])
    assert plan_path.is_file()
    # Template content should be present
    content = plan_path.read_text(encoding="utf-8")
    assert len(content) > 0


@requires_bash
def test_setup_plan_preserves_existing_plan(plan_repo: Path) -> None:
    """Rerun must not overwrite an existing plan.md."""
    feat = plan_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    existing_content = "# My carefully authored plan\n\nDo not overwrite me.\n"
    (feat / "plan.md").write_text(existing_content, encoding="utf-8")

    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    # Plan must be unchanged
    assert (feat / "plan.md").read_text(encoding="utf-8") == existing_content


@requires_bash
def test_setup_plan_skip_message_on_stderr_in_json_mode(plan_repo: Path) -> None:
    """In --json mode, status messages must go to stderr, not stdout."""
    feat = plan_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# existing\n", encoding="utf-8")

    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    # stdout must be valid JSON (no status messages mixed in)
    data = json.loads(result.stdout)
    assert "IMPL_PLAN" in data
    # The skip message should be on stderr
    assert "already exists" in result.stderr


@requires_bash
def test_setup_plan_json_parseable_on_first_run(plan_repo: Path) -> None:
    """In --json mode, first-run stdout must be parseable JSON (no status on stdout)."""
    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "IMPL_PLAN" in data
    assert "Copied plan template" in result.stderr


# ── PowerShell tests ──────────────────────────────────────────────────────


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_setup_plan_creates_plan_when_missing(plan_repo: Path) -> None:
    """First run must create plan.md from the template."""
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    plan_path = Path(data["IMPL_PLAN"])
    assert plan_path.is_file()
    content = plan_path.read_text(encoding="utf-8")
    assert len(content) > 0


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_setup_plan_preserves_existing_plan(plan_repo: Path) -> None:
    """Rerun must not overwrite an existing plan.md."""
    feat = plan_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    existing_content = "# My carefully authored plan\n\nDo not overwrite me.\n"
    (feat / "plan.md").write_text(existing_content, encoding="utf-8")

    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    assert (feat / "plan.md").read_text(encoding="utf-8") == existing_content
    # stdout must be valid JSON (no status messages mixed in)
    data = json.loads(result.stdout)
    assert "IMPL_PLAN" in data
    # The skip message should be on stderr
    assert "already exists" in result.stderr


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_setup_plan_copied_message_on_stderr_in_json_mode(plan_repo: Path) -> None:
    """First run in -Json mode must emit 'Copied plan template' on stderr (matching
    the bash twin) while keeping stdout pure JSON. Before the fix the PowerShell
    script emitted no copy status at all."""
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    # stdout stays parseable JSON; the status message goes to stderr.
    data = json.loads(result.stdout)
    assert "IMPL_PLAN" in data
    assert "Copied plan template" in result.stderr


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_setup_plan_template_not_found_warning_matches_bash(plan_repo: Path) -> None:
    """When no plan template resolves, -Json mode must emit 'Warning: Plan template
    not found' on stderr (matching the bash twin's wording and stream routing) while
    keeping stdout pure JSON. Before the fix the PowerShell script used Write-Warning,
    producing a different 'WARNING:' prefix on the warning stream instead."""
    # Remove the template the fixture installs so resolution finds nothing.
    (plan_repo / ".specify" / "templates" / "plan-template.md").unlink()
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "IMPL_PLAN" in data
    assert "Warning: Plan template not found" in result.stderr
