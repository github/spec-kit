"""Tests for preset command artifacts in specify_cli.presets._manager_commands."""

from pathlib import Path

import pytest
import yaml

from specify_cli.presets import PresetManager
from tests.specify_cli.presets._helpers import (
    PresetArtifactTestHelpers,
    install_self_test_preset,
)


class TestSelfTestPreset:
    """Command registration and removal using self-test."""

    def test_self_test_registers_commands_for_claude(self, project_dir):
        """Test that installing self-test registers skills in .claude/skills/."""
        # Create Claude skills directory to simulate Claude being set up
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        # Check the skill was registered
        cmd_file = claude_dir / "speckit-specify" / "SKILL.md"
        assert cmd_file.exists(), "Skill not registered in .claude/skills/"
        content = cmd_file.read_text()
        assert "self-test" in content
        assert "source:" in content  # skill frontmatter includes metadata.source

    def test_self_test_registers_commands_for_gemini(self, project_dir):
        """Test that installing self-test registers commands in .gemini/commands/ as TOML."""
        # Create Gemini agent directory
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        # Check the command was registered in TOML format
        cmd_file = gemini_dir / "speckit.specify.toml"
        assert cmd_file.exists(), "Command not registered in .gemini/commands/"
        content = cmd_file.read_text()
        assert "prompt" in content  # TOML format has a prompt field
        assert "{{args}}" in content  # Gemini uses {{args}} placeholder

    def test_self_test_unregisters_commands_on_remove(self, project_dir):
        """Test that removing self-test cleans up registered commands."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        cmd_file = claude_dir / "speckit-specify" / "SKILL.md"
        assert cmd_file.exists()

        manager.remove("self-test")
        assert not cmd_file.exists(), "Command not cleaned up after preset removal"

    def test_self_test_no_commands_without_agent_dirs(self, project_dir):
        """Test that no commands are registered when no agent dirs exist."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        metadata = manager.registry.get("self-test")
        assert metadata["registered_commands"] == {}

    def test_selfcontained_namespaced_command_scaffolds_without_extension(self, project_dir, temp_dir):
        """A preset shipping a self-contained ``speckit.<ns>.<cmd>`` command
        scaffolds even when no matching extension is installed.

        The command template ships its own body, so it is self-contained and
        must render just like a short ``speckit.<cmd>`` command. It is not
        dropped merely because ``.specify/extensions/fakeext/`` is absent.
        """
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        preset_dir = temp_dir / "ext-override-preset"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\nOverridden content"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-override",
                "name": "Ext Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "description": "Override fakeext cmd",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Extension not installed, but the preset ships its own command body —
        # it must scaffold (as a native-skill SKILL.md for claude) and be
        # tracked in the preset's registered_commands.
        skill_file = claude_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert skill_file.exists(), "Self-contained namespaced command was dropped"
        metadata = manager.registry.get("ext-override")
        assert metadata["registered_commands"] != {}

    def test_extension_command_registered_when_extension_present(self, project_dir, temp_dir):
        """Test that extension command overrides ARE registered when the extension is installed."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)
        (project_dir / ".specify" / "extensions" / "fakeext").mkdir(parents=True)

        preset_dir = temp_dir / "ext-override-preset2"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\nOverridden content"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-override2",
                "name": "Ext Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "description": "Override fakeext cmd",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_file = claude_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert cmd_file.exists(), "Skill not registered despite extension being present"


class TestPresetSkills(PresetArtifactTestHelpers):
    """Preset command activation, reconciliation, and mode switching."""

    def test_preset_add_corrupted_init_options_fails_closed(self, project_dir, temp_dir):
        """Corrupted (but present) init-options.json must not back-fill every
        detected agent for preset command registration.

        Before the shared ``resolve_active_agent_for_registration`` fix,
        ``load_init_options`` returning ``{}`` for a corrupted file was
        indistinguishable from "no file at all", so ``_register_commands``
        treated it like a legacy pre-init-options project and registered
        the preset's command override for every detected agent (#2948).
        """
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("{not valid json", encoding="utf-8")

        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "corrupt-init-preset", "speckit.specify",
            "Corrupt init test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        metadata = manager.registry.get("corrupt-init-preset")
        assert metadata.get("registered_commands") == {}, (
            "a corrupted init-options.json must fail closed, not "
            "back-fill every detected agent (#2948)"
        )
        assert not list(gemini_dir.glob("*specify*")), (
            "no command file should be written for any agent when "
            "init-options.json is corrupted"
        )

    def test_reconciliation_restricted_to_active_agent(self, project_dir, temp_dir):
        """Reconciliation after install/remove must also respect the
        single-active rule, not just the initial registration.

        ``_reconcile_composed_commands`` (invoked after
        ``install_from_directory``/``remove``) resolves composition winners
        via ``register_commands_for_non_skill_agents``, a separate code
        path from ``_register_commands``'s initial registration. Before the
        fix it ignored the active-agent restriction entirely and wrote the
        winning content for every detected non-skill agent, leaving
        untracked orphaned artifacts in inactive integrations (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        # A non-replace (append) strategy command forces reconciliation to
        # run register_commands_for_non_skill_agents for every non-skill
        # agent directory it detects.
        preset_dir = temp_dir / "reconcile-active-only"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: Appended\nstrategy: append\n---\n\nAppended body\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "reconcile-active-only",
                "name": "Reconcile Active Only",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [{
                    "type": "command",
                    "name": "speckit.specify",
                    "file": "commands/speckit.specify.md",
                    "strategy": "append",
                }]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        assert not list(gemini_dir.glob("*specify*")), (
            "reconciliation must not write command files for a detected "
            "but inactive non-skill agent (#2948)"
        )

    def test_use_rescaffold_reconciles_project_override(self, project_dir, temp_dir):
        """``integration use``/``switch`` rescaffolding must reconcile the
        full priority stack, not just write each preset's own content.

        Project overrides are the highest-priority layer, above every
        preset. ``register_enabled_presets_for_agent`` (invoked by
        ``integration use``/``switch``) calls ``_register_commands`` for
        each enabled preset directly, the same as ``install_from_directory``
        — but unlike install/remove, it never followed up with
        ``_reconcile_composed_commands``. Before the fix, rescaffolding a
        newly activated agent could leave the preset's raw content in
        place instead of resolving the real winner (the project override)
        from the full stack (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "use-reconcile-preset", "speckit.specify",
            "Preset specify", "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Simulate `integration use gemini`: switch the active agent and
        # rescaffold enabled presets for it, mirroring what the CLI does.
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        manager.register_enabled_presets_for_agent("gemini")

        cmd_file = gemini_dir / "speckit.specify.toml"
        assert cmd_file.exists(), "sanity: gemini should get a command file at all"
        content = cmd_file.read_text()
        assert "Override body" in content, (
            "the project override must still win after rescaffold "
            "reconciliation, not the preset's raw content (#2948)"
        )
        assert "Preset body" not in content

    def test_hermes_rescaffold_reconciles_global_skill_output(
        self, project_dir, temp_dir, monkeypatch
    ):
        home = temp_dir / "home"
        home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: home)
        (home / ".hermes" / "skills").mkdir(parents=True)
        self._write_init_options(project_dir, ai="hermes", ai_skills=True)
        (project_dir / ".hermes" / "skills").mkdir(parents=True)

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        preset_dir = self._create_command_preset(
            temp_dir, "hermes-reconcile-preset", "speckit.specify",
            "Preset specify", "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.register_enabled_presets_for_agent("hermes")

        skill_file = (
            home / ".hermes" / "skills" / "speckit-specify" / "SKILL.md"
        )
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "Override body" in content
        assert "Preset body" not in content
        assert not list(
            (project_dir / ".hermes" / "skills").glob("speckit-*/SKILL.md")
        )

        (overrides_dir / "speckit.specify.md").unlink()
        assert manager.remove("hermes-reconcile-preset") is True
        if skill_file.exists():
            restored = skill_file.read_text(encoding="utf-8")
            assert "Override body" not in restored
            assert "Preset body" not in restored

    def test_rescaffold_persists_commands_before_fallible_skills_phase(
        self, project_dir, temp_dir
    ):
        """A failure in the skills phase must not lose track of command
        files the commands phase already wrote to disk.

        ``register_enabled_presets_for_agent`` computes both
        ``registered_commands`` and ``registered_skills`` and persists them
        together in a single ``registry.update()`` call after both phases
        run. If ``_register_skills`` raises, the whole per-preset ``try``
        block is caught and ``registry.update()`` is never reached — even
        though ``_register_commands`` already wrote a real command file to
        disk. That file becomes untracked and preset removal can no longer
        clean it up. ``install_from_directory`` avoids this by persisting
        ``registered_commands`` immediately after the commands phase,
        before starting the independently fallible skills phase; rescaffold
        must do the same (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        preset_dir = self._create_command_preset(
            temp_dir, "rescaffold-persist-preset", "speckit.specify",
            "Rescaffold persist test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Switch to gemini (a plain command-file agent, so _register_commands
        # writes a real file) and make the *skills* phase blow up.
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_commands_dir = project_dir / ".gemini" / "commands"
        gemini_commands_dir.mkdir(parents=True)

        from unittest.mock import patch

        with patch.object(
            PresetManager, "_register_skills",
            side_effect=RuntimeError("simulated skills failure"),
        ):
            manager.register_enabled_presets_for_agent("gemini")

        cmd_file = gemini_commands_dir / "speckit.specify.toml"
        assert cmd_file.exists(), (
            "sanity: the commands phase must have written the file before "
            "the skills phase raised"
        )

        metadata = manager.registry.get("rescaffold-persist-preset")
        assert metadata["registered_commands"].get("gemini"), (
            "registered_commands must be persisted immediately after the "
            "commands phase, not only after the (fallible) skills phase "
            "also succeeds — otherwise the file written above is untracked "
            "and preset removal can't clean it up (#2948)"
        )

    def test_rescaffold_reconciles_override_even_when_skills_phase_fails(
        self, project_dir, temp_dir
    ):
        """A project override must still win after rescaffold even if the
        independently-fallible skills phase raises for that preset.

        ``register_enabled_presets_for_agent`` only records a preset's
        command names into ``affected_cmd_names`` — the set later passed to
        ``_reconcile_composed_commands``/``_reconcile_skills`` — in the
        ``for tmpl in manifest.templates`` loop that runs *after*
        ``_register_skills`` inside the per-preset ``try`` block. If
        ``_register_skills`` raises, the per-preset ``except`` catches it
        and ``continue``s before that loop ever runs, so this preset's
        command names never make it into ``affected_cmd_names`` even though
        ``_register_commands`` already wrote its raw content to disk. The
        final reconciliation call is skipped for this preset entirely,
        leaving the raw preset content in place instead of the project
        override that should win (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "reconcile-despite-skills-failure", "speckit.specify",
            "Preset specify", "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Simulate `integration use gemini` with the skills phase failing
        # for this preset (e.g. a symlink/permission error unrelated to the
        # commands phase, which already succeeded).
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)

        from unittest.mock import patch

        with patch.object(
            PresetManager, "_register_skills",
            side_effect=RuntimeError("simulated skills failure"),
        ):
            manager.register_enabled_presets_for_agent("gemini")

        cmd_file = gemini_dir / "speckit.specify.toml"
        assert cmd_file.exists(), "sanity: gemini should get a command file at all"
        content = cmd_file.read_text()
        assert "Override body" in content, (
            "the project override must still win after rescaffold, even "
            "though this preset's skills phase raised — a fallible skills "
            "phase must not skip reconciliation for command writes that "
            "already succeeded (#2948)"
        )
        assert "Preset body" not in content

    def test_rescaffold_reconciles_partial_command_write_after_failure(
        self, project_dir, temp_dir, monkeypatch
    ):
        """A command written before _register_commands raises must still be
        included in final priority-stack reconciliation."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "partial-command-failure-preset",
            "speckit.specify",
            "Preset specify",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)
        cmd_file = gemini_dir / "speckit.specify.toml"

        def partial_register(manifest, pack_dir):
            cmd_file.write_text("Partially written preset body\n", encoding="utf-8")
            raise RuntimeError("simulated partial command failure")

        monkeypatch.setattr(manager, "_register_commands", partial_register)
        manager.register_enabled_presets_for_agent("gemini")

        content = cmd_file.read_text(encoding="utf-8")
        assert "Override body" in content
        assert "Partially written preset body" not in content

    def test_copilot_skills_mode_skips_command_registration(self, project_dir, temp_dir):
        """``integration use copilot`` with skills mode enabled must only
        write the SKILL.md mirror, not also copilot's static command file.

        Copilot is command-backed (``extension: ".agent.md"``), but when
        ``ai_skills`` is enabled its preset overrides are meant to render
        exclusively as skills via ``_register_skills``. Before the fix,
        ``_register_commands`` had no ``ai_skills`` guard (unlike the
        extensions path), so both a stale ``.agent.md`` command file and
        the ``SKILL.md`` mirror were written for the same override (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "copilot-skills-preset", "speckit.specify",
            "Copilot skills test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        assert not list(copilot_commands_dir.glob("*specify*")), (
            "command-mode and skills-mode artifacts are mutually exclusive: "
            "no .agent.md command file should be written when copilot is "
            "running in skills mode (#2948)"
        )
        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:copilot-skills-preset" in skill_file.read_text()

    def test_rescaffold_toggle_command_to_skills_removes_stale_command_file(
        self, project_dir, temp_dir
    ):
        """Toggling the *same* agent from command mode to skills mode must
        remove the stale command-mode artifact, not just add the new one.

        Copilot stays the active agent throughout (``integration upgrade
        copilot`` after flipping ``ai_skills``, not a switch to a different
        agent). Before the fix, ``_register_commands``'s ``ai_skills`` guard
        made rescaffold a no-op for the commands phase once skills mode was
        on, leaving the previously written ``.agent.md`` file and its
        ``registered_commands`` entry behind even though ``_register_skills``
        went on to also write the ``SKILL.md`` mirror — violating the
        command/skill mutual-exclusion invariant this PR otherwise enforces
        (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "toggle-cmd-to-skill-preset", "speckit.specify",
            "Toggle test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        assert cmd_file.exists(), (
            "sanity: command mode should have written copilot's command file"
        )
        metadata = manager.registry.get("toggle-cmd-to-skill-preset")
        assert metadata["registered_commands"].get("copilot"), (
            "sanity: the command-mode write should be tracked for copilot"
        )

        # Flip ai_skills on for the *same* active agent and rescaffold, as
        # `integration upgrade copilot` would after the mode toggle.
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert not cmd_file.exists(), (
            "the stale command-mode file must be removed once copilot has "
            "toggled to skills mode for the same agent (#2948)"
        )
        metadata = manager.registry.get("toggle-cmd-to-skill-preset")
        assert not metadata["registered_commands"].get("copilot"), (
            "registered_commands must stop tracking copilot once its "
            "artifact has been unregistered, or removal will try to clean "
            "up a file that no longer exists (#2948)"
        )
        skill_file = project_dir / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        assert "preset:toggle-cmd-to-skill-preset" in skill_file.read_text(), (
            "sanity: the new skills-mode artifact should still be written"
        )

    def test_rescaffold_scaffolds_selfcontained_namespaced_commands(
        self, project_dir, temp_dir
    ):
        """A self-contained ``speckit.<ns>.<cmd>`` preset command scaffolds and
        survives rescaffold, even when no matching extension is installed.

        The preset ships the command body itself, so it is materialized just
        like a short ``speckit.<cmd>`` command — both at install and through a
        later reconciliation/rescaffold pass. It is not dropped by the
        ``speckit.<ns>.<cmd>`` name shape (#4076).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "ext-scoped-preset", "speckit.git.feature",
            "Ext override", "ext body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        ext_cmd = commands_dir / "speckit.git.feature.agent.md"
        assert ext_cmd.exists(), (
            "sanity: install must scaffold a self-contained namespaced command "
            "even when its like-named extension isn't installed"
        )

        manager.register_enabled_presets_for_agent("copilot")

        assert ext_cmd.exists(), (
            "rescaffold must keep the self-contained namespaced command"
        )
        metadata = manager.registry.get("ext-scoped-preset")
        assert (metadata.get("registered_commands") or {}).get("copilot")

    def test_rescaffold_scaffolds_selfcontained_namespaced_skills(
        self, project_dir, temp_dir
    ):
        """A self-contained ``speckit.<ns>.<cmd>`` preset command renders its
        skill even when no matching extension is installed."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        skills_dir = project_dir / ".github" / "skills"
        skills_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir,
            "ext-scoped-skill-preset",
            "speckit.git.feature",
            "Ext override",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_name = "speckit-git-feature"
        skill_file = skills_dir / skill_name / "SKILL.md"
        assert skill_file.exists(), (
            "install must render a self-contained namespaced command's skill "
            "even when its like-named extension isn't installed"
        )

        manager.register_enabled_presets_for_agent("copilot")

        assert skill_file.exists(), (
            "rescaffold must keep the self-contained namespaced command's skill"
        )

    def test_uncomposable_wrap_command_skips_skill_in_skills_mode(
        self, project_dir, temp_dir
    ):
        """A wrap command with no base layer must not materialize a broken
        skill in skills mode.

        When ``_register_commands`` skips an uncomposable wrap command (no
        base to compose onto — e.g. the command it wraps comes from an
        uninstalled extension), ``_register_skills`` must skip it too. Before
        this fix, skills mode fell back to the raw preset body and wrote a
        SKILL.md containing a literal ``{CORE_TEMPLATE}`` placeholder.
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        skills_dir = project_dir / ".github" / "skills"
        skills_dir.mkdir(parents=True)

        preset_dir = temp_dir / "uncomposable-wrap"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        # speckit.git.feature has no core command template and no installed
        # extension, so there is no base layer to wrap.
        (preset_dir / "commands" / "speckit.git.feature.md").write_text(
            "---\ndescription: Wrap\nstrategy: wrap\n---\n\n"
            "wrap start\n{CORE_TEMPLATE}\nwrap end\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "uncomposable-wrap",
                "name": "uncomposable-wrap",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.git.feature",
                        "file": "commands/speckit.git.feature.md",
                        "strategy": "wrap",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="no base command layer"):
            manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-git-feature" / "SKILL.md"
        assert not skill_file.exists(), (
            "an uncomposable wrap command must not be rendered as a skill"
        )
        # Belt-and-suspenders: no artifact anywhere may leak the raw placeholder.
        leaked = [
            p for p in skills_dir.rglob("*")
            if p.is_file() and "{CORE_TEMPLATE}" in p.read_text(encoding="utf-8")
        ]
        assert not leaked, f"literal {{CORE_TEMPLATE}} leaked into {leaked}"

    def test_same_mode_partial_command_rescaffold_keeps_skipped_tracking(
        self, project_dir, temp_dir
    ):
        """A partial command refresh must keep still-live skipped artifacts tracked."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)
        preset_dir = self._create_multi_command_preset(
            temp_dir,
            "same-mode-partial-command-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        installed_dir = manager.presets_dir / "same-mode-partial-command-preset"
        (installed_dir / "commands" / "speckit.plan.md").unlink()
        manager.register_enabled_presets_for_agent("copilot")

        metadata = manager.registry.get("same-mode-partial-command-preset")
        assert set(metadata["registered_commands"]["copilot"]) == {
            "speckit.specify",
            "speckit.plan",
        }
        assert (commands_dir / "speckit.plan.agent.md").exists()

    def test_same_mode_partial_skill_rescaffold_keeps_skipped_tracking(
        self, project_dir, temp_dir
    ):
        """A partial skill refresh must keep still-live skipped artifacts tracked."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")
        self._create_skill(skills_dir, "speckit-plan")
        preset_dir = self._create_multi_command_preset(
            temp_dir,
            "same-mode-partial-skill-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        installed_dir = manager.presets_dir / "same-mode-partial-skill-preset"
        (installed_dir / "commands" / "speckit.plan.md").unlink()
        manager.register_enabled_presets_for_agent("copilot")

        metadata = manager.registry.get("same-mode-partial-skill-preset")
        assert set(metadata["registered_skills"]["copilot"]) == {
            "speckit-specify",
            "speckit-plan",
        }

    def test_toggle_command_to_skills_preserves_old_command_on_skills_failure(
        self, project_dir, temp_dir, monkeypatch
    ):
        """A command->skills toggle must not destroy the old command
        artifact before the new skill registration has actually succeeded.

        Before the fix, the stale command-mode file/tracking was
        unregistered unconditionally as soon as ``_register_commands``'s
        ``ai_skills`` guard made the commands phase a no-op — regardless
        of whether the subsequent, independently-fallible
        ``_register_skills()`` call actually succeeded. If skills raises
        (e.g. a transient I/O error), the per-preset exception handler
        just logs and continues, leaving neither the old command file
        nor a new skill file — the preset's command override vanishes
        entirely from copilot until the next successful rescaffold
        (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "toggle-failure-preset", "speckit.specify",
            "Toggle failure test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        assert cmd_file.exists(), (
            "sanity: command mode should have written copilot's command file"
        )
        metadata = manager.registry.get("toggle-failure-preset")
        assert metadata["registered_commands"].get("copilot"), (
            "sanity: the command-mode write should be tracked for copilot"
        )

        # Flip ai_skills on for the *same* active agent and rescaffold, as
        # `integration upgrade copilot` would, but with skills registration
        # injected to fail.
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        def _raise_register_skills(*args, **kwargs):
            raise OSError("simulated skills-phase failure")

        monkeypatch.setattr(manager, "_register_skills", _raise_register_skills)
        manager.register_enabled_presets_for_agent("copilot")

        assert cmd_file.exists(), (
            "the old command-mode artifact must survive when the "
            "replacement skills registration fails — deleting it before "
            "the new artifact is confirmed leaves neither in place (#2948)"
        )
        metadata = manager.registry.get("toggle-failure-preset")
        assert metadata["registered_commands"].get("copilot"), (
            "registered_commands must keep tracking copilot's still-live "
            "command file when the skills replacement failed, or a later "
            "removal/rescaffold will believe there is nothing to clean up "
            "even though the file is still on disk (#2948)"
        )

    def test_toggle_command_to_skills_empty_result_preserves_old_command(
        self, project_dir, temp_dir
    ):
        """A non-raising but empty skills result must not delete the old command.

        Before the fix, the stale command-mode artifact was retired as
        soon as ``_register_skills()`` completed without raising —
        regardless of whether it actually wrote anything for this agent.
        Deleting the preset's own command source file (simulating a
        missing/corrupted override) makes ``_register_skills`` return
        ``{}`` for copilot without raising at all, which must leave the
        old command file and its tracking untouched (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "toggle-empty-result-preset", "speckit.specify",
            "Toggle empty-result test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        assert cmd_file.exists(), (
            "sanity: command mode should have written copilot's command file"
        )

        # Remove the *installed* copy of the preset's source file (not the
        # original temp source) so _register_skills can find nothing to
        # render — a real "missing source" case, not an exception — leaving
        # registered_skills empty for copilot.
        (manager.presets_dir / "toggle-empty-result-preset" / "commands" / "speckit.specify.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert cmd_file.exists(), (
            "an empty (non-raising) skills registration result must not "
            "cause the old command-mode artifact to be deleted (#2948)"
        )
        metadata = manager.registry.get("toggle-empty-result-preset")
        assert metadata["registered_commands"].get("copilot"), (
            "registered_commands must keep tracking copilot's still-live "
            "command file when nothing was actually replaced (#2948)"
        )
        skill_file = project_dir / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        assert not skill_file.exists(), (
            "sanity: no skill should have been written when the source "
            "was missing"
        )

    def test_toggle_command_to_skills_partial_result_only_removes_replaced_command(
        self, project_dir, temp_dir
    ):
        """Only the command whose skill replacement actually landed is retired.

        A two-command preset where one command's source file goes missing
        right before the toggle: ``_register_skills`` genuinely returns a
        partial result (one name present, one silently skipped) without
        raising. The command whose skill was written must be retired; the
        other must keep both its old command file and its registry
        tracking, since no replacement for it actually landed (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_multi_command_preset(
            temp_dir, "toggle-partial-result-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        specify_cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        plan_cmd_file = copilot_commands_dir / "speckit.plan.agent.md"
        assert specify_cmd_file.exists() and plan_cmd_file.exists(), (
            "sanity: command mode should have written both command files"
        )
        metadata = manager.registry.get("toggle-partial-result-preset")
        assert set(metadata["registered_commands"].get("copilot", [])) == {
            "speckit.specify", "speckit.plan",
        }, "sanity: both commands should be tracked for copilot"

        # Remove only the plan command's *installed* source so its skill
        # replacement is silently skipped (missing source), while
        # specify's succeeds — a genuine partial result, not an injected
        # exception.
        (manager.presets_dir / "toggle-partial-result-preset" / "commands" / "speckit.plan.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert not specify_cmd_file.exists(), (
            "the specify command's old artifact must be retired since its "
            "skill replacement actually landed (#2948)"
        )
        assert plan_cmd_file.exists(), (
            "the plan command's old artifact must survive since its skill "
            "replacement never landed (missing source) (#2948)"
        )
        metadata = manager.registry.get("toggle-partial-result-preset")
        tracked_commands = metadata["registered_commands"].get("copilot", [])
        assert "speckit.specify" not in tracked_commands, (
            "specify must stop being tracked as a command once its "
            "artifact has been unregistered (#2948)"
        )
        assert "speckit.plan" in tracked_commands, (
            "plan must keep being tracked as a command since its old "
            "artifact is still on disk (#2948)"
        )
        specify_skill_file = (
            project_dir / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        )
        assert "preset:toggle-partial-result-preset" in specify_skill_file.read_text(), (
            "sanity: specify's new skill artifact should exist"
        )
        plan_skill_file = project_dir / ".github" / "skills" / "speckit-plan"
        assert not plan_skill_file.exists(), (
            "sanity: no skill should have been written for plan since its "
            "source was missing"
        )

    def test_lower_priority_skill_does_not_remove_failed_winner_command(
        self, project_dir, temp_dir
    ):
        """Only a successfully rendered winning layer may retire a command."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        lower_dir = self._create_command_preset(
            temp_dir,
            "lower-toggle-preset",
            "speckit.specify",
            "Lower preset",
            "Lower body",
        )
        higher_dir = self._create_command_preset(
            temp_dir,
            "higher-toggle-preset",
            "speckit.specify",
            "Higher preset",
            "Higher body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)

        command_file = commands_dir / "speckit.specify.agent.md"
        assert "Higher body" in command_file.read_text(encoding="utf-8")

        higher_source = (
            manager.presets_dir
            / "higher-toggle-preset"
            / "commands"
            / "speckit.specify.md"
        )
        higher_source.unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        manager.register_enabled_presets_for_agent("copilot")

        assert command_file.exists(), (
            "a lower-priority skill replacement must not remove the existing "
            "higher-priority command when the winning layer did not render"
        )
        assert "Higher body" in command_file.read_text(encoding="utf-8")

        higher_source.write_text(
            "---\ndescription: Higher preset\n---\n\nHigher body\n",
            encoding="utf-8",
        )
        manager.register_enabled_presets_for_agent("copilot")

        assert not command_file.exists(), (
            "the old command should be retired after the winning skill "
            "layer renders successfully"
        )
        for preset_id in ("lower-toggle-preset", "higher-toggle-preset"):
            metadata = manager.registry.get(preset_id)
            assert not metadata["registered_commands"].get("copilot"), (
                "all layers sharing the retired command output must drop "
                "their stale command tracking"
            )

    def test_successful_winner_without_stale_tracking_retires_lower_command(
        self, project_dir, temp_dir
    ):
        """Winner success is independent of whether that layer tracked a command."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        lower_dir = self._create_command_preset(
            temp_dir,
            "lower-command-preset",
            "speckit.specify",
            "Lower preset",
            "Lower body",
        )
        higher_dir = self._create_command_preset(
            temp_dir,
            "higher-skill-preset",
            "speckit.specify",
            "Higher preset",
            "Higher body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)

        command_file = commands_dir / "speckit.specify.agent.md"
        assert command_file.exists()

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)
        higher_metadata = manager.registry.get("higher-skill-preset")
        assert not higher_metadata["registered_commands"].get("copilot")

        manager.register_enabled_presets_for_agent("copilot")

        assert not command_file.exists(), (
            "a successfully rendered winning skill must retire a lower "
            "layer's stale command even when the winner never tracked one"
        )
        lower_metadata = manager.registry.get("lower-command-preset")
        assert not lower_metadata["registered_commands"].get("copilot")

    def test_lower_priority_command_does_not_remove_failed_winner_skill(
        self, project_dir, temp_dir
    ):
        """Only a successfully rendered winning command may retire a skill."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        lower_dir = self._create_command_preset(
            temp_dir,
            "lower-skill-preset",
            "speckit.specify",
            "Lower preset",
            "Lower body",
        )
        higher_dir = self._create_command_preset(
            temp_dir,
            "higher-command-preset",
            "speckit.specify",
            "Higher preset",
            "Higher body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)

        skill_file = (
            project_dir
            / ".github"
            / "skills"
            / "speckit-specify"
            / "SKILL.md"
        )
        assert "Higher body" in skill_file.read_text(encoding="utf-8")

        higher_source = (
            manager.presets_dir
            / "higher-command-preset"
            / "commands"
            / "speckit.specify.md"
        )
        higher_source.unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)

        manager.register_enabled_presets_for_agent("copilot")

        assert skill_file.exists(), (
            "a lower-priority command replacement must not remove the "
            "existing higher-priority skill when the winner did not render"
        )
        assert "Higher body" in skill_file.read_text(encoding="utf-8")

        higher_source.write_text(
            "---\ndescription: Higher preset\n---\n\nHigher body\n",
            encoding="utf-8",
        )
        manager.register_enabled_presets_for_agent("copilot")

        assert not skill_file.exists(), (
            "the old skill should be retired after the winning command "
            "layer renders successfully"
        )
        for preset_id in ("lower-skill-preset", "higher-command-preset"):
            metadata = manager.registry.get(preset_id)
            assert not metadata["registered_skills"].get("copilot"), (
                "all layers sharing the retired skill output must drop "
                "their stale skill tracking"
            )

    def test_project_override_command_retires_stale_preset_skill(
        self, project_dir, temp_dir
    ):
        """A reconciled project override can replace a stale preset skill."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir,
            "override-toggle-preset",
            "speckit.specify",
            "Preset",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = (
            project_dir
            / ".github"
            / "skills"
            / "speckit-specify"
            / "SKILL.md"
        )
        assert skill_file.exists()

        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Project override\n---\n\nOverride body\n",
            encoding="utf-8",
        )
        (
            manager.presets_dir
            / "override-toggle-preset"
            / "commands"
            / "speckit.specify.md"
        ).unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)

        manager.register_enabled_presets_for_agent("copilot")

        command_file = commands_dir / "speckit.specify.agent.md"
        assert "Override body" in command_file.read_text(encoding="utf-8")
        assert not skill_file.exists(), (
            "the stale preset skill must be retired once the project "
            "override command is successfully reconciled"
        )
        metadata = manager.registry.get("override-toggle-preset")
        assert not metadata["registered_skills"].get("copilot")

    def test_project_override_command_retires_reconciled_override_skill(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir,
            "reconciled-override-toggle-preset",
            "speckit.specify",
            "Preset",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Project override\n---\n\nOverride body\n",
            encoding="utf-8",
        )
        (
            manager.presets_dir
            / "reconciled-override-toggle-preset"
            / "commands"
            / "speckit.specify.md"
        ).unlink()

        manager.register_enabled_presets_for_agent("copilot")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "override:speckit.specify" in skill_file.read_text(
            encoding="utf-8"
        )

        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_presets_for_agent("copilot")

        assert "Override body" in (
            commands_dir / "speckit.specify.agent.md"
        ).read_text(encoding="utf-8")
        assert not skill_file.exists()
        metadata = manager.registry.get(
            "reconciled-override-toggle-preset"
        )
        assert not metadata["registered_skills"].get("copilot")

    def test_project_override_skill_retires_stale_preset_command(
        self, project_dir, temp_dir
    ):
        """A reconciled override skill may retire a stale preset command."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir,
            "override-skill-toggle-preset",
            "speckit.specify",
            "Preset",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        command_file = commands_dir / "speckit.specify.agent.md"
        assert command_file.exists()
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")
        manager.registry.update(
            "override-skill-toggle-preset",
            {"registered_skills": {"copilot": ["speckit-specify"]}},
        )

        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Project override\n---\n\nOverride body\n",
            encoding="utf-8",
        )
        (
            manager.presets_dir
            / "override-skill-toggle-preset"
            / "commands"
            / "speckit.specify.md"
        ).unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        manager.register_enabled_presets_for_agent("copilot")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "Override body" in skill_file.read_text(encoding="utf-8")
        assert not command_file.exists(), (
            "the stale preset command must be retired after the project "
            "override skill is successfully reconciled"
        )
        metadata = manager.registry.get("override-skill-toggle-preset")
        assert not metadata["registered_commands"].get("copilot")

    def test_toggle_skills_to_command_empty_result_preserves_old_skill(
        self, project_dir, temp_dir
    ):
        """A non-raising but empty command result must not delete the old skill.

        Mirror image of the empty-result command->skills case: deleting the
        preset's own source file makes ``_register_commands`` return ``{}``
        for copilot without raising, which must leave the old SKILL.md and
        its tracking untouched (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "toggle-skill-empty-result-preset", "speckit.specify",
            "Toggle empty-result test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:toggle-skill-empty-result-preset" in skill_file.read_text(), (
            "sanity: skills mode should have written the SKILL.md mirror"
        )

        # Remove the preset's own *installed* source file so
        # _register_commands can find nothing to render — a real "missing
        # source" case, not an exception — leaving registered_commands
        # empty for copilot.
        (manager.presets_dir / "toggle-skill-empty-result-preset" / "commands" / "speckit.specify.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_presets_for_agent("copilot")

        assert "preset:toggle-skill-empty-result-preset" in skill_file.read_text(), (
            "an empty (non-raising) command registration result must not "
            "cause the old skills-mode artifact to be deleted/reverted "
            "(#2948)"
        )
        metadata = manager.registry.get("toggle-skill-empty-result-preset")
        assert "speckit-specify" in metadata["registered_skills"].get("copilot", []), (
            "registered_skills must keep tracking copilot's still-live "
            "skill file when nothing was actually replaced (#2948)"
        )

    def test_toggle_skills_to_command_partial_result_only_removes_replaced_skill(
        self, project_dir, temp_dir
    ):
        """Only the skill whose command replacement actually landed is retired.

        Mirror image of the partial-result command->skills case: a
        two-command preset where one command's source file goes missing
        right before the toggle, so ``_register_commands`` genuinely
        returns a partial result. The skill whose command was written
        must be retired; the other must keep both its old SKILL.md and
        its registry tracking, since no replacement for it landed (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")
        self._create_skill(skills_dir, "speckit-plan")

        # A core template lets the retired skill restore to core content
        # instead of being removed entirely (it has nothing else to fall
        # back to), matching _unregister_skills's behaviour elsewhere.
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        preset_dir = self._create_multi_command_preset(
            temp_dir, "toggle-skill-partial-result-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        specify_skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        plan_skill_file = skills_dir / "speckit-plan" / "SKILL.md"
        assert "preset:toggle-skill-partial-result-preset" in specify_skill_file.read_text()
        assert "preset:toggle-skill-partial-result-preset" in plan_skill_file.read_text()
        metadata = manager.registry.get("toggle-skill-partial-result-preset")
        assert set(metadata["registered_skills"].get("copilot", [])) == {
            "speckit-specify", "speckit-plan",
        }, "sanity: both skills should be tracked for copilot"

        # Remove only the plan command's *installed* source so its command
        # replacement is silently skipped (missing source), while
        # specify's succeeds.
        (manager.presets_dir / "toggle-skill-partial-result-preset" / "commands" / "speckit.plan.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_presets_for_agent("copilot")

        assert "preset:toggle-skill-partial-result-preset" not in specify_skill_file.read_text(), (
            "the specify skill's old artifact must be retired/reverted "
            "since its command replacement actually landed (#2948)"
        )
        assert "preset:toggle-skill-partial-result-preset" in plan_skill_file.read_text(), (
            "the plan skill's old artifact must survive since its command "
            "replacement never landed (missing source) (#2948)"
        )
        metadata = manager.registry.get("toggle-skill-partial-result-preset")
        tracked_skills = metadata["registered_skills"].get("copilot", [])
        assert "speckit-specify" not in tracked_skills, (
            "specify must stop being tracked as a skill once its artifact "
            "has been unregistered/reverted (#2948)"
        )
        assert "speckit-plan" in tracked_skills, (
            "plan must keep being tracked as a skill since its old "
            "artifact is still on disk (#2948)"
        )
        assert (copilot_commands_dir / "speckit.specify.agent.md").exists(), (
            "sanity: specify's new command artifact should exist"
        )

    def test_toggle_command_to_skills_retires_alias_group_when_primary_skill_lands(
        self, project_dir, temp_dir
    ):
        """A command's aliases must be retired together with its primary
        once the primary's skill replacement lands.

        ``CommandRegistrar.register_commands()`` tracks and returns
        primary + alias names flattened together, but ``_register_skills()``
        only ever renders/returns the *primary* command name's skill. The
        alias's own name run through ``_skill_names_for_command()`` never
        matches anything real, so without grouping by primary, the alias
        command artifact and its tracking entry would survive forever even
        after mutual exclusion is otherwise enforced for the primary (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_multi_command_preset_with_aliases(
            temp_dir, "alias-group-success-preset",
            [("speckit.specify", ["speckit.spec"])],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        primary_cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        alias_cmd_file = copilot_commands_dir / "speckit.spec.agent.md"
        assert primary_cmd_file.exists() and alias_cmd_file.exists(), (
            "sanity: command mode should have written both the primary "
            "and alias command files"
        )
        metadata = manager.registry.get("alias-group-success-preset")
        assert set(metadata["registered_commands"].get("copilot", [])) == {
            "speckit.specify", "speckit.spec",
        }, "sanity: both primary and alias should be tracked for copilot"

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert not primary_cmd_file.exists(), (
            "the primary's old command artifact must be retired once its "
            "skill replacement lands (#2948)"
        )
        assert not alias_cmd_file.exists(), (
            "the alias's old command artifact must be retired together "
            "with its primary once the primary's skill replacement lands "
            "(#2948)"
        )
        metadata = manager.registry.get("alias-group-success-preset")
        registered_commands = metadata.get("registered_commands", {})
        assert not registered_commands.get("copilot"), (
            "neither the primary nor the alias should remain tracked as "
            "commands once both artifacts are retired (#2948)"
        )
        skill_file = project_dir / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        assert skill_file.exists(), "sanity: the primary's skill should have been written"

    def test_toggle_command_to_skills_keeps_alias_group_when_primary_skill_missing(
        self, project_dir, temp_dir
    ):
        """A command's aliases must survive together with its primary when
        the primary's skill replacement never lands.

        Mirror image of the group-retirement case: deleting the preset's
        own installed command source makes ``_register_skills`` genuinely
        return nothing for ``speckit.specify``, so neither the primary nor
        its alias have a real replacement — both old command artifacts and
        their tracking must survive (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_multi_command_preset_with_aliases(
            temp_dir, "alias-group-failure-preset",
            [("speckit.specify", ["speckit.spec"])],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        primary_cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        alias_cmd_file = copilot_commands_dir / "speckit.spec.agent.md"
        assert primary_cmd_file.exists() and alias_cmd_file.exists(), (
            "sanity: command mode should have written both the primary "
            "and alias command files"
        )

        # Remove the installed source so _register_skills can find nothing
        # to render for the primary — a real "missing source" case.
        (manager.presets_dir / "alias-group-failure-preset" / "commands" / "speckit.specify.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert primary_cmd_file.exists(), (
            "the primary's old command artifact must survive since its "
            "skill replacement never landed (#2948)"
        )
        assert alias_cmd_file.exists(), (
            "the alias's old command artifact must survive together with "
            "its primary since neither has a real replacement (#2948)"
        )
        metadata = manager.registry.get("alias-group-failure-preset")
        assert set(metadata["registered_commands"].get("copilot", [])) == {
            "speckit.specify", "speckit.spec",
        }, (
            "both the primary and alias must keep being tracked since "
            "nothing was actually replaced (#2948)"
        )
        skill_file = project_dir / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        assert not skill_file.exists(), (
            "sanity: no skill should have been written when the source "
            "was missing"
        )

    def test_toggle_command_to_skills_partial_multi_group_only_retires_successful_group(
        self, project_dir, temp_dir
    ):
        """With two independent alias groups, only the group whose primary
        skill actually lands is retired; the other survives intact.

        A preset with two commands (``speckit.specify`` with alias
        ``speckit.spec``, and ``speckit.plan`` with alias
        ``speckit.plan-alt``) where only ``speckit.plan``'s installed
        source goes missing: ``speckit.specify``'s group (primary + alias)
        must be fully retired, while ``speckit.plan``'s entire group
        (primary + alias) must survive together, since grouping is
        per-primary, not per-individual-name (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_multi_command_preset_with_aliases(
            temp_dir, "alias-group-partial-preset",
            [
                ("speckit.specify", ["speckit.spec"]),
                ("speckit.plan", ["speckit.plan-alt"]),
            ],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        specify_cmd = copilot_commands_dir / "speckit.specify.agent.md"
        spec_alias_cmd = copilot_commands_dir / "speckit.spec.agent.md"
        plan_cmd = copilot_commands_dir / "speckit.plan.agent.md"
        plan_alias_cmd = copilot_commands_dir / "speckit.plan-alt.agent.md"
        assert all(
            f.exists() for f in (specify_cmd, spec_alias_cmd, plan_cmd, plan_alias_cmd)
        ), "sanity: command mode should have written all four command files"

        # Remove only plan's installed source so its group's skill
        # replacement is silently skipped, while specify's group succeeds.
        (manager.presets_dir / "alias-group-partial-preset" / "commands" / "speckit.plan.md").unlink()

        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        assert not specify_cmd.exists() and not spec_alias_cmd.exists(), (
            "specify's whole group (primary + alias) must be retired "
            "since its skill replacement landed (#2948)"
        )
        assert plan_cmd.exists() and plan_alias_cmd.exists(), (
            "plan's whole group (primary + alias) must survive together "
            "since its skill replacement never landed (#2948)"
        )
        metadata = manager.registry.get("alias-group-partial-preset")
        tracked_commands = set(metadata["registered_commands"].get("copilot", []))
        assert tracked_commands == {"speckit.plan", "speckit.plan-alt"}, (
            "only plan's group should remain tracked as commands; "
            "specify's group must be fully untracked (#2948)"
        )

    def test_rescaffold_toggle_skills_to_command_removes_stale_skill_file(
        self, project_dir, temp_dir
    ):
        """Toggling the *same* agent from skills mode to command mode must
        remove the stale skills-mode artifact, not just add the new one.

        Mirror image of the command-to-skills toggle: once ``ai_skills`` is
        turned off for copilot (still the active agent), ``_get_skills_dir``
        stops resolving a skills directory for it, so ``_register_skills``
        becomes a no-op — but the ``SKILL.md`` written while skills mode was
        on, and its ``registered_skills`` entry, were left behind even
        though ``_register_commands`` went on to (re)write the ``.agent.md``
        command file, again breaking mutual exclusion (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # A core template lets the stale skill restore to core content
        # (instead of being removed entirely, since it has nothing to fall
        # back to), matching how `_unregister_skills` behaves elsewhere.
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        preset_dir = self._create_command_preset(
            temp_dir, "toggle-skill-to-cmd-preset", "speckit.specify",
            "Toggle test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:toggle-skill-to-cmd-preset" in skill_file.read_text(), (
            "sanity: skills mode should have written the SKILL.md mirror"
        )
        metadata = manager.registry.get("toggle-skill-to-cmd-preset")
        assert metadata["registered_skills"].get("copilot"), (
            "sanity: the skills-mode write should be tracked for copilot"
        )

        # Flip ai_skills off for the *same* active agent and rescaffold, as
        # `integration upgrade copilot` would after the mode toggle.
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_presets_for_agent("copilot")

        restored_content = skill_file.read_text()
        assert "preset:toggle-skill-to-cmd-preset" not in restored_content, (
            "the stale skills-mode artifact must be reverted once copilot "
            "has toggled to command mode for the same agent (#2948)"
        )
        assert "Core specify body" in restored_content, (
            "sanity: the skill should fall back to core content, not just "
            "lose the preset's override"
        )
        metadata = manager.registry.get("toggle-skill-to-cmd-preset")
        assert not metadata["registered_skills"].get("copilot"), (
            "registered_skills must stop tracking copilot once its "
            "artifact has been unregistered/restored (#2948)"
        )
        cmd_file = copilot_commands_dir / "speckit.specify.agent.md"
        assert cmd_file.exists(), (
            "sanity: the new command-mode artifact should still be written"
        )
        assert "preset body" in cmd_file.read_text()

    def test_native_skill_activation_recreates_deleted_skills_root(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")
        preset_dir = self._create_command_preset(
            temp_dir,
            "native-root-recovery-preset",
            "speckit.specify",
            "Native root recovery",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        codex_skills_dir = project_dir / ".agents" / "skills"
        assert not codex_skills_dir.exists()
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")

        skill_file = codex_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:native-root-recovery-preset" in skill_file.read_text()
        metadata = manager.registry.get("native-root-recovery-preset")
        assert "speckit.specify" in metadata["registered_commands"]["codex"]

    def test_rescaffold_migrates_legacy_flat_list_registered_skills(
        self, project_dir, temp_dir
    ):
        """Rescaffolding a preset with a legacy flat-list ``registered_skills``
        entry must persist the migrated per-agent dict even when the
        rescaffolded skill names are unchanged from before.

        ``_normalize_registered_skills`` converts a legacy flat ``List[str]``
        (predating per-agent provenance) into ``{agent_name: [...]}`` in
        memory, but the persistence check compared only the *normalized*
        ``merged_skills`` against the *normalized* ``existing_skills`` —
        both derived from the same raw legacy list. When the freshly
        registered names are identical to what the legacy list already
        held (the common case: nothing about the preset or skill actually
        changed), that comparison is a no-op and ``registry.update()`` is
        skipped, leaving the *raw* on-disk value as the un-migrated flat
        list. A later switch to a different skill-mode agent and removal
        then follows the legacy best-effort restore path (only the
        currently active agent's directory) instead of the per-agent
        provenance path, orphaning the first agent's override (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")
        codex_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "legacy-skills-preset", "speckit.specify",
            "Legacy skills test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Simulate a registry entry written by a pre-#2948 spec-kit version:
        # registered_skills stored as a flat list with no per-agent
        # provenance, rather than the dict shape install_from_directory
        # writes today.
        manager.registry.update(
            "legacy-skills-preset", {"registered_skills": ["speckit-specify"]},
        )
        metadata = manager.registry.get("legacy-skills-preset")
        assert isinstance(metadata["registered_skills"], list), (
            "sanity: the injected legacy format is a flat list"
        )

        # Rescaffold for the *same* active agent (claude) with no actual
        # change to the registered skill names, mirroring `integration
        # upgrade claude` re-running registration for the active
        # integration.
        manager.register_enabled_presets_for_agent("claude")

        metadata = manager.registry.get("legacy-skills-preset")
        registered_skills = metadata.get("registered_skills")
        assert isinstance(registered_skills, dict), (
            "rescaffold must migrate a legacy flat-list registered_skills "
            "entry to the per-agent dict format even when the "
            "rescaffolded names are unchanged, or the raw registry stays "
            "un-migrated and later removal loses per-agent provenance "
            "(#2948)"
        )
        assert registered_skills.get("claude") == ["speckit-specify"]

        # Switch to a different skill-mode agent and rescaffold again —
        # with the dict format now in place, both directories should be
        # tracked and therefore restorable on removal.
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")

        metadata = manager.registry.get("legacy-skills-preset")
        assert set(metadata.get("registered_skills", {})) == {"claude", "codex"}, (
            "the migrated dict must keep recording every agent directory "
            "the preset actually wrote to, exactly like a preset that was "
            "always in dict format (#2948)"
        )

        assert manager.remove("legacy-skills-preset") is True

        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        codex_skill = codex_skills_dir / "speckit-specify" / "SKILL.md"
        for skill_file, label in ((claude_skill, "claude"), (codex_skill, "codex")):
            assert skill_file.exists(), f"{label} skill file should still exist after removal"
            content = skill_file.read_text()
            assert "preset:legacy-skills-preset" not in content, (
                f"{label}'s preset override must be restored on removal, "
                "not orphaned because the registry stayed in legacy "
                "flat-list format (#2948)"
            )
            assert "Core specify body" in content

    def test_rescaffold_legacy_flat_list_direct_switch_preserves_original_agent(
        self, project_dir, temp_dir
    ):
        """A legacy flat-list ``registered_skills`` entry must not be
        misattributed to the wrong agent when the *first* post-upgrade
        operation is a direct switch to a different skill-mode agent.

        Blindly attributing every legacy flat-list name to ``agent_name`` —
        the agent currently being (re)activated — loses the actual writer
        whenever that first operation is ``integration use codex`` (or
        ``switch``) run directly against a legacy Claude override, without
        an intervening same-agent rescaffold for Claude first. The
        migrated dict then only records ``{"codex": [...]}``, so a later
        ``remove()`` restores Codex but permanently orphans the Claude
        override that was never in the registry to begin with (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")
        codex_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "legacy-direct-switch-preset", "speckit.specify",
            "Legacy direct switch test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # install_from_directory wrote the preset's override to Claude's
        # skill directory (the active agent at install time) — sanity-check
        # that the marker is actually there before simulating the legacy
        # registry format.
        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:legacy-direct-switch-preset" in claude_skill.read_text(), (
            "sanity: install should have written the override under claude"
        )

        # Simulate a pre-#2948 registry: a flat list with no per-agent
        # provenance, even though the file on disk was actually written
        # under claude's directory.
        manager.registry.update(
            "legacy-direct-switch-preset",
            {"registered_skills": ["speckit-specify"]},
        )

        # Directly switch to codex — no intervening rescaffold for claude —
        # mirroring `integration use codex` / `switch codex` run right after
        # upgrading spec-kit versions.
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")

        metadata = manager.registry.get("legacy-direct-switch-preset")
        registered_skills = metadata.get("registered_skills")
        assert isinstance(registered_skills, dict)
        assert set(registered_skills) == {"claude", "codex"}, (
            "migrating a legacy flat-list entry on a direct switch must "
            "infer the actual writer (claude) from the existing on-disk "
            "SKILL.md provenance, not attribute every name to whichever "
            "agent happens to be activated first after the upgrade "
            "(#2948)"
        )

        assert manager.remove("legacy-direct-switch-preset") is True

        codex_skill = codex_skills_dir / "speckit-specify" / "SKILL.md"
        for skill_file, label in ((claude_skill, "claude"), (codex_skill, "codex")):
            assert skill_file.exists(), f"{label} skill file should still exist after removal"
            content = skill_file.read_text()
            assert "preset:legacy-direct-switch-preset" not in content, (
                f"{label}'s preset override must be restored on removal, "
                "not permanently orphaned by a misattributed legacy "
                "migration (#2948)"
            )
            assert "Core specify body" in content

    def test_rescaffold_legacy_flat_list_infers_command_backed_skills_owner(
        self, project_dir, temp_dir
    ):
        """Legacy provenance inference must also probe command-backed agents
        that were running in skills mode, not only agents whose command
        registrar config is statically ``/SKILL.md``-only.

        Copilot is command-backed (``extension: ".agent.md"``), but with
        ``ai_skills`` enabled its preset overrides render as ``SKILL.md``
        files under ``.github/skills`` exactly like a native skill-only
        agent (claude, codex, ...). Before the fix,
        ``_infer_legacy_skill_provenance`` only probed agents whose
        registrar config has a static ``extension == "/SKILL.md"``, so a
        real preset-owned ``.github/skills/.../SKILL.md`` written while
        Copilot was the active, skills-mode agent was never found — the
        legacy flat list was misattributed entirely to whichever agent the
        first post-upgrade switch happened to activate, permanently
        orphaning Copilot's override on later removal (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        copilot_skills_dir = project_dir / ".github" / "skills"
        self._create_skill(copilot_skills_dir, "speckit-specify")
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "legacy-copilot-skills-preset", "speckit.specify",
            "Legacy copilot skills test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        copilot_skill = copilot_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:legacy-copilot-skills-preset" in copilot_skill.read_text(), (
            "sanity: install should have written the override under "
            "copilot's skills directory while copilot was active in "
            "skills mode"
        )
        # Sanity: no command-mode artifact was written either — copilot's
        # command file and skills file are mutually exclusive.
        assert not list((project_dir / ".github" / "agents").glob("*specify*")), (
            "sanity: copilot in skills mode must not also write a command "
            "file that could be falsely attributed instead"
        )

        # Simulate a pre-#2948 registry: a flat list with no per-agent
        # provenance, even though the file on disk was actually written
        # under copilot's skills directory.
        manager.registry.update(
            "legacy-copilot-skills-preset",
            {"registered_skills": ["speckit-specify"]},
        )

        # Directly switch to claude — no intervening rescaffold for
        # copilot — mirroring `integration use claude` run right after
        # upgrading spec-kit versions.
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        manager.register_enabled_presets_for_agent("claude")

        metadata = manager.registry.get("legacy-copilot-skills-preset")
        registered_skills = metadata.get("registered_skills")
        assert isinstance(registered_skills, dict)
        assert set(registered_skills) == {"copilot", "claude"}, (
            "migrating a legacy flat-list entry on a direct switch must "
            "infer the actual writer (copilot, running in skills mode) "
            "even though copilot's registrar config is command-backed, "
            "not just agents with a static /SKILL.md extension (#2948)"
        )

        assert manager.remove("legacy-copilot-skills-preset") is True

        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        for skill_file, label in ((copilot_skill, "copilot"), (claude_skill, "claude")):
            assert skill_file.exists(), f"{label} skill file should still exist after removal"
            content = skill_file.read_text()
            assert "preset:legacy-copilot-skills-preset" not in content, (
                f"{label}'s preset override must be restored on removal, "
                "not permanently orphaned by a legacy migration that "
                "failed to probe command-backed skills-mode agents (#2948)"
            )
            assert "Core specify body" in content

    def test_composed_none_unregister_respects_active_agent(
        self, project_dir, temp_dir
    ):
        """Unregistering a stale composed command must only touch the
        active agent's directory, not every configured non-skill agent.

        When a wrap preset's base layer is removed, ``resolve_content`` can
        no longer find a replace layer to compose onto and returns
        ``None``, triggering the "composed is None" branch of
        ``_reconcile_composed_commands``. Before the fix, that
        unregistration mapping covered every configured non-skill agent
        regardless of ``only_agent``, deleting historical artifacts from
        integrations that were never active for this preset (#2948).
        """
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_commands_dir = project_dir / ".gemini" / "commands"
        gemini_commands_dir.mkdir(parents=True)

        # A made-up command name with no bundled/core equivalent, so the
        # *only* base layer is the "compose-base" preset installed below —
        # once it's removed, no base remains for the wrap preset to compose
        # onto.
        cmd_name = "speckit.fake-compose-test"
        base_dir = self._create_command_preset(
            temp_dir, "compose-base", cmd_name, "Base", "base body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(base_dir, "0.1.5", priority=10)

        wrap_dir = temp_dir / "compose-wrap"
        wrap_dir.mkdir()
        (wrap_dir / "commands").mkdir()
        (wrap_dir / "commands" / f"{cmd_name}.md").write_text(
            "---\ndescription: Wrap\nstrategy: wrap\n---\n\n"
            "wrap start\n{CORE_TEMPLATE}\nwrap end\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "compose-wrap",
                "name": "compose-wrap",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": cmd_name,
                        "file": f"commands/{cmd_name}.md",
                        "strategy": "wrap",
                    }
                ]
            },
        }
        with open(wrap_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)
        manager.install_from_directory(wrap_dir, "0.1.5", priority=5)

        cmd_file = gemini_commands_dir / f"{cmd_name}.toml"
        assert cmd_file.exists(), (
            "sanity: the composed command should register for the active agent"
        )

        # Simulate a pre-existing artifact for an inactive agent, predating
        # this preset entirely — active-only unregistration must never
        # touch it.
        opencode_dir = project_dir / ".opencode" / "commands"
        opencode_dir.mkdir(parents=True, exist_ok=True)
        opencode_stale_file = opencode_dir / f"{cmd_name}.md"
        opencode_stale_file.write_text("stale opencode content\n")

        assert manager.remove("compose-base") is True

        assert not cmd_file.exists(), (
            "sanity: the active agent's now-uncomposable command file must "
            "be unregistered"
        )
        assert opencode_stale_file.read_text() == "stale opencode content\n", (
            "unregistering a stale composed command must not touch an "
            "inactive agent's directory (#2948)"
        )

    def test_remove_reconciles_command_for_every_historical_agent(
        self, project_dir, temp_dir
    ):
        """Removing a preset must reconcile every historical agent its
        ``registered_commands`` actually targeted, not only the currently
        active one.

        Preset B (lower precedence, survives) is installed while gemini is
        active, then preset A (higher precedence) overrides the same
        command while gemini is still active. Switching the active
        integration to opencode and rescaffolding re-registers both
        presets under opencode too, so preset A's ``registered_commands``
        now spans two agents: gemini (now inactive) and opencode (active).
        Removing A deletes its command file from *both* directories via
        ``_unregister_commands``, but active-only reconciliation used to
        recreate the surviving preset B's content only for the active
        agent (opencode), leaving gemini's directory with a stale/missing
        file (#2948).
        """
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        preset_b_dir = self._create_command_preset(
            temp_dir, "hist-preset-b", "speckit.specify",
            "Preset B", "preset B body",
        )
        preset_a_dir = self._create_command_preset(
            temp_dir, "hist-preset-a", "speckit.specify",
            "Preset A", "preset A body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_b_dir, "0.1.5", priority=10)
        manager.install_from_directory(preset_a_dir, "0.1.5", priority=1)

        gemini_cmd_files = list(gemini_dir.glob("*specify*"))
        assert gemini_cmd_files, "sanity: gemini should have the command file"
        assert "preset A body" in gemini_cmd_files[0].read_text(), (
            "sanity: preset A (higher precedence) should win initially"
        )

        # Switch the active integration to opencode and rescaffold, mirroring
        # `integration use opencode`. This merges opencode into both
        # presets' registered_commands alongside the pre-existing gemini
        # entry recorded while gemini was active.
        self._write_init_options(project_dir, ai="opencode", ai_skills=False)
        opencode_dir = project_dir / ".opencode" / "commands"
        opencode_dir.mkdir(parents=True, exist_ok=True)
        manager.register_enabled_presets_for_agent("opencode")

        metadata_a = manager.registry.get("hist-preset-a")
        assert set(metadata_a.get("registered_commands", {})) == {"gemini", "opencode"}, (
            "sanity: preset A's registered_commands must span both the "
            "historical (gemini) and currently active (opencode) agents"
        )

        assert manager.remove("hist-preset-a") is True

        gemini_cmd_files = list(gemini_dir.glob("*specify*"))
        opencode_cmd_files = list(opencode_dir.glob("*specify*"))
        assert gemini_cmd_files, "gemini's command file must still exist after removal"
        assert opencode_cmd_files, "opencode's command file must still exist after removal"
        assert "preset B body" in gemini_cmd_files[0].read_text(), (
            "removing the higher-precedence preset must restore the "
            "surviving preset's content in the historical (inactive) "
            "agent's directory too, not only the active agent's (#2948)"
        )
        assert "preset B body" in opencode_cmd_files[0].read_text(), (
            "the surviving preset's content must also be restored for the "
            "currently active agent"
        )

    def test_remove_reconciliation_tracks_new_historical_agent_for_survivor(
        self, project_dir, temp_dir
    ):
        """Historical-agent reconciliation writes must be recorded in the
        surviving preset's own ``registered_commands``, not just written
        to disk and forgotten.

        Preset A is installed while gemini is active, then survives to be
        active under opencode too (so A's ``registered_commands`` spans
        both gemini and opencode). Preset B is installed *only* while
        opencode is active — B's ``registered_commands`` is
        ``{"opencode": [...]}`` and never mentions gemini. Removing A
        triggers reconciliation that writes B's content into gemini's
        directory (an agent B never wrote to before) via ``extra_agents``,
        but if that write isn't merged back into B's own
        ``registered_commands``, B's registry entry still only says
        ``{"opencode": [...]}`` even though B's content now lives in
        gemini's directory too. A later ``remove('b')`` then only cleans
        up opencode, leaving the gemini file — reconciled there entirely
        by side effect of removing A — as a permanent orphan with no
        preset tracking it (#2948).
        """
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        preset_a_dir = self._create_command_preset(
            temp_dir, "orphan-preset-a", "speckit.specify",
            "Preset A", "preset A body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_a_dir, "0.1.5", priority=1)

        self._write_init_options(project_dir, ai="opencode", ai_skills=False)
        opencode_dir = project_dir / ".opencode" / "commands"
        opencode_dir.mkdir(parents=True, exist_ok=True)
        manager.register_enabled_presets_for_agent("opencode")

        metadata_a = manager.registry.get("orphan-preset-a")
        assert set(metadata_a.get("registered_commands", {})) == {"gemini", "opencode"}, (
            "sanity: preset A must be tracked under both agents"
        )

        # Preset B is installed only now, while opencode is the sole
        # active agent — it never writes to or tracks gemini.
        preset_b_dir = self._create_command_preset(
            temp_dir, "orphan-preset-b", "speckit.specify",
            "Preset B", "preset B body",
        )
        manager.install_from_directory(preset_b_dir, "0.1.5", priority=10)

        metadata_b = manager.registry.get("orphan-preset-b")
        assert set(metadata_b.get("registered_commands", {})) == {"opencode"}, (
            "sanity: preset B must only be tracked for opencode before "
            "preset A is removed"
        )

        assert manager.remove("orphan-preset-a") is True

        # B is now written into gemini's directory as a side effect of
        # reconciling A's removal, via the historical-agent extra_agents
        # pass.
        gemini_cmd_files = list(gemini_dir.glob("*specify*"))
        assert gemini_cmd_files, "sanity: gemini's directory must have B's restored content"
        assert "preset B body" in gemini_cmd_files[0].read_text(encoding="utf-8")

        metadata_b = manager.registry.get("orphan-preset-b")
        assert set(metadata_b.get("registered_commands", {})) == {"gemini", "opencode"}, (
            "preset B's own registered_commands must be updated to "
            "include gemini once reconciliation actually writes content "
            "there on its behalf — otherwise B's registry entry silently "
            "lies about which directories it owns (#2948)"
        )

        assert manager.remove("orphan-preset-b") is True

        # No preset is installed any more, so gemini's file must have been
        # reconciled down to the core bundled template (or removed
        # entirely) — but it must NOT still contain B's stale content,
        # which would mean B's write there was never tracked for cleanup.
        remaining_gemini_files = list(gemini_dir.glob("*specify*"))
        for f in remaining_gemini_files:
            assert "preset B body" not in f.read_text(encoding="utf-8"), (
                "removing preset B must clean up gemini's directory too, "
                "since B's registered_commands was updated to include it "
                "— otherwise B's stale content is orphaned there forever "
                "with no preset left to track or clean it up (#2948)"
            )

    def test_extension_reconciliation_tracks_new_historical_agent(
        self, project_dir
    ):
        from specify_cli.extensions import ExtensionRegistry

        self._write_init_options(project_dir, ai="opencode", ai_skills=False)
        (project_dir / ".opencode" / "commands").mkdir(parents=True)
        (project_dir / ".gemini" / "commands").mkdir(parents=True)

        ext_dir = project_dir / ".specify" / "extensions" / "tracked-ext"
        (ext_dir / "commands").mkdir(parents=True)
        (ext_dir / "commands" / "tracked.md").write_text(
            "---\ndescription: tracked\n---\n\nExtension body\n",
            encoding="utf-8",
        )
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: tracked-ext\n  name: Tracked\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  commands:\n"
            "    - name: speckit.tracked\n"
            "      file: commands/tracked.md\n"
            "      description: Tracked command\n",
            encoding="utf-8",
        )
        ExtensionRegistry(ext_dir.parent).add(
            "tracked-ext",
            {
                "version": "1.0.0",
                "source": "dev",
                "enabled": True,
                "registered_commands": {
                    "opencode": ["speckit.tracked-ext.tracked"]
                },
            },
        )

        manager = PresetManager(project_dir)
        manager._reconcile_composed_commands(
            ["speckit.tracked-ext.tracked"], extra_agents={"gemini"}
        )

        assert list((project_dir / ".gemini" / "commands").glob("*tracked*"))
        metadata = ExtensionRegistry(ext_dir.parent).get("tracked-ext")
        assert set(metadata["registered_commands"]) == {"gemini", "opencode"}

    def test_copilot_skills_registration_restored_after_process_restart(
        self, project_dir, temp_dir
    ):
        """Copilot skills-mode registrations must restore even when the
        transient ``_skills_mode`` integration attribute has been reset,
        simulating a fresh CLI process.

        ``_skills_mode`` is set during ``setup()`` and is never persisted;
        after switching the active agent and running ``preset remove`` in
        a brand-new process, a naive "is this integration currently in
        skills mode" check would be False even though Copilot's
        ``.github/skills`` directory holds a live override this preset
        wrote. Restoration must rely on the persisted per-agent provenance
        recorded at write time, not on runtime integration state (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )
        copilot_skills_dir = project_dir / ".github" / "skills"
        self._create_skill(copilot_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "copilot-fresh-process-preset", "speckit.specify",
            "Copilot fresh process test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = copilot_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:copilot-fresh-process-preset" in skill_file.read_text()

        metadata = manager.registry.get("copilot-fresh-process-preset")
        assert "copilot" in metadata.get("registered_skills", {})

        # Switch the active agent away from copilot, then simulate a fresh
        # CLI process (a brand-new PresetManager, so any transient
        # `_skills_mode` state set during a prior setup() call is gone)
        # removing the preset.
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        fresh_manager = PresetManager(project_dir)

        assert fresh_manager.remove("copilot-fresh-process-preset") is True

        assert "preset:copilot-fresh-process-preset" not in skill_file.read_text(), (
            "removal must restore copilot's .github/skills override even "
            "when copilot's transient skills-mode state isn't set in this "
            "process (#2948)"
        )
        assert "Core specify body" in skill_file.read_text()

    def test_unregister_agent_artifacts_scoped_to_target_agent_only(
        self, project_dir, temp_dir
    ):
        """``unregister_agent_artifacts`` must remove only the target
        agent's own tracked command/skill artifacts.

        Used by ``integration switch`` when deactivating the previous
        integration for a not-yet-installed target (#2948): without this,
        a preset's command override -- including a custom preset command --
        and skill mirror rendered for the old agent remain orphaned once a
        different integration becomes active. Another agent's own
        registrations (files and registry tracking) must survive
        untouched, and no priority-stack reconciliation should run as a
        side effect.
        """
        self._write_init_options(project_dir, ai="auggie", ai_skills=False)
        # Registration only writes to an agent's directory once it's
        # "detected" on disk (mirroring a real `integration install`
        # having already created it), so pre-create both agents'
        # directories before installing the preset.
        (project_dir / ".augment" / "commands").mkdir(parents=True)
        (project_dir / ".opencode" / "commands").mkdir(parents=True)
        preset_dir = self._create_command_preset(
            temp_dir, "switch-cleanup-preset", "speckit.specify",
            "Custom preset command", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        auggie_cmd = project_dir / ".augment" / "commands" / "speckit.specify.md"
        assert auggie_cmd.exists(), "sanity: preset command registered for auggie"

        # Simulate a later `integration use opencode` rescaffold that also
        # registered the preset for opencode, while auggie's own
        # registration (from before the switch) is still present in the
        # registry.
        self._write_init_options(project_dir, ai="opencode", ai_skills=False)
        manager.register_enabled_presets_for_agent("opencode")

        opencode_cmd = project_dir / ".opencode" / "commands" / "speckit.specify.md"
        assert opencode_cmd.exists(), "sanity: preset command registered for opencode"

        metadata = manager.registry.get("switch-cleanup-preset")
        registered_commands = metadata.get("registered_commands", {})
        assert "auggie" in registered_commands and "opencode" in registered_commands

        manager.unregister_agent_artifacts("auggie")

        assert not auggie_cmd.exists(), (
            "auggie's own preset command must be removed when switching "
            "away from auggie to a not-yet-installed integration (#2948)"
        )
        assert opencode_cmd.exists(), (
            "opencode's preset command must survive unregistering auggie's "
            "artifacts -- cleanup must stay scoped to the target agent"
        )

        metadata = manager.registry.get("switch-cleanup-preset")
        registered_commands = metadata.get("registered_commands", {})
        assert "auggie" not in registered_commands, (
            "auggie's tracking must be dropped after unregistering its artifacts"
        )
        assert "opencode" in registered_commands, (
            "opencode's tracking must be preserved untouched"
        )

    def test_unregister_agent_artifacts_deletes_marker_owned_skill(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")
        preset_dir = self._create_command_preset(
            temp_dir,
            "deactivated-skill-preset",
            "speckit.specify",
            "Deactivation cleanup",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_dir = skills_dir / "speckit-specify"
        assert "preset:deactivated-skill-preset" in (
            skill_dir / "SKILL.md"
        ).read_text()

        manager.unregister_agent_artifacts("copilot")

        assert not skill_dir.exists()

    def test_unregister_agent_artifacts_deletes_reconciled_override_skill(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        skills_dir = project_dir / ".github" / "skills"
        self._create_skill(skills_dir, "speckit-specify")
        preset_dir = self._create_command_preset(
            temp_dir,
            "deactivated-override-preset",
            "speckit.specify",
            "Deactivation override cleanup",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Project override\n---\n\nOverride body\n",
            encoding="utf-8",
        )
        (
            manager.presets_dir
            / "deactivated-override-preset"
            / "commands"
            / "speckit.specify.md"
        ).unlink()
        manager.register_enabled_presets_for_agent("copilot")

        skill_dir = skills_dir / "speckit-specify"
        assert "override:speckit.specify" in (
            skill_dir / "SKILL.md"
        ).read_text(encoding="utf-8")

        manager.unregister_agent_artifacts("copilot")

        assert not skill_dir.exists()
        metadata = manager.registry.get("deactivated-override-preset")
        assert "copilot" not in metadata.get("registered_skills", {})

    def test_unregister_native_agent_persists_skills_metadata_pop(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="agy", ai_skills=True)
        (project_dir / ".agents" / "skills").mkdir(parents=True)
        preset_dir = self._create_command_preset(
            temp_dir,
            "native-metadata-cleanup-preset",
            "speckit.shared-cleanup",
            "Shared cleanup",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        metadata = manager.registry.get("native-metadata-cleanup-preset")
        assert "agy" in metadata.get("registered_commands", {})
        manager.registry.update(
            "native-metadata-cleanup-preset",
            {"registered_skills": {"agy": ["speckit-shared-cleanup"]}},
        )

        manager.unregister_agent_artifacts("agy")

        metadata = manager.registry.get("native-metadata-cleanup-preset")
        assert "agy" not in metadata.get("registered_commands", {})
        assert "agy" not in metadata.get("registered_skills", {})

    def test_unregister_native_agent_preserves_shared_output_owner(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="agy", ai_skills=True)
        (project_dir / ".agents" / "skills").mkdir(parents=True)
        preset_dir = self._create_command_preset(
            temp_dir,
            "shared-native-output-preset",
            "speckit.shared-owner",
            "Shared owner",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")
        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-shared-owner"
            / "SKILL.md"
        )
        assert skill_file.exists()
        metadata = manager.registry.get("shared-native-output-preset")
        registered_commands = metadata.get("registered_commands", {})
        assert "agy" in registered_commands and "codex" in registered_commands

        manager.unregister_agent_artifacts("agy")

        assert skill_file.exists(), (
            "shared SKILL.md must survive while codex still owns the same "
            "physical output"
        )
        metadata = manager.registry.get("shared-native-output-preset")
        registered_commands = metadata.get("registered_commands", {})
        assert "agy" not in registered_commands
        assert "codex" in registered_commands

    def test_unregister_agent_artifacts_migrates_legacy_skill_list_scoped(
        self, project_dir, temp_dir
    ):
        """Unregistering an agent's artifacts from a legacy flat-list
        ``registered_skills`` entry must infer real per-agent ownership
        before removing anything, so only the target agent's own share is
        cleaned up and any other agent's still-live mirror survives,
        rather than either guessing every name belongs to the target agent
        or dropping all tracking wholesale (#2948).

        Uses Copilot (command-backed, rendering skills via ``ai_skills``)
        as the agent being switched away from, and Claude (a native
        SKILL.md agent) as the separate, still-live owner — mirroring the
        established legacy-provenance test pattern used elsewhere for
        this exact registry shape.
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        copilot_skills_dir = project_dir / ".github" / "skills"
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(copilot_skills_dir, "speckit-specify")
        self._create_skill(claude_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "switch-legacy-skill-preset", "speckit.specify",
            "Legacy skill switch test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        copilot_skill = copilot_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:switch-legacy-skill-preset" in copilot_skill.read_text(), (
            "sanity: install wrote the override under copilot"
        )

        # A separate activation under claude (before provenance tracking
        # existed) also left a live, marker-verified mirror there.
        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        claude_skill.write_text(
            "---\nname: speckit-specify\nmetadata:\n  source: preset:switch-legacy-skill-preset\n"
            "---\n\npreset body\n",
            encoding="utf-8",
        )

        # Simulate a pre-#2948 registry: a flat list with no per-agent
        # provenance for either writer.
        manager.registry.update(
            "switch-legacy-skill-preset",
            {"registered_skills": ["speckit-specify"]},
        )

        manager.unregister_agent_artifacts("copilot")

        assert not copilot_skill.parent.exists(), (
            "copilot's marker-owned preset skill must be deleted when "
            "switching away from copilot"
        )

        assert "preset:switch-legacy-skill-preset" in claude_skill.read_text(), (
            "claude's own, separately-written mirror must survive "
            "unregistering copilot's artifacts -- legacy-list inference "
            "must not misattribute or drop claude's real ownership (#2948)"
        )

        metadata = manager.registry.get("switch-legacy-skill-preset")
        registered_skills = metadata.get("registered_skills")
        assert isinstance(registered_skills, dict), (
            "legacy flat-list value must migrate to per-agent form"
        )
        assert "copilot" not in registered_skills
        assert "claude" in registered_skills and "speckit-specify" in registered_skills["claude"], (
            "claude's real ownership must be preserved in the migrated tracking"
        )

    def test_short_and_namespaced_commands_scaffold_consistently(
        self, project_dir, temp_dir
    ):
        """A preset's ``speckit.<cmd>`` and ``speckit.<ns>.<cmd>`` commands must
        scaffold identically in command mode, with no installed extension.

        Regression: the 3-part (``speckit.<ns>.<cmd>``) form was silently
        dropped by a name-shape guard whenever ``.specify/extensions/<ns>/``
        was absent, even though the preset ships the command body itself. The
        2-part form always scaffolded. Both are self-contained and must behave
        the same (#4076).
        """
        self._write_init_options(project_dir, ai="gemini", ai_skills=False)
        gemini_commands_dir = project_dir / ".gemini" / "commands"
        gemini_commands_dir.mkdir(parents=True)

        short_preset = self._create_command_preset(
            temp_dir, "short-cmd", "speckit.newcmd", "Short", "short body",
        )
        ns_preset = self._create_command_preset(
            temp_dir, "ns-cmd", "speckit.fakeext.newcmd", "Namespaced", "ns body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(short_preset, "0.1.5")
        manager.install_from_directory(ns_preset, "0.1.5")

        short_file = gemini_commands_dir / "speckit.newcmd.toml"
        ns_file = gemini_commands_dir / "speckit.fakeext.newcmd.toml"
        assert short_file.exists(), "2-part command should scaffold"
        assert ns_file.exists(), (
            "3-part namespaced command must scaffold too, even without the "
            "matching extension installed"
        )
        assert manager.registry.get("short-cmd")["registered_commands"] != {}
        assert manager.registry.get("ns-cmd")["registered_commands"] != {}


class TestWrapStrategy:
    """Tests for strategy: wrap preset command substitution."""

    def test_substitute_core_template_replaces_placeholder(self, project_dir):
        """Core template body replaces {CORE_TEMPLATE} in preset command body."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        # Set up a core command template
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\n---\n\n# Core Specify\n\nDo the thing.\n"
        )

        registrar = CommandRegistrar()
        body = "## Pre-Logic\n\nBefore stuff.\n\n{CORE_TEMPLATE}\n\n## Post-Logic\n\nAfter stuff.\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        assert "{CORE_TEMPLATE}" not in result
        assert "# Core Specify" in result
        assert "## Pre-Logic" in result
        assert "## Post-Logic" in result
        assert core_fm.get("description") == "core"

    def test_substitute_core_template_no_op_when_placeholder_absent(self, project_dir):
        """Returns body unchanged when {CORE_TEMPLATE} is not present."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCore body.\n")

        registrar = CommandRegistrar()
        body = "## No placeholder here.\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)
        assert result == body
        assert core_fm == {}

    def test_substitute_core_template_no_op_when_core_missing(self, project_dir):
        """Returns body unchanged when core template file does not exist."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        registrar = CommandRegistrar()
        body = "Pre.\n\n{CORE_TEMPLATE}\n\nPost.\n"
        result, core_fm = _substitute_core_template(body, "nonexistent", project_dir, registrar)
        assert result == body
        assert "{CORE_TEMPLATE}" in result
        assert core_fm == {}

    def test_substitute_core_template_unreadable_core_treated_as_missing(
        self, project_dir
    ):
        """An undecodable core template must not crash substitution.

        The wrap-strategy callers (``CommandRegistrar.register_pack`` and
        ``_register_commands``) skip an unreadable preset source with a
        warning, but the core template read inside
        ``_substitute_core_template`` had no boundary, so one corrupted
        project-owned override in ``.specify/templates/commands/`` crashed
        the whole registration with a raw ``UnicodeDecodeError``. An
        unreadable core is treated like a missing one.
        """
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_bytes(b"\xff\xfe not utf-8")

        registrar = CommandRegistrar()
        body = "Pre.\n\n{CORE_TEMPLATE}\n\nPost.\n"
        with pytest.warns(UserWarning, match="Ignoring core template"):
            result, core_fm = _substitute_core_template(
                body, "specify", project_dir, registrar
            )
        assert result == body
        assert core_fm == {}

    def test_register_commands_substitutes_core_template_for_wrap_strategy(self, project_dir):
        """register_commands substitutes {CORE_TEMPLATE} when strategy: wrap."""
        from specify_cli.agents import CommandRegistrar

        # Set up core command template
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\n---\n\n# Core Specify\n\nCore body here.\n"
        )

        # Create a preset command dir with a wrap-strategy command
        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: wrap test\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        commands = [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}]
        registrar = CommandRegistrar()

        # Use a generic agent that writes markdown to commands/
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Patch AGENT_CONFIGS to use a simple markdown agent pointing at our dir
        import copy
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-agent", commands, "test-preset",
                project_dir / "preset", project_dir
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "# Core Specify" in written
        assert "## Pre" in written
        assert "## Post" in written

    def test_end_to_end_wrap_via_self_test_preset(self, project_dir):
        """Installing self-test preset with a wrap command substitutes {CORE_TEMPLATE}."""
        from specify_cli.presets import PresetManager

        # Install a core template that wrap-test will wrap around
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "wrap-test.md").write_text(
            "---\ndescription: core wrap-test\n---\n\n# Core Wrap-Test Body\n"
        )

        # Set up skills dir (simulating --integration claude)
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_subdir = skills_dir / "speckit-wrap-test"
        skill_subdir.mkdir()
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-wrap-test\n---\n\nold content\n")

        # Write init-options so _register_skills finds the claude skills dir
        import json
        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        written = (skill_subdir / "SKILL.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "# Core Wrap-Test Body" in written
        assert "preset:self-test wrap-pre" in written
        assert "preset:self-test wrap-post" in written

    def test_substitute_core_template_returns_core_scripts(self, project_dir):
        """core_frontmatter in the returned tuple includes scripts/agent_scripts."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: run.sh\nagent_scripts:\n  sh: agent-run.sh\n---\n\n# Body\n"
        )

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        assert "# Body" in result
        assert core_fm.get("scripts") == {"sh": "run.sh"}
        assert core_fm.get("agent_scripts") == {"sh": "agent-run.sh"}

    def test_register_commands_inherits_scripts_from_core(self, project_dir):
        """register_commands merges scripts/agent_scripts from core and normalizes paths."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        # Preset has strategy: wrap but no scripts of its own
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: wrap no scripts\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "Run:" in written
        assert "scripts:" in written
        assert "run.sh" in written

    def test_register_commands_toml_resolves_inherited_scripts(self, project_dir):
        """TOML agents resolve {SCRIPT} from inherited core scripts when preset omits them."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: toml wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        toml_dir = project_dir / ".gemini" / "commands"
        toml_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-toml-agent"] = {
            "dir": str(toml_dir.relative_to(project_dir)),
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-toml-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (toml_dir / "speckit.specify.toml").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        # args token must use TOML format, not the intermediate $ARGUMENTS
        assert "$ARGUMENTS" not in written
        assert "{{args}}" in written

    def test_register_commands_markdown_resolves_inherited_scripts(self, project_dir):
        """Markdown agents resolve {SCRIPT} from inherited core scripts when preset omits them."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: markdown wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-md-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-md-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        assert "strategy" not in written

    def test_register_commands_markdown_converts_args_after_script_resolution(self, project_dir):
        """Markdown agents re-run arg placeholder conversion after resolve_skill_placeholders.

        resolve_skill_placeholders injects $ARGUMENTS (via {ARGS} expansion). A second
        _convert_argument_placeholder call must convert those to the agent's native format.
        """
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: forge wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".forge" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-forge-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "{{parameters}}",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-forge-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        # $ARGUMENTS injected by resolve_skill_placeholders must be re-converted
        assert "$ARGUMENTS" not in written
        assert "{{parameters}}" in written


def _make_wrap_preset_dir(
    base: Path,
    preset_id: str,
    cmd_name: str,
    pre: str,
    post: str,
    aliases: list[str] | None = None,
    file_rel: str | None = None,
) -> Path:
    """Create a minimal wrap-strategy preset directory for testing."""
    preset_dir = base / preset_id
    cmd_dir = preset_dir / "commands"
    cmd_dir.mkdir(parents=True)
    file_rel = file_rel or f"commands/{cmd_name}.md"
    template = {
        "type": "command",
        "name": cmd_name,
        "file": file_rel,
        "description": f"{preset_id} wrap",
    }
    if aliases is not None:
        template["aliases"] = aliases
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": preset_id,
            "name": preset_id,
            "version": "1.0.0",
            "description": f"Preset {preset_id}",
            "author": "test",
            "repository": "https://example.com",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [template]
        },
        "tags": [],
    }
    import yaml as _yaml
    (preset_dir / "preset.yml").write_text(_yaml.dump(manifest))
    command_path = preset_dir / file_rel
    command_path.parent.mkdir(parents=True, exist_ok=True)
    command_path.write_text(
        f"---\ndescription: {preset_id} wrap\nstrategy: wrap\n---\n\n"
        f"[{pre}]\n\n{{CORE_TEMPLATE}}\n\n[{post}]\n"
    )
    return preset_dir


class TestRemoveReconciliation:
    """Test that removing a preset re-registers the next layer's command."""

    def test_install_composes_extension_command_and_rewrites_subdir_paths_for_non_skill_agent(
        self, project_dir, temp_dir
    ):
        """When a preset overlays (append) an extension-provided base command,
        the initial composed non-skill-agent command file must have the
        extension's own subdir references rewritten to their installed
        location (#2101), matching the live repro: extension body
        'Read agents/control/commander.md', preset appends to
        speckit.fakeext.cmd, generated Gemini content retains the bare path."""
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/cmd.md",
                        "description": "Fake extension command",
                    }
                ]
            },
        }
        with open(extension_dir / "extension.yml", "w") as f:
            yaml.dump(extension_manifest, f)

        preset_dir = temp_dir / "ext-cmd-append"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Append fakeext cmd\n---\n\n## Extra\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-cmd-append",
                "name": "Ext Cmd Append",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "strategy": "append",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should exist in gemini dir"
        content = cmd_files[0].read_text()
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content
