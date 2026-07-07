"""
Parity tests for the Python port of the git extension scripts (extensions/git/scripts/python/).

Each test runs the bash script and its Python twin in identical twin projects
and asserts matching output, exit codes, and resulting git state.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.extensions.git.test_git_extension import (
    _GIT_ENV,
    _init_git,
    _run_bash,
    _setup_project,
    _write_config,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_PY = PROJECT_ROOT / "extensions" / "git" / "scripts" / "python"
CORE_COMMON_PY = PROJECT_ROOT / "scripts" / "python" / "common.py"

PY_SCRIPTS = {
    "create-new-feature-branch": "create_new_feature_branch.py",
    "initialize-repo": "initialize_repo.py",
    "auto-commit": "auto_commit.py",
}


def _setup_py_project(tmp_path: Path, *, git: bool = True) -> Path:
    """Twin of _setup_project that also installs the Python scripts."""
    project = _setup_project(tmp_path, git=git)

    py_core = project / "scripts" / "python"
    py_core.mkdir(parents=True, exist_ok=True)
    shutil.copy(CORE_COMMON_PY, py_core / "common.py")

    ext_py = project / ".specify" / "extensions" / "git" / "scripts" / "python"
    ext_py.mkdir(parents=True, exist_ok=True)
    for f in EXT_PY.iterdir():
        if f.suffix == ".py":
            shutil.copy(f, ext_py / f.name)
    return project


def _run_py(script_name: str, cwd: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run an extension Python script."""
    script = (
        cwd / ".specify" / "extensions" / "git" / "scripts" / "python" / PY_SCRIPTS[script_name]
    )
    env = {**os.environ, **_GIT_ENV, **(env_extra or {})}
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _twin_projects(tmp_path: Path, *, git: bool = True) -> tuple[Path, Path]:
    """Two identically named projects so {app} tokens match."""
    bash_proj = _setup_py_project(tmp_path / "bash" / "proj", git=git)
    py_proj = _setup_py_project(tmp_path / "py" / "proj", git=git)
    return bash_proj, py_proj


def _assert_parity(
    bash_result: subprocess.CompletedProcess,
    py_result: subprocess.CompletedProcess,
    *,
    stdout: bool = True,
) -> None:
    assert py_result.returncode == bash_result.returncode, (
        f"exit codes diverge: bash={bash_result.returncode} py={py_result.returncode}\n"
        f"bash stderr: {bash_result.stderr}\npy stderr: {py_result.stderr}"
    )
    if stdout:
        assert py_result.stdout == bash_result.stdout


@requires_bash
class TestCreateFeatureBranchParity:
    def test_sequential_branch_json(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "Add user authentication")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "Add user authentication")
        _assert_parity(b, p)
        data = json.loads(p.stdout)
        assert data == {"BRANCH_NAME": "001-user-authentication", "FEATURE_NUM": "001"}
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=py_proj,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert branch == "001-user-authentication"

    def test_slug_generation_stop_words_and_acronyms(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        description = "I want to add DB caching for the API layer"
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", description)
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", description)
        _assert_parity(b, p)

    def test_short_name_cleaning(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        # Single separator runs only: the bash twin's collapse step
        # (sed 's/-\+/-/g') is a GNU-ism that BSD sed treats literally.
        b = _run_bash(
            "create-new-feature-branch.sh", bash_proj,
            "--json", "--dry-run", "--short-name", "User_Auth!", "desc",
        )
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "--dry-run", "--short-name", "User_Auth!", "desc",
        )
        _assert_parity(b, p)
        assert json.loads(p.stdout)["BRANCH_NAME"] == "001-user-auth"

    def test_numbering_from_specs_and_branches(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            (proj / "specs" / "007-existing").mkdir(parents=True)
            (proj / "specs" / "20260101-120000-timestamped").mkdir(parents=True)
            subprocess.run(["git", "branch", "012-in-branch"], cwd=proj, check=True)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", "next feature")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", "next feature")
        _assert_parity(b, p)
        assert json.loads(p.stdout)["FEATURE_NUM"] == "013"

    def test_explicit_number(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--number", "42", "some feature")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--number", "42", "some feature")
        _assert_parity(b, p)
        assert json.loads(p.stdout)["FEATURE_NUM"] == "042"

    def test_timestamp_mode_format(self, tmp_path: Path):
        _, py_proj = _twin_projects(tmp_path)
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "--timestamp", "--short-name", "user-auth", "desc",
        )
        assert p.returncode == 0
        data = json.loads(p.stdout)
        assert re.fullmatch(r"[0-9]{8}-[0-9]{6}", data["FEATURE_NUM"])
        assert data["BRANCH_NAME"] == f"{data['FEATURE_NUM']}-user-auth"

    def test_timestamp_with_number_warns(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash(
            "create-new-feature-branch.sh", bash_proj,
            "--json", "--dry-run", "--timestamp", "--number", "5", "desc word",
        )
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "--dry-run", "--timestamp", "--number", "5", "desc word",
        )
        assert p.returncode == b.returncode == 0
        warning = "[specify] Warning: --number is ignored when --timestamp is used"
        assert warning in b.stderr
        assert warning in p.stderr

    def test_branch_template_author_app(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, 'branch_template: "{author}/{app}/{number}-{slug}"\n')
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", "new payment flow")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", "new payment flow")
        _assert_parity(b, p)
        assert json.loads(p.stdout)["BRANCH_NAME"] == "test-user/proj/001-new-payment-flow"

    def test_branch_prefix_shorthand(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, "branch_prefix: feat\n")
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", "new payment flow")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", "new payment flow")
        _assert_parity(b, p)
        assert json.loads(p.stdout)["BRANCH_NAME"] == "feat/001-new-payment-flow"

    def test_template_scopes_existing_branch_numbers(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, 'branch_template: "{author}/{number}-{slug}"\n')
            subprocess.run(["git", "branch", "test-user/008-scoped"], cwd=proj, check=True)
            subprocess.run(["git", "branch", "other-user/030-unscoped"], cwd=proj, check=True)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", "next thing")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", "next thing")
        _assert_parity(b, p)
        assert json.loads(p.stdout)["FEATURE_NUM"] == "009"

    @pytest.mark.parametrize(
        "template",
        [
            'branch_template: "feat/{slug}"\n',
            'branch_template: "{slug}/{number}-x"\n',
            'branch_template: "{number}/{slug}-x"\n',
        ],
    )
    def test_invalid_template_rejected(self, tmp_path: Path, template: str):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, template)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "--dry-run", "desc word")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "--dry-run", "desc word")
        assert b.returncode == p.returncode == 1
        assert p.stderr.strip() == b.stderr.strip()

    def test_git_branch_name_override(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        env = {"GIT_BRANCH_NAME": "team/042-exact-name"}
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "desc word", env_extra=env)
        p = _run_py("create-new-feature-branch", py_proj, "--json", "desc word", env_extra=env)
        _assert_parity(b, p)
        assert json.loads(p.stdout) == {"BRANCH_NAME": "team/042-exact-name", "FEATURE_NUM": "042"}

    def test_long_branch_name_truncated_to_244_bytes(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        long_name = "-".join(["word"] * 60)
        b = _run_bash(
            "create-new-feature-branch.sh", bash_proj,
            "--json", "--dry-run", "--short-name", long_name, "desc",
        )
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "--dry-run", "--short-name", long_name, "desc",
        )
        _assert_parity(b, p)
        assert len(json.loads(p.stdout)["BRANCH_NAME"].encode()) <= 244

    def test_existing_branch_errors_without_flag(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            subprocess.run(["git", "branch", "001-user-auth"], cwd=proj, check=True)
        args = ("--json", "--number", "1", "--short-name", "user-auth", "desc")
        b = _run_bash("create-new-feature-branch.sh", bash_proj, *args)
        p = _run_py("create-new-feature-branch", py_proj, *args)
        assert b.returncode == p.returncode == 1
        assert p.stderr.strip() == b.stderr.strip()

    def test_existing_branch_switches_with_allow_flag(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            subprocess.run(["git", "branch", "001-user-auth"], cwd=proj, check=True)
        args = ("--json", "--number", "1", "--short-name", "user-auth", "--allow-existing-branch", "desc")
        b = _run_bash("create-new-feature-branch.sh", bash_proj, *args)
        p = _run_py("create-new-feature-branch", py_proj, *args)
        _assert_parity(b, p)
        for proj in (bash_proj, py_proj):
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=proj,
                capture_output=True,
                text=True,
            ).stdout.strip()
            assert branch == "001-user-auth"

    def test_no_git_graceful_degradation(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path, git=False)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "offline feature")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "offline feature")
        _assert_parity(b, p)
        assert "skipped branch creation" in p.stderr

    def test_empty_description_errors(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash("create-new-feature-branch.sh", bash_proj, "--json", "   ")
        p = _run_py("create-new-feature-branch", py_proj, "--json", "   ")
        assert b.returncode == p.returncode == 1
        assert p.stderr.strip() == b.stderr.strip()
        assert "cannot be empty or contain only whitespace" in p.stderr

    def test_specify_init_dir_resolves_target_project(self, tmp_path: Path):
        _, py_proj = _twin_projects(tmp_path)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "--dry-run", "init dir feature",
            env_extra={"SPECIFY_INIT_DIR": str(py_proj)},
        )
        assert p.returncode == 0
        assert json.loads(p.stdout)["FEATURE_NUM"] == "001"

    def test_specify_init_dir_without_core_errors(self, tmp_path: Path):
        _, py_proj = _twin_projects(tmp_path)
        (py_proj / "scripts" / "python" / "common.py").unlink()
        p = _run_py(
            "create-new-feature-branch", py_proj,
            "--json", "desc word",
            env_extra={"SPECIFY_INIT_DIR": str(py_proj)},
        )
        assert p.returncode == 1
        assert "SPECIFY_INIT_DIR requires updated Spec Kit core scripts" in p.stderr


@requires_bash
class TestInitializeRepoParity:
    def test_initializes_repo_with_default_message(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path, git=False)
        b = _run_bash("initialize-repo.sh", bash_proj)
        p = _run_py("initialize-repo", py_proj)
        _assert_parity(b, p)
        assert p.stderr.strip() == b.stderr.strip()
        for proj in (bash_proj, py_proj):
            message = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=proj,
                capture_output=True,
                text=True,
            ).stdout.strip()
            assert message == "[Spec Kit] Initial commit"

    def test_custom_commit_message(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path, git=False)
        for proj in (bash_proj, py_proj):
            _write_config(proj, 'init_commit_message: "Custom initial commit"\n')
        b = _run_bash("initialize-repo.sh", bash_proj)
        p = _run_py("initialize-repo", py_proj)
        _assert_parity(b, p)
        for proj in (bash_proj, py_proj):
            message = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=proj,
                capture_output=True,
                text=True,
            ).stdout.strip()
            assert message == "Custom initial commit"

    def test_skips_existing_repo(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash("initialize-repo.sh", bash_proj)
        p = _run_py("initialize-repo", py_proj)
        _assert_parity(b, p)
        assert p.stderr.strip() == b.stderr.strip()
        assert "already initialized" in p.stderr


@requires_bash
class TestAutoCommitParity:
    def _dirty(self, proj: Path) -> None:
        (proj / "change.txt").write_text("dirty\n", encoding="utf-8")

    def _last_message(self, proj: Path) -> str:
        return subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=proj,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_disabled_by_default(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, "auto_commit:\n  after_specify:\n    enabled: false\n")
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert self._last_message(py_proj) == "seed"

    def test_enabled_per_command_with_custom_message(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        config = (
            "auto_commit:\n"
            "  default: false\n"
            "  after_specify:\n"
            "    enabled: true\n"
            '    message: "spec done"\n'
        )
        for proj in (bash_proj, py_proj):
            _write_config(proj, config)
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert p.stderr.strip() == b.stderr.strip()
        assert self._last_message(bash_proj) == self._last_message(py_proj) == "spec done"

    def test_default_true_applies_to_unlisted_event(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, "auto_commit:\n  default: true\n")
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "after_plan")
        p = _run_py("auto-commit", py_proj, "after_plan")
        _assert_parity(b, p)
        expected = "[Spec Kit] Auto-commit after plan"
        assert self._last_message(bash_proj) == self._last_message(py_proj) == expected

    def test_explicit_false_beats_default_true(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        config = "auto_commit:\n  default: true\n  after_specify:\n    enabled: false\n"
        for proj in (bash_proj, py_proj):
            _write_config(proj, config)
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert self._last_message(py_proj) == "seed"

    def test_before_event_message(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, "auto_commit:\n  before_plan:\n    enabled: true\n")
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "before_plan")
        p = _run_py("auto-commit", py_proj, "before_plan")
        _assert_parity(b, p)
        expected = "[Spec Kit] Auto-commit before plan"
        assert self._last_message(bash_proj) == self._last_message(py_proj) == expected

    def test_no_changes_skips(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            _write_config(proj, "auto_commit:\n  after_specify:\n    enabled: true\n")
            subprocess.run(["git", "add", "-A"], cwd=proj, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "clean"],
                cwd=proj,
                check=True,
                env={**os.environ, **_GIT_ENV},
            )
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert p.stderr.strip() == b.stderr.strip()
        assert "No changes to commit" in p.stderr

    def test_no_config_file_skips(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        for proj in (bash_proj, py_proj):
            self._dirty(proj)
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert self._last_message(py_proj) == "seed"

    def test_missing_event_argument_errors(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path)
        b = _run_bash("auto-commit.sh", bash_proj)
        p = _run_py("auto-commit", py_proj)
        assert b.returncode == p.returncode == 1

    def test_not_a_repo_skips(self, tmp_path: Path):
        bash_proj, py_proj = _twin_projects(tmp_path, git=False)
        b = _run_bash("auto-commit.sh", bash_proj, "after_specify")
        p = _run_py("auto-commit", py_proj, "after_specify")
        _assert_parity(b, p)
        assert "Not a Git repository" in p.stderr


class TestGitCommonPython:
    """Unit tests for git_common.py (imported directly)."""

    @pytest.fixture()
    def git_common(self):
        sys.path.insert(0, str(EXT_PY))
        try:
            import git_common

            yield git_common
        finally:
            sys.path.remove(str(EXT_PY))
            sys.modules.pop("git_common", None)

    def test_has_git(self, git_common, tmp_path: Path):
        assert git_common.has_git(tmp_path) is False
        _init_git(tmp_path)
        assert git_common.has_git(tmp_path) is True

    @pytest.mark.parametrize(
        ("branch", "expected"),
        [
            ("001-feature-name", True),
            ("1234-feature-name", True),
            ("20260319-143022-feature-name", True),
            ("feat/004-name", True),
            ("main", False),
            ("2026031-143022", False),
            ("20260319-143022", False),
            ("2026031-143022-slug", False),
        ],
    )
    def test_check_feature_branch(self, git_common, branch: str, expected: bool, capsys):
        assert git_common.check_feature_branch(branch, True) is expected

    def test_check_feature_branch_no_git_warns_but_passes(self, git_common, capsys):
        assert git_common.check_feature_branch("main", False) is True
        assert "skipped branch validation" in capsys.readouterr().err
