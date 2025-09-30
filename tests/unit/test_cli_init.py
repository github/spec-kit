"""Tests for specify init command."""

import pytest

from specify_cli import app


class TestInitCommand:
    """Test suite for specify init command."""

    def test_init_requires_project_name_or_here_flag(self, runner):
        """Test that init fails without project name or --here flag."""
        # Act
        result = runner.invoke(app, ["init"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.stdout
        assert "project name" in result.stdout.lower()

    def test_init_rejects_both_project_name_and_here(self, runner):
        """Test that init rejects both project name and --here flag."""
        # Act
        result = runner.invoke(app, ["init", "test-project", "--here"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.stdout
        assert "Cannot specify both" in result.stdout

    @pytest.mark.parametrize(
        "ai_choice",
        [
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
        ],
    )
    def test_init_accepts_valid_ai_choices(self, runner, ai_choice, tmp_path, mocker):
        """Test init with all supported AI agents."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        project_dir = tmp_path / "test-project"

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                str(project_dir),
                "--ai",
                ai_choice,
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_rejects_invalid_ai_choice(self, runner):
        """Test that invalid AI choice is rejected."""
        # Act
        result = runner.invoke(app, ["init", "test-project", "--ai", "invalid-ai"])

        # Assert
        assert result.exit_code != 0
        assert "Invalid AI assistant" in result.stdout or "invalid" in result.stdout.lower()

    @pytest.mark.parametrize("script_type", ["sh", "ps", "fish"])
    def test_init_accepts_valid_script_types(
        self, runner, script_type, tmp_path, mocker
    ):
        """Test init with all script types."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        project_dir = tmp_path / "test-project"

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                str(project_dir),
                "--ai",
                "claude",
                "--script",
                script_type,
                "--ignore-agent-tools",
                "--no-git",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_dot_shorthand_for_current_directory(self, runner, tmp_path, mocker):
        """Test that '.' works as shorthand for current directory."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
        mocker.patch("pathlib.Path.iterdir", return_value=[])

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                ".",
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
                "--force",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_here_flag_works(self, runner, tmp_path, mocker):
        """Test that --here flag works correctly."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
        mocker.patch("pathlib.Path.iterdir", return_value=[])

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                "--here",
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
                "--force",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_rejects_existing_directory(self, runner, tmp_path, mocker):
        """Test that init fails if project directory already exists."""
        # Arrange
        project_dir = tmp_path / "existing-project"
        project_dir.mkdir()

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                str(project_dir),
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
            ],
        )

        # Assert
        assert result.exit_code != 0
        assert "already" in result.stdout.lower() and "exist" in result.stdout.lower()


class TestInitCommandFlags:
    """Test suite for init command flags."""

    def test_init_skip_tls_flag(self, runner, tmp_path, mocker):
        """Test that --skip-tls flag is accepted."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        project_dir = tmp_path / "test-project"

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                str(project_dir),
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
                "--skip-tls",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_debug_flag(self, runner, tmp_path, mocker):
        """Test that --debug flag is accepted."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        project_dir = tmp_path / "test-project"

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                str(project_dir),
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
                "--debug",
            ],
        )

        # Assert
        assert result.exit_code == 0

    def test_init_force_flag(self, runner, tmp_path, mocker):
        """Test that --force flag skips confirmation."""
        # Arrange
        mocker.patch("specify_cli.download_and_extract_template")
        mocker.patch("specify_cli.run_command")
        mocker.patch("os.chdir")
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
        mocker.patch("pathlib.Path.iterdir", return_value=[tmp_path / "file.txt"])

        # Act
        result = runner.invoke(
            app,
            [
                "init",
                "--here",
                "--ai",
                "claude",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--no-git",
                "--force",
            ],
        )

        # Assert
        assert result.exit_code == 0
        assert "force" in result.stdout.lower()
