"""
Tests for Cursor .mdc frontmatter generation (issue #669).

Verifies that update-agent-context.sh properly prepends YAML frontmatter
to .mdc files so that Cursor IDE auto-includes the rules.
"""

import os
import shutil
import subprocess
import textwrap

import pytest

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    "scripts",
    "bash",
    "update-agent-context.sh",
)

EXPECTED_FRONTMATTER_LINES = [
    "---",
    "description: Project Development Guidelines",
    'globs: ["**/*"]',
    "alwaysApply: true",
    "---",
]

requires_git = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is not installed",
)


class TestScriptFrontmatterPattern:
    """Static analysis — no git required."""

    def test_create_new_has_mdc_frontmatter_logic(self):
        """create_new_agent_file() must contain .mdc frontmatter logic."""
        with open(SCRIPT_PATH, encoding="utf-8") as f:
            content = f.read()
        assert 'if [[ "$target_file" == *.mdc ]]' in content
        assert "alwaysApply: true" in content

    def test_update_existing_has_mdc_frontmatter_logic(self):
        """update_existing_agent_file() must also handle .mdc frontmatter."""
        with open(SCRIPT_PATH, encoding="utf-8") as f:
            content = f.read()
        # There should be two occurrences of the .mdc check — one per function
        occurrences = content.count('if [[ "$target_file" == *.mdc ]]')
        assert occurrences >= 2, (
            f"Expected at least 2 .mdc frontmatter checks, found {occurrences}"
        )

    def test_powershell_script_has_mdc_frontmatter_logic(self):
        """PowerShell script must also handle .mdc frontmatter."""
        ps_path = os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            "scripts",
            "powershell",
            "update-agent-context.ps1",
        )
        with open(ps_path, encoding="utf-8") as f:
            content = f.read()
        assert "alwaysApply: true" in content
        occurrences = content.count(r"\.mdc$")
        assert occurrences >= 2, (
            f"Expected at least 2 .mdc frontmatter checks in PS script, found {occurrences}"
        )


@requires_git
class TestCursorFrontmatterIntegration:
    """Integration tests using a real git repo."""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a minimal git repo with the spec-kit structure."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Init git repo
        subprocess.run(
            ["git", "init"], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )

        # Create .specify dir with config
        specify_dir = repo / ".specify"
        specify_dir.mkdir()
        (specify_dir / "config.yaml").write_text(
            textwrap.dedent("""\
                project_type: webapp
                language: python
                framework: fastapi
                database: N/A
            """)
        )

        # Create template
        templates_dir = specify_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "agent-file-template.md").write_text(
            "# [PROJECT NAME] Development Guidelines\n\n"
            "Auto-generated from all feature plans. Last updated: [DATE]\n\n"
            "## Active Technologies\n\n"
            "[EXTRACTED FROM ALL PLAN.MD FILES]\n\n"
            "## Project Structure\n\n"
            "[ACTUAL STRUCTURE FROM PLANS]\n\n"
            "## Development Commands\n\n"
            "[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]\n\n"
            "## Coding Conventions\n\n"
            "[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]\n\n"
            "## Recent Changes\n\n"
            "[LAST 3 FEATURES AND WHAT THEY ADDED]\n"
        )

        # Create initial commit
        subprocess.run(
            ["git", "add", "-A"], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )

        # Create a feature branch so CURRENT_BRANCH detection works
        subprocess.run(
            ["git", "checkout", "-b", "001-test-feature"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )

        # Create a spec so the script detects the feature
        spec_dir = repo / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        (spec_dir / "plan.md").write_text(
            "# Test Feature Plan\n\n"
            "## Technology Stack\n\n"
            "- Language: Python\n"
            "- Framework: FastAPI\n"
        )

        return repo

    def _run_update(self, repo, agent_type="cursor-agent"):
        """Run update-agent-context.sh for a specific agent type."""
        script = os.path.abspath(SCRIPT_PATH)
        result = subprocess.run(
            ["bash", script, agent_type],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result

    def test_new_mdc_file_has_frontmatter(self, git_repo):
        """Creating a new .mdc file must include YAML frontmatter."""
        result = self._run_update(git_repo)
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        mdc_file = git_repo / ".cursor" / "rules" / "specify-rules.mdc"
        assert mdc_file.exists(), "Cursor .mdc file was not created"

        content = mdc_file.read_text()
        lines = content.splitlines()

        # First line must be the opening ---
        assert lines[0] == "---", f"Expected frontmatter start, got: {lines[0]}"

        # Check all frontmatter lines are present
        for expected in EXPECTED_FRONTMATTER_LINES:
            assert expected in content, f"Missing frontmatter line: {expected}"

        # Content after frontmatter should be the template content
        assert "Development Guidelines" in content

    def test_existing_mdc_without_frontmatter_gets_it_added(self, git_repo):
        """Updating an existing .mdc file that lacks frontmatter must add it."""
        # First, create the file WITHOUT frontmatter (simulating pre-fix state)
        cursor_dir = git_repo / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mdc_file = cursor_dir / "specify-rules.mdc"
        mdc_file.write_text(
            "# repo Development Guidelines\n\n"
            "Auto-generated from all feature plans. Last updated: 2025-01-01\n\n"
            "## Active Technologies\n\n"
            "- Python + FastAPI (main)\n\n"
            "## Recent Changes\n\n"
            "- main: Added Python + FastAPI\n"
        )

        result = self._run_update(git_repo)
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        content = mdc_file.read_text()
        lines = content.splitlines()

        assert lines[0] == "---", f"Expected frontmatter start, got: {lines[0]}"
        for expected in EXPECTED_FRONTMATTER_LINES:
            assert expected in content, f"Missing frontmatter line: {expected}"

    def test_existing_mdc_with_frontmatter_not_duplicated(self, git_repo):
        """Updating an .mdc file that already has frontmatter must not duplicate it."""
        cursor_dir = git_repo / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mdc_file = cursor_dir / "specify-rules.mdc"

        frontmatter = (
            "---\n"
            "description: Project Development Guidelines\n"
            'globs: ["**/*"]\n'
            "alwaysApply: true\n"
            "---\n\n"
        )
        body = (
            "# repo Development Guidelines\n\n"
            "Auto-generated from all feature plans. Last updated: 2025-01-01\n\n"
            "## Active Technologies\n\n"
            "- Python + FastAPI (main)\n\n"
            "## Recent Changes\n\n"
            "- main: Added Python + FastAPI\n"
        )
        mdc_file.write_text(frontmatter + body)

        result = self._run_update(git_repo)
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        content = mdc_file.read_text()
        # Count occurrences of the frontmatter delimiter
        assert content.count("alwaysApply: true") == 1, (
            "Frontmatter was duplicated"
        )

    def test_non_mdc_file_has_no_frontmatter(self, git_repo):
        """Non-.mdc agent files (e.g., Claude) must NOT get frontmatter."""
        result = self._run_update(git_repo, agent_type="claude")
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        claude_file = git_repo / ".claude" / "CLAUDE.md"
        if claude_file.exists():
            content = claude_file.read_text()
            assert not content.startswith("---"), (
                "Non-mdc file should not have frontmatter"
            )
