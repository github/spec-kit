"""Tests for BobIntegration."""

import os
import warnings

import pytest
import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import SkillsIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class TestBobIntegrationRegistration:
    def test_registered(self):
        assert "bob" in INTEGRATION_REGISTRY
        assert get_integration("bob") is not None

    def test_is_integration_base_not_skills_integration(self):
        """BobIntegration extends IntegrationBase directly — not SkillsIntegration.

        It must NOT be an instance of SkillsIntegration so that consumers
        such as _update_init_options_for_integration and the init next-steps
        builder derive the effective mode from _skills_mode rather than the
        class hierarchy.  invoke_separator='-' is set explicitly on the class.
        """
        from specify_cli.integrations.base import IntegrationBase
        bob = get_integration("bob")
        assert isinstance(bob, IntegrationBase)
        assert not isinstance(bob, SkillsIntegration)
        assert bob.invoke_separator == "-"

    def test_key_and_config(self):
        bob = get_integration("bob")
        assert bob.key == "bob"
        assert bob.config["folder"] == ".bob/"
        assert bob.config["commands_subdir"] == "skills"
        assert bob.registrar_config["dir"] == ".bob/skills"
        assert bob.registrar_config["extension"] == "/SKILL.md"

    def test_invoke_separator_is_hyphen(self):
        """Class-level invoke_separator must be '-' so CommandRegistrar.AGENT_CONFIGS
        generates correct /speckit-<name> refs without calling effective_invoke_separator."""
        bob = get_integration("bob")
        assert bob.invoke_separator == "-"


class TestBobOptionsFlag:
    def test_options_include_legacy_commands_flag(self):
        bob = get_integration("bob")
        opts = bob.options()
        legacy_opts = [o for o in opts if o.name == "--legacy-commands"]
        assert len(legacy_opts) == 1
        opt = legacy_opts[0]
        assert opt.is_flag is True
        # Legacy must be OPT-IN (default=False) — skills are the default
        assert opt.default is False

    def test_no_skills_flag(self):
        """The old --skills flag must be gone; it has been replaced by the default."""
        bob = get_integration("bob")
        opts = bob.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 0


class TestBobDefaultSkillsMode:
    """Default mode: .bob/skills/speckit-<name>/SKILL.md layout."""

    def test_setup_creates_skill_files(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        assert len(created) > 0
        for f in created:
            assert f.exists()
            assert f.name == "SKILL.md"
            assert f.parent.name.startswith("speckit-")

    def test_setup_writes_to_correct_directory(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m)
        skills_dir = tmp_path / ".bob" / "skills"
        assert skills_dir.is_dir()

    def test_setup_does_not_warn(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bob.setup(tmp_path, m)
        assert not any(
            "legacy" in str(item.message).lower() for item in caught
        )

    def test_setup_no_commands_dir(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m)
        assert not (tmp_path / ".bob" / "commands").exists()

    def test_skill_directory_structure(self, tmp_path):
        """Each command produces speckit-<name>/SKILL.md."""
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)

        expected_commands = {
            "analyze", "clarify", "constitution", "converge", "implement",
            "plan", "checklist", "specify", "tasks", "taskstoissues",
        }
        actual_commands = {f.parent.name.removeprefix("speckit-") for f in created}
        assert actual_commands == expected_commands

    def test_skill_frontmatter_structure(self, tmp_path):
        """SKILL.md must have name, description, compatibility, metadata."""
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        for f in created:
            content = f.read_text(encoding="utf-8")
            assert content.startswith("---\n"), f"{f} missing frontmatter"
            parts = content.split("---", 2)
            fm = yaml.safe_load(parts[1])
            assert "name" in fm
            assert "description" in fm
            assert "compatibility" in fm
            assert "metadata" in fm
            assert fm["metadata"]["author"] == "github-spec-kit"

    def test_templates_are_processed(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        for f in created:
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{f.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{f.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{f.name} has unprocessed {{ARGS}}"
            assert "__SPECKIT_COMMAND_" not in content, f"{f.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_command_refs_use_hyphen_separator(self, tmp_path):
        """Default skills layout must use /speckit-<name>, not /speckit.<name>."""
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        for f in created:
            content = f.read_text(encoding="utf-8")
            assert "/speckit." not in content, (
                f"{f.name} contains dot-notation /speckit. reference; "
                "skills must use /speckit-<name>"
            )

    def test_all_files_tracked_in_manifest(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        bob = get_integration("bob")
        m = IntegrationManifest("bob", tmp_path)
        created = bob.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = bob.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []


class TestBobLegacyCommandsMode:
    """Legacy opt-in mode: .bob/commands/speckit.<name>.md layout."""

    def test_setup_legacy_creates_markdown_files(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m, parsed_options={"legacy_commands": True})
        assert len(created) > 0
        for f in created:
            assert f.exists()
            assert f.suffix == ".md"
            assert f.name.startswith("speckit.")
            assert f.parent == tmp_path / ".bob" / "commands"

    def test_setup_legacy_warns_deprecated(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        with pytest.warns(UserWarning, match="Bob legacy commands mode"):
            bob.setup(tmp_path, m, parsed_options={"legacy_commands": True})

    def test_setup_legacy_no_skills_dir(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m, parsed_options={"legacy_commands": True})
        assert not (tmp_path / ".bob" / "skills").exists()

    def test_setup_legacy_templates_are_processed(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        bob.setup(tmp_path, m, parsed_options={"legacy_commands": True})
        commands_dir = tmp_path / ".bob" / "commands"
        for md_file in commands_dir.glob("speckit.*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content
            assert "__AGENT__" not in content
            assert "{ARGS}" not in content
            assert "__SPECKIT_COMMAND_" not in content

    def test_setup_legacy_all_files_tracked(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.setup(tmp_path, m, parsed_options={"legacy_commands": True})
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_setup_legacy_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.bob import BobIntegration
        bob = BobIntegration()
        m = IntegrationManifest("bob", tmp_path)
        created = bob.install(tmp_path, m, parsed_options={"legacy_commands": True})
        assert len(created) > 0
        m.save()
        removed, skipped = bob.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []


class TestBobInitFlowDefault:
    """CLI init creates skills by default."""

    def test_init_default_creates_skills(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "test-proj"
        result = CliRunner().invoke(app, [
            "init", str(target), "--integration", "bob",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init --integration bob failed: {result.output}"
        assert (target / ".bob" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert not (target / ".bob" / "commands").exists()

    def test_init_default_complete_file_inventory_sh(self, tmp_path):
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
            assert (project / ".bob" / "skills" / f"speckit-{cmd}" / "SKILL.md").exists(), (
                f"Missing .bob/skills/speckit-{cmd}/SKILL.md"
            )


class TestBobInitFlowLegacy:
    """CLI init with --legacy-commands produces .bob/commands/*.md."""

    def test_init_legacy_creates_commands(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "test-proj"
        result = CliRunner().invoke(app, [
            "init", str(target), "--integration", "bob",
            "--integration-options", "--legacy-commands",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init --integration bob --legacy-commands failed: {result.output}"
        assert (target / ".bob" / "commands" / "speckit.plan.md").exists()
        assert not (target / ".bob" / "skills").exists()
