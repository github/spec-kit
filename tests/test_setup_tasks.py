"""Tests for setup-tasks.{sh,ps1} template resolution and branch validation."""
 
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
 
import pytest
 
from tests.conftest import requires_bash
from tests._path_utils import assert_normalized_path_equal, bash_path_from_host, path_from_bash_output
 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
SETUP_TASKS_SH = PROJECT_ROOT / "scripts" / "bash" / "setup-tasks.sh"
CHECK_PREREQ_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
SETUP_TASKS_PS = PROJECT_ROOT / "scripts" / "powershell" / "setup-tasks.ps1"
CHECK_PREREQ_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"
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
    rely purely on git branch + feature.json state set up by each fixture.
    """
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _is_shell_absolute(path_value: str) -> bool:
    return Path(path_value).is_absolute() or path_value.startswith("/")


def _assert_tasks_template_matches(tasks_tmpl_raw: str, expected_path: Path) -> None:
    assert _is_shell_absolute(tasks_tmpl_raw), "TASKS_TEMPLATE must be an absolute path"
    expected = expected_path.resolve()
    if os.name == "nt":
        tasks_tmpl = path_from_bash_output(tasks_tmpl_raw)
        assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
        assert_normalized_path_equal(tasks_tmpl_raw, expected)
        return
    tasks_tmpl = Path(tasks_tmpl_raw)
    assert tasks_tmpl.is_file(), "TASKS_TEMPLATE must point to an existing file"
    assert tasks_tmpl.resolve() == expected, f"Expected {expected} but got: {tasks_tmpl}"


def _run_bash_template_resolver(
    repo: Path,
    resolver_fn: str,
    path_override: str | None = None,
    *,
    replace_path_override: bool = False,
) -> subprocess.CompletedProcess:
    script = repo / ".specify" / "scripts" / "bash" / "common.sh"
    cmd = 'source "$1"; '
    if path_override is not None:
        if replace_path_override:
            cmd += 'export PATH="$2"; '
        else:
            cmd += 'export PATH="$2:$PATH"; '
    cmd += f'{resolver_fn} tasks-template "$PWD"'
    argv = ["bash", "-c", cmd, "bash", str(script)]
    if path_override is not None:
        argv.append(path_override)
    return subprocess.run(
        argv,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=_clean_env(),
    )


def _run_bash_resolve_template(
    repo: Path,
    path_override: str | None = None,
    *,
    replace_path_override: bool = False,
) -> subprocess.CompletedProcess:
    return _run_bash_template_resolver(
        repo,
        "resolve_template",
        path_override,
        replace_path_override=replace_path_override,
    )


def _run_bash_resolve_template_content(
    repo: Path,
    path_override: str | None = None,
    *,
    replace_path_override: bool = False,
) -> subprocess.CompletedProcess:
    return _run_bash_template_resolver(
        repo,
        "resolve_template_content",
        path_override,
        replace_path_override=replace_path_override,
    )


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
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
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
    _assert_tasks_template_matches(
        data["TASKS_TEMPLATE"],
        tasks_repo / ".specify" / "templates" / "tasks-template.md",
    )
 
 
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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], override_file)
 
 
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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], extension_file)
 
 
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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], preset_file)
 
 
@requires_bash
def test_setup_tasks_bash_preset_priority_order(tasks_repo: Path) -> None:
    """
    When two presets both provide tasks-template.md, the one listed first in
    .specify/presets/.registry wins.
    """
    _minimal_feature(tasks_repo)
 
    # resolve_template reads .specify/presets/.registry as a JSON object with a
    # "presets" map where each entry has a numeric "priority" (lower = higher
    # precedence). Use explicit registry priorities instead of inferring from
    # preset IDs so the contract is unambiguous on all platforms.
    low_priority_dir = (
        tasks_repo / ".specify" / "presets" / "priority-2-preset" / "templates"
    )

    low_priority_dir.mkdir(parents=True, exist_ok=True)
    low_priority_file = low_priority_dir / "tasks-template.md"
    low_priority_file.write_text("# low priority preset tasks template\n", encoding="utf-8")

    high_priority_dir = (
        tasks_repo / ".specify" / "presets" / "priority-1-preset" / "templates"
    )
    high_priority_dir.mkdir(parents=True, exist_ok=True)
    high_priority_file = high_priority_dir / "tasks-template.md"
    high_priority_file.write_text("# high priority preset tasks template\n", encoding="utf-8")

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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], high_priority_file)


@requires_bash
def test_setup_tasks_bash_preset_priority_tie_breaks_by_id(tasks_repo: Path) -> None:
    """When priorities tie, lower preset id should win deterministically."""
    _minimal_feature(tasks_repo)

    alpha_dir = tasks_repo / ".specify" / "presets" / "alpha-preset" / "templates"
    zulu_dir = tasks_repo / ".specify" / "presets" / "zulu-preset" / "templates"
    alpha_dir.mkdir(parents=True, exist_ok=True)
    zulu_dir.mkdir(parents=True, exist_ok=True)

    alpha_file = alpha_dir / "tasks-template.md"
    zulu_file = zulu_dir / "tasks-template.md"
    alpha_file.write_text("# alpha preset tasks template\n", encoding="utf-8")
    zulu_file.write_text("# zulu preset tasks template\n", encoding="utf-8")

    registry_json = tasks_repo / ".specify" / "presets" / ".registry"
    # Intentionally place zulu first to verify tie-break is id-based, not insertion-order.
    registry_json.write_text(
        json.dumps({
            "presets": {
                "zulu-preset": {"priority": 1, "enabled": True},
                "alpha-preset": {"priority": 1, "enabled": True},
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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], alpha_file)


@requires_bash
def test_setup_tasks_bash_preset_priority_coerces_mixed_types(tasks_repo: Path) -> None:
    """Mixed-type priority values should still produce deterministic registry ordering."""
    _minimal_feature(tasks_repo)

    alpha_dir = tasks_repo / ".specify" / "presets" / "alpha-mixed" / "templates"
    zulu_dir = tasks_repo / ".specify" / "presets" / "zulu-mixed" / "templates"
    alpha_dir.mkdir(parents=True, exist_ok=True)
    zulu_dir.mkdir(parents=True, exist_ok=True)

    alpha_file = alpha_dir / "tasks-template.md"
    zulu_file = zulu_dir / "tasks-template.md"
    alpha_file.write_text("# alpha mixed\n", encoding="utf-8")
    zulu_file.write_text("# zulu mixed\n", encoding="utf-8")

    (tasks_repo / ".specify" / "presets" / ".registry").write_text(
        json.dumps(
            {
                "presets": {
                    "alpha-mixed": {"priority": "20", "enabled": True},
                    "zulu-mixed": {"priority": 1, "enabled": True},
                }
            }
        ),
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
    _assert_tasks_template_matches(data["TASKS_TEMPLATE"], zulu_file)


@requires_bash
def test_resolve_template_allows_benign_double_dot_preset_ids(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "v1..0" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# benign dots\n", encoding="utf-8")

    (presets_root / ".registry").write_text(
        json.dumps({"presets": {"v1..0": {"priority": 1, "enabled": True}}}),
        encoding="utf-8",
    )

    result = _run_bash_resolve_template(tasks_repo)
    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), preset_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_ignores_unsafe_registry_preset_ids(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    safe_dir = presets_root / "safe-preset" / "templates"
    safe_dir.mkdir(parents=True, exist_ok=True)
    (safe_dir / "tasks-template.md").write_text("# safe preset\n", encoding="utf-8")

    outside_dir = tasks_repo / ".specify" / "escaped" / "templates"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "tasks-template.md").write_text("# escaped preset\n", encoding="utf-8")

    (presets_root / ".registry").write_text(
        json.dumps({
            "presets": {
                "../escaped": {"priority": 0, "enabled": True},
                "safe-preset": {"priority": 1, "enabled": True},
            }
        }),
        encoding="utf-8",
    )

    result = _run_bash_resolve_template(tasks_repo)
    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), safe_dir / "tasks-template.md")
 
 
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

    script = tasks_repo / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

    env = _clean_env()
    if os.name == "nt":
        shim_dir = tasks_repo / ".specify" / "shim-bin"
        shim_dir.mkdir(parents=True, exist_ok=True)
        python3_shim = shim_dir / "python3"
        python_exe = sys.executable.replace("\\", "/")
        python3_shim.write_text(
            f"#!/usr/bin/env bash\n\"{python_exe}\" \"$@\"\n",
            encoding="utf-8",
            newline="\n",
        )
        python3_shim.chmod(0o755)
        shim_dir_posix = bash_path_from_host(shim_dir)
        # Keep inherited PATH bytes unchanged; rewriting Windows PATH delimiters
        # can corrupt drive-letter entries under Git Bash.
        inherited_path = env.get("PATH", "")
        env["PATH"] = f"{shim_dir_posix}:{inherited_path}" if inherited_path else shim_dir_posix

    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
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
def test_resolve_template_uses_python_when_python3_missing(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "py-fallback" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# py fallback\n", encoding="utf-8")
    (presets_root / ".registry").write_text(json.dumps({"presets": {"py-fallback": {"priority": 1}}}), encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-fallback-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    python_shim = shim_dir / "python"
    python_shim.write_text(
        "#!/bin/sh\n"
        "[ \"$1\" = \"-c\" ] || exit 10\n"
        "if [ -n \"$SPECKIT_REGISTRY\" ]; then\n"
        "  [ -f \"$SPECKIT_REGISTRY\" ] || exit 12\n"
        "  printf 'py-fallback\\n'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
        newline="\n",
    )
    python_shim.chmod(0o755)

    result = _run_bash_resolve_template(
        tasks_repo,
        bash_path_from_host(shim_dir),
        replace_path_override=True,
    )

    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), preset_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_skips_python_when_python_is_not_py3(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "py2-fallback" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# py2 fallback\n", encoding="utf-8")
    (presets_root / ".registry").write_text(json.dumps({"presets": {"py2-fallback": {"priority": 1}}}), encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-py2-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)

    python3_shim = shim_dir / "python3"
    python3_shim.write_text(
        "#!/bin/sh\n"
        "[ \"$1\" = \"-c\" ] || exit 1\n"
        "exit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    python3_shim.chmod(0o755)

    python_shim = shim_dir / "python"
    python_shim.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ]; then\n"
        "  if [ -n \"$SPECKIT_REGISTRY\" ]; then\n"
        "    exit 1\n"
        "  fi\n"
        "  exit 1\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    python_shim.chmod(0o755)

    result = _run_bash_resolve_template(
        tasks_repo,
        f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin",
        replace_path_override=True,
    )

    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), preset_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_trims_crlf_preset_ids(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "crlf-preset" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# crlf\n", encoding="utf-8")
    (presets_root / ".registry").write_text(json.dumps({"presets": {"crlf-preset": {"priority": 1}}}), encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-crlf-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    python3_shim = shim_dir / "python3"
    python3_shim.write_text("#!/usr/bin/env bash\nprintf 'crlf-preset\\r\\n'\n", encoding="utf-8", newline="\n")
    python3_shim.chmod(0o755)

    result = _run_bash_resolve_template(tasks_repo, f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin")

    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), preset_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_content_trims_crlf_preset_ids(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "crlf-content" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    expected_content = "# crlf content\n"
    (preset_dir / "tasks-template.md").write_text(expected_content, encoding="utf-8")
    (presets_root / ".registry").write_text(json.dumps({"presets": {"crlf-content": {"priority": 1}}}), encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-crlf-content-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    python3_shim = shim_dir / "python3"
    python3_shim.write_text("#!/usr/bin/env bash\nprintf 'crlf-content\r\n'\n", encoding="utf-8", newline="\n")
    python3_shim.chmod(0o755)

    result = _run_bash_resolve_template_content(tasks_repo, f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin")

    assert result.returncode == 0, result.stderr
    assert result.stdout == expected_content


@requires_bash
def test_resolve_template_uses_python_when_python3_is_not_py3(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "python3-stub-fallback" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# python fallback\n", encoding="utf-8")
    (presets_root / ".registry").write_text(
        json.dumps({"presets": {"python3-stub-fallback": {"priority": 1}}}),
        encoding="utf-8",
    )

    shim_dir = tasks_repo / ".specify" / "python3-stub-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)

    python3_shim = shim_dir / "python3"
    python3_shim.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ]; then\n"
        "  exit 1\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    python3_shim.chmod(0o755)

    python_shim = shim_dir / "python"
    python_shim.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ]; then\n"
        "  if [ -n \"$SPECKIT_REGISTRY\" ]; then\n"
        "    printf 'python3-stub-fallback\\n'\n"
        "    exit 0\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    python_shim.chmod(0o755)

    result = _run_bash_resolve_template(
        tasks_repo,
        bash_path_from_host(shim_dir),
        replace_path_override=True,
    )

    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), preset_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_python_probe_is_cached_across_resolver_calls(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "cache-probe" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    (preset_dir / "tasks-template.md").write_text("# cache probe\n", encoding="utf-8")
    (presets_root / ".registry").write_text(
        json.dumps({"presets": {"cache-probe": {"priority": 1}}}),
        encoding="utf-8",
    )

    shim_dir = tasks_repo / ".specify" / "python-cache-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    python3_shim = shim_dir / "python3"
    python3_shim.write_text(
        "#!/usr/bin/env bash\n"
        "counter=\"${SPECKIT_COUNTER_FILE:?}\"\n"
        "kind=parse\n"
        "if [[ \"$2\" == *\"sys.version_info\"* ]]; then\n"
        "  kind=probe\n"
        "fi\n"
        "printf '%s\\n' \"$kind\" >> \"$counter\"\n"
        "if [[ -n \"${SPECKIT_REGISTRY:-}\" ]]; then\n"
        "  printf 'cache-probe\\n'\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
        newline="\n",
    )
    python3_shim.chmod(0o755)

    counter_file = tasks_repo / ".specify" / "python-call-kinds.log"
    script = tasks_repo / ".specify" / "scripts" / "bash" / "common.sh"
    path_override = f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin"
    counter_file_arg = bash_path_from_host(counter_file)

    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; export PATH="$2"; export SPECKIT_COUNTER_FILE="$3"; '
            'resolve_template tasks-template "$PWD" >/dev/null; '
            'resolve_template_content tasks-template "$PWD" >/dev/null',
            "bash",
            str(script),
            path_override,
            counter_file_arg,
        ],
        cwd=tasks_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr
    kinds = [line.strip() for line in counter_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert kinds.count("probe") == 1
    assert kinds.count("parse") == 2


@requires_bash
def test_resolve_template_fallback_scan_is_deterministic_when_python_fails(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    a_dir = presets_root / "a-preset" / "templates"
    b_dir = presets_root / "b-preset" / "templates"
    a_dir.mkdir(parents=True, exist_ok=True)
    b_dir.mkdir(parents=True, exist_ok=True)
    (a_dir / "tasks-template.md").write_text("# a\n", encoding="utf-8")
    (b_dir / "tasks-template.md").write_text("# b\n", encoding="utf-8")
    (presets_root / ".registry").write_text("{invalid json", encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-fail-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    fail_script = "#!/usr/bin/env bash\nexit 1\n"
    (shim_dir / "python3").write_text(fail_script, encoding="utf-8", newline="\n")
    (shim_dir / "python").write_text(fail_script, encoding="utf-8", newline="\n")
    (shim_dir / "python3").chmod(0o755)
    (shim_dir / "python").chmod(0o755)

    path_override = f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin"
    result = _run_bash_resolve_template(tasks_repo, path_override)

    assert result.returncode == 0, result.stderr
    _assert_tasks_template_matches(result.stdout.strip(), a_dir / "tasks-template.md")


@requires_bash
def test_resolve_template_content_fallback_scan_is_deterministic_when_python_fails(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    a_dir = presets_root / "a-content" / "templates"
    b_dir = presets_root / "b-content" / "templates"
    a_dir.mkdir(parents=True, exist_ok=True)
    b_dir.mkdir(parents=True, exist_ok=True)
    a_content = "# a content\n"
    b_content = "# b content\n"
    (a_dir / "tasks-template.md").write_text(a_content, encoding="utf-8")
    (b_dir / "tasks-template.md").write_text(b_content, encoding="utf-8")
    (presets_root / ".registry").write_text("{invalid json", encoding="utf-8")

    shim_dir = tasks_repo / ".specify" / "python-fail-content-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    fail_script = "#!/usr/bin/env bash\nexit 1\n"
    (shim_dir / "python3").write_text(fail_script, encoding="utf-8", newline="\n")
    (shim_dir / "python").write_text(fail_script, encoding="utf-8", newline="\n")
    (shim_dir / "python3").chmod(0o755)
    (shim_dir / "python").chmod(0o755)

    path_override = f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin"
    result = _run_bash_resolve_template_content(tasks_repo, path_override)

    assert result.returncode == 0, result.stderr
    assert result.stdout == a_content


@requires_bash
def test_resolve_template_content_uses_cached_python_fallback_for_manifest_parse(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"
    preset_dir = presets_root / "manifest-python-fallback" / "templates"
    preset_dir.mkdir(parents=True, exist_ok=True)
    fallback_content = "Fallback preset content\n"
    (preset_dir / "tasks-template.md").write_text(fallback_content, encoding="utf-8")

    overlay_path = presets_root / "manifest-python-fallback" / "overlay.md"
    overlay_content = "Overlay content\n"
    overlay_path.write_text(overlay_content, encoding="utf-8")

    manifest_path = presets_root / "manifest-python-fallback" / "preset.yml"
    manifest_path.write_text(
        "provides:\n"
        "  templates:\n"
        "    - name: tasks-template\n"
        "      type: template\n"
        "      strategy: append\n"
        "      file: overlay.md\n",
        encoding="utf-8",
    )

    (presets_root / ".registry").write_text(
        json.dumps({"presets": {"manifest-python-fallback": {"priority": 1, "enabled": True}}}),
        encoding="utf-8",
    )

    shim_dir = tasks_repo / ".specify" / "python-manifest-fallback-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    python_shim = shim_dir / "python"
    python_shim.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$2\" == *\"sys.version_info\"* ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [[ -n \"${SPECKIT_REGISTRY:-}\" ]]; then\n"
        "  printf 'manifest-python-fallback\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [[ -n \"${SPECKIT_MANIFEST:-}\" ]]; then\n"
        "  printf 'append\\toverlay.md\\n'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    python_shim.chmod(0o755)

    result = _run_bash_resolve_template_content(
        tasks_repo,
        f"{bash_path_from_host(shim_dir)}:/usr/bin:/bin",
        replace_path_override=True,
    )

    assert result.returncode == 0, result.stderr
    output = (result.stdout or "")
    assert overlay_content.strip() in output
    assert fallback_content not in output


@requires_bash
def test_resolve_template_content_ignores_unsafe_registry_preset_ids(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"

    safe_dir = presets_root / "safe-content" / "templates"
    safe_dir.mkdir(parents=True, exist_ok=True)
    safe_content = "Safe content layer\n"
    (safe_dir / "tasks-template.md").write_text(safe_content, encoding="utf-8")

    escaped_dir = tasks_repo / ".specify" / "escaped-content" / "templates"
    escaped_dir.mkdir(parents=True, exist_ok=True)
    escaped_content = "Escaped content layer\n"
    (escaped_dir / "tasks-template.md").write_text(escaped_content, encoding="utf-8")

    (presets_root / ".registry").write_text(
        json.dumps({
            "presets": {
                "../escaped-content": {"priority": 0, "enabled": True},
                "safe-content": {"priority": 1, "enabled": True},
            }
        }),
        encoding="utf-8",
    )

    result = _run_bash_resolve_template_content(tasks_repo)
    assert result.returncode == 0, result.stderr
    output = result.stdout or ""
    assert safe_content.strip() in output
    assert escaped_content.strip() not in output


@requires_bash
def test_resolve_template_content_does_not_leak_manifest_state_between_presets(tasks_repo: Path) -> None:
    presets_root = tasks_repo / ".specify" / "presets"

    first_preset = presets_root / "first-preset"
    second_preset = presets_root / "second-preset"
    (first_preset / "templates").mkdir(parents=True, exist_ok=True)
    (second_preset / "templates").mkdir(parents=True, exist_ok=True)

    first_overlay = first_preset / "overlay.md"
    first_overlay_content = "First overlay content\n"
    first_overlay.write_text(first_overlay_content, encoding="utf-8")

    (first_preset / "preset.yml").write_text(
        "provides:\n"
        "  templates:\n"
        "    - name: tasks-template\n"
        "      type: template\n"
        "      strategy: append\n"
        "      file: overlay.md\n",
        encoding="utf-8",
    )

    second_template = second_preset / "templates" / "tasks-template.md"
    second_content = "Second base content\n"
    second_template.write_text(second_content, encoding="utf-8")

    (presets_root / ".registry").write_text(
        json.dumps(
            {
                "presets": {
                    "first-preset": {"priority": 1, "enabled": True},
                    "second-preset": {"priority": 2, "enabled": True},
                }
            }
        ),
        encoding="utf-8",
    )

    result = _run_bash_resolve_template_content(tasks_repo)

    assert result.returncode == 0, result.stderr
    output = result.stdout or ""
    assert second_content.strip() in output
    assert first_overlay_content.strip() in output
    assert "Task list template for feature implementation" not in output


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
    _minimal_feature(tasks_repo)
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
    _minimal_feature(tasks_repo)
 
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
    _minimal_feature(tasks_repo)
 
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


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_powershell_command_hint_preserves_hyphens_inside_segments(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "copilot", ".")

    result = _run_powershell_format_command(tasks_repo, "speckit.jira.sync-status")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/speckit.jira.sync-status"


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_tasks_ps_uses_invoke_separator_in_plan_hint(tasks_repo: Path) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    feat = tasks_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")

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

    output = result.stderr + result.stdout
    assert result.returncode != 0
    assert "Run /speckit-plan first" in output
    assert "/speckit.plan" not in output


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_check_prerequisites_ps_uses_invoke_separator_in_tasks_hint(
    tasks_repo: Path,
) -> None:
    _write_integration_state(tasks_repo, "claude", "-")
    _minimal_feature(tasks_repo)

    script = tasks_repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL

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
