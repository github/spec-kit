"""Tests for ZcodeIntegration — skills-based integration (Z.AI)."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestZcodeIntegration(SkillsIntegrationTests):
    KEY = "zcode"
    FOLDER = ".zcode/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".zcode/skills"

    def test_constitution_skill_uses_dollar_follow_up(self, tmp_path):
        integration = get_integration("zcode")
        manifest = IntegrationManifest("zcode", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        skill = tmp_path / ".zcode/skills/speckit-constitution/SKILL.md"
        content = skill.read_text(encoding="utf-8")
        assert "$speckit-specify <intent>" in content
        assert "/speckit-specify <intent>" not in content


class TestZcodeInvocation:
    """ZCode renders $speckit-* chat invocations (like Codex)."""

    def test_next_steps_show_dollar_skill_invocation(self, tmp_path):
        """ZCode next-steps guidance should display $speckit-* usage."""
        import os
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "zcode-next-steps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--integration", "zcode",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "$speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
