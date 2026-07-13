"""Tests for BobIntegration."""

import os
import warnings

import pytest

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import IntegrationBase, SkillsIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class TestBobIntegrationRegistration:
    def test_registered(self):
        assert "bob" in INTEGRATION_REGISTRY
        assert get_integration("bob") is not None

    def test_is_integration_base(self):
        assert isinstance(get_integration("bob"), IntegrationBase)

    def test_not_skills_integration_directly(self):
        """BobIntegration is not itself a SkillsIntegration — it's dual-mode."""
        from specify_cli.integrations.bob import BobIntegration
        assert not isinstance(BobIntegration(), SkillsIntegration)

    def test_key_and_config(self):
        bob = get_integration("bob")
        assert bob.key == "bob"
        assert bob.config["folder"] == ".bob/"
        # Default mode is commands (markdown)
        assert bob.config["commands_subdir"] == "commands"
        assert bob.registrar_config["dir"] == ".bob/commands"
        assert bob.registrar_config["extension"] == ".md"


class TestBobOptionsFlag:
    def test_options_include_skills_flag(self):
        bob = get_integration("bob")
        opts = bob.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 1
        opt = skills_opts[0]
        assert opt.is_flag is True
        # Skills must be OPT-IN (default=False) — not the default
        assert opt.default is False


class TestBobDefaultMarkdownMode:
    """Default mode: .bob/commands/speckit.<name>.md layout."""

    def test_setup_creates_markdown_files(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        assert len(created) > 0
        for f in created:
            assert f.exists()
            assert f.suffix == ".md"
            assert f.name.startswith("speckit.")
            assert f.parent == tmp_path / ".bob" / "commands"

    def test_setup_warns_legacy_markdown_is_deprecated(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)

        with pytest.warns(UserWarning, match="Bob legacy markdown mode"):
            bob.setup(tmp_path, m)

    def test_setup_explicit_skills_false_no_warn(self, tmp_path):
        """Explicitly passing skills=False is a conscious choice — no warning.

        The warning fires only when ``skills`` is absent from parsed_options
        (i.e. the user gave no opinion), matching the Copilot pattern.
        """
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bob.setup(tmp_path, m, parsed_options={"skills": False})

        assert not any(
            "Bob legacy markdown mode" in str(item.message)
            for item in caught
        )

    def test_setup_no_skills_dirs_created(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m)
        skills_dir = tmp_path / ".bob" / "skills"
        assert not skills_dir.exists()

    def test_templates_are_processed(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m)
        commands_dir = tmp_path / ".bob" / "commands"
        for md_file in commands_dir.glob("speckit.*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{md_file.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{md_file.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{md_file.name} has unprocessed {{ARGS}}"
            assert "__SPECKIT_COMMAND_" not in content, f"{md_file.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_all_files_tracked_in_manifest(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = bob.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []


class TestBobSkillsMode:
    """Skills mode: .bob/skills/speckit-<name>/SKILL.md layout."""

    def test_setup_skills_creates_skill_files(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m, parsed_options={"skills": True})
        assert len(created) > 0
        for f in created:
            assert f.exists()
            assert f.name == "SKILL.md"
            assert f.parent.name.startswith("speckit-")

    def test_setup_skills_does_not_warn_about_legacy(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bob.setup(tmp_path, m, parsed_options={"skills": True})

        assert not any(
            "Bob legacy markdown mode" in str(item.message)
            for item in caught
        )

    def test_setup_skills_creates_correct_directory(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m, parsed_options={"skills": True})
        skills_dir = tmp_path / ".bob" / "skills"
        assert skills_dir.is_dir()

    def test_setup_skills_no_commands_dir(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m, parsed_options={"skills": True})
        commands_dir = tmp_path / ".bob" / "commands"
        assert not commands_dir.exists()

    def test_setup_skills_has_expected_commands(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m, parsed_options={"skills": True})

        expected_commands = {
            "analyze", "clarify", "constitution", "converge", "implement",
            "plan", "checklist", "specify", "tasks", "taskstoissues",
        }
        actual_commands = {f.parent.name.removeprefix("speckit-") for f in created}
        assert actual_commands == expected_commands

    def test_setup_skills_all_files_tracked(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m, parsed_options={"skills": True})
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_skills_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.install(tmp_path, m, parsed_options={"skills": True})
        assert len(created) > 0
        m.save()
        removed, skipped = bob.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []


class TestBobInitFlowDefault:
    """CLI init integration tests for default (markdown) mode."""

    def test_init_default_creates_commands(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "test-proj"
        result = CliRunner().invoke(app, [
            "init", str(target), "--integration", "bob",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init --integration bob failed: {result.output}"
        assert (target / ".bob" / "commands" / "speckit.plan.md").exists()
        assert not (target / ".bob" / "skills").exists()

    def test_init_default_complete_file_inventory_sh(self, tmp_path):
        """Default init creates .bob/commands/*.md files."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-sh-bob"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "bob", "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"

        commands = [
            "analyze", "clarify", "constitution", "converge", "implement",
            "plan", "checklist", "specify", "tasks", "taskstoissues",
        ]
        for cmd in commands:
            assert (project / ".bob" / "commands" / f"speckit.{cmd}.md").exists(), (
                f"Missing .bob/commands/speckit.{cmd}.md"
            )


class TestBobInitFlowSkills:
    """CLI init integration tests for skills mode."""

    def test_init_skills_creates_skill_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "test-proj"
        result = CliRunner().invoke(app, [
            "init", str(target), "--integration", "bob",
            "--integration-options", "--skills",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init --integration bob --skills failed: {result.output}"
        assert (target / ".bob" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert not (target / ".bob" / "commands").exists()
