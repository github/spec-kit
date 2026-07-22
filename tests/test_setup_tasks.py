"""Tests for setup-tasks.{sh,ps1} template resolution and feature resolution."""

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
CHECK_PREREQ_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
SETUP_TASKS_PS = PROJECT_ROOT / "scripts" / "powershell" / "setup-tasks.ps1"
CHECK_PREREQ_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"
TASKS_TEMPLATE = PROJECT_ROOT / "templates" / "tasks-template.md"

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (shutil.which("powershell.exe") or shutil.which("powershell")) if os.name == "nt" else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, d / "common.sh")
    shutil.copy(SETUP_TASKS_SH, d / "setup-tasks.sh")
    shutil.copy(CHECK_PREREQ_SH, d / "check-prerequisites.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, d / "common.ps1")
    shutil.copy(SETUP_TASKS_PS, d / "setup-tasks.ps1")
    shutil.copy(CHECK_PREREQ_PS, d / "check-prerequisites.ps1")


def _install_core_tasks_template(repo: Path) -> None:
    """Copy the real tasks-template.md into the core template location."""
    tdir = repo / ".specify" / "templates"
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(TASKS_TEMPLATE, tdir / "tasks-template.md")


def _write_feature_json(
    repo: Path, feature_directory: str = "specs/001-my-feature"
) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}),
        encoding="utf-8",
    )


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
    _write_feature_json(repo)
    return feat


def _write_integration_state(repo: Path, integration: str = "claude", separator: str = "-") -> None:
    specify_dir = repo / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "integration": integration,
        "default_integration": integration,
        "installed_integrations": [integration],
        "integration_settings": {
            integration: {
                "invoke_separator": separator,
            },
        },
    }
    (specify_dir / "integration.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def _clean_env() -> dict[str, str]:
    """
    Return os.environ with all SPECIFY_* variables stripped so the scripts
    rely purely on feature.json and on-disk feature directories set up by each fixture.
    """
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _run_bash_format_command(repo: Path, command_name: str) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "bash" / "common.sh"
    return subprocess.run(
        ["bash", "-c", 'source "$1"; format_speckit_command "$2" "$PWD"', "bash", str(script), command_name],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


def _run_powershell_format_command(repo: Path, command_name: str) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "powershell" / "common.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return subprocess.run(
        [
            exe,
            "-NoProfile",
            "-Command",
            '& { param($common, $commandName) . $common; Format-SpecKitCommand -CommandName $commandName -RepoRoot (Get-Location).Path }',
            str(script),
            command_name,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


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

    # Keep a numbered branch name in this repo fixture; setup-tasks now resolves
    # feature directories from repository state rather than validating git branches.
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
    _minimal_feature(tasks_repo)
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
    _minimal_feature(tasks_repo)

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
def test_setup_tasks_bash_extension_wins_over_core(tasks_repo: Path) -> None:
    """
    When an extension template exists, setup-tasks.sh --json must resolve
    tasks-template.md from the extension before falling back to the core path.
    """
    _minimal_feature(tasks_repo)

    # FIX: real extension layout is .specify/extensions/<id>/templates/<name>.md
    extension_dir = (
        tasks_repo / ".specify" / "extensions" / "test-extension" / "templates"
    )
    extension_dir.mkdir(parents=True, exist_ok=True)
    extension_file = extension_dir / "tasks-template.md"
    extension_file.write_text("# extension tasks template\n", encoding="utf-8")

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
    assert tasks_tmpl == extension_file.resolve(), (
        f"Expected extension path but got: {tasks_tmpl}"
    )


@requires_bash
def test_setup_tasks_bash_preset_wins_over_extension(tasks_repo: Path) -> None:
    """
    When both preset and extension templates exist, setup-tasks.sh --json must
    resolve the preset path because presets outrank extensions.
    """
    _minimal_feature(tasks_repo)

    # FIX: real extension layout is .specify/extensions/<id>/templates/<name>.md
    extension_dir = (
        tasks_repo / ".specify" / "extensions" / "test-extension" / "templates"
    )
    extension_dir.mkdir(parents=True, exist_ok=True)
    extension_file = extension_dir / "tasks-template.md"
    extension_file.write_text("# extension tasks template\n", encoding="utf-8")

    # FIX: real preset layout is .specify/presets/<id>/templates/<name>.md
    preset_dir = tasks_repo / ".specify" / "presets" / "test-preset" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    preset_file = preset_dir / "tasks-template.md"
    preset_file.write_text("# preset tasks template\n", encoding="utf-8")

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
    assert tasks_tmpl == preset_file.resolve(), (
        f"Expected preset path but got: {tasks_tmpl}"
    )


@requires_bash
def test_setup_tasks_bash_preset_priority_order(tasks_repo: Path) -> None:
    """
    When two presets both provide tasks-template.md, the one listed first in
    .specify/presets/.registry wins.
    """
    _minimal_feature(tasks_repo)

    # resolve_template reads .specify/presets/.registry as a JSON object with a
    # "presets" map where each entry has a numeric "priority" (lower = higher
    # precedence). Create two presets; priority-1-preset wins over priority-2-preset.
    high_priority_dir = (
        tasks_repo / ".specify" / "presets" / "priority-1-preset" / "templates"
    )
    high_priority_dir.mkdir(parents=True, exist_ok=True)
    high_priority_file = high_priority_dir / "tasks-template.md"
    high_priority_file.write_text("# high priority preset tasks template\n", encoding="utf-8")
    low_priority_dir = (
        tasks_repo / ".specify" / "presets" / "priority-2-preset" / "templates"
    )

    low_priority_dir.mkdir(parents=True, exist_ok=True)
    low_priority_file = low_priority_dir / "tasks-template.md"
    low_priority_file.write_text("# low priority preset tasks template\n", encoding="utf-8")

    # Write .registry JSON using the correct schema: object with "presets" map,
    # each preset has a numeric "priority" (lower number = higher precedence).
    registry_json = tasks_repo / ".specify" / "presets" / ".registry"
    registry_json.write_text(
        json.dumps({
            "presets": {
                "priority-1-preset": {"priority": 1, "enabled": True},
                "priority-2-preset": {"priority": 2, "enabled": True},
            }
        }),
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

    data = json.loads(result.stdout)
    tasks_tmpl = Path(data["TASKS_TEMPLATE"])
    assert tasks_tmpl.is_absolute(), "TASKS_TEMPLATE must be an absolute path"
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    assert tasks_tmpl == high_priority_file.resolve(), (
        f"Expected high-priority preset path but got: {tasks_tmpl}"
    )


@requires_bash
def test_setup_tasks_bash_missing_template_errors(tasks_repo: Path) -> None:
    """
    When tasks-template.md is absent from all locations, setup-tasks.sh must
    exit non-zero and print a helpful ERROR message to stderr.
    """
    _minimal_feature(tasks_repo)

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
def test_bash_command_hint_defaults_to_dot_without_integration_json(tasks_repo: Path) -> None:
    integration_json = tasks_repo / ".specify" / "integration.json"
    if integration_json.exists():
        integration_json.unlink()

    result = _run_bash_format_command(tasks_repo, "plan")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.plan"


@requires_bash
def test_bash_command_hint_rejects_invalid_invoke_separator(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "claude", "/")

    result = _run_bash_format_command(tasks_repo, "plan")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.plan"


@requires_bash
def test_bash_command_hint_normalizes_mixed_separators(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "copilot", ".")

    result = _run_bash_format_command(tasks_repo, "/speckit-git.commit")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.git.commit"

    _write_integration_state(tasks_repo, "claude", "-")

    result = _run_bash_format_command(tasks_repo, "speckit.git-commit")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit-git-commit"


@requires_bash
def test_bash_command_hint_preserves_hyphens_inside_segments(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "copilot", ".")

    result = _run_bash_format_command(tasks_repo, "speckit.jira.sync-status")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.jira.sync-status"


def _install_broken_json_tool_stubs(repo: Path) -> Path:
    """Create a bin dir with `jq` and `python3` stubs that exist but fail.

    Mimics stock Windows + Git Bash, where a JSON tool may be missing or broken
    and `python3` resolves to the Microsoft Store App Execution Alias stub: both
    satisfy `command -v` yet fail at runtime (the alias exits 49). Prepending
    this to PATH forces the invoke-separator parser past jq and python3 to its
    awk text fallback (#3304).
    """
    stub_dir = repo / "_broken_bin"
    stub_dir.mkdir(exist_ok=True)
    for name in ("jq", "python3"):
        stub = stub_dir / name
        stub.write_text(
            "#!/bin/sh\n"
            'echo "simulated broken interpreter/tool" >&2\n'
            "exit 49\n",
            encoding="utf-8",
            newline="\n",
        )
        stub.chmod(0o755)
    return stub_dir


@requires_bash
def test_bash_command_hint_falls_back_to_awk_when_jq_and_python3_broken(
    tasks_repo: Path,
) -> None:
    """Separator resolution survives broken jq and python3 stubs (#3304).

    `get_invoke_separator` historically selected python3 by availability and
    had no text fallback, so a Windows Store python3 stub made it silently
    return "." even for `-`-separator integrations (e.g. forge), yielding a
    wrong hint like `/speckit.plan`. The awk fallback must recover `-`.
    """
    _write_integration_state(tasks_repo, "forge", "-")
    stub_dir = _install_broken_json_tool_stubs(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "bash" / "common.sh"
    env = _clean_env()
    env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"

    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; format_speckit_command "$2" "$PWD"',
            "bash",
            str(script),
            "plan",
        ],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit-plan"


@requires_bash
def test_bash_command_hint_caches_invoke_separator_per_process(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    script = tasks_repo / ".specify" / "scripts" / "bash" / "common.sh"
    dot_state = {
        "integration": "copilot",
        "default_integration": "copilot",
        "installed_integrations": ["copilot"],
        "integration_settings": {"copilot": {"invoke_separator": "."}},
    }

    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; format_speckit_command plan "$PWD"; printf "%s" "$2" > .specify/integration.json; format_speckit_command tasks "$PWD"',
            "bash",
            str(script),
            json.dumps(dot_state),
        ],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["/speckit-plan", "/speckit-tasks"]


@requires_bash
def test_setup_tasks_bash_uses_invoke_separator_in_plan_hint(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    feat = tasks_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(tasks_repo)

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
    assert "Run /speckit-plan first" in result.stderr
    assert "/speckit.plan" not in result.stderr


@requires_bash
def test_check_prerequisites_bash_uses_invoke_separator_in_tasks_hint(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    _minimal_feature(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"

    result = subprocess.run(
        ["bash", str(script), "--require-tasks"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode != 0
    assert "Run /speckit-tasks first" in result.stderr
    assert "/speckit.tasks" not in result.stderr


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
    _write_feature_json(tasks_repo)

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
def test_setup_tasks_bash_errors_without_feature_context(
    tasks_repo: Path,
) -> None:
    """Without feature.json or SPECIFY_FEATURE_DIRECTORY, setup-tasks.sh must error."""
    main_feat = tasks_repo / "specs" / "main"
    main_feat.mkdir(parents=True, exist_ok=True)
    (main_feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (main_feat / "plan.md").write_text("# plan\n", encoding="utf-8")

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
    assert "Feature directory not found" in result.stderr

# ===========================================================================
# POWERSHELL TESTS
# ===========================================================================

@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_core_template_resolved(tasks_repo: Path) -> None:
    """
    When the core tasks-template.md is present and all prerequisites are met,
    setup-tasks.ps1 -Json should exit 0 and return an absolute, existing
    TASKS_TEMPLATE path.
    """
    _minimal_feature(tasks_repo)
    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_override_wins(tasks_repo: Path) -> None:
    """
    When an override exists at .specify/templates/overrides/tasks-template.md,
    setup-tasks.ps1 -Json must return the override path, not the core path.
    """
    _minimal_feature(tasks_repo)

    overrides_dir = tasks_repo / ".specify" / "templates" / "overrides"
    overrides_dir.mkdir(parents=True, exist_ok=True)
    override_file = overrides_dir / "tasks-template.md"
    override_file.write_text("# override tasks template\n", encoding="utf-8")

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_missing_template_errors(tasks_repo: Path) -> None:
    """
    When tasks-template.md is absent from all locations, setup-tasks.ps1 must
    exit non-zero and write a helpful error to stderr.
    """
    _minimal_feature(tasks_repo)

    core = tasks_repo / ".specify" / "templates" / "tasks-template.md"
    core.unlink()

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

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


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_powershell_command_hint_normalizes_mixed_separators(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "copilot", ".")

    result = _run_powershell_format_command(tasks_repo, "/speckit-git.commit")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.git.commit"

    _write_integration_state(tasks_repo, "claude", "-")

    result = _run_powershell_format_command(tasks_repo, "speckit.git-commit")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit-git-commit"


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_powershell_command_hint_preserves_hyphens_inside_segments(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "copilot", ".")

    result = _run_powershell_format_command(tasks_repo, "speckit.jira.sync-status")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.jira.sync-status"


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_uses_invoke_separator_in_plan_hint(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    feat = tasks_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    _write_feature_json(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    output = result.stderr + result.stdout
    assert result.returncode != 0
    assert "Run /speckit-plan first" in output
    assert "/speckit.plan" not in output


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_check_prerequisites_ps_uses_invoke_separator_in_tasks_hint(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    _minimal_feature(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-RequireTasks"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    output = result.stderr + result.stdout
    assert result.returncode != 0
    assert "Run /speckit-tasks first" in output
    assert "/speckit.tasks" not in output


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
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
    _write_feature_json(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_errors_without_feature_context(
    tasks_repo: Path,
) -> None:
    """Without feature.json or SPECIFY_FEATURE_DIRECTORY, setup-tasks.ps1 must error."""
    main_feat = tasks_repo / "specs" / "main"
    main_feat.mkdir(parents=True, exist_ok=True)
    (main_feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (main_feat / "plan.md").write_text("# plan\n", encoding="utf-8")

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "setup-tasks.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL

    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(script), "-Json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    output = result.stderr + result.stdout
    assert result.returncode != 0
    assert "Feature directory not found" in output


# ---------------------------------------------------------------------------
# Directory non-emptiness parity: a dir whose only contents are subdirectories
# (e.g. contracts/v1/openapi.yaml) must count as non-empty in both shells.
# ---------------------------------------------------------------------------

def _run_bash_check_dir(repo: Path, target: Path) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "bash" / "common.sh"
    return subprocess.run(
        ["bash", "-c", 'source "$1"; check_dir "$2" "contracts/"', "bash", str(script), str(target)],
        # check_dir echoes the non-ASCII markers ✓/✗; decode UTF-8 explicitly so
        # the result does not depend on the platform locale (e.g. cp1252 on Windows).
        cwd=repo, capture_output=True, text=True, encoding="utf-8", check=False, env=_clean_env(),
    )


def _run_powershell_test_dir(repo: Path, target: Path) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "powershell" / "common.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return subprocess.run(
        [exe, "-NoProfile", "-Command",
         '& { param($common, $dir) . $common; Test-DirHasFiles -Path $dir -Description "contracts/" }',
         str(script), str(target)],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", check=False, env=_clean_env(),
    )


@requires_bash
def test_check_dir_bash_counts_subdir_only_contracts(tasks_repo: Path) -> None:
    """bash check_dir treats a dir containing only subdirectories as non-empty."""
    contracts = tasks_repo / "contracts" / "v1"
    contracts.mkdir(parents=True)
    (contracts / "openapi.yaml").write_text("openapi: 3.0\n", encoding="utf-8")
    result = _run_bash_check_dir(tasks_repo, tasks_repo / "contracts")
    # check_dir always exits 0 (it echoes ✓/✗ instead of setting an exit code),
    # so the ✓ marker in stdout — not the return code — is what proves non-emptiness.
    assert "✓" in result.stdout and "✗" not in result.stdout, result.stderr + result.stdout


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_dir_has_files_ps_counts_subdir_only_contracts(tasks_repo: Path) -> None:
    """Test-DirHasFiles must match bash: a subdir-only dir counts as non-empty."""
    contracts = tasks_repo / "contracts" / "v1"
    contracts.mkdir(parents=True)
    (contracts / "openapi.yaml").write_text("openapi: 3.0\n", encoding="utf-8")
    result = _run_powershell_test_dir(tasks_repo, tasks_repo / "contracts")
    # Test-DirHasFiles returns a boolean and pwsh still exits 0 when it returns
    # $false, so the [OK] marker in stdout — not the return code — is what proves
    # non-emptiness.
    assert "[OK]" in result.stdout and "[FAIL]" not in result.stdout, result.stderr + result.stdout
