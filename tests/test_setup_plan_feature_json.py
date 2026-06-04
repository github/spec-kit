"""Tests for setup-plan bypassing branch-pattern checks when feature.json is valid."""

import json
import os
import shutil
import subprocess
import sys
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


def _is_windows_powershell(exe: str) -> bool:
    return (
        sys.platform != "win32"
        and str(exe).endswith("powershell.exe")
        and shutil.which("wslpath") is not None
    )


def _to_windows_path(path: Path) -> str:
    result = subprocess.run(
        ["wslpath", "-w", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _quote_ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_powershell(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = _clean_env()
    env.setdefault("NO_COLOR", "1")
    run_args = list(args)
    if args and _is_windows_powershell(args[0]):
        exe, rest = args[0], args[1:]
        cwd_command = f"Set-Location -LiteralPath {_quote_ps(_to_windows_path(cwd))}"
        if "-File" in rest:
            index = rest.index("-File")
            script = rest[index + 1]
            script_args = rest[index + 2 :]
            command = f"{cwd_command}; & {_quote_ps(script)}"
            if script_args:
                command += " " + " ".join(script_args)
            run_args = [exe, *rest[:index], "-Command", command]
        elif "-Command" in rest:
            index = rest.index("-Command")
            command = f"{cwd_command}; {rest[index + 1]}"
            run_args = [exe, *rest[:index], "-Command", command, *rest[index + 2 :]]

    result = subprocess.run(
        run_args,
        cwd=cwd,
        capture_output=True,
        check=False,
        env=env,
    )
    return subprocess.CompletedProcess(
        result.args,
        result.returncode,
        result.stdout.decode("utf-8", errors="replace"),
        result.stderr.decode("utf-8", errors="replace"),
    )


def _powershell_script_arg(exe: str, script: Path) -> str:
    if _is_windows_powershell(exe):
        return _to_windows_path(script)
    return str(script)


def _powershell_has_git(exe: str, cwd: Path) -> bool:
    result = _run_powershell(
        [exe, "-NoProfile", "-Command", "git rev-parse --is-inside-work-tree"],
        cwd=cwd,
    )
    return result.returncode == 0 and "true" in result.stdout.lower()


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
    (plan_repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-tiny-notes-app"}),
        encoding="utf-8",
    )
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
def test_setup_plan_fails_custom_branch_without_feature_json(plan_repo: Path) -> None:
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
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
    assert "Not on a feature branch" in result.stderr


@requires_bash
def test_setup_plan_numbered_branch_unchanged_without_feature_json(
    plan_repo: Path,
) -> None:
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-tiny-notes-app"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
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
    (plan_repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-tiny-notes-app"}),
        encoding="utf-8",
    )
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = _run_powershell(
        [exe, "-NoProfile", "-File", _powershell_script_arg(exe, script)],
        cwd=plan_repo,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (feat / "plan.md").is_file()


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_plan_ps_fails_custom_branch_without_feature_json(
    plan_repo: Path,
) -> None:
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    if not _powershell_has_git(exe, plan_repo):
        pytest.skip("PowerShell cannot access git in this environment")
    result = _run_powershell(
        [exe, "-NoProfile", "-File", _powershell_script_arg(exe, script)],
        cwd=plan_repo,
    )
    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr
