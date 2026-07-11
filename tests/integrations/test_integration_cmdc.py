"""Tests for CmcIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestCmcIntegration(SkillsIntegrationTests):
    KEY = "cmdc"
    FOLDER = ".commandcode/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".commandcode/skills"


class TestCmcInitFlow:
    """--integration cmdc creates expected files."""

    def test_integration_cmdc_creates_skills(self, tmp_path):
        """--integration cmdc should create skills in .commandcode/skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, [
            "init", str(target), "--integration", "cmdc",
            "--ignore-agent-tools", "--script", "sh",
        ])

        assert result.exit_code == 0, (
            f"init --integration cmdc failed: {result.output}"
        )
        assert (
            target / ".commandcode" / "skills" / "speckit-plan" / "SKILL.md"
        ).exists()

    def test_slash_command_refs_use_hyphens(self, tmp_path):
        """CMDC slash commands must use /speckit-<name> (hyphens)."""
        integration = get_integration("cmdc")
        manifest = IntegrationManifest("cmdc", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        plan_skill = (
            tmp_path / ".commandcode" / "skills" / "speckit-plan" / "SKILL.md"
        )
        content = plan_skill.read_text(encoding="utf-8")
        assert "/speckit-" in content
        assert "/speckit." not in content, (
            "CMDC skills must use /speckit-<name> not /speckit.<name>"
        )
