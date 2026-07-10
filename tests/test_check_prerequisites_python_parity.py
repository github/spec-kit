"""Parity tests for the Python check-prerequisites PoC."""

from __future__ import annotations

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
CHECK_PREREQS_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
CHECK_PREREQS_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"
COMMON_PY = PROJECT_ROOT / "scripts" / "python" / "common.py"
CHECK_PREREQS_PY = PROJECT_ROOT / "scripts" / "python" / "check_prerequisites.py"

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (
    shutil.which("powershell.exe") or shutil.which("powershell")
) if os.name == "nt" else None


def _install_scripts(repo: Path) -> None:
    bash_dir = repo / ".specify" / "scripts" / "bash"
    bash_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, bash_dir / "common.sh")
    shutil.copy(CHECK_PREREQS_SH, bash_dir / "check-prerequisites.sh")

    ps_dir = repo / ".specify" / "scripts" / "powershell"
    ps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, ps_dir / "common.ps1")
    shutil.copy(CHECK_PREREQS_PS, ps_dir / "check-prerequisites.ps1")

    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PY, py_dir / "common.py")
    shutil.copy(CHECK_PREREQS_PY, py_dir / "check_prerequisites.py")


def _write_feature_json(
    repo: Path, feature_directory: str = "specs/001-my-feature"
) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}, separators=(",", ":"))
        + "\n",
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
    _install_scripts(repo)
    return repo


def _py_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "python" / "check_prerequisites.py"
    return [sys.executable, str(script), *args]


def _repo_copy_py_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / "scripts" / "python" / "check_prerequisites.py"
    return [sys.executable, str(script), *args]


def _bash_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    return ["bash", str(script), *args]


def _ps_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return [exe, "-NoProfile", "-File", str(script), *args]


def _run(
    cmd: list[str], repo: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env or _clean_env(),
    )


def _json_stdout(result: subprocess.CompletedProcess[str]) -> object:
    return json.loads(result.stdout)


def _normalize_status_text(text: str) -> str:
    return (
        text.replace("  ✓ ", "  [OK] ")
        .replace("  ✗ ", "  [FAIL] ")
        .replace("\r\n", "\n")
    )


def _normalize_help_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace(
        "check-prerequisites.sh", "check_prerequisites.py"
    )
    return "\n".join("" if not line.strip() else line for line in normalized.split("\n"))


@requires_bash
@pytest.mark.parametrize(
    "args",
    [
        ("--json",),
        ("--json", "--include-tasks"),
        ("--json", "--require-tasks", "--include-tasks"),
        ("--json", "--paths-only"),
    ],
)
def test_python_json_output_matches_bash(prereq_repo: Path, args: tuple[str, ...]) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    (feat / "data-model.md").write_text("# model\n", encoding="utf-8")
    (feat / "quickstart.md").write_text("# quickstart\n", encoding="utf-8")
    (feat / "contracts" / "v1").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    bash = _run(_bash_cmd(prereq_repo, *args), prereq_repo)
    py = _run(_py_cmd(prereq_repo, *args), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _json_stdout(py) == _json_stdout(bash)


@requires_bash
def test_python_text_output_matches_bash(prereq_repo: Path) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "contracts").mkdir()
    _write_feature_json(prereq_repo)

    bash = _run(_bash_cmd(prereq_repo, "--include-tasks"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--include-tasks"), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _normalize_status_text(py.stdout) == _normalize_status_text(bash.stdout)


@requires_bash
def test_python_help_output_matches_bash(prereq_repo: Path) -> None:
    bash = _run(_bash_cmd(prereq_repo, "--help"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--help"), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _normalize_help_text(py.stdout) == _normalize_help_text(bash.stdout)


@requires_bash
def test_python_unknown_option_matches_bash_error_shape(prereq_repo: Path) -> None:
    bash = _run(_bash_cmd(prereq_repo, "--bogus"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--bogus"), prereq_repo)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert py.stderr == bash.stderr


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
@pytest.mark.parametrize(
    ("py_args", "ps_args"),
    [
        (("--json",), ("-Json",)),
        (("--json", "--include-tasks"), ("-Json", "-IncludeTasks")),
        (
            ("--json", "--require-tasks", "--include-tasks"),
            ("-Json", "-RequireTasks", "-IncludeTasks"),
        ),
        (("--json", "--paths-only"), ("-Json", "-PathsOnly")),
    ],
    ids=[
        "json",
        "json_include_tasks",
        "json_require_tasks_include_tasks",
        "json_paths_only",
    ],
)
def test_python_json_output_matches_powershell(
    prereq_repo: Path, py_args: tuple[str, ...], ps_args: tuple[str, ...]
) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    (feat / "data-model.md").write_text("# model\n", encoding="utf-8")
    (feat / "quickstart.md").write_text("# quickstart\n", encoding="utf-8")
    (feat / "contracts" / "v1").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    ps = _run(_ps_cmd(prereq_repo, *ps_args), prereq_repo)
    py = _run(_py_cmd(prereq_repo, *py_args), prereq_repo)

    assert py.returncode == ps.returncode == 0
    assert py.stderr == ps.stderr == ""
    assert _json_stdout(py) == _json_stdout(ps)


def test_python_repo_copy_script_file_fallback_finds_repo_root(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _write_feature_json(repo)
    (repo / "specs" / "001-my-feature").mkdir(parents=True)

    py_dir = repo / "scripts" / "python"
    py_dir.mkdir(parents=True)
    shutil.copy(COMMON_PY, py_dir / "common.py")
    shutil.copy(CHECK_PREREQS_PY, py_dir / "check_prerequisites.py")

    py = _run(_repo_copy_py_cmd(repo, "--json", "--paths-only"), outside)

    assert py.returncode == 0, py.stderr
    assert Path(_json_stdout(py)["REPO_ROOT"]) == repo


def test_python_paths_only_does_not_persist_feature_json(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    (prereq_repo / "specs" / "002-other").mkdir(parents=True)
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    feature_json = prereq_repo / ".specify" / "feature.json"
    before = feature_json.read_text(encoding="utf-8")
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"

    py = _run(_py_cmd(prereq_repo, "--json", "--paths-only"), prereq_repo, env=env)

    assert py.returncode == 0, py.stderr
    assert "002-other" in _json_stdout(py)["FEATURE_DIR"]
    assert feature_json.read_text(encoding="utf-8") == before


def test_python_normal_mode_persists_feature_json(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    feat = prereq_repo / "specs" / "002-other"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"

    py = _run(_py_cmd(prereq_repo, "--json"), prereq_repo, env=env)

    assert py.returncode == 0, py.stderr
    data = json.loads(
        (prereq_repo / ".specify" / "feature.json").read_text(encoding="utf-8")
    )
    assert data["feature_directory"] == "specs/002-other"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("--json",), "Feature directory not found"),
        (("--json",), "plan.md not found"),
        (("--json", "--require-tasks"), "tasks.md not found"),
    ],
    ids=["missing_feature_context", "missing_plan", "missing_tasks"],
)
def test_python_negative_errors_are_stderr_only(
    tmp_path: Path, args: tuple[str, ...], expected: str
) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _install_scripts(repo)

    if expected in {"plan.md not found", "tasks.md not found"}:
        feat = repo / "specs" / "001-my-feature"
        feat.mkdir(parents=True)
        _write_feature_json(repo)
        if expected == "tasks.md not found":
            (feat / "plan.md").write_text("# plan\n", encoding="utf-8")

    py = _run(_py_cmd(repo, *args), repo)

    assert py.returncode != 0
    assert expected in py.stderr
    assert expected not in py.stdout
    assert py.stdout.strip() == ""


def test_python_branch_falls_back_to_feature_dir_basename(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    py = _run(_py_cmd(prereq_repo, "--json", "--paths-only"), prereq_repo)

    assert py.returncode == 0, py.stderr
    assert _json_stdout(py)["BRANCH"] == "001-my-feature"
