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

        Bob is dual-mode (skills by default, legacy commands via
        ``--legacy-commands``), so its skills-ness is a per-project config
        decision resolved by the ``is_skills_mode`` hook — not a class-hierarchy
        property.  It therefore must NOT be a ``SkillsIntegration`` (which is
        reserved for statically skills-only agents); shared code consults
        ``is_skills_mode(parsed_options)`` instead of ``isinstance``.
        ``invoke_separator='-'`` is set explicitly on the class to match the
        default (skills) layout.
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
        # registrar_config mirrors the legacy commands layout so that
        # CommandRegistrar.AGENT_CONFIGS["bob"] follows the Copilot pattern:
        # extension registration writes to .bob/commands/ for legacy-mode
        # projects and is skipped for skills-mode projects (skills_mode_active).
        assert bob.config["commands_subdir"] == "commands"
        assert bob.registrar_config["dir"] == ".bob/commands"
        assert bob.registrar_config["extension"] == ".md"

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


class TestBobIsSkillsModeHook:
    """The is_skills_mode hook is the single source of truth for the mode."""

    def test_default_is_skills(self):
        bob = get_integration("bob")
        assert bob.is_skills_mode(None) is True
        assert bob.is_skills_mode({}) is True

    def test_legacy_commands_disables_skills(self):
        bob = get_integration("bob")
        assert bob.is_skills_mode({"legacy_commands": True}) is False

    def test_existing_commands_layout_preserved_on_use(self, tmp_path):
        """Regression (review #3415): an existing Bob 1.x project (only
        ``.bob/commands/`` on disk, no stored ``legacy_commands``) must NOT be
        treated as skills mode when re-resolved with a project_root, so
        ``use``/``switch``/``upgrade`` never silently migrate it to skills.
        """
        bob = get_integration("bob")
        (tmp_path / ".bob" / "commands").mkdir(parents=True)
        # No parsed options at all — the pre-existing-install scenario.
        assert bob.is_skills_mode(None, project_root=tmp_path) is False
        assert bob.is_skills_mode({}, project_root=tmp_path) is False

    def test_existing_skills_layout_stays_skills_on_use(self, tmp_path):
        """A ``.bob/skills/`` project resolves to skills mode."""
        bob = get_integration("bob")
        (tmp_path / ".bob" / "skills").mkdir(parents=True)
        assert bob.is_skills_mode(None, project_root=tmp_path) is True

    def test_fresh_project_defaults_to_skills_with_project_root(self, tmp_path):
        """A project with no ``.bob/`` layout yet still defaults to skills."""
        bob = get_integration("bob")
        assert bob.is_skills_mode(None, project_root=tmp_path) is True

    def test_explicit_legacy_flag_wins_over_disk_layout(self, tmp_path):
        """An explicit ``--legacy-commands`` overrides on-disk detection."""
        bob = get_integration("bob")
        (tmp_path / ".bob" / "skills").mkdir(parents=True)
        assert (
            bob.is_skills_mode({"legacy_commands": True}, project_root=tmp_path)
            is False
        )

    def test_effective_invoke_separator_tracks_mode(self):
        bob = get_integration("bob")
        assert bob.effective_invoke_separator(None) == "-"
        assert bob.effective_invoke_separator({"legacy_commands": True}) == "."

    def test_invoke_separator_for_mode_tracks_persisted_state(self):
        """Registration paths resolve the separator from persisted ai_skills."""
        bob = get_integration("bob")
        assert bob.invoke_separator_for_mode(True) == "-"
        assert bob.invoke_separator_for_mode(False) == "."

    def test_no_skills_mode_method_leaks(self):
        """The old callable _skills_mode method must be gone; consumers use the hook."""
        bob = get_integration("bob")
        assert not callable(getattr(bob, "_skills_mode", None))


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

    def test_init_legacy_does_not_set_ai_skills(self, tmp_path):
        """Legacy install must NOT write ai_skills=True to init-options.json.

        Behavioral guard for the dual-mode contract: with --legacy-commands,
        BobIntegration.is_skills_mode(parsed_options) returns False, so
        _update_init_options_for_integration must not persist ai_skills=True.
        (Regression origin: shared code previously probed a bound _skills_mode
        method object, which is always truthy, and wrongly enabled skills for
        legacy projects.)
        """
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli import load_init_options

        target = tmp_path / "test-proj"
        result = CliRunner().invoke(app, [
            "init", str(target), "--integration", "bob",
            "--integration-options", "--legacy-commands",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init failed: {result.output}"
        init_opts = load_init_options(target)
        assert init_opts.get("ai_skills") is not True, (
            "Legacy Bob project must not have ai_skills=True in init-options.json"
        )


class TestBobRegistrarConfig:
    """Verify AGENT_CONFIGS["bob"] follows the Copilot pattern for extension registration."""

    def test_registrar_config_uses_commands_layout(self):
        """AGENT_CONFIGS["bob"] must use the legacy .md layout (not /SKILL.md).

        This mirrors Copilot: the static registrar config targets the non-skills
        format so that:
        - skills_mode_active becomes True when ai_skills=True, preventing
          extension registration from writing SKILL.md files into .bob/skills/
          on projects that never asked for legacy files.
        - legacy-mode projects receive extension .md files in .bob/commands/.
        """
        from specify_cli.agents import CommandRegistrar
        registrar = CommandRegistrar()
        bob_cfg = registrar.AGENT_CONFIGS.get("bob")
        assert bob_cfg is not None, "bob must be in AGENT_CONFIGS"
        assert bob_cfg["extension"] == ".md", (
            "AGENT_CONFIGS['bob']['extension'] must be '.md' so that "
            "skills_mode_active=True suppresses extension registration on "
            "skills-mode projects (mirrors the Copilot pattern)"
        )
        assert bob_cfg["dir"] == ".bob/commands"

    def test_skills_mode_project_extension_registration_skipped(self, tmp_path):
        """Extension registrar skips Bob on skills-mode projects (no .bob/commands dir)."""
        from specify_cli.agents import CommandRegistrar
        # Simulate a skills-mode Bob project: .bob/skills exists, .bob/commands does not
        (tmp_path / ".bob" / "skills").mkdir(parents=True)

        registrar = CommandRegistrar()
        results = registrar.register_commands_for_all_agents(
            commands=[{"name": "speckit.test-cmd", "file": "test.md"}],
            source_id="test",
            source_dir=tmp_path,
            project_root=tmp_path,
        )
        # Bob must not appear in results — .bob/commands doesn't exist
        assert "bob" not in results

    def test_legacy_mode_project_extension_registration_runs(self, tmp_path):
        """Extension registrar writes to .bob/commands/ for legacy-mode projects."""
        import textwrap
        from specify_cli.agents import CommandRegistrar

        # Simulate a legacy-mode Bob project: .bob/commands exists, .bob/skills does not
        commands_dir = tmp_path / ".bob" / "commands"
        commands_dir.mkdir(parents=True)

        # Provide a minimal command source file
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text(
            textwrap.dedent("""\
                ---
                description: "Test command"
                ---
                Test body.
            """),
            encoding="utf-8",
        )

        registrar = CommandRegistrar()
        results = registrar.register_commands_for_all_agents(
            commands=[{"name": "speckit.test-cmd", "file": "test.md"}],
            source_id="test",
            source_dir=tmp_path,
            project_root=tmp_path,
        )
        assert "bob" in results, "bob must appear in results for legacy-mode project"
        registered_file = commands_dir / "speckit.test-cmd.md"
        assert registered_file.exists(), f"Expected {registered_file} to be written"

    def test_legacy_extension_command_refs_use_dot_separator(self, tmp_path):
        """Regression (review #3415): legacy .bob/commands/ extension commands must
        render Bob 1.x ``/speckit.<cmd>`` refs, not the skills-layout ``/speckit-<cmd>``.

        The single static AGENT_CONFIGS["bob"]["invoke_separator"] is "-" (the
        default skills layout); register_commands must instead resolve the
        separator from the project's persisted mode via
        BobIntegration.invoke_separator_for_mode(False) -> ".".
        """
        import textwrap
        from specify_cli.agents import CommandRegistrar

        # Legacy-mode project: .bob/commands exists, ai_skills is NOT set.
        commands_dir = tmp_path / ".bob" / "commands"
        commands_dir.mkdir(parents=True)
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text(
            textwrap.dedent("""\
                ---
                description: "Test command"
                ---
                See __SPECKIT_COMMAND_SPECIFY__ for details.
            """),
            encoding="utf-8",
        )

        registrar = CommandRegistrar()
        registrar.register_commands_for_all_agents(
            commands=[{"name": "speckit.test-cmd", "file": "test.md"}],
            source_id="test",
            source_dir=tmp_path,
            project_root=tmp_path,
        )
        rendered = (commands_dir / "speckit.test-cmd.md").read_text(encoding="utf-8")
        assert "/speckit.specify" in rendered, (
            "legacy Bob extension commands must render /speckit.specify (dot)"
        )
        assert "/speckit-specify" not in rendered


class TestBobUseFlowPreservesLegacyLayout:
    """Regression (review #3415): re-activating an existing Bob 1.x project
    must not silently migrate it to the skills layout.
    """

    def test_update_init_options_preserves_legacy_commands_project(self, tmp_path):
        """``use``/``switch``/``upgrade`` on a ``.bob/commands``-only project
        (no stored ``legacy_commands``) must not write ``ai_skills=True``.
        """
        from specify_cli.integrations._helpers import (
            _update_init_options_for_integration,
        )
        from specify_cli import load_init_options

        # Existing Bob 1.x project: legacy commands dir on disk, no ai_skills.
        (tmp_path / ".bob" / "commands").mkdir(parents=True)
        bob = get_integration("bob")

        # Simulate the use/switch path: no parsed options were stored.
        _update_init_options_for_integration(tmp_path, bob, parsed_options=None)

        opts = load_init_options(tmp_path)
        assert opts.get("ai") == "bob"
        assert opts.get("ai_skills") is not True, (
            "an existing .bob/commands project must stay legacy on re-activation"
        )

    def test_update_init_options_keeps_skills_project_as_skills(self, tmp_path):
        """A ``.bob/skills`` project stays skills on re-activation."""
        from specify_cli.integrations._helpers import (
            _update_init_options_for_integration,
        )
        from specify_cli import load_init_options

        (tmp_path / ".bob" / "skills").mkdir(parents=True)
        bob = get_integration("bob")

        _update_init_options_for_integration(tmp_path, bob, parsed_options=None)

        opts = load_init_options(tmp_path)
        assert opts.get("ai_skills") is True

    def test_with_integration_setting_stores_dot_separator_for_legacy(self, tmp_path):
        """Regression (review #3415): shared-infra refresh on the use/switch
        path resolves the command-ref separator *before* init-options are
        rewritten, via ``effective_invoke_separator``.  For an existing
        ``.bob/commands`` project with no stored options this must resolve to
        ``"."`` (project-aware), not the skills-layout ``"-"``; otherwise core
        command references get rewritten to ``/speckit-*``.
        """
        from specify_cli.integration_runtime import with_integration_setting

        (tmp_path / ".bob" / "commands").mkdir(parents=True)
        bob = get_integration("bob")

        # Simulate the use/switch path: no parsed options stored.
        settings = with_integration_setting(
            {}, "bob", bob, parsed_options=None, project_root=tmp_path
        )
        assert settings["bob"]["invoke_separator"] == ".", (
            "legacy .bob/commands project must persist the dot separator so "
            "shared templates render Bob 1.x /speckit.<cmd> references"
        )

    def test_use_force_keeps_legacy_command_refs_in_shared_templates(self, tmp_path):
        """End-to-end (review #3415): ``integration use bob --force`` on an
        existing Bob 1.x project (legacy layout on disk, stored options
        stripped as a pre-PR install would be) must re-render shared templates
        with ``/speckit.<cmd>`` (dot), not ``/speckit-<cmd>``.
        """
        import json
        from typer.testing import CliRunner
        from specify_cli import app

        # Create a real legacy Bob project (renders shared templates).
        target = tmp_path / "proj"
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(target), "--integration", "bob",
            "--integration-options", "--legacy-commands",
            "--ignore-agent-tools", "--script", "sh",
        ])
        assert result.exit_code == 0, f"init failed: {result.output}"

        template = target / ".specify" / "templates" / "plan-template.md"
        assert template.is_file(), "expected a rendered shared plan template"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")

        # Simulate a pre-PR Bob 1.x install: no stored options/separator.
        integ_json = target / ".specify" / "integration.json"
        data = json.loads(integ_json.read_text(encoding="utf-8"))
        bob_settings = data["integration_settings"]["bob"]
        for stale in ("raw_options", "parsed_options", "invoke_separator"):
            bob_settings.pop(stale, None)
        integ_json.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Re-activate with --force so shared templates are re-rendered.
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(target)
            result = runner.invoke(
                app, ["integration", "use", "bob", "--force"]
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"use failed: {result.output}"

        rendered = template.read_text(encoding="utf-8")
        assert "/speckit.plan" in rendered, (
            "legacy Bob project must keep /speckit.plan (dot) after refresh"
        )
        assert "/speckit-plan" not in rendered, (
            "shared templates must not be rewritten to the skills /speckit-plan"
        )
        # And the persisted separator must reflect the legacy layout.
        data = json.loads(integ_json.read_text(encoding="utf-8"))
        assert data["integration_settings"]["bob"].get("invoke_separator") == "."
