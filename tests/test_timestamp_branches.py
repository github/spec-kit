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
    PROJECT_ROOT / "extensions" / "git" / "scripts" / "bash" / "create-new-feature-branch.sh"
)
EXT_CREATE_FEATURE_PS = (
    PROJECT_ROOT / "extensions" / "git" / "scripts" / "powershell" / "create-new-feature-branch.ps1"
)
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"

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
    shutil.copy(EXT_CREATE_FEATURE, ext_dir / "create-new-feature-branch.sh")
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
    shutil.copy(EXT_CREATE_FEATURE_PS, ext_ps / "create-new-feature-branch.ps1")
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

    def test_branch_name_short_word_case_sensitivity(self, git_repo: Path):
        """A short word is dropped from the derived branch name unless it appears
        as an acronym in UPPERCASE in the description. The PowerShell twin must use
        case-sensitive -cmatch to produce the same result."""
        r1 = run_script(git_repo, "--json", "--dry-run", "Add go support")
        assert r1.returncode == 0, r1.stderr
        assert json.loads(r1.stdout)["BRANCH_NAME"] == "001-support"
        r2 = run_script(git_repo, "--json", "--dry-run", "Use GO now")
        assert r2.returncode == 0, r2.stderr
        assert json.loads(r2.stdout)["BRANCH_NAME"] == "001-use-go-now"

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

    def test_explicit_number_zero_is_honored(self, git_repo: Path):
        """An explicit --number 0 is honored literally (FEATURE_NUM 000), not treated
        as auto-detect, even when higher-numbered specs already exist. This pins the
        canonical bash behavior the PowerShell twin must mirror."""
        (git_repo / "specs" / "003-existing").mkdir(parents=True)
        r = run_script(
            git_repo, "--json", "--dry-run", "--number", "0", "--short-name", "zero", "Zero feature",
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["FEATURE_NUM"] == "000"
        assert data["BRANCH_NAME"] == "000-zero"


class TestSequentialBranchPowerShell:
    def test_powershell_scanner_uses_long_tryparse_for_large_prefixes(self):
        """PowerShell scanner should parse large prefixes without [int] casts."""
        content = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "[long]::TryParse($matches[1], [ref]$num)" in content
        assert "$num = [int]$matches[1]" not in content

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_branch_name_short_word_case_sensitivity(self, ps_git_repo: Path):
        """Core create-new-feature.ps1 must drop a short word unless it appears as
        an acronym in UPPERCASE (case-sensitive -cmatch), matching the bash twin."""
        script = ps_git_repo / "scripts" / "powershell" / "create-new-feature.ps1"

        def _run(desc: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["pwsh", "-NoProfile", "-File", str(script), "-Json", "-DryRun", desc],
                cwd=ps_git_repo, capture_output=True, text=True,
            )

        r1 = _run("Add go support")
        assert r1.returncode == 0, r1.stderr
        assert json.loads(r1.stdout)["BRANCH_NAME"] == "001-support"
        r2 = _run("Use GO now")
        assert r2.returncode == 0, r2.stderr
        assert json.loads(r2.stdout)["BRANCH_NAME"] == "001-use-go-now"

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_explicit_number_zero_is_honored_matching_bash(self, ps_git_repo: Path):
        """An explicit -Number 0 must be honored (FEATURE_NUM 000) like the bash twin,
        even when higher-numbered specs exist. Before the fix, PowerShell could not
        distinguish -Number 0 from the default and silently auto-detected (e.g. 004)."""
        script = ps_git_repo / "scripts" / "powershell" / "create-new-feature.ps1"
        (ps_git_repo / "specs" / "003-existing").mkdir(parents=True)
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-File", str(script),
             "-Json", "-DryRun", "-Number", "0", "-ShortName", "zero", "Zero feature"],
            cwd=ps_git_repo, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["FEATURE_NUM"] == "000"
        assert data["BRANCH_NAME"] == "000-zero"

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_missing_spec_template_warns_matching_bash(self, ps_git_repo: Path):
        """When no spec template can be resolved, create-new-feature.ps1 must warn on
        stderr (and still create an empty spec file), matching the bash twin's
        'Warning: Spec template not found; created empty spec file'. Before the fix
        PowerShell created the empty file silently."""
        # Remove the template the fixture installs so resolution finds nothing.
        (ps_git_repo / ".specify" / "templates" / "spec-template.md").unlink()
        script = ps_git_repo / "scripts" / "powershell" / "create-new-feature.ps1"
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-File", str(script),
             "-Json", "-ShortName", "no-tmpl", "No template feature"],
            cwd=ps_git_repo, capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 0, result.stderr
        assert "Spec template not found" in result.stderr
        # stdout stays parseable JSON and the empty spec file is still created.
        data = json.loads(result.stdout)
        spec_file = Path(data["SPEC_FILE"])
        assert spec_file.is_file()


# ── check_feature_branch Tests ───────────────────────────────────────────────


@requires_bash
class TestCoreCommonRemovesGitHelpers:
    def test_check_feature_branch_removed(self):
        result = source_and_call('declare -F check_feature_branch >/dev/null')
        assert result.returncode != 0

    def test_has_git_removed(self):
        result = source_and_call('declare -F has_git >/dev/null')
        assert result.returncode != 0


# ── find_feature_dir_by_prefix Tests ─────────────────────────────────────────


@requires_bash
class TestFindFeatureDirByPrefixRemoved:
    def test_find_feature_dir_by_prefix_removed(self):
        """Directory scanning helper is removed from core common.sh."""
        result = source_and_call('declare -F find_feature_dir_by_prefix >/dev/null')
        assert result.returncode != 0


# ── get_feature_paths + single-prefix integration ───────────────────────────


class TestGetFeaturePathsSinglePrefix:
    @requires_bash
    def test_bash_specify_feature_prefixed_requires_explicit_feature_context(
        self, tmp_path: Path
    ):
        """SPECIFY_FEATURE alone no longer triggers path lookup in bash."""
        (tmp_path / ".specify").mkdir()
        (tmp_path / "specs" / "001-target-spec").mkdir(parents=True)
        cmd = (
            f'cd "{tmp_path}" && export SPECIFY_FEATURE="feat/001-other" && '
            f'source "{COMMON_SH}" && get_feature_paths'
        )
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Feature directory not found" in result.stderr

    @pytest.mark.skipif(not _has_pwsh(), reason="pwsh not installed")
    def test_ps_specify_feature_prefixed_requires_explicit_feature_context(
        self, git_repo: Path
    ):
        """PowerShell also requires feature.json or SPECIFY_FEATURE_DIRECTORY."""
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
        assert result.returncode != 0
        assert "Feature directory not found" in (result.stderr + result.stdout)


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
        """Test 13: Timestamp mode works without git and creates a spec dir."""
        result = run_script(no_git_dir, "--timestamp", "--short-name", "no-git-feat", "No git feature")
        assert result.returncode == 0, result.stderr
        spec_dirs = list((no_git_dir / "specs").iterdir()) if (no_git_dir / "specs").exists() else []
        assert len(spec_dirs) > 0, "spec dir not created"


# ── E2E Flow Tests ───────────────────────────────────────────────────────────


@requires_bash
class TestE2EFlow:
    def test_e2e_timestamp(self, git_repo: Path):
        """Test 14: E2E timestamp flow creates only a feature directory."""
        before = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        result = run_script(git_repo, "--timestamp", "--short-name", "e2e-ts", "E2E timestamp test")
        assert result.returncode == 0, result.stderr

        branch_name = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch_name = line.split(":", 1)[1].strip()
                break

        assert branch_name is not None
        assert re.match(r"^\d{8}-\d{6}-e2e-ts$", branch_name), f"branch: {branch_name}"
        assert (git_repo / "specs" / branch_name).is_dir()

        after = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert after == before

    def test_e2e_sequential(self, git_repo: Path):
        """Test 15: E2E sequential flow creates only a feature directory."""
        before = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        result = run_script(git_repo, "--short-name", "seq-feat", "Sequential feature")
        assert result.returncode == 0, result.stderr

        branch_name = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch_name = line.split(":", 1)[1].strip()
                break

        assert branch_name == "001-seq-feat"
        assert (git_repo / "specs" / branch_name).is_dir()

        after = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert after == before


# ── Allow Existing Branch Tests ──────────────────────────────────────────────


@requires_bash
class TestAllowExistingBranch:
    def test_allow_existing_reuses_existing_feature_dir(self, git_repo: Path):
        """T006: Existing feature directory can be reused when the flag is set."""
        feature_dir = git_repo / "specs" / "004-pre-exist"
        feature_dir.mkdir(parents=True)

        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "pre-exist",
            "--number", "4", "Pre-existing feature",
        )
        assert result.returncode == 0, result.stderr
        assert feature_dir.is_dir()
        assert (feature_dir / "spec.md").exists()

    def test_without_flag_still_errors(self, git_repo: Path):
        """T009: Existing feature directories still fail without the flag."""
        (git_repo / "specs" / "007-no-flag").mkdir(parents=True)
        result = run_script(
            git_repo, "--short-name", "no-flag", "--number", "7", "No flag feature",
        )
        assert result.returncode != 0, "should fail without --allow-existing-branch"
        assert "already exists" in result.stderr

    def test_allow_existing_no_overwrite_spec(self, git_repo: Path):
        """T010: Pre-create spec.md with content, verify it is preserved."""
        spec_dir = git_repo / "specs" / "008-no-overwrite"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("# My custom spec content\n")

        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "no-overwrite",
            "--number", "8", "No overwrite feature",
        )
        assert result.returncode == 0, result.stderr
        assert spec_file.read_text() == "# My custom spec content\n"

    def test_allow_existing_creates_feature_dir_when_missing(self, git_repo: Path):
        """T011: Verify normal directory creation when the feature dir does not exist."""
        result = run_script(
            git_repo, "--allow-existing-branch", "--short-name", "new-branch",
            "New branch feature",
        )
        assert result.returncode == 0, result.stderr
        assert (git_repo / "specs" / "001-new-branch").is_dir()

    def test_allow_existing_with_json(self, git_repo: Path):
        """T012: Verify JSON output is correct."""
        import json

        (git_repo / "specs" / "009-json-test").mkdir(parents=True)
        result = run_script(
            git_repo, "--allow-existing-branch", "--json", "--short-name", "json-test",
            "--number", "9", "JSON test",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "009-json-test"

    def test_allow_existing_no_git(self, no_git_dir: Path):
        """T013: Verify flag also works in non-git repos."""
        result = run_script(
            no_git_dir, "--allow-existing-branch", "--short-name", "no-git",
            "No git feature",
        )
        assert result.returncode == 0, result.stderr


class TestAllowExistingBranchPowerShell:
    def test_powershell_supports_allow_existing_branch_flag(self):
        """Static guard: PS script exposes and uses -AllowExistingBranch."""
        contents = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "-AllowExistingBranch" in contents
        assert "AllowExistingBranch" in contents.replace("-AllowExistingBranch", "")

    def test_powershell_reuses_existing_feature_dir(self):
        """Static guard: PS script handles existing feature directories without git."""
        contents = CREATE_FEATURE_PS.read_text(encoding="utf-8")
        assert "Feature directory '$featureDir' already exists" in contents
        assert "-not $AllowExistingBranch" in contents

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

    def test_dry_run_does_not_change_git_branch(self, git_repo: Path):
        """T010: Dry-run leaves the current git branch untouched."""
        before = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        result = run_script(
            git_repo, "--dry-run", "--short-name", "no-branch", "No branch feature"
        )
        assert result.returncode == 0, result.stderr
        after = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert after == before

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

    def test_dry_run_ignores_git_branches(self, git_repo: Path):
        """Dry-run uses only spec directories for numbering."""
        (git_repo / "specs" / "001-existing").mkdir(parents=True)
        subprocess.run(
            ["git", "checkout", "-b", "005-git-only"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        dry_result = run_script(
            git_repo, "--dry-run", "--short-name", "remote-test", "Remote test"
        )
        assert dry_result.returncode == 0, dry_result.stderr
        dry_branch = None
        for line in dry_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                dry_branch = line.split(":", 1)[1].strip()
        assert dry_branch == "002-remote-test", f"expected 002-remote-test, got: {dry_branch}"

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
        """T017: Dry-run works with --timestamp flag without mutating git state."""
        before = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
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
        after = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert after == before

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

    def test_ps_dry_run_does_not_change_git_branch(self, ps_git_repo: Path):
        """PowerShell -DryRun leaves the current git branch untouched."""
        before = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ps_git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        result = run_ps_script(
            ps_git_repo, "-DryRun", "-ShortName", "no-ps-branch", "No branch"
        )
        assert result.returncode == 0, result.stderr
        after = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ps_git_repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert after == before

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


# ── Short-Word / Acronym Branch-Name Tests ──────────────────────────────────


def _branch_from_output(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("BRANCH_NAME:"):
            return line.split(":", 1)[1].strip()
    return None


SHORT_WORD_CASES = [
    # description, expected branch — "go" (lowercase short word) is dropped,
    # "AI" (uppercase short word / acronym) is kept, "now" (>=3 chars) is kept.
    ("go AI now", "001-ai-now"),
    # A short word that is lowercase everywhere is dropped entirely.
    ("go to the pub", "001-pub"),
]


@requires_bash
class TestShortWordRetentionBash:
    """A short word is kept only when it appears in uppercase (an acronym)."""

    @pytest.mark.parametrize("description,expected", SHORT_WORD_CASES)
    def test_short_word_retention(self, git_repo: Path, description: str, expected: str):
        result = run_script(git_repo, "--dry-run", description)
        assert result.returncode == 0, result.stderr
        assert _branch_from_output(result.stdout) == expected


@pytest.mark.skipif(not _has_pwsh(), reason="pwsh not available")
class TestShortWordRetentionPowerShell:
    """PowerShell must match bash: a short word is kept only when uppercase.

    Regression guard for the `-match` (case-insensitive) vs `-cmatch`
    (case-sensitive) divergence — with `-match`, every short non-stop word
    leaked into the branch name even when it was lowercase.
    """

    @pytest.mark.parametrize("description,expected", SHORT_WORD_CASES)
    def test_short_word_retention(self, ps_git_repo: Path, description: str, expected: str):
        result = run_ps_script(ps_git_repo, "-DryRun", description)
        assert result.returncode == 0, result.stderr
        assert _branch_from_output(result.stdout) == expected


# ── GIT_BRANCH_NAME Override Tests ──────────────────────────────────────────


@requires_bash
class TestGitBranchNameOverrideBash:
    """Tests for GIT_BRANCH_NAME env var override in extension create-new-feature-branch.sh."""

    def _run_ext(self, ext_git_repo: Path, env_extras: dict, *extra_args: str):
        script = ext_git_repo / ".specify" / "extensions" / "git" / "scripts" / "bash" / "create-new-feature-branch.sh"
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
    """Tests for GIT_BRANCH_NAME env var override in extension create-new-feature-branch.ps1."""

    def _run_ext(self, ext_ps_git_repo: Path, env_extras: dict):
        script = ext_ps_git_repo / ".specify" / "extensions" / "git" / "scripts" / "powershell" / "create-new-feature-branch.ps1"
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
    def test_errors_without_env_var_or_feature_json(self, git_repo: Path):
        """Without env var or feature.json, get_feature_paths now errors."""
        spec_dir = git_repo / "specs" / "001-test-feat"
        spec_dir.mkdir(parents=True)

        result = subprocess.run(
            ["bash", "-c", f'source "{COMMON_SH}" && get_feature_paths'],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Feature directory not found" in result.stderr

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
        """Extension create-new-feature-branch.sh succeeds with special characters in description."""
        script = (
            ext_git_repo
            / ".specify"
            / "extensions"
            / "git"
            / "scripts"
            / "bash"
            / "create-new-feature-branch.sh"
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
