"""Tests for KimiIntegration — skills integration with legacy migration."""

from pathlib import Path

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.kimi import (
    _migrate_legacy_kimi_dotted_skills,
    _migrate_legacy_kimi_skills_dir,
)
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


def _symlink_or_skip(
    link: Path, target: Path, *, target_is_directory: bool = False
) -> None:
    """Create *link* pointing at *target*, skipping the test if unsupported.

    Symlink creation fails on Windows without the create-symlink privilege and
    in some restricted CI sandboxes. The symlink-safety tests below assert
    behavior that only matters when symlinks exist, so skip (rather than error)
    when the platform cannot create them.
    """
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


class TestKimiIntegration(SkillsIntegrationTests):
    KEY = "kimi"
    FOLDER = ".kimi-code/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".kimi-code/skills"


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

    def test_setup_migrate_legacy_moves_old_skills_dir(self, tmp_path):
        """--migrate-legacy moves hyphenated skills from .kimi/skills to .kimi-code/skills."""
        i = get_integration("kimi")

        old_skills_dir = tmp_path / ".kimi" / "skills"
        new_skills_dir = tmp_path / ".kimi-code" / "skills"
        legacy = old_skills_dir / "speckit-oldcmd"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("# Legacy\n")

        m = IntegrationManifest("kimi", tmp_path)
        i.setup(tmp_path, m, parsed_options={"migrate_legacy": True})

        assert not legacy.exists()
        assert not old_skills_dir.exists()
        assert (new_skills_dir / "speckit-oldcmd" / "SKILL.md").exists()
        # New skills from templates should also exist
        assert (new_skills_dir / "speckit-specify" / "SKILL.md").exists()

    def test_setup_with_migrate_legacy_option(self, tmp_path):
        """KimiIntegration.setup() with --migrate-legacy migrates dotted dirs."""
        i = get_integration("kimi")

        old_skills_dir = tmp_path / ".kimi" / "skills"
        new_skills_dir = tmp_path / ".kimi-code" / "skills"
        legacy = old_skills_dir / "speckit.oldcmd"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("# Legacy\n")

        m = IntegrationManifest("kimi", tmp_path)
        i.setup(tmp_path, m, parsed_options={"migrate_legacy": True})

        assert not legacy.exists()
        assert (new_skills_dir / "speckit-oldcmd" / "SKILL.md").exists()
        # New skills from templates should also exist
        assert (new_skills_dir / "speckit-specify" / "SKILL.md").exists()


class TestKimiTeardownLegacyCleanup:
    """teardown() removes leftover legacy .kimi/skills/ directories."""

    def test_teardown_removes_legacy_speckit_skills(self, tmp_path):
        i = get_integration("kimi")

        legacy_skill = tmp_path / ".kimi" / "skills" / "speckit-plan" / "SKILL.md"
        legacy_skill.parent.mkdir(parents=True)
        legacy_skill.write_text(
            "---\n"
            "name: \"speckit-plan\"\n"
            "description: \"Plan workflow\"\n"
            "metadata:\n"
            "  author: \"github-spec-kit\"\n"
            "  source: \"templates/commands/plan.md\"\n"
            "---\n"
        )

        m = IntegrationManifest("kimi", tmp_path)
        i.teardown(tmp_path, m)

        assert not legacy_skill.exists()
        assert not (tmp_path / ".kimi" / "skills").exists()

    def test_teardown_preserves_user_skills_in_legacy_dir(self, tmp_path):
        i = get_integration("kimi")

        user_skill = tmp_path / ".kimi" / "skills" / "my-custom" / "SKILL.md"
        user_skill.parent.mkdir(parents=True)
        user_skill.write_text("# My custom skill\n")

        m = IntegrationManifest("kimi", tmp_path)
        i.teardown(tmp_path, m)

        assert user_skill.exists()


class TestKimiCommandInvocation:
    """Kimi dispatch must use the native ``/skill:`` slash command."""

    def test_build_command_invocation_uses_skill_prefix(self):
        i = get_integration("kimi")
        assert i.build_command_invocation("specify") == "/skill:speckit-specify"
        assert i.build_command_invocation("speckit.plan") == "/skill:speckit-plan"

    def test_build_command_invocation_dotted_extension(self):
        i = get_integration("kimi")
        assert (
            i.build_command_invocation("speckit.git.commit")
            == "/skill:speckit-git-commit"
        )

    def test_build_command_invocation_appends_args(self):
        i = get_integration("kimi")
        assert (
            i.build_command_invocation("specify", "my feature")
            == "/skill:speckit-specify my feature"
        )


class TestKimiLegacySymlinkSafety:
    """Legacy migration/cleanup must not follow symlinks out of the project."""

    def test_migrate_skips_symlinked_legacy_skills_dir(self, tmp_path):
        # An attacker-controlled directory outside the project root. Use a
        # non-template skill name so a successful migration would be visible
        # (the bundled templates never create "speckit-evillegacy").
        outside = tmp_path / "outside"
        (outside / "speckit-evillegacy").mkdir(parents=True)
        (outside / "speckit-evillegacy" / "SKILL.md").write_text("# evil\n")

        project = tmp_path / "project"
        (project / ".kimi").mkdir(parents=True)
        # .kimi/skills is a symlink to the outside directory.
        _symlink_or_skip(
            project / ".kimi" / "skills", outside, target_is_directory=True
        )

        i = get_integration("kimi")
        m = IntegrationManifest("kimi", project)
        i.setup(project, m, parsed_options={"migrate_legacy": True})

        # Outside content must be untouched (not moved into .kimi-code).
        assert (outside / "speckit-evillegacy" / "SKILL.md").exists()
        assert not (
            project / ".kimi-code" / "skills" / "speckit-evillegacy"
        ).exists()

    def test_teardown_skips_symlinked_legacy_skills_dir(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        keep = outside / "keep.txt"
        keep.write_text("important\n")

        project = tmp_path / "project"
        (project / ".kimi").mkdir(parents=True)
        _symlink_or_skip(
            project / ".kimi" / "skills", outside, target_is_directory=True
        )

        i = get_integration("kimi")
        m = IntegrationManifest("kimi", project)
        i.teardown(project, m)

        # The symlink target and its contents must survive teardown.
        assert keep.exists()

    def test_migrate_skips_symlinked_legacy_parent_dir(self, tmp_path):
        # `.kimi` is itself a symlink to the project root, so `.kimi/skills`
        # resolves to `./skills` — an unrelated in-tree directory. Even though
        # the resolved path stays inside the project, migration must not
        # operate on it because a path component is a symlink.
        project = tmp_path / "project"
        unrelated = project / "skills" / "speckit-evillegacy"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("# unrelated\n")
        # .kimi -> project root, so .kimi/skills == ./skills.
        _symlink_or_skip(project / ".kimi", project, target_is_directory=True)

        i = get_integration("kimi")
        m = IntegrationManifest("kimi", project)
        i.setup(project, m, parsed_options={"migrate_legacy": True})

        # The unrelated ./skills content must be untouched.
        assert (unrelated / "SKILL.md").exists()
        assert not (
            project / ".kimi-code" / "skills" / "speckit-evillegacy"
        ).exists()

    def test_teardown_skips_symlinked_legacy_parent_dir(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        # Looks Speckit-generated, so only the symlink check protects it.
        unrelated = project / "skills" / "speckit-evillegacy"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text(
            "---\nmetadata:\n  author: github-spec-kit\n---\n# x\n"
        )
        _symlink_or_skip(project / ".kimi", project, target_is_directory=True)

        i = get_integration("kimi")
        m = IntegrationManifest("kimi", project)
        i.teardown(project, m)

        # The unrelated ./skills content must survive teardown.
        assert (unrelated / "SKILL.md").exists()

    def test_setup_rejects_symlinked_destination_before_writing(self, tmp_path):
        # `.kimi-code` is a symlink to the project root, so the skills
        # destination `.kimi-code/skills` resolves to `./skills` — an
        # unintended in-tree location. base setup() only rejects a
        # destination that escapes the project root, so without the
        # pre-check it would write SKILL.md files into `./skills`. setup()
        # must refuse before any write occurs.
        project = tmp_path / "project"
        project.mkdir()
        _symlink_or_skip(project / ".kimi-code", project, target_is_directory=True)

        i = get_integration("kimi")
        m = IntegrationManifest("kimi", project)
        with pytest.raises(ValueError, match="symlinked"):
            i.setup(project, m)

        # Nothing was written into the unintended `./skills` location.
        assert not (project / "skills").exists()

    def test_migrate_skips_symlinked_target_dir(self, tmp_path):
        # The destination `.kimi-code/skills/speckit-foo` already exists but is
        # a symlink to a directory outside the project. Migration compares
        # SKILL.md bytes to decide whether to drop the legacy copy; it must not
        # follow the symlinked target dir to read SKILL.md from outside.
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "SKILL.md").write_text("# shared\n")

        project = tmp_path / "project"
        legacy = project / ".kimi" / "skills" / "speckit-foo"
        legacy.mkdir(parents=True)
        # Identical bytes: without the symlink guard the legacy dir would be
        # removed after following the link out of the project.
        (legacy / "SKILL.md").write_text("# shared\n")

        target = project / ".kimi-code" / "skills" / "speckit-foo"
        target.parent.mkdir(parents=True)
        _symlink_or_skip(target, outside, target_is_directory=True)

        _migrate_legacy_kimi_skills_dir(
            project / ".kimi" / "skills", project / ".kimi-code" / "skills"
        )

        # Legacy copy is preserved (migration refused to follow the symlink),
        # and the outside target is untouched.
        assert (legacy / "SKILL.md").exists()
        assert (outside / "SKILL.md").exists()

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
                "init", "--here", "--integration", "kimi",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "/skill:speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
        assert "Optional skills that you can use for your specs" in result.output
