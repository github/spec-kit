"""
Pytest tests for timestamp-based branch naming in create-new-feature.sh and common.sh.

Converted from tests/test_timestamp_branches.sh so they are discovered by `uv run pytest`.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREATE_FEATURE = PROJECT_ROOT / "scripts" / "bash" / "create-new-feature.sh"
CREATE_FEATURE_PS = PROJECT_ROOT / "scripts" / "powershell" / "create-new-feature.ps1"
EXT_CREATE_FEATURE = (
    PROJECT_ROOT / "extensions" / "git" / "scripts" / "bash" / "create-new-feature.sh"
)
EXT_CREATE_FEATURE_PS = (
    PROJECT_ROOT / "extensions" / "git" / "scripts" / "powershell" / "create-new-feature.ps1"
)
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
EXT_CREATE_FEATURE = PROJECT_ROOT / "extensions" / "git" / "scripts" / "bash" / "create-new-feature.sh"
EXT_CREATE_FEATURE_PS = PROJECT_ROOT / "extensions" / "git" / "scripts" / "powershell" / "create-new-feature.ps1"

HAS_PWSH = shutil.which("pwsh") is not None


def _has_pwsh() -> bool:
    """Check if pwsh is available."""
    return HAS_PWSH


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with scripts and .specify dir."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=tmp_path,
        check=True,
    )
    scripts_dir = tmp_path / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def ext_git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with extension scripts (for GIT_BRANCH_NAME tests)."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp_path, check=True)
    # Extension script needs common.sh at .specify/scripts/bash/
    specify_scripts = tmp_path / ".specify" / "scripts" / "bash"
    specify_scripts.mkdir(parents=True)
    shutil.copy(COMMON_SH, specify_scripts / "common.sh")
    # Also install core scripts for compatibility
    core_scripts = tmp_path / "scripts" / "bash"
    core_scripts.mkdir(parents=True)
    shutil.copy(COMMON_SH, core_scripts / "common.sh")
    # Copy extension script
    ext_dir = tmp_path / ".specify" / "extensions" / "git" / "scripts" / "bash"
    ext_dir.mkdir(parents=True)
    shutil.copy(EXT_CREATE_FEATURE, ext_dir / "create-new-feature.sh")
    # Also copy git-common.sh if it exists
    git_common = PROJECT_ROOT / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
    if git_common.exists():
        shutil.copy(git_common, ext_dir / "git-common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "specs").mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture
def ext_ps_git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with PowerShell extension scripts."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp_path, check=True)
    # Install core PS scripts
    ps_dir = tmp_path / "scripts" / "powershell"
    ps_dir.mkdir(parents=True)
    common_ps = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
    shutil.copy(common_ps, ps_dir / "common.ps1")
    # Also install at .specify/scripts/powershell/ for extension resolution
    specify_ps = tmp_path / ".specify" / "scripts" / "powershell"
    specify_ps.mkdir(parents=True)
    shutil.copy(common_ps, specify_ps / "common.ps1")
    # Copy extension script
    ext_ps = tmp_path / ".specify" / "extensions" / "git" / "scripts" / "powershell"
    ext_ps.mkdir(parents=True)
    shutil.copy(EXT_CREATE_FEATURE_PS, ext_ps / "create-new-feature.ps1")
    git_common_ps = PROJECT_ROOT / "extensions" / "git" / "scripts" / "powershell" / "git-common.ps1"
    if git_common_ps.exists():
        shutil.copy(git_common_ps, ext_ps / "git-common.ps1")
    (tmp_path / ".specify" / "templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "specs").mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture
def ps_git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with PowerShell scripts and a BOM-prefixed template."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=tmp_path,
        check=True,
    )
    ps_dir = tmp_path / "scripts" / "powershell"
    ps_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE_PS, ps_dir / "create-new-feature.ps1")
    common_ps = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
    shutil.copy(common_ps, ps_dir / "common.ps1")
    templates_dir = tmp_path / ".specify" / "templates"
    templates_dir.mkdir(parents=True)
    # Write a BOM-prefixed template to ensure the WriteAllText fix is actually exercised.
    # If WriteAllText regresses, the output file will contain the BOM.
    bom = b"\xef\xbb\xbf"
    template_content = "# Feature Spec\n\nDescribe the feature here.\n"
    (templates_dir / "spec-template.md").write_bytes(bom + template_content.encode("utf-8"))
    return tmp_path


@pytest.fixture
def no_git_dir(tmp_path: Path) -> Path:
    """Create a temp directory without git, but with scripts."""
    scripts_dir = tmp_path / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True)
    return tmp_path


def run_script(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run create-new-feature.sh with given args."""
    cmd = ["bash", "scripts/bash/create-new-feature.sh", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def source_and_call(func_call: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Source common.sh and call a function."""
    cmd = f'source "{COMMON_SH}" && {func_call}'
    return subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


# ── Timestamp Branch Tests ───────────────────────────────────────────────────


@requires_bash
class TestTimestampBranch:
    def test_timestamp_creates_branch(self, git_repo: Path):
        """Test 1: --timestamp creates branch with YYYYMMDD-HHMMSS prefix."""
        result = run_script(git_repo, "--timestamp", "--short-name", "user-auth", "Add user auth")
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch is not None
        assert re.match(r"^\d{8}-\d{6}-user-auth$", branch), f"unexpected branch: {branch}"

    def test_number_and_timestamp_warns(self, git_repo: Path):
        """Test 3: --number + --timestamp warns and uses timestamp."""
        result = run_script(git_repo, "--timestamp", "--number", "42", "--short-name", "feat", "Feature")
        assert result.returncode == 0, result.stderr
        assert "Warning" in result.stderr and "--number" in result.stderr

    def test_json_output_keys(self, git_repo: Path):
        """Test 4: JSON output contains expected keys."""
        import json
        result = run_script(git_repo, "--json", "--timestamp", "--short-name", "api", "API feature")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        for key in ("BRANCH_NAME", "SPEC_FILE", "FEATURE_NUM"):
            assert key in data, f"missing {key} in JSON: {data}"
        assert re.match(r"^\d{8}-\d{6}$", data["FEATURE_NUM"])

    def test_long_name_truncation(self, git_repo: Path):
        """Test 5: Long branch name is truncated to <= 244 chars."""
        long_name = "a-" * 150 + "end"
        result = run_script(git_repo, "--timestamp", "--short-name", long_name, "Long feature")
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch is not None
        assert len(branch) <= 244
        assert re.match(r"^\d{8}-\d{6}-", branch)


# ── Sequential Branch Tests ──────────────────────────────────────────────────


@requires_bash
class TestSequentialBranch:
    def test_sequential_default_with_existing_specs(self, git_repo: Path):
        """Test 2: Sequential default with existing specs."""
        (git_repo / "specs" / "001-first-feat").mkdir(parents=True)
        (git_repo / "specs" / "002-second-feat").mkdir(parents=True)
        result = run_script(git_repo, "--short-name", "new-feat", "New feature")
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch is not None
        assert re.match(r"^\d{3,}-new-feat$", branch), f"unexpected branch: {branch}"

    def test_sequential_ignores_timestamp_dirs(self, git_repo: Path):
        """Sequential numbering skips timestamp dirs when computing next number."""
        (git_repo / "specs" / "002-first-feat").mkdir(parents=True)
        (git_repo / "specs" / "20260319-143022-ts-feat").mkdir(parents=True)
        result = run_script(git_repo, "--short-name", "next-feat", "Next feature")
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "003-next-feat", f"expected 003-next-feat, got: {branch}"

    def test_sequential_supports_four_digit_prefixes(self, git_repo: Path):
        """Sequential numbering should continue past 999 without truncation."""
        (git_repo / "specs" / "999-last-3digit").mkdir(parents=True)
        (git_repo / "specs" / "1000-first-4digit").mkdir(parents=True)
        result = run_script(git_repo, "--short-name", "next-feat", "Next feature")
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "1001-next-feat", f"expected 1001-next-feat, got: {branch}"


class TestSequentialBranchPowerShell:
    def test_powershell_scanner_uses_long_tryparse_for_large_prefixes(self):
        """PowerShell scanner should parse large prefixes without [int] casts."""
        content = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "[long]::TryParse($matches[1], [ref]$num)" in content
        assert "$num = [int]$matches[1]" not in content


# ── check_feature_branch Tests ───────────────────────────────────────────────


@requires_bash
class TestCheckFeatureBranch:
    def test_accepts_timestamp_branch(self):
        """Test 6: check_feature_branch accepts timestamp branch."""
        result = source_and_call('check_feature_branch "20260319-143022-feat" "true"')
        assert result.returncode == 0

    def test_accepts_sequential_branch(self):
        """Test 7: check_feature_branch accepts sequential branch."""
        result = source_and_call('check_feature_branch "004-feat" "true"')
        assert result.returncode == 0

    def test_rejects_main(self):
        """Test 8: check_feature_branch rejects main."""
        result = source_and_call('check_feature_branch "main" "true"')
        assert result.returncode != 0

    def test_accepts_four_digit_sequential_branch(self):
        """check_feature_branch accepts 4+ digit sequential branch."""
        result = source_and_call('check_feature_branch "1234-feat" "true"')
        assert result.returncode == 0

    def test_rejects_partial_timestamp(self):
        """Test 9: check_feature_branch rejects 7-digit date."""
        result = source_and_call('check_feature_branch "2026031-143022-feat" "true"')
        assert result.returncode != 0

    def test_rejects_timestamp_without_slug(self):
        """check_feature_branch rejects timestamp-like branch missing trailing slug."""
        result = source_and_call('check_feature_branch "20260319-143022" "true"')
        assert result.returncode != 0

    def test_rejects_7digit_timestamp_without_slug(self):
        """check_feature_branch rejects 7-digit date + 6-digit time without slug."""
        result = source_and_call('check_feature_branch "2026031-143022" "true"')
        assert result.returncode != 0

    def test_accepts_single_prefix_sequential(self):
        """Optional gitflow-style prefix: one segment + sequential feature name."""
        result = source_and_call('check_feature_branch "feat/004-my-feature" "true"')
        assert result.returncode == 0

    def test_accepts_single_prefix_timestamp(self):
        """Optional prefix + timestamp-style feature name."""
        result = source_and_call('check_feature_branch "release/20260319-143022-feat" "true"')
        assert result.returncode == 0

    def test_rejects_invalid_suffix_with_single_prefix(self):
        result = source_and_call('check_feature_branch "feat/main" "true"')
        assert result.returncode != 0
        assert "feat/main" in result.stderr

    def test_rejects_two_level_prefix_before_feature(self):
        """More than one slash: no stripping; whole name must match (fails)."""
        result = source_and_call('check_feature_branch "feat/fix/004-feat" "true"')
        assert result.returncode != 0

    def test_rejects_malformed_timestamp_with_prefix(self):
        result = source_and_call('check_feature_branch "feat/2026031-143022-feat" "true"')
        assert result.returncode != 0


# ── find_feature_dir_by_prefix Tests ─────────────────────────────────────────


@requires_bash
class TestFindFeatureDirByPrefix:
    def test_timestamp_branch(self, tmp_path: Path):
        """Test 10: find_feature_dir_by_prefix with timestamp branch."""
        (tmp_path / "specs" / "20260319-143022-user-auth").mkdir(parents=True)
        result = source_and_call(
            f'find_feature_dir_by_prefix "{tmp_path}" "20260319-143022-user-auth"'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == f"{tmp_path}/specs/20260319-143022-user-auth"

    def test_cross_branch_prefix(self, tmp_path: Path):
        """Test 11: find_feature_dir_by_prefix cross-branch (different suffix, same timestamp)."""
        (tmp_path / "specs" / "20260319-143022-original-feat").mkdir(parents=True)
        result = source_and_call(
            f'find_feature_dir_by_prefix "{tmp_path}" "20260319-143022-different-name"'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == f"{tmp_path}/specs/20260319-143022-original-feat"

    def test_four_digit_sequential_prefix(self, tmp_path: Path):
        """find_feature_dir_by_prefix resolves 4+ digit sequential prefix."""
        (tmp_path / "specs" / "1000-original-feat").mkdir(parents=True)
        result = source_and_call(
            f'find_feature_dir_by_prefix "{tmp_path}" "1000-different-name"'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == f"{tmp_path}/specs/1000-original-feat"

    def test_sequential_with_single_path_prefix(self, tmp_path: Path):
        """Strip one optional prefix segment before prefix directory lookup."""
        (tmp_path / "specs" / "004-only-dir").mkdir(parents=True)
        result = source_and_call(
            f'find_feature_dir_by_prefix "{tmp_path}" "feat/004-other-suffix"'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == f"{tmp_path}/specs/004-only-dir"

    def test_timestamp_with_single_path_prefix_cross_branch(self, tmp_path: Path):
        (tmp_path / "specs" / "20260319-143022-canonical").mkdir(parents=True)
        result = source_and_call(
            f'find_feature_dir_by_prefix "{tmp_path}" "hotfix/20260319-143022-alias"'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == f"{tmp_path}/specs/20260319-143022-canonical"


# ── get_feature_paths + single-prefix integration ───────────────────────────


class TestGetFeaturePathsSinglePrefix:
    @requires_bash
    def test_bash_specify_feature_prefixed_resolves_by_prefix(self, tmp_path: Path):
        """get_feature_paths: SPECIFY_FEATURE with one optional prefix uses effective name for lookup."""
        (tmp_path / ".specify").mkdir()
        (tmp_path / "specs" / "001-target-spec").mkdir(parents=True)
        cmd = (
            f'cd "{tmp_path}" && export SPECIFY_FEATURE="feat/001-other" && '
            f'source "{COMMON_SH}" && eval "$(get_feature_paths)" && printf "%s" "$FEATURE_DIR"'
        )
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(tmp_path / "specs" / "001-target-spec")


    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_ps_specify_feature_prefixed_resolves_by_prefix(self, git_repo: Path):
        """PowerShell Get-FeaturePathsEnv: same prefix stripping as bash."""
        common_ps = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
        spec_dir = git_repo / "specs" / "001-ps-prefix-spec"
        spec_dir.mkdir(parents=True)
        ps_cmd = f'. "{common_ps}"; $r = Get-FeaturePathsEnv; Write-Output "FEATURE_DIR=$($r.FEATURE_DIR)"'
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", ps_cmd],
            cwd=git_repo,
            capture_output=True,
            text=True,
            env={**os.environ, "SPECIFY_FEATURE": "feat/001-other"},
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip()
                assert val == str(spec_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in PowerShell output")


# ── get_current_branch Tests ─────────────────────────────────────────────────


@requires_bash
class TestGetCurrentBranch:
    def test_env_var(self):
        """Test 12: get_current_branch returns SPECIFY_FEATURE env var."""
        result = source_and_call("get_current_branch", env={"SPECIFY_FEATURE": "my-custom-branch"})
        assert result.stdout.strip() == "my-custom-branch"


# ── No-git Tests ─────────────────────────────────────────────────────────────


@requires_bash
class TestNoGitTimestamp:
    def test_no_git_timestamp(self, no_git_dir: Path):
        """Test 13: No-git repo + timestamp creates spec dir with warning."""
        result = run_script(no_git_dir, "--timestamp", "--short-name", "no-git-feat", "No git feature")
        assert result.returncode == 0, result.stderr
        spec_dirs = list((no_git_dir / "specs").iterdir()) if (no_git_dir / "specs").exists() else []
        assert len(spec_dirs) > 0, "spec dir not created"
        assert "git" in result.stderr.lower() or "warning" in result.stderr.lower()


# ── E2E Flow Tests ───────────────────────────────────────────────────────────


@requires_bash
class TestE2EFlow:
    def test_e2e_timestamp(self, git_repo: Path):
        """Test 14: E2E timestamp flow — branch, dir, validation."""
        run_script(git_repo, "--timestamp", "--short-name", "e2e-ts", "E2E timestamp test")
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert re.match(r"^\d{8}-\d{6}-e2e-ts$", branch), f"branch: {branch}"
        assert (git_repo / "specs" / branch).is_dir()
        val = source_and_call(f'check_feature_branch "{branch}" "true"')
        assert val.returncode == 0

    def test_e2e_sequential(self, git_repo: Path):
        """Test 15: E2E sequential flow (regression guard)."""
        run_script(git_repo, "--short-name", "seq-feat", "Sequential feature")
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert re.match(r"^\d{3,}-seq-feat$", branch), f"branch: {branch}"
        assert (git_repo / "specs" / branch).is_dir()
        val = source_and_call(f'check_feature_branch "{branch}" "true"')
        assert val.returncode == 0


# ── Allow Existing Branch Tests ──────────────────────────────────────────────


@requires_bash
class TestAllowExistingBranch:
    def test_allow_existing_switches_to_branch(self, git_repo: Path):
        """T006: Pre-create branch, verify script switches to it."""
        subprocess.run(
            ["git", "checkout", "-b", "004-pre-exist"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "pre-exist",
            "--number", "4", "Pre-existing feature",
        )
        assert result.returncode == 0, result.stderr
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo, capture_output=True, text=True,
        ).stdout.strip()
        assert current == "004-pre-exist", f"expected 004-pre-exist, got {current}"

    def test_allow_existing_already_on_branch(self, git_repo: Path):
        """T007: Verify success when already on the target branch."""
        subprocess.run(
            ["git", "checkout", "-b", "005-already-on"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "already-on",
            "--number", "5", "Already on branch",
        )
        assert result.returncode == 0, result.stderr

    def test_allow_existing_creates_spec_dir(self, git_repo: Path):
        """T008: Verify spec directory created on existing branch."""
        subprocess.run(
            ["git", "checkout", "-b", "006-spec-dir"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "spec-dir",
            "--number", "6", "Spec dir feature",
        )
        assert result.returncode == 0, result.stderr
        assert (git_repo / "specs" / "006-spec-dir").is_dir()
        assert (git_repo / "specs" / "006-spec-dir" / "spec.md").exists()

    def test_without_flag_still_errors(self, git_repo: Path):
        """T009: Verify backwards compatibility (error without flag)."""
        subprocess.run(
            ["git", "checkout", "-b", "007-no-flag"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--short-name", "no-flag", "--number", "7", "No flag feature",
        )
        assert result.returncode != 0, "should fail without --allow-existing-branch"
        assert "already exists" in result.stderr

    def test_allow_existing_no_overwrite_spec(self, git_repo: Path):
        """T010: Pre-create spec.md with content, verify it is preserved."""
        subprocess.run(
            ["git", "checkout", "-b", "008-no-overwrite"],
            cwd=git_repo, check=True, capture_output=True,
        )
        spec_dir = git_repo / "specs" / "008-no-overwrite"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("# My custom spec content\n")
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "no-overwrite",
            "--number", "8", "No overwrite feature",
        )
        assert result.returncode == 0, result.stderr
        assert spec_file.read_text() == "# My custom spec content\n"

    def test_allow_existing_creates_branch_if_not_exists(self, git_repo: Path):
        """T011: Verify normal creation when branch doesn't exist."""
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "new-branch",
            "New branch feature",
        )
        assert result.returncode == 0, result.stderr
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo, capture_output=True, text=True,
        ).stdout.strip()
        assert "new-branch" in current

    def test_allow_existing_with_json(self, git_repo: Path):
        """T012: Verify JSON output is correct."""
        import json

        subprocess.run(
            ["git", "checkout", "-b", "009-json-test"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        result = run_script(
            git_repo, "--allow-existing-branch", "--json", "--short-name", "json-test",
            "--number", "9", "JSON test",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "009-json-test"

    def test_allow_existing_no_git(self, no_git_dir: Path):
        """T013: Verify flag is silently ignored in non-git repos."""
        result = run_script(
            no_git_dir, "--allow-existing-branch", "--short-name", "no-git",
            "No git feature",
        )
        assert result.returncode == 0, result.stderr

    def test_allow_existing_surfaces_checkout_error(self, git_repo: Path):
        """Checkout failures on an existing branch should include Git's stderr."""
        shared_file = git_repo / "shared.txt"
        shared_file.write_text("base\n")
        subprocess.run(
            ["git", "add", "shared.txt"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "add shared file", "-q"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "010-checkout-failure"],
            cwd=git_repo, check=True, capture_output=True,
        )
        shared_file.write_text("branch version\n")
        subprocess.run(
            ["git", "commit", "-am", "branch change", "-q"],
            cwd=git_repo, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo, check=True, capture_output=True,
        )
        shared_file.write_text("uncommitted main change\n")

        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "checkout-failure",
            "--number", "10", "Checkout failure",
        )

        assert result.returncode != 0, "checkout should fail with conflicting local changes"
        assert "Failed to switch to existing branch '010-checkout-failure'" in result.stderr
        assert "would be overwritten by checkout" in result.stderr
        assert "shared.txt" in result.stderr


class TestAllowExistingBranchPowerShell:
    def test_powershell_supports_allow_existing_branch_flag(self):
        """Static guard: PS script exposes and uses -AllowExistingBranch."""
        contents = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "-AllowExistingBranch" in contents
        # Ensure the flag is referenced in script logic, not just declared
        assert "AllowExistingBranch" in contents.replace("-AllowExistingBranch", "")

    def test_powershell_surfaces_checkout_errors(self):
        """Static guard: PS script preserves checkout stderr on existing-branch failures."""
        contents = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "$switchBranchError = git checkout -q $branchName 2>&1 | Out-String" in contents
        assert "exists but could not be checked out.`n$($switchBranchError.Trim())" in contents

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    @pytest.mark.skipif(
        os.name != "nt" or shutil.which("powershell.exe") is None,
        reason="Windows PowerShell not installed",
    )
    def test_ps_spec_file_written_without_bom(self, ps_git_repo: Path):
        """spec.md generated from a BOM-prefixed template must not contain a UTF-8 BOM."""
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(CREATE_FEATURE_PS),
                "-ShortName",
                "bom-check",
                "BOM check feature",
            ],
            cwd=ps_git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        spec_file = next((ps_git_repo / "specs").rglob("spec.md"), None)
        assert spec_file is not None, (
            f"spec.md was not created.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        raw = spec_file.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            f"spec.md must not start with a UTF-8 BOM — got first 3 bytes: {raw[:3]!r}"
        )
        # Verify template content was copied (not just an empty New-Item fallback)
        assert "Feature Spec" in raw.decode("utf-8"), (
            "spec.md does not contain template content — WriteAllText path was not exercised"
        )


class TestGitExtensionParity:
    def test_bash_extension_surfaces_checkout_errors(self):
        """Static guard: git extension bash script preserves checkout stderr."""
        contents = EXT_CREATE_FEATURE.read_text(encoding="utf-8")
        assert 'switch_branch_error=$(git checkout -q "$BRANCH_NAME" 2>&1)' in contents
        assert "Failed to switch to existing branch '$BRANCH_NAME'" in contents

    def test_powershell_extension_surfaces_checkout_errors(self):
        """Static guard: git extension PowerShell script preserves checkout stderr."""
        contents = EXT_CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "$switchBranchError = git checkout -q $branchName 2>&1 | Out-String" in contents
        assert "exists but could not be checked out.`n$($switchBranchError.Trim())" in contents


# ── Dry-Run Tests ────────────────────────────────────────────────────────────


@requires_bash
class TestDryRun:
    def test_dry_run_sequential_outputs_name(self, git_repo: Path):
        """T009: Dry-run computes correct branch name with existing specs."""
        (git_repo / "specs" / "001-first-feat").mkdir(parents=True)
        (git_repo / "specs" / "002-second-feat").mkdir(parents=True)
        result = run_script(
            git_repo, "--dry-run", "--short-name", "new-feat", "New feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "003-new-feat", f"expected 003-new-feat, got: {branch}"

    def test_dry_run_no_branch_created(self, git_repo: Path):
        """T010: Dry-run does not create a git branch."""
        result = run_script(
            git_repo, "--dry-run", "--short-name", "no-branch", "No branch feature"
        )
        assert result.returncode == 0, result.stderr
        branches = subprocess.run(
            ["git", "branch", "--list", "*no-branch*"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert branches.returncode == 0, f"'git branch --list' failed: {branches.stderr}"
        assert branches.stdout.strip() == "", "branch should not exist after dry-run"

    def test_dry_run_no_spec_dir_created(self, git_repo: Path):
        """T011: Dry-run does not create any directories (including root specs/)."""
        specs_root = git_repo / "specs"
        if specs_root.exists():
            shutil.rmtree(specs_root)
        assert not specs_root.exists(), "specs/ should not exist before dry-run"

        result = run_script(
            git_repo, "--dry-run", "--short-name", "no-dir", "No dir feature"
        )
        assert result.returncode == 0, result.stderr
        assert not specs_root.exists(), "specs/ should not be created during dry-run"

    def test_dry_run_empty_repo(self, git_repo: Path):
        """T012: Dry-run returns 001 prefix when no existing specs or branches."""
        result = run_script(
            git_repo, "--dry-run", "--short-name", "first", "First feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "001-first", f"expected 001-first, got: {branch}"

    def test_dry_run_with_short_name(self, git_repo: Path):
        """T013: Dry-run with --short-name produces expected name."""
        (git_repo / "specs" / "001-existing").mkdir(parents=True)
        (git_repo / "specs" / "002-existing").mkdir(parents=True)
        (git_repo / "specs" / "003-existing").mkdir(parents=True)
        result = run_script(
            git_repo, "--dry-run", "--short-name", "user-auth", "Add user authentication"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "004-user-auth", f"expected 004-user-auth, got: {branch}"

    def test_dry_run_then_real_run_match(self, git_repo: Path):
        """T014: Dry-run name matches subsequent real creation."""
        (git_repo / "specs" / "001-existing").mkdir(parents=True)
        # Dry-run first
        dry_result = run_script(
            git_repo, "--dry-run", "--short-name", "match-test", "Match test"
        )
        assert dry_result.returncode == 0, dry_result.stderr
        dry_branch = None
        for line in dry_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                dry_branch = line.split(":", 1)[1].strip()
        # Real run
        real_result = run_script(
            git_repo, "--short-name", "match-test", "Match test"
        )
        assert real_result.returncode == 0, real_result.stderr
        real_branch = None
        for line in real_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                real_branch = line.split(":", 1)[1].strip()
        assert dry_branch == real_branch, f"dry={dry_branch} != real={real_branch}"

    def test_dry_run_accounts_for_remote_branches(self, git_repo: Path):
        """Dry-run queries remote refs via ls-remote (no fetch) for accurate numbering."""
        (git_repo / "specs" / "001-existing").mkdir(parents=True)

        # Set up a bare remote and push (use subdirs of git_repo for isolation)
        remote_dir = git_repo / "test-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote_dir)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote_dir)],
            check=True, cwd=git_repo, capture_output=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "HEAD"],
            check=True, cwd=git_repo, capture_output=True,
        )

        # Clone into a second copy, create a higher-numbered branch, push it
        second_clone = git_repo / "test-second-clone"
        subprocess.run(
            ["git", "clone", str(remote_dir), str(second_clone)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=second_clone, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=second_clone, check=True, capture_output=True,
        )
        # Create branch 005 on the remote (higher than local 001)
        subprocess.run(
            ["git", "checkout", "-b", "005-remote-only"],
            cwd=second_clone, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "push", "origin", "005-remote-only"],
            cwd=second_clone, check=True, capture_output=True,
        )

        # Primary repo: dry-run should see 005 via ls-remote and return 006
        dry_result = run_script(
            git_repo, "--dry-run", "--short-name", "remote-test", "Remote test"
        )
        assert dry_result.returncode == 0, dry_result.stderr
        dry_branch = None
        for line in dry_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                dry_branch = line.split(":", 1)[1].strip()
        assert dry_branch == "006-remote-test", f"expected 006-remote-test, got: {dry_branch}"

    def test_dry_run_json_includes_field(self, git_repo: Path):
        """T015: JSON output includes DRY_RUN field when --dry-run is active."""
        import json

        result = run_script(
            git_repo, "--dry-run", "--json", "--short-name", "json-test", "JSON test"
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "DRY_RUN" in data, f"DRY_RUN missing from JSON: {data}"
        assert data["DRY_RUN"] is True

    def test_dry_run_json_absent_without_flag(self, git_repo: Path):
        """T016: Normal JSON output does NOT include DRY_RUN field."""
        import json

        result = run_script(
            git_repo, "--json", "--short-name", "no-dry", "No dry run"
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "DRY_RUN" not in data, f"DRY_RUN should not be in normal JSON: {data}"

    def test_dry_run_with_timestamp(self, git_repo: Path):
        """T017: Dry-run works with --timestamp flag."""
        result = run_script(
            git_repo, "--dry-run", "--timestamp", "--short-name", "ts-feat", "Timestamp feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch is not None, "no BRANCH_NAME in output"
        assert re.match(r"^\d{8}-\d{6}-ts-feat$", branch), f"unexpected: {branch}"
        # Verify no side effects
        branches = subprocess.run(
            ["git", "branch", "--list", "*ts-feat*"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert branches.returncode == 0, f"'git branch --list' failed: {branches.stderr}"
        assert branches.stdout.strip() == ""

    def test_dry_run_with_number(self, git_repo: Path):
        """T018: Dry-run works with --number flag."""
        result = run_script(
            git_repo, "--dry-run", "--number", "42", "--short-name", "num-feat", "Number feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "042-num-feat", f"expected 042-num-feat, got: {branch}"

    def test_dry_run_no_git(self, no_git_dir: Path):
        """T019: Dry-run works in non-git directory."""
        (no_git_dir / "specs" / "001-existing").mkdir(parents=True)
        result = run_script(
            no_git_dir, "--dry-run", "--short-name", "no-git-dry", "No git dry run"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "002-no-git-dry", f"expected 002-no-git-dry, got: {branch}"
        # Verify no spec dir created
        spec_dirs = [
            d.name
            for d in (no_git_dir / "specs").iterdir()
            if d.is_dir() and "no-git-dry" in d.name
        ]
        assert len(spec_dirs) == 0


# ── PowerShell Dry-Run Tests ─────────────────────────────────────────────────


def run_ps_script(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run create-new-feature.ps1 from the temp repo's scripts directory."""
    script = cwd / "scripts" / "powershell" / "create-new-feature.ps1"
    cmd = ["pwsh", "-NoProfile", "-File", str(script), *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


@pytest.mark.skipif(not _has_pwsh(), reason="pwsh not available")
class TestPowerShellDryRun:
    def test_ps_dry_run_outputs_name(self, ps_git_repo: Path):
        """PowerShell -DryRun computes correct branch name."""
        (ps_git_repo / "specs" / "001-first").mkdir(parents=True)
        result = run_ps_script(
            ps_git_repo, "-DryRun", "-ShortName", "ps-feat", "PS feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "002-ps-feat", f"expected 002-ps-feat, got: {branch}"

    def test_ps_dry_run_no_branch_created(self, ps_git_repo: Path):
        """PowerShell -DryRun does not create a git branch."""
        result = run_ps_script(
            ps_git_repo, "-DryRun", "-ShortName", "no-ps-branch", "No branch"
        )
        assert result.returncode == 0, result.stderr
        branches = subprocess.run(
            ["git", "branch", "--list", "*no-ps-branch*"],
            cwd=ps_git_repo,
            capture_output=True,
            text=True,
        )
        assert branches.returncode == 0, f"'git branch --list' failed: {branches.stderr}"
        assert branches.stdout.strip() == "", "branch should not exist after dry-run"

    def test_ps_dry_run_no_spec_dir_created(self, ps_git_repo: Path):
        """PowerShell -DryRun does not create specs/ directory."""
        specs_root = ps_git_repo / "specs"
        if specs_root.exists():
            shutil.rmtree(specs_root)
        assert not specs_root.exists()

        result = run_ps_script(
            ps_git_repo, "-DryRun", "-ShortName", "no-ps-dir", "No dir"
        )
        assert result.returncode == 0, result.stderr
        assert not specs_root.exists(), "specs/ should not be created during dry-run"

    def test_ps_dry_run_json_includes_field(self, ps_git_repo: Path):
        """PowerShell -DryRun JSON output includes DRY_RUN field."""
        import json

        result = run_ps_script(
            ps_git_repo, "-DryRun", "-Json", "-ShortName", "ps-json", "JSON test"
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "DRY_RUN" in data, f"DRY_RUN missing from JSON: {data}"
        assert data["DRY_RUN"] is True

    def test_ps_dry_run_json_absent_without_flag(self, ps_git_repo: Path):
        """PowerShell normal JSON output does NOT include DRY_RUN field."""
        import json

        result = run_ps_script(
            ps_git_repo, "-Json", "-ShortName", "ps-no-dry", "No dry run"
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "DRY_RUN" not in data, f"DRY_RUN should not be in normal JSON: {data}"


# ── GIT_BRANCH_NAME Override Tests ──────────────────────────────────────────


@requires_bash
class TestGitBranchNameOverrideBash:
    """Tests for GIT_BRANCH_NAME env var override in extension create-new-feature.sh."""

    def _run_ext(self, ext_git_repo: Path, env_extras: dict, *extra_args: str):
        script = ext_git_repo / ".specify" / "extensions" / "git" / "scripts" / "bash" / "create-new-feature.sh"
        cmd = ["bash", str(script), "--json", *extra_args, "ignored"]
        return subprocess.run(cmd, cwd=ext_git_repo, capture_output=True, text=True,
                              env={**os.environ, **env_extras})

    def test_exact_name_no_prefix(self, ext_git_repo: Path):
        """GIT_BRANCH_NAME is used verbatim with no numeric prefix added."""
        result = self._run_ext(ext_git_repo, {"GIT_BRANCH_NAME": "my-exact-branch"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "my-exact-branch"
        assert data["FEATURE_NUM"] == "my-exact-branch"

    def test_sequential_prefix_extraction(self, ext_git_repo: Path):
        """FEATURE_NUM extracted from sequential-style prefix (digits before dash)."""
        result = self._run_ext(ext_git_repo, {"GIT_BRANCH_NAME": "042-custom-branch"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "042-custom-branch"
        assert data["FEATURE_NUM"] == "042"

    def test_timestamp_prefix_extraction(self, ext_git_repo: Path):
        """FEATURE_NUM extracted as full YYYYMMDD-HHMMSS for timestamp-style names."""
        result = self._run_ext(ext_git_repo, {"GIT_BRANCH_NAME": "20260407-143022-my-feature"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "20260407-143022-my-feature"
        assert data["FEATURE_NUM"] == "20260407-143022"

    def test_overlong_name_rejected(self, ext_git_repo: Path):
        """GIT_BRANCH_NAME exceeding 244 bytes is rejected with an error."""
        long_name = "a" * 245
        result = self._run_ext(ext_git_repo, {"GIT_BRANCH_NAME": long_name})
        assert result.returncode != 0
        assert "244" in result.stderr

    def test_dry_run_with_override(self, ext_git_repo: Path):
        """GIT_BRANCH_NAME works with --dry-run (no branch created)."""
        result = self._run_ext(ext_git_repo, {"GIT_BRANCH_NAME": "dry-run-override"}, "--dry-run")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "dry-run-override"
        assert data.get("DRY_RUN") is True
        branches = subprocess.run(
            ["git", "branch", "--list", "dry-run-override"],
            cwd=ext_git_repo, capture_output=True, text=True,
        )
        assert "dry-run-override" not in branches.stdout


@pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
class TestGitBranchNameOverridePowerShell:
    """Tests for GIT_BRANCH_NAME env var override in extension create-new-feature.ps1."""

    def _run_ext(self, ext_ps_git_repo: Path, env_extras: dict):
        script = ext_ps_git_repo / ".specify" / "extensions" / "git" / "scripts" / "powershell" / "create-new-feature.ps1"
        return subprocess.run(
            ["pwsh", "-NoProfile", "-File", str(script), "-Json", "ignored"],
            cwd=ext_ps_git_repo, capture_output=True, text=True,
            env={**os.environ, **env_extras},
        )

    def test_exact_name_no_prefix(self, ext_ps_git_repo: Path):
        """GIT_BRANCH_NAME is used verbatim with no numeric prefix added."""
        result = self._run_ext(ext_ps_git_repo, {"GIT_BRANCH_NAME": "ps-exact-branch"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "ps-exact-branch"
        assert data["FEATURE_NUM"] == "ps-exact-branch"

    def test_sequential_prefix_extraction(self, ext_ps_git_repo: Path):
        """FEATURE_NUM extracted from sequential-style prefix."""
        result = self._run_ext(ext_ps_git_repo, {"GIT_BRANCH_NAME": "099-ps-numbered"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "099-ps-numbered"
        assert data["FEATURE_NUM"] == "099"

    def test_timestamp_prefix_extraction(self, ext_ps_git_repo: Path):
        """FEATURE_NUM extracted as full YYYYMMDD-HHMMSS for timestamp-style names."""
        result = self._run_ext(ext_ps_git_repo, {"GIT_BRANCH_NAME": "20260407-143022-ps-feature"})
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "20260407-143022-ps-feature"
        assert data["FEATURE_NUM"] == "20260407-143022"

    def test_overlong_name_rejected(self, ext_ps_git_repo: Path):
        """GIT_BRANCH_NAME exceeding 244 bytes is rejected."""
        long_name = "a" * 245
        result = self._run_ext(ext_ps_git_repo, {"GIT_BRANCH_NAME": long_name})
        assert result.returncode != 0
        assert "244" in result.stderr


# ── Feature Directory Resolution Tests ───────────────────────────────────────


class TestFeatureDirectoryResolution:
    """Tests for SPECIFY_FEATURE_DIRECTORY and .specify/feature.json resolution."""

    @requires_bash
    def test_env_var_overrides_branch_lookup(self, git_repo: Path):
        """SPECIFY_FEATURE_DIRECTORY env var takes priority over branch-based lookup."""
        custom_dir = git_repo / "my-custom-specs" / "my-feature"
        custom_dir.mkdir(parents=True)

        result = subprocess.run(
            ["bash", "-c", f'source "{COMMON_SH}" && get_feature_paths'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            env={**os.environ, "SPECIFY_FEATURE_DIRECTORY": str(custom_dir)},
        )
        assert result.returncode == 0, result.stderr
        assert str(custom_dir) in result.stdout
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(custom_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in output")

    @requires_bash
    def test_feature_json_overrides_branch_lookup(self, git_repo: Path):
        """feature.json feature_directory takes priority over branch-based lookup."""
        custom_dir = git_repo / "specs" / "custom-feature"
        custom_dir.mkdir(parents=True)

        feature_json = git_repo / ".specify" / "feature.json"
        feature_json.write_text(
            json.dumps({"feature_directory": str(custom_dir)}) + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            ["bash", "-c", f'source "{COMMON_SH}" && get_feature_paths'],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(custom_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in output")

    @requires_bash
    def test_env_var_takes_priority_over_feature_json(self, git_repo: Path):
        """Env var wins over feature.json."""
        env_dir = git_repo / "specs" / "env-feature"
        env_dir.mkdir(parents=True)
        json_dir = git_repo / "specs" / "json-feature"
        json_dir.mkdir(parents=True)

        feature_json = git_repo / ".specify" / "feature.json"
        feature_json.write_text(
            json.dumps({"feature_directory": str(json_dir)}) + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            ["bash", "-c", f'source "{COMMON_SH}" && get_feature_paths'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            env={**os.environ, "SPECIFY_FEATURE_DIRECTORY": str(env_dir)},
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(env_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in output")

    @requires_bash
    def test_fallback_to_branch_lookup(self, git_repo: Path):
        """Without env var or feature.json, falls back to branch-based lookup."""
        subprocess.run(["git", "checkout", "-q", "-b", "001-test-feat"], cwd=git_repo, check=True)
        spec_dir = git_repo / "specs" / "001-test-feat"
        spec_dir.mkdir(parents=True)

        result = subprocess.run(
            ["bash", "-c", f'source "{COMMON_SH}" && get_feature_paths'],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(spec_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in output")

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_ps_env_var_overrides_branch_lookup(self, git_repo: Path):
        """PowerShell: SPECIFY_FEATURE_DIRECTORY env var takes priority."""
        common_ps = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
        custom_dir = git_repo / "my-custom-specs" / "ps-feature"
        custom_dir.mkdir(parents=True)

        ps_cmd = f'. "{common_ps}"; $r = Get-FeaturePathsEnv; Write-Output "FEATURE_DIR=$($r.FEATURE_DIR)"'
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", ps_cmd],
            cwd=git_repo,
            capture_output=True,
            text=True,
            env={**os.environ, "SPECIFY_FEATURE_DIRECTORY": str(custom_dir)},
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(custom_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in PowerShell output")

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_ps_feature_json_overrides_branch_lookup(self, git_repo: Path):
        """PowerShell: feature.json takes priority over branch-based lookup."""
        common_ps = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
        custom_dir = git_repo / "specs" / "ps-json-feature"
        custom_dir.mkdir(parents=True)

        feature_json = git_repo / ".specify" / "feature.json"
        feature_json.write_text(
            json.dumps({"feature_directory": str(custom_dir)}) + "\n",
            encoding="utf-8",
        )

        ps_cmd = f'. "{common_ps}"; $r = Get-FeaturePathsEnv; Write-Output "FEATURE_DIR=$($r.FEATURE_DIR)"'
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", ps_cmd],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            if line.startswith("FEATURE_DIR="):
                val = line.split("=", 1)[1].strip("'\"")
                assert val == str(custom_dir)
                break
        else:
            pytest.fail("FEATURE_DIR not found in PowerShell output")



# ── Description Quoting Tests (issue #2339) ──────────────────────────────────


@requires_bash
class TestDescriptionQuoting:
    """Descriptions with quotes, apostrophes, and backslashes must not break the script.
    Regression tests for https://github.com/github/spec-kit/issues/2339
    """

    @pytest.mark.parametrize(
        "description",
        [
            "Add user's profile page",
            'Fix the "login" bug',
            "Handle path\\with\\backslashes",
            'It\'s a "complex" feature\\here',
        ],
        ids=["apostrophe", "double-quotes", "backslashes", "mixed"],
    )
    def test_core_script_handles_special_chars(self, git_repo: Path, description: str):
        """Core create-new-feature.sh succeeds with special characters in description."""
        result = run_script(git_repo, "--dry-run", "--short-name", "feat", description)
        assert result.returncode == 0, (
            f"Script failed for description {description!r}: {result.stderr}"
        )

    @pytest.mark.parametrize(
        "description",
        [
            "Add user's profile page",
            'Fix the "login" bug',
            "Handle path\\with\\backslashes",
            'It\'s a "complex" feature\\here',
        ],
        ids=["apostrophe", "double-quotes", "backslashes", "mixed"],
    )
    def test_ext_script_handles_special_chars(self, ext_git_repo: Path, description: str):
        """Extension create-new-feature.sh succeeds with special characters in description."""
        script = (
            ext_git_repo
            / ".specify"
            / "extensions"
            / "git"
            / "scripts"
            / "bash"
            / "create-new-feature.sh"
        )
        result = subprocess.run(
            ["bash", str(script), "--dry-run", "--short-name", "feat", description],
            cwd=ext_git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Script failed for description {description!r}: {result.stderr}"
        )

    def test_whitespace_only_still_rejected(self, git_repo: Path):
        """Whitespace-only descriptions must still be rejected after trimming."""
        result = run_script(git_repo, "--dry-run", "--short-name", "feat", "   ")
        assert result.returncode != 0
        assert "empty" in result.stderr.lower() or "whitespace" in result.stderr.lower()

    def test_plain_description_still_works(self, git_repo: Path):
        """Plain description without special characters continues to work."""
        result = run_script(git_repo, "--dry-run", "--short-name", "feat", "Add login feature")
        assert result.returncode == 0, result.stderr
        