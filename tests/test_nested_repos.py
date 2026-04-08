"""
Pytest tests for nested independent git repository support.

Tests cover:
- Discovery of nested git repos via find_nested_git_repos (bash)
- Configurable scan depth for discovery
- Excluded directories are skipped
- setup-plan.sh reports discovered nested repos in JSON output
- create-new-feature.sh does NOT create branches in nested repos
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
SETUP_PLAN = PROJECT_ROOT / "scripts" / "bash" / "setup-plan.sh"
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


def _setup_scripts(root: Path) -> None:
    """Copy scripts and create .specify structure in a test repo."""
    scripts_dir = root / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    shutil.copy(CREATE_FEATURE, scripts_dir / "create-new-feature.sh")
    shutil.copy(SETUP_PLAN, scripts_dir / "setup-plan.sh")
    shutil.copy(COMMON_SH, scripts_dir / "common.sh")
    (root / ".specify" / "templates").mkdir(parents=True)


@pytest.fixture
def git_repo_with_nested(tmp_path: Path) -> Path:
    """Create a root git repo with nested independent git repos."""
    _init_git_repo(tmp_path)
    _setup_scripts(tmp_path)

    # Nested repo at level 2: components/core
    core_dir = tmp_path / "components" / "core"
    core_dir.mkdir(parents=True)
    _init_git_repo(core_dir)

    # Nested repo at level 2: components/api
    api_dir = tmp_path / "components" / "api"
    api_dir.mkdir(parents=True)
    _init_git_repo(api_dir)

    return tmp_path


@pytest.fixture
def git_repo_no_nested(tmp_path: Path) -> Path:
    """Create a root git repo with no nested git repos."""
    _init_git_repo(tmp_path)
    _setup_scripts(tmp_path)

    # Regular subdirectory without .git
    (tmp_path / "components" / "core").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def git_repo_with_excluded_dirs(tmp_path: Path) -> Path:
    """Create a root git repo where git repos exist inside excluded directories."""
    _init_git_repo(tmp_path)
    _setup_scripts(tmp_path)

    # Git repo inside node_modules (should be excluded)
    nm_dir = tmp_path / "node_modules" / "some-pkg"
    nm_dir.mkdir(parents=True)
    _init_git_repo(nm_dir)

    # Valid nested repo
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir(parents=True)
    _init_git_repo(lib_dir)

    return tmp_path


def run_create_feature(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run create-new-feature.sh with given args."""
    cmd = [BASH, "scripts/bash/create-new-feature.sh", *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def run_setup_plan(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run setup-plan.sh with given args."""
    cmd = [BASH, "scripts/bash/setup-plan.sh", *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def parse_json_from_output(stdout: str) -> dict:
    """Extract JSON object from script output that may contain non-JSON lines (warnings)."""
    for line in stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError(f"No JSON found in output: {stdout!r}")


def source_and_call(func_call: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Source common.sh and call a function."""
    cmd = f'source "{COMMON_SH}" && {func_call}'
    return subprocess.run(
        [BASH, "-c", cmd], cwd=cwd, capture_output=True, text=True, env=os.environ.copy()
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
        scripts_dir = tmp_path / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        shutil.copy(COMMON_SH, scripts_dir / "common.sh")

        nested = tmp_path / "mylib"
        nested.mkdir()
        _init_git_repo(nested)

        result = source_and_call(
            f'find_nested_git_repos "{tmp_path}"',
            cwd=tmp_path,
        )
        assert result.returncode == 0
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
        assert len(paths) == 1
        assert os.path.basename(paths[0]) == "mylib"


# ── Configurable Depth Tests ─────────────────────────────────────────────────


class TestConfigurableDepth:
    def test_depth_1_misses_level2_repos(self, git_repo_with_nested: Path):
        """Depth 1 only scans immediate children; level-2 repos are missed."""
        result = source_and_call(
            f'find_nested_git_repos "{git_repo_with_nested}" 1',
            cwd=git_repo_with_nested,
        )
        assert result.returncode == 0, result.stderr
        paths = [p.strip().rstrip("/") for p in result.stdout.strip().splitlines() if p.strip()]
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

    def test_depth_3_finds_deep_repos(self, tmp_path: Path):
        """Depth 3 discovers repos at level 3."""
        _init_git_repo(tmp_path)
        (tmp_path / ".specify").mkdir()
        scripts_dir = tmp_path / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        shutil.copy(COMMON_SH, scripts_dir / "common.sh")

        deep_dir = tmp_path / "services" / "backend" / "auth"
        deep_dir.mkdir(parents=True)
        _init_git_repo(deep_dir)

        # Depth 2: should NOT find it
        result2 = source_and_call(f'find_nested_git_repos "{tmp_path}" 2', cwd=tmp_path)
        assert result2.returncode == 0
        assert result2.stdout.strip() == ""

        # Depth 3: should find it
        result3 = source_and_call(f'find_nested_git_repos "{tmp_path}" 3', cwd=tmp_path)
        assert result3.returncode == 0
        paths3 = [p.strip().rstrip("/") for p in result3.stdout.strip().splitlines() if p.strip()]
        assert len(paths3) == 1
        assert os.path.basename(paths3[0]) == "auth"


# ── Create Feature Does NOT Branch Nested Repos ─────────────────────────────


class TestCreateFeatureNoNestedBranching:
    def test_no_nested_repos_in_json(self, git_repo_with_nested: Path):
        """create-new-feature JSON output should NOT contain NESTED_REPOS."""
        result = run_create_feature(
            git_repo_with_nested,
            "--json", "--short-name", "my-feat", "Add a feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        assert "NESTED_REPOS" not in data
        assert "BRANCH_NAME" in data

    def test_nested_repos_not_branched(self, git_repo_with_nested: Path):
        """create-new-feature should not create branches in nested repos."""
        result = run_create_feature(
            git_repo_with_nested,
            "--json", "--short-name", "no-nest", "No nesting",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout.strip())
        branch_name = data["BRANCH_NAME"]

        # Nested repos should still be on their original branch
        for subdir in ["components/core", "components/api"]:
            br = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_repo_with_nested / subdir,
                capture_output=True, text=True,
            )
            assert br.stdout.strip() != branch_name


# ── Setup Plan Discovery Tests ───────────────────────────────────────────────


class TestSetupPlanDiscovery:
    def _create_feature_first(self, repo: Path) -> str:
        """Helper: create a feature branch so setup-plan has a valid branch."""
        result = run_create_feature(
            repo, "--json", "--short-name", "plan-test", "Plan test feature",
        )
        assert result.returncode == 0, result.stderr
        data = parse_json_from_output(result.stdout)
        return data["BRANCH_NAME"]

    def test_discovers_nested_repos_in_json(self, git_repo_with_nested: Path):
        """setup-plan JSON output includes NESTED_REPOS with discovered repos."""
        self._create_feature_first(git_repo_with_nested)
        result = run_setup_plan(git_repo_with_nested, "--json")
        assert result.returncode == 0, result.stderr
        data = parse_json_from_output(result.stdout)

        assert "NESTED_REPOS" in data
        nested = sorted(data["NESTED_REPOS"], key=lambda x: x["path"])
        assert len(nested) == 2
        assert nested[0]["path"] == "components/api"
        assert nested[1]["path"] == "components/core"

    def test_no_nested_repos_returns_empty_array(self, git_repo_no_nested: Path):
        """setup-plan JSON has empty NESTED_REPOS when no nested repos exist."""
        self._create_feature_first(git_repo_no_nested)
        result = run_setup_plan(git_repo_no_nested, "--json")
        assert result.returncode == 0, result.stderr
        data = parse_json_from_output(result.stdout)
        assert data["NESTED_REPOS"] == []

    def test_scan_depth_flag(self, tmp_path: Path):
        """--scan-depth controls discovery depth in setup-plan."""
        _init_git_repo(tmp_path)
        _setup_scripts(tmp_path)

        # Level 3 repo
        deep_dir = tmp_path / "services" / "backend" / "auth"
        deep_dir.mkdir(parents=True)
        _init_git_repo(deep_dir)

        # Create feature branch first
        run_create_feature(
            tmp_path, "--json", "--short-name", "depth-plan", "Depth plan test",
        )

        # Default depth (2): should not find level-3 repo
        result = run_setup_plan(tmp_path, "--json")
        assert result.returncode == 0, result.stderr
        data = parse_json_from_output(result.stdout)
        assert data["NESTED_REPOS"] == []

        # Depth 3: should find it
        result3 = run_setup_plan(tmp_path, "--json", "--scan-depth", "3")
        assert result3.returncode == 0, result3.stderr
        data3 = parse_json_from_output(result3.stdout)
        assert len(data3["NESTED_REPOS"]) == 1
        assert data3["NESTED_REPOS"][0]["path"] == "services/backend/auth"

    def test_discovery_does_not_create_branches(self, git_repo_with_nested: Path):
        """setup-plan discovers repos but does NOT create branches in them."""
        self._create_feature_first(git_repo_with_nested)
        result = run_setup_plan(git_repo_with_nested, "--json")
        assert result.returncode == 0, result.stderr
        data = parse_json_from_output(result.stdout)
        branch_name = data["BRANCH"]

        # Nested repos should still be on their original branch
        for subdir in ["components/core", "components/api"]:
            br = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_repo_with_nested / subdir,
                capture_output=True, text=True,
            )
            assert br.stdout.strip() != branch_name
