"""
Pytest tests for nested independent git repository support in create-new-feature scripts.

Tests cover:
- Discovery of nested git repos via find_nested_git_repos (bash) / Find-NestedGitRepos (PS)
- Configurable scan depth for nested repo discovery
- Selective branching via --repos flag
- Branch creation in nested repos during feature creation
- JSON output includes NESTED_REPOS field
- --dry-run reports nested repos without creating branches
- --allow-existing-branch propagates to nested repos
- Excluded directories are skipped
- Graceful handling when nested repos cannot be branched
"""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREATE_FEATURE = PROJECT_ROOT / "scripts" / "bash" / "create-new-feature.sh"
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"

# On Windows, prefer Git Bash over WSL bash
if platform.system() == "Windows":
    _GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
    BASH = str(_GIT_BASH) if _GIT_BASH.exists() else "bash"
else:
    BASH = "bash"


def _init_git_repo(path: Path) -> None:
    """Initialize a git repo at the given path with an initial commit."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=path,
        check=True,
    )


@pytest.fixture
def git_repo_with_nested(tmp_path: Path) -> Path:
    """Create a root git repo with nested independent git repos."""
    # Root repo
    _init_git_repo(tmp_path)
    scripts_dir = tmp_path / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True)

    # Nested repo at level 1: components/core
    core_dir = tmp_path / "components" / "core"
    core_dir.mkdir(parents=True)
    _init_git_repo(core_dir)

    # Nested repo at level 1: components/api
    api_dir = tmp_path / "components" / "api"
    api_dir.mkdir(parents=True)
    _init_git_repo(api_dir)

    return tmp_path


@pytest.fixture
def git_repo_no_nested(tmp_path: Path) -> Path:
    """Create a root git repo with no nested git repos."""
    _init_git_repo(tmp_path)
    scripts_dir = tmp_path / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True)

    # Regular subdirectory without .git
    (tmp_path / "components" / "core").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def git_repo_with_excluded_dirs(tmp_path: Path) -> Path:
    """Create a root git repo where git repos exist inside excluded directories."""
    _init_git_repo(tmp_path)
    scripts_dir = tmp_path / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (tmp_path / ".specify" / "templates").mkdir(parents=True)

    # Git repo inside node_modules (should be excluded)
    nm_dir = tmp_path / "node_modules" / "some-pkg"
    nm_dir.mkdir(parents=True)
    _init_git_repo(nm_dir)

    # Valid nested repo
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir(parents=True)
    _init_git_repo(lib_dir)

    return tmp_path


def run_script(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run create-new-feature.sh with given args."""
    cmd = [BASH, "scripts/bash/create-new-feature.sh", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def source_and_call(func_call: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Source common.sh and call a function."""
    cmd = f'source "{COMMON_SH}" && {func_call}'
    return subprocess.run(
        [BASH, "-c", cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


# ── Discovery Tests ──────────────────────────────────────────────────────────


class TestFindNestedGitRepos:
    def test_discovers_nested_repos(self, git_repo_with_nested: Path):
        """find_nested_git_repos discovers nested repos at level 2."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_with_nested}"',
            cwd=git_repo_with_nested,
        )
        assert result.returncode == 0, result.stderr
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        assert len(paths) == 2
        basenames = sorted(os.path.basename(p) for p in paths)
        assert basenames == ["api", "core"]

    def test_no_nested_repos_returns_empty(self, git_repo_no_nested: Path):
        """find_nested_git_repos returns empty when no nested repos exist."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_no_nested}"',
            cwd=git_repo_no_nested,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_excludes_node_modules(self, git_repo_with_excluded_dirs: Path):
        """find_nested_git_repos skips repos inside excluded directories."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_with_excluded_dirs}"',
            cwd=git_repo_with_excluded_dirs,
        )
        assert result.returncode == 0
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        assert len(paths) == 1
        assert os.path.basename(paths[0]) == "lib"

    def test_discovers_level1_repos(self, tmp_path: Path):
        """find_nested_git_repos discovers repos directly under root (level 1)."""
        _init_git_repo(tmp_path)
        (tmp_path / ".specify").mkdir()

        # Level 1 nested repo
        nested = tmp_path / "mylib"
        nested.mkdir()
        _init_git_repo(nested)

        scripts_dir = tmp_path / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        shutil.copy(COMMON_SH, scripts_dir / "common.sh")

        result = source_and_call(
            f'find_nested_git_repos "{tmp_path}"',
            cwd=tmp_path,
        )
        assert result.returncode == 0
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        assert len(paths) == 1
        assert os.path.basename(paths[0]) == "mylib"


# ── Branch Creation Tests ────────────────────────────────────────────────────


class TestNestedRepoBranchCreation:
    def test_creates_branch_in_nested_repos(self, git_repo_with_nested: Path):
        """Feature branch is created in all nested repos."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--short-name", "my-feat",
            "Add a feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        # Verify root branch
        assert data["BRANCH_NAME"] == "001-my-feat"

        # Verify nested repos
        assert "NESTED_REPOS" in data
        nested = sorted(data["NESTED_REPOS"], key=lambda x: x["path"])
        assert len(nested) == 2
        assert nested[0]["path"] == "components/api"
        assert nested[0]["status"] == "created"
        assert nested[1]["path"] == "components/core"
        assert nested[1]["status"] == "created"

        # Verify branches actually exist in nested repos
        for subdir in ["components/core", "components/api"]:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_repo_with_nested / subdir,
                capture_output=True,
                text=True,
            )
            assert branch_result.stdout.strip() == "001-my-feat"

    def test_no_nested_repos_returns_empty_array(self, git_repo_no_nested: Path):
        """JSON output has empty NESTED_REPOS when no nested repos exist."""
        result = run_script(
            git_repo_no_nested,
            "--json",
            "--short-name", "solo-feat",
            "Solo feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        assert data["NESTED_REPOS"] == []

    def test_dry_run_does_not_create_branches(self, git_repo_with_nested: Path):
        """--dry-run reports nested repos but does not create branches."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--dry-run",
            "--short-name", "dry-feat",
            "Dry run feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        assert data.get("DRY_RUN") is True

        nested = data.get("NESTED_REPOS", [])
        assert len(nested) == 2
        for entry in nested:
            assert entry["status"] == "dry_run"

        # Verify branches were NOT created in nested repos
        for subdir in ["components/core", "components/api"]:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_repo_with_nested / subdir,
                capture_output=True,
                text=True,
            )
            # Should still be on the default branch (main or master)
            assert branch_result.stdout.strip() != "001-dry-feat"

    def test_allow_existing_branch_in_nested(self, git_repo_with_nested: Path):
        """--allow-existing-branch works for nested repos where branch already exists."""
        # First, create the branch in one nested repo manually
        subprocess.run(
            ["git", "checkout", "-b", "001-existing-feat"],
            cwd=git_repo_with_nested / "components" / "core",
            check=True,
            capture_output=True,
        )
        # Switch back so the create script can still create in root
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=git_repo_with_nested / "components" / "core",
            check=True,
            capture_output=True,
        )

        result = run_script(
            git_repo_with_nested,
            "--json",
            "--allow-existing-branch",
            "--number", "1",
            "--short-name", "existing-feat",
            "Existing feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        nested = {e["path"]: e["status"] for e in data["NESTED_REPOS"]}
        # core had the branch pre-created, should report 'existing'
        assert nested["components/core"] == "existing"
        # api should be freshly created
        assert nested["components/api"] == "created"

    def test_excluded_dirs_not_branched(self, git_repo_with_excluded_dirs: Path):
        """Repos inside excluded directories like node_modules are not branched."""
        result = run_script(
            git_repo_with_excluded_dirs,
            "--json",
            "--short-name", "excl-feat",
            "Exclusion test",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        nested = data.get("NESTED_REPOS", [])
        paths = [e["path"] for e in nested]
        assert "lib" in paths
        assert not any("node_modules" in p for p in paths)


# ── Configurable Depth Tests ─────────────────────────────────────────────────


class TestConfigurableDepth:
    def test_depth_1_misses_level2_repos(self, git_repo_with_nested: Path):
        """Depth 1 only scans immediate children; level-2 repos under components/ are missed."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_with_nested}" 1',
            cwd=git_repo_with_nested,
        )
        assert result.returncode == 0, result.stderr
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        # components/core and components/api are at depth 2, so depth=1 should find nothing
        assert len(paths) == 0

    def test_depth_2_finds_level2_repos(self, git_repo_with_nested: Path):
        """Depth 2 (default) discovers repos at level 2."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_with_nested}" 2',
            cwd=git_repo_with_nested,
        )
        assert result.returncode == 0, result.stderr
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        assert len(paths) == 2
        basenames = sorted(os.path.basename(p) for p in paths)
        assert basenames == ["api", "core"]

    def test_depth_3_finds_deep_repos(self, tmp_path: Path):
        """Depth 3 discovers repos at level 3."""
        _init_git_repo(tmp_path)
        (tmp_path / ".specify").mkdir()
        scripts_dir = tmp_path / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        shutil.copy(COMMON_SH, scripts_dir / "common.sh")

        # Level 3 nested repo: services/backend/auth
        deep_dir = tmp_path / "services" / "backend" / "auth"
        deep_dir.mkdir(parents=True)
        _init_git_repo(deep_dir)

        # With depth=2, should NOT find it
        result2 = source_and_call(
            f'find_nested_git_repos "{tmp_path}" 2',
            cwd=tmp_path,
        )
        assert result2.returncode == 0
        paths2 = [p.strip().rstrip("/") for p in result2.stdout.strip().splitlines() if p.strip()]
        assert len(paths2) == 0

        # With depth=3, should find it
        result3 = source_and_call(
            f'find_nested_git_repos "{tmp_path}" 3',
            cwd=tmp_path,
        )
        assert result3.returncode == 0
        paths3 = [p.strip().rstrip("/") for p in result3.stdout.strip().splitlines() if p.strip()]
        assert len(paths3) == 1
        assert os.path.basename(paths3[0]) == "auth"

    def test_scan_depth_flag(self, tmp_path: Path):
        """--scan-depth flag controls discovery depth in create-new-feature."""
        _init_git_repo(tmp_path)
        scripts_dir = tmp_path / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
        shutil.copy(COMMON_SH, scripts_dir / "common.sh")
        (tmp_path / ".specify" / "templates").mkdir(parents=True)

        # Level 3 repo
        deep_dir = tmp_path / "services" / "backend" / "auth"
        deep_dir.mkdir(parents=True)
        _init_git_repo(deep_dir)

        # Default depth (2): should not find level-3 repo
        result = run_script(tmp_path, "--json", "--short-name", "depth-test", "Depth test")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        assert data["NESTED_REPOS"] == []

        # Depth 3: should find it (need a new branch name since first run took 001)
        result3 = run_script(
            tmp_path, "--json", "--scan-depth", "3",
            "--short-name", "depth-test3", "Depth test 3",
        )
        assert result3.returncode == 0, result3.stderr
        data3 = json.loads(result3.stdout.strip())
        assert len(data3["NESTED_REPOS"]) == 1
        assert data3["NESTED_REPOS"][0]["path"] == "services/backend/auth"
        assert data3["NESTED_REPOS"][0]["status"] == "created"


# ── Selective Branching Tests ────────────────────────────────────────────────


class TestSelectiveBranching:
    def test_repos_flag_filters_to_selected(self, git_repo_with_nested: Path):
        """--repos flag causes only selected repos to be branched."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--repos", "components/core",
            "--short-name", "sel-feat",
            "Selective feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        nested = data["NESTED_REPOS"]
        assert len(nested) == 1
        assert nested[0]["path"] == "components/core"
        assert nested[0]["status"] == "created"

        # api should NOT have the branch
        api_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo_with_nested / "components" / "api",
            capture_output=True, text=True,
        )
        assert api_branch.stdout.strip() != "001-sel-feat"

    def test_repos_flag_multiple_repos(self, git_repo_with_nested: Path):
        """--repos with comma-separated list branches only those repos."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--repos", "components/core,components/api",
            "--short-name", "multi-sel",
            "Multi select",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        nested = sorted(data["NESTED_REPOS"], key=lambda x: x["path"])
        assert len(nested) == 2
        assert nested[0]["path"] == "components/api"
        assert nested[0]["status"] == "created"
        assert nested[1]["path"] == "components/core"
        assert nested[1]["status"] == "created"

    def test_repos_flag_nonexistent_repo_excluded(self, git_repo_with_nested: Path):
        """--repos with a path that doesn't match any discovered repo produces empty result."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--repos", "nonexistent/repo",
            "--short-name", "no-match",
            "No match feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        assert data["NESTED_REPOS"] == []

    def test_repos_flag_with_dry_run(self, git_repo_with_nested: Path):
        """--repos combined with --dry-run filters and reports dry_run status."""
        result = run_script(
            git_repo_with_nested,
            "--json",
            "--dry-run",
            "--repos", "components/api",
            "--short-name", "dry-sel",
            "Dry selective",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())

        nested = data["NESTED_REPOS"]
        assert len(nested) == 1
        assert nested[0]["path"] == "components/api"
        assert nested[0]["status"] == "dry_run"
