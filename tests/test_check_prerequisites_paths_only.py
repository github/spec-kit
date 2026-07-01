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
_WINDOWS_POWERSHELL = (shutil.which("powershell.exe") or shutil.which("powershell")) if os.name == "nt" else None


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
    """--paths-only must return paths when feature.json pins the feature dir."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
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
    """--paths-only must also work when feature.json and SPECIFY_FEATURE agree."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    env = _clean_env()
    env["SPECIFY_FEATURE"] = "001-my-feature"
    result = subprocess.run(
        ["bash", str(script), "--json", "--paths-only"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "FEATURE_DIR" in data
    assert "001-my-feature" in data.get("BRANCH", "")


@requires_bash
def test_paths_only_text_mode_on_non_spec_branch(prereq_repo: Path) -> None:
    """--paths-only without --json must return text paths from feature.json."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
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
    """Without --paths-only, feature directory validation must still fail on main.

    The error must go to stderr and stdout must stay clean, so a caller that
    parses stdout as JSON is not handed the error string instead (#3122).
    """
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
    assert "Feature directory not found" in result.stderr
    assert "Feature directory not found" not in result.stdout
    assert result.stdout.strip() == ""


@requires_bash
def test_paths_only_does_not_persist_feature_json(prereq_repo: Path) -> None:
    """--paths-only must not rewrite feature.json even when the env override
    differs from the pinned value (#3025).

    Path resolution is read-only, so it must never dirty the working tree or
    overwrite the persisted feature directory.
    """
    pinned = "specs/001-my-feature"
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True, exist_ok=True)
    (prereq_repo / "specs" / "002-other").mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo, pinned)
    fj = prereq_repo / ".specify" / "feature.json"
    before = fj.read_text(encoding="utf-8")

    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"
    result = subprocess.run(
        ["bash", str(script), "--json", "--paths-only"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    # The override is honored in the output...
    data = json.loads(result.stdout)
    assert "002-other" in data["FEATURE_DIR"]
    # ...but the pinned file on disk is untouched.
    assert fj.read_text(encoding="utf-8") == before


@requires_bash
def test_normal_mode_still_persists_feature_json(prereq_repo: Path) -> None:
    """Without --paths-only, the env override is still persisted to feature.json,
    so the --no-persist opt-out does not regress normal write behavior (#3025)."""
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True, exist_ok=True)
    feat = prereq_repo / "specs" / "002-other"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    fj = prereq_repo / ".specify" / "feature.json"

    script = prereq_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(fj.read_text(encoding="utf-8"))["feature_directory"] == "specs/002-other"


# ── PowerShell tests ──────────────────────────────────────────────────────


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_paths_only_succeeds_on_non_spec_branch(prereq_repo: Path) -> None:
    """-PathsOnly must return paths when feature.json pins the feature dir."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_paths_only_succeeds_on_spec_branch(prereq_repo: Path) -> None:
    """-PathsOnly must also work when feature.json and SPECIFY_FEATURE agree."""
    subprocess.run(
        ["git", "checkout", "-q", "-b", "001-my-feature"],
        cwd=prereq_repo,
        check=True,
    )
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    env = _clean_env()
    env["SPECIFY_FEATURE"] = "001-my-feature"
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json", "-PathsOnly"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "FEATURE_DIR" in data


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_normal_mode_still_validates_branch(prereq_repo: Path) -> None:
    """Without -PathsOnly, feature directory validation must still fail on main.

    The error must land on stderr only, leaving stdout clean for -Json
    callers that parse it as JSON (#3122).
    """
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "Feature directory not found" in result.stderr
    assert "Feature directory not found" not in result.stdout
    assert result.stdout.strip() == ""


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_missing_plan_error_goes_to_stderr(prereq_repo: Path) -> None:
    """A missing plan.md must report on stderr, not stdout (#3122)."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo)
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "plan.md not found" in result.stderr
    assert "plan.md not found" not in result.stdout
    assert result.stdout.strip() == ""


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_missing_tasks_error_goes_to_stderr(prereq_repo: Path) -> None:
    """With -RequireTasks, a missing tasks.md must report on stderr only (#3122)."""
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    _write_feature_json(prereq_repo)
    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json", "-RequireTasks"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode != 0
    assert "tasks.md not found" in result.stderr
    assert "tasks.md not found" not in result.stdout
    assert result.stdout.strip() == ""


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_paths_only_does_not_persist_feature_json(prereq_repo: Path) -> None:
    """-PathsOnly must not rewrite feature.json even when the env override
    differs from the pinned value (#3025)."""
    pinned = "specs/001-my-feature"
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True, exist_ok=True)
    (prereq_repo / "specs" / "002-other").mkdir(parents=True, exist_ok=True)
    _write_feature_json(prereq_repo, pinned)
    fj = prereq_repo / ".specify" / "feature.json"
    before = fj.read_text(encoding="utf-8")

    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json", "-PathsOnly"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "002-other" in data["FEATURE_DIR"]
    assert fj.read_text(encoding="utf-8") == before


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_normal_mode_still_persists_feature_json(prereq_repo: Path) -> None:
    """Without -PathsOnly, the env override is still persisted to feature.json,
    so the -NoPersist opt-out does not regress normal write behavior (#3025).

    Symmetric to the bash test_normal_mode_still_persists_feature_json guard:
    asserts the default path still persists and that -NoPersist is not passed
    unconditionally.
    """
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True, exist_ok=True)
    feat = prereq_repo / "specs" / "002-other"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    fj = prereq_repo / ".specify" / "feature.json"

    script = prereq_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=prereq_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(fj.read_text(encoding="utf-8"))["feature_directory"] == "specs/002-other"
