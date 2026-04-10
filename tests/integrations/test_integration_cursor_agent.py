"""Tests for CursorAgentIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestCursorAgentIntegration(SkillsIntegrationTests):
    KEY = "cursor-agent"
    FOLDER = ".cursor/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".cursor/skills"
    CONTEXT_FILE = ".cursor/rules/specify-rules.mdc"


class TestCursorAgentAutoPromote:
    """--ai cursor-agent auto-promotes to integration path."""

    def test_ai_cursor_agent_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai cursor-agent should work the same as --integration cursor-agent."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--ai", "cursor-agent", "--no-git", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --ai cursor-agent failed: {result.output}"
        assert (target / ".cursor" / "skills" / "speckit-plan" / "SKILL.md").exists()

