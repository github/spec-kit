"""Tests for setup-plan bypassing branch-pattern checks when feature.json is valid."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import make_python3_path_shim

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
def test_setup_plan_survives_broken_python3_stub(plan_repo: Path) -> None:
    """A `python3` on PATH that exists but fails at runtime must not defeat
    feature.json parsing.

    On Windows `python3` typically resolves to the Microsoft Store App Execution
    Alias stub: it satisfies `command -v python3` yet exits non-zero at runtime.
    The parser must fall through to the grep/sed fallback on that failure instead
    of selecting python3 by mere availability and swallowing its error (#3304).
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / "001-tiny-notes-app"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(plan_repo, "specs/001-tiny-notes-app")

    # A stub python3 that mimics the Windows Store alias: on PATH, exits 49.
    stub_dir = plan_repo / "_stubbin"
    stub_dir.mkdir()
    stub = stub_dir / "python3"
    stub.write_text(
        "#!/bin/sh\n"
        'echo "Python was not found; run without arguments to install from the '
        'Microsoft Store" >&2\n'
        "exit 49\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    # A stub jq that shadows any real jq on PATH and also fails, so the parser
    # cannot short-circuit on jq and must reach the broken python3 stub and then
    # fall through to grep/sed. Without this, a runner that has jq installed
    # would parse feature.json via jq and never exercise the fallback this test
    # is meant to cover.
    jq_stub = stub_dir / "jq"
    jq_stub.write_text(
        "#!/bin/sh\n"
        'echo "jq: simulated failure" >&2\n'
        "exit 1\n",
        encoding="utf-8",
    )
    jq_stub.chmod(0o755)

    env = _clean_env()
    # Prepend the stub dir so the failing jq and python3 stubs take precedence
    # over any real ones; PATH still needs the real bash utilities for grep/sed.
    env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"

    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=plan_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (feat / "plan.md").is_file()


@requires_bash
@pytest.mark.parametrize("ensure_ascii", [False, True], ids=["raw-utf8", "ascii-escaped"])
@pytest.mark.parametrize(
    ("code_page", "name"),
    [("cp1252", "001-café"), ("gbk", "001-添加用户")],
    ids=["cp1252-latin", "gbk-cjk"],
)
def test_setup_plan_reads_non_ascii_feature_json_through_a_legacy_stdout(
    plan_repo: Path, tmp_path: Path, code_page: str, name: str, ensure_ascii: bool
) -> None:
    """The python3 feature.json parser must hand bash UTF-8, not the code page.

    On Windows a piped stdout uses the ANSI code page (cp1252 on Western
    systems, GBK on Simplified Chinese ones) rather than UTF-8. Without jq,
    printing the parsed path re-encoded it in that code page ("é" became the
    single byte 0xE9), so setup-plan.sh reported, and on some platforms
    created, a different directory from the one feature.json names.
    """
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature/my-feature-branch"],
        cwd=plan_repo,
        check=True,
    )
    feat = plan_repo / "specs" / name
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (plan_repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": f"specs/{name}"}, ensure_ascii=ensure_ascii),
        encoding="utf-8",
    )

    # A working python3 (Windows venvs only ship python.exe) and a failing jq,
    # so feature.json is parsed by python3 even on runners that have jq.
    stub_dir = make_python3_path_shim(tmp_path / "bin")
    jq_stub = stub_dir / "jq"
    jq_stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
    jq_stub.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"
    env["PYTHONIOENCODING"] = code_page

    script = plan_repo / ".specify" / "scripts" / "bash" / "setup-plan.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=plan_repo,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert (feat / "plan.md").is_file()
    assert [p.name for p in (plan_repo / "specs").iterdir()] == [name]
    # The reported paths must be UTF-8 too: agents read them from this output.
    feature_dir_line = next(
        line
        for line in result.stdout.decode("utf-8").splitlines()
        if line.startswith("FEATURE_DIR: ")
    )
    assert feature_dir_line.endswith(f"/specs/{name}")


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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
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
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_plan_ps_errors_without_feature_context(
    plan_repo: Path,
) -> None:
    script = plan_repo / ".specify" / "scripts" / "powershell" / "setup-plan.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
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
