"""
Tests for scripts/bash/create-new-feature.sh.

Tests cover:
- JSON output validity when git fetch produces stdout noise (#1592)
- Correct stdout/stderr suppression in check_existing_branches()
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "bash" / "create-new-feature.sh"

requires_git = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is not installed",
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo for testing create-new-feature.sh."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], capture_output=True, check=True)

    # Create an initial commit so HEAD exists
    (repo / "README.md").write_text("# Test")
    subprocess.run(["git", "-C", str(repo), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "config", "commit.gpgsign", "false"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], capture_output=True, check=True)

    # Create .specify dir to simulate an initialized project
    (repo / ".specify").mkdir()
    (repo / ".specify" / "templates").mkdir()

    yield repo


@requires_git
class TestCreateNewFeatureJsonOutput:
    """Test that --json output is always valid JSON (#1592)."""

    def test_json_output_is_valid(self, git_repo):
        """Script should produce valid JSON with BRANCH_NAME, SPEC_FILE, FEATURE_NUM."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--json", "Test feature description"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        output = result.stdout.strip()
        parsed = json.loads(output)

        assert "BRANCH_NAME" in parsed
        assert "SPEC_FILE" in parsed
        assert "FEATURE_NUM" in parsed

    def test_feature_num_is_numeric(self, git_repo):
        """FEATURE_NUM should be a zero-padded numeric string."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--json", "Another feature"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        parsed = json.loads(result.stdout.strip())
        feature_num = parsed["FEATURE_NUM"]

        assert feature_num.isdigit(), f"FEATURE_NUM is not numeric: {feature_num}"
        assert len(feature_num) == 3, f"FEATURE_NUM is not zero-padded: {feature_num}"


@requires_git
class TestGitFetchSilencing:
    """Verify that git fetch stdout does not contaminate branch number detection."""

    def test_script_does_not_leak_git_fetch_stdout(self, git_repo):
        """JSON output should contain only the JSON line, no git fetch noise."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--json", "Verify no fetch noise"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        stdout_lines = result.stdout.strip().splitlines()
        # In JSON mode, stdout should contain exactly one line: the JSON object
        json_lines = [line for line in stdout_lines if line.startswith("{")]
        assert len(json_lines) == 1, f"Expected 1 JSON line, got {len(json_lines)}: {stdout_lines}"

    def test_script_does_not_leak_git_fetch_to_json(self, git_repo):
        """Repeated runs should always produce clean JSON without fetch artifacts."""
        for i in range(2):
            result = subprocess.run(
                ["bash", str(SCRIPT_PATH), "--json", f"Run {i} verify clean"],
                capture_output=True,
                text=True,
                cwd=str(git_repo),
            )
            assert result.returncode == 0, f"Run {i} failed: {result.stderr}"
            parsed = json.loads(result.stdout.strip())
            assert parsed["FEATURE_NUM"].isdigit()


class TestScriptRedirectPattern:
    """Static analysis: verify the script uses correct redirect patterns."""

    def test_git_fetch_redirect_pattern_in_script(self):
        """The git fetch call should redirect both stdout and stderr to /dev/null."""
        script_content = SCRIPT_PATH.read_text()

        assert "git fetch --all --prune >/dev/null 2>&1" in script_content, (
            "git fetch should redirect both stdout and stderr: >/dev/null 2>&1"
        )
        assert "git fetch --all --prune 2>/dev/null" not in script_content, (
            "git fetch should NOT redirect only stderr (old pattern)"
        )
