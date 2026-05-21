"""Tests for HermesIntegration.

Hermes is special among SkillsIntegration subclasses: it writes skills
to ``~/.hermes/skills/`` (global) rather than the project-local
``.hermes/skills/`` directory.  A project-local marker (empty directory)
is created so extension commands (e.g. git) can detect Hermes.

Several shared tests from ``SkillsIntegrationTests`` assume project-local
skills — they are overridden here with Hermes-appropriate assertions.
"""

from pathlib import Path

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.hermes import HermesIntegration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestHermesIntegration(SkillsIntegrationTests):
    KEY = "hermes"
    FOLDER = ".hermes/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".hermes/skills"
    CONTEXT_FILE = "AGENTS.md"

    # -- Hermes-specific setup: skills go to ~/.hermes/skills/ -------------

    def test_setup_writes_to_global_skills_dir(self, tmp_path):
        """Skills are written to ~/.hermes/skills/, not project-local."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]

        assert len(skill_files) > 0, "No skill files were created"
        for f in skill_files:
            # Every skill file should be under ~/.hermes/skills/speckit-*/
            assert str(f).startswith(
                str(Path.home() / ".hermes" / "skills")
            ), f"{f} is not under ~/.hermes/skills/"

    def test_local_marker_dir_created(self, tmp_path):
        """Project-local .hermes/skills/ should exist but be empty."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        marker = tmp_path / ".hermes" / "skills"
        assert marker.is_dir(), "Marker directory was not created"
        # Should be empty (no SKILL.md files)
        children = list(marker.iterdir())
        assert children == [], f"Marker directory should be empty, got: {children}"

    # -- Override shared tests that assume project-local skills ------------

    def test_setup_writes_to_correct_directory(self, tmp_path):
        """Override: Hermes writes to global, not project-local."""
        self.test_setup_writes_to_global_skills_dir(tmp_path)

    def test_plan_references_correct_context_file(self, tmp_path):
        """Plan skill goes to global dir, but we check it still references AGENTS.md."""
        i = get_integration(self.KEY)
        if not i.context_file:
            return
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        # Find the plan skill in global ~/.hermes/skills/
        plan_file = Path.home() / ".hermes" / "skills" / "speckit-plan" / "SKILL.md"
        assert plan_file.exists(), f"Plan skill {plan_file} not created globally"
        content = plan_file.read_text(encoding="utf-8")
        assert i.context_file in content, (
            f"Plan skill should reference {i.context_file!r} but it was not found"
        )
        assert "__CONTEXT_FILE__" not in content, (
            "Plan skill has unprocessed __CONTEXT_FILE__ placeholder"
        )

    def test_all_files_tracked_in_manifest(self, tmp_path):
        """Override: Hermes does not track skills in the project manifest
        since they live globally.  Only project-local files (scripts,
        templates, context) are tracked."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        for f in created:
            # Global files (in ~/.hermes/) are not tracked in manifest
            if str(f).startswith(str(Path.home())):
                continue
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        """Override: Hermes uninstall removes global skills + local marker."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        # All SKILL.md files should exist globally
        for f in created:
            if "SKILL.md" in str(f):
                assert f.exists(), f"{f} does not exist"
        removed, skipped = i.uninstall(tmp_path, m)
        # Global skills should be gone
        for f in created:
            if "SKILL.md" in str(f):
                assert not f.exists(), f"{f} should have been removed"
        # Local marker should be gone
        assert not (tmp_path / ".hermes" / "skills").exists()

    def test_modified_file_survives_uninstall(self, tmp_path):
        """Override: Hermes global skills are always removed on uninstall
        (no hash-based preservation since they're not in manifest)."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        # Pick a global skill file
        skill_files = [f for f in created if "SKILL.md" in str(f)]
        assert len(skill_files) > 0
        modified_file = skill_files[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        # Global skills are removed unconditionally (no manifest tracking)
        assert not modified_file.exists(), (
            "Modified global skill should be removed on uninstall"
        )

    def test_pre_existing_skills_not_removed(self, tmp_path):
        """Override: pre-existing non-speckit skills in the global dir
        should survive Hermes uninstall."""
        i = get_integration(self.KEY)
        # Create a foreign skill in the global dir first
        global_skills_dir = i._hermes_home_skills_dir()
        foreign_dir = global_skills_dir / "other-tool"
        foreign_dir.mkdir(parents=True, exist_ok=True)
        (foreign_dir / "SKILL.md").write_text("# Foreign skill\n")

        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)

        assert (foreign_dir / "SKILL.md").exists(), "Foreign skill was removed"

    def test_complete_file_inventory_sh(self, tmp_path):
        """Override: Hermes init produces no local SKILL.md files,
        only the empty .hermes/skills/ marker."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-sh-{self.KEY}"
        project.mkdir()
        old_cwd = Path.cwd()
        import os
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "sh", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        # Ensure no .hermes/skills/speckit-*/SKILL.md in project dir
        hermes_skill_files = [f for f in actual if f.startswith(".hermes/skills/speckit-")]
        assert hermes_skill_files == [], (
            f"Expected no local SKILL.md files, found: {hermes_skill_files}"
        )
        # Ensure the marker exists (empty dir won't appear in file listing)
        assert (project / ".hermes" / "skills").is_dir()

    def test_complete_file_inventory_ps(self, tmp_path):
        """Override: Same as sh variant but for PowerShell script type."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-ps-{self.KEY}"
        project.mkdir()
        old_cwd = Path.cwd()
        import os
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "ps", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        hermes_skill_files = [f for f in actual if f.startswith(".hermes/skills/speckit-")]
        assert hermes_skill_files == [], (
            f"Expected no local SKILL.md files, found: {hermes_skill_files}"
        )
        assert (project / ".hermes" / "skills").is_dir()

    def test_install_uninstall_cleanup(self, tmp_path):
        """Verify global skills are cleaned and local marker is removed."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)

        # Verify global skills exist
        global_skills = [
            f for f in created
            if "SKILL.md" in str(f)
            and str(f).startswith(str(Path.home() / ".hermes"))
        ]
        assert len(global_skills) > 0
        for f in global_skills:
            assert f.exists()

        # Verify local marker exists
        assert (tmp_path / ".hermes" / "skills").is_dir()

        # Teardown
        removed, skipped = i.teardown(tmp_path, m)

        # Global skills removed
        for f in global_skills:
            assert not f.exists(), f"{f} should have been removed"

        # Local marker removed
        assert not (tmp_path / ".hermes" / "skills").exists(), (
            "Local marker should be removed on teardown"
        )


class TestHermesAutoPromote:
    """--ai hermes auto-promotes to integration path."""

    def test_ai_hermes_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai hermes should work the same as --integration hermes,
        creating global skills and a local marker."""
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
        # Skills should be in global ~/.hermes/skills/
        assert (Path.home() / ".hermes" / "skills" / "speckit-plan" / "SKILL.md").exists()
        # Local marker should exist
        assert (target / ".hermes" / "skills").is_dir()
        # No SKILL.md files in project-local dir
        local_skills = list((target / ".hermes" / "skills").iterdir())
        assert local_skills == [], f"Local skills dir should be empty, got: {local_skills}"
