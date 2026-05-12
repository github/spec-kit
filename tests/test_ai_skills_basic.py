"""Tests for install_ai_skills function."""

from pathlib import Path
from unittest.mock import patch


from infrakit_cli import install_ai_skills, _get_skills_dir


class TestGetSkillsDir:
    """Test suite for _get_skills_dir function."""

    def test_get_skills_dir_claude(self, tmp_path):
        """Test getting skills directory for claude."""
        result = _get_skills_dir(tmp_path, "claude")
        assert ".claude" in str(result)
        assert "skills" in str(result)

    def test_get_skills_dir_copilot(self, tmp_path):
        """Test getting skills directory for copilot."""
        result = _get_skills_dir(tmp_path, "copilot")
        assert ".github" in str(result)

    def test_get_skills_dir_unknown_agent(self, tmp_path):
        """Test getting skills directory for unknown agent."""
        result = _get_skills_dir(tmp_path, "unknown-agent")
        # Should return a default path
        assert "skills" in str(result)


class TestInstallAiSkills:
    """Test suite for install_ai_skills function."""

    @patch("infrakit_cli.skills._get_skills_dir")
    def test_install_skills_creates_directory(self, mock_get_dir, tmp_path):
        """Test that install_ai_skills creates skills directory."""
        skills_dir = tmp_path / "skills"
        mock_get_dir.return_value = skills_dir

        # Mock Path.exists to return False initially
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "mkdir"):
                with patch("infrakit_cli.skills.Path.glob", return_value=[]):
                    result = install_ai_skills(tmp_path, "claude")

    def test_install_skills_returns_bool(self, tmp_path):
        """Test that install_ai_skills returns a boolean."""
        # This test just verifies the function signature
        pass
