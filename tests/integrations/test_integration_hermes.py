"""Tests for HermesIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestHermesIntegration(SkillsIntegrationTests):
    KEY = "hermes"
    FOLDER = ".hermes/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".hermes/skills"
    CONTEXT_FILE = "AGENTS.md"


class TestHermesAutoPromote:
    """--ai hermes auto-promotes to integration path."""

    def test_ai_hermes_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai hermes should work the same as --integration hermes."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, [
            "init", str(target),
            "--ai", "hermes",
            "--no-git",
            "--ignore-agent-tools",
            "--script", "sh",
        ])

        assert result.exit_code == 0, f"init --ai hermes failed: {result.output}"
        assert (target / ".hermes" / "skills" / "speckit-plan" / "SKILL.md").exists()
