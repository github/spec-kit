"""Tests for utility functions in specify_cli."""

from specify_cli import AI_CHOICES, SCRIPT_TYPE_CHOICES


class TestConstants:
    """Test module constants."""

    def test_ai_choices_not_empty(self):
        """Verify AI_CHOICES contains expected agents."""
        # Assert
        assert len(AI_CHOICES) > 0
        assert isinstance(AI_CHOICES, dict)

    def test_ai_choices_contains_core_agents(self):
        """Verify core AI agents are available."""
        # Assert
        expected_agents = {"claude", "gemini", "copilot", "cursor"}
        assert expected_agents.issubset(set(AI_CHOICES.keys()))

    def test_ai_choices_contains_all_supported_agents(self):
        """Verify all documented AI agents are in choices."""
        # Assert
        documented_agents = {
            "claude",
            "gemini",
            "copilot",
            "cursor",
            "qwen",
            "opencode",
            "codex",
            "windsurf",
            "kilocode",
            "auggie",
            "roo",
        }
        assert documented_agents.issubset(set(AI_CHOICES.keys()))

    def test_ai_choices_values_are_strings(self):
        """Verify AI choice values are descriptive strings."""
        # Assert
        for key, value in AI_CHOICES.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value) > 0

    def test_script_type_choices_not_empty(self):
        """Verify SCRIPT_TYPE_CHOICES contains expected shells."""
        # Assert
        assert len(SCRIPT_TYPE_CHOICES) > 0
        assert isinstance(SCRIPT_TYPE_CHOICES, dict)

    def test_script_type_choices_contains_all_shells(self):
        """Verify all script types are available."""
        # Assert
        expected_shells = {"sh", "ps", "fish"}
        assert expected_shells.issubset(set(SCRIPT_TYPE_CHOICES.keys()))

    def test_script_type_choices_values_are_strings(self):
        """Verify script type choice values are descriptive strings."""
        # Assert
        for key, value in SCRIPT_TYPE_CHOICES.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value) > 0


class TestTemplateFiles:
    """Test template file operations."""

    def test_template_directory_exists(self, sample_templates):
        """Verify templates directory exists."""
        # Assert
        assert sample_templates.exists()
        assert sample_templates.is_dir()

    def test_core_template_files_exist(self, sample_templates):
        """Verify required template files exist."""
        # Assert
        core_templates = [
            "spec-template.md",
            "plan-template.md",
            "tasks-template.md",
        ]
        for template in core_templates:
            template_path = sample_templates / template
            assert template_path.exists(), f"{template} should exist"
            assert template_path.is_file(), f"{template} should be a file"

    def test_command_templates_directory_exists(self, sample_templates):
        """Verify command templates directory exists."""
        # Assert
        commands_dir = sample_templates / "commands"
        assert commands_dir.exists()
        assert commands_dir.is_dir()

    def test_command_template_files_exist(self, sample_templates):
        """Verify command template files exist."""
        # Assert
        commands_dir = sample_templates / "commands"
        command_templates = [
            "specify.md",
            "plan.md",
            "tasks.md",
            "implement.md",
            "clarify.md",
            "analyze.md",
        ]
        for template in command_templates:
            template_path = commands_dir / template
            assert template_path.exists(), f"{template} should exist"
            assert template_path.is_file(), f"{template} should be a file"


class TestGitHelpers:
    """Test git helper functions."""

    def test_is_git_repo_true(self, mocker, tmp_path):
        """Test is_git_repo returns True for git repository."""
        # Arrange
        from specify_cli import is_git_repo

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0

        # Act
        result = is_git_repo(tmp_path)

        # Assert
        assert result is True
        mock_run.assert_called_once()

    def test_is_git_repo_false(self, mocker, tmp_path):
        """Test is_git_repo returns False for non-git directory."""
        # Arrange
        from specify_cli import is_git_repo

        # Act
        result = is_git_repo(tmp_path)

        # Assert
        assert result is False
