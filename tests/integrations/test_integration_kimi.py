"""Tests for KimiIntegration — skills integration with legacy migration."""

import shutil

from specify_cli.integrations import get_integration
from specify_cli.integrations.kimi import _migrate_legacy_kimi_dotted_skills
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestKimiIntegration(SkillsIntegrationTests):
    KEY = "kimi"
    FOLDER = ".kimi/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".kimi/skills"
    CONTEXT_FILE = "KIMI.md"


class TestKimiOptions:
    """Kimi declares --skills and --migrate-legacy options."""

    def test_migrate_legacy_option(self):
        i = get_integration("kimi")
        opts = i.options()
        migrate_opts = [o for o in opts if o.name == "--migrate-legacy"]
        assert len(migrate_opts) == 1
        assert migrate_opts[0].is_flag is True
        assert migrate_opts[0].default is False


class TestKimiLegacyMigration:
    """Test Kimi dotted → hyphenated skill directory migration."""

    def test_migrate_dotted_to_hyphenated(self, tmp_path):
        skills_dir = tmp_path / ".kimi" / "skills"
        legacy = skills_dir / "speckit.plan"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("# Plan Skill\n")

        migrated, removed = _migrate_legacy_kimi_dotted_skills(skills_dir)

        assert migrated == 1
        assert removed == 0
        assert not legacy.exists()
        assert (skills_dir / "speckit-plan" / "SKILL.md").exists()

    def test_skip_when_target_exists_different_content(self, tmp_path):
        skills_dir = tmp_path / ".kimi" / "skills"
        legacy = skills_dir / "speckit.plan"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("# Old\n")

        target = skills_dir / "speckit-plan"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("# New (different)\n")

        migrated, removed = _migrate_legacy_kimi_dotted_skills(skills_dir)

        assert migrated == 0
        assert removed == 0
        assert legacy.exists()
        assert target.exists()

    def test_remove_when_target_exists_same_content(self, tmp_path):
        skills_dir = tmp_path / ".kimi" / "skills"
        content = "# Identical\n"
        legacy = skills_dir / "speckit.plan"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text(content)

        target = skills_dir / "speckit-plan"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text(content)

        migrated, removed = _migrate_legacy_kimi_dotted_skills(skills_dir)

        assert migrated == 0
        assert removed == 1
        assert not legacy.exists()
        assert target.exists()

    def test_preserve_legacy_with_extra_files(self, tmp_path):
        skills_dir = tmp_path / ".kimi" / "skills"
        content = "# Same\n"
        legacy = skills_dir / "speckit.plan"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text(content)
        (legacy / "extra.md").write_text("user file")

        target = skills_dir / "speckit-plan"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text(content)

        migrated, removed = _migrate_legacy_kimi_dotted_skills(skills_dir)

        assert migrated == 0
        assert removed == 0
        assert legacy.exists()

    def test_nonexistent_dir_returns_zeros(self, tmp_path):
        migrated, removed = _migrate_legacy_kimi_dotted_skills(
            tmp_path / ".kimi" / "skills"
        )
        assert migrated == 0
        assert removed == 0

    def test_setup_with_migrate_legacy_option(self, tmp_path):
        """KimiIntegration.setup() with --migrate-legacy migrates dotted dirs."""
        i = get_integration("kimi")

        skills_dir = tmp_path / ".kimi" / "skills"
        legacy = skills_dir / "speckit.oldcmd"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("# Legacy\n")

        m = IntegrationManifest("kimi", tmp_path)
        i.setup(tmp_path, m, parsed_options={"migrate_legacy": True})

        assert not legacy.exists()
        assert (skills_dir / "speckit-oldcmd" / "SKILL.md").exists()
        # New skills from templates should also exist
        assert (skills_dir / "speckit-specify" / "SKILL.md").exists()


class TestKimiNextSteps:
    """CLI output tests for kimi next-steps display."""

    def test_next_steps_show_skill_invocation(self, tmp_path):
        """Kimi next-steps guidance should display /skill:speckit-* usage."""
        import os
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "kimi-next-steps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "kimi", "--no-git",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "/skill:speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
        assert "Optional skills that you can use for your specs" in result.output
