"""Tests for preset skill artifacts in specify_cli.presets._manager_skills."""

import shutil
from pathlib import Path

import pytest
import yaml

from specify_cli.presets import PresetManager
from tests.specify_cli.presets._helpers import (
    PresetArtifactTestHelpers,
    install_self_test_preset,
)


class TestPresetSkills(PresetArtifactTestHelpers):
    """Tests for preset skill registration and unregistration.

    Tests that install the self-test preset use ``install_self_test_preset``
    which scopes a narrow filter to the expected wrap-strategy warning.
    Reconciliation failures remain audible so real regressions surface.
    """

    def test_skill_overridden_on_preset_install(self, project_dir, temp_dir):
        """When skills mode was used, a preset command override should update the skill."""
        # Simulate skills mode having been used: write init-options + create skill
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Also create the claude commands dir so commands get registered
        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        # Install self-test preset (has a command override for speckit.specify)
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content, "Skill should reference preset source"
        assert "disable-model-invocation: false" in content

        # Verify it was recorded in registry, keyed by the active agent
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", {}).get("claude", [])

    def _install_arg_hint_preset(self, project_dir, temp_dir, ai, skills_dir, description, arg_hint):
        """Install a preset whose command declares argument-hint; return the SKILL.md path."""
        self._write_init_options(project_dir, ai=ai)
        self._create_skill(skills_dir, "speckit-hinttest-cmd")
        (project_dir / ".specify" / "extensions" / "hinttest").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / f"hint-preset-{ai}"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.hinttest.cmd.md").write_text(
            "---\n"
            f'description: "{description}"\n'
            f'argument-hint: "{arg_hint}"\n'
            "---\n\n"
            "Preset command body.\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": f"hint-preset-{ai}",
                "name": "Hint Preset",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.hinttest.cmd",
                        "file": "commands/speckit.hinttest.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        return skills_dir / "speckit-hinttest-cmd" / "SKILL.md"

    def test_argument_hint_preserved_for_preset_command(self, project_dir, temp_dir):
        """argument-hint from a preset command must survive into the SKILL.md.

        Follow-up to #2903/#2916 for the preset skill generator. The
        description is long enough to fold across lines when serialized,
        guarding against an in-place string injection that would split the
        folded scalar into invalid YAML.
        """
        long_description = (
            "Build and maintain a lean, static context/ knowledge folder so "
            "coding agents load only what is relevant and save tokens"
        )
        arg_hint = "<init | update | list | check> [area] [slug] [-- notes]"
        skills_dir = project_dir / ".claude" / "skills"

        skill_file = self._install_arg_hint_preset(
            project_dir, temp_dir, "claude", skills_dir, long_description, arg_hint
        )
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        assert parsed["argument-hint"] == arg_hint
        assert parsed["description"] == long_description

    def test_argument_hint_not_added_for_non_claude_preset_command(self, project_dir, temp_dir):
        """Non-Claude skills agents must not receive argument-hint in preset skills."""
        arg_hint = "<init | update | list | check> [area]"
        skills_dir = project_dir / ".agents" / "skills"

        skill_file = self._install_arg_hint_preset(
            project_dir, temp_dir, "codex", skills_dir, "Build context", arg_hint
        )
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        assert "argument-hint" not in parsed

    def test_wrap_preset_inherits_argument_hint_from_core(self, project_dir, temp_dir):
        """A wrap-strategy preset that omits argument-hint must inherit it from the core template.

        Regression for issue #3991: the wrap-composition path in _register_skills
        previously inherited only scripts/agent_scripts from core_frontmatter,
        silently discarding argument-hint and leaking its value into description.
        """
        core_arg_hint = "Describe the feature you want to specify"
        preset_description = "Wrapped speckit.specify — extra project context added"
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Place a core template that declares argument-hint
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\n"
            "description: Core specify description.\n"
            f'argument-hint: "{core_arg_hint}"\n'
            "---\n\n"
            "Core specify body.\n",
            encoding="utf-8",
        )

        # Wrap preset: only declares description (no argument-hint)
        preset_dir = temp_dir / "wrap-hint-preset"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\n"
            f'description: "{preset_description}"\n'
            "strategy: wrap\n"
            "---\n\n"
            "{CORE_TEMPLATE}\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "wrap-hint-preset",
                "name": "Wrap Hint Preset",
                "version": "1.0.0",
                "description": "Test wrap hint inheritance",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                        "strategy": "wrap",
                    }
                ]
            },
        }
        import yaml as _yaml
        with open(preset_dir / "preset.yml", "w") as f:
            _yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "1.0.0")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        # argument-hint must be inherited from core, not dropped
        assert parsed.get("argument-hint") == core_arg_hint, (
            f"argument-hint was not inherited from core; parsed={parsed}"
        )
        # description must be exactly the preset's declared value, not concatenated
        assert parsed["description"] == preset_description, (
            f"description was corrupted; parsed={parsed}"
        )

    def test_wrap_preset_inherits_argument_hint_for_unmapped_command(self, project_dir, temp_dir):
        """Wrap inheritance must carry argument-hint for a command NOT in ARGUMENT_HINTS.

        Regression guard for issue #3991. The companion test above wraps
        ``speckit.specify``, whose stem is in Claude's ``ARGUMENT_HINTS`` map, so
        the string-injection fallback in ``post_process_skill_content`` re-adds
        ``argument-hint`` even when wrap composition drops it — masking the bug.
        This test wraps an extension-like command (``speckit.myfeature``) that is
        absent from that map, so the *only* thing that can carry the hint into the
        SKILL.md is the wrap-composition inheritance fix itself. Without the fix
        the key is dropped and this test fails.
        """
        core_arg_hint = "Custom hint that lives only on the core template"
        preset_description = "Wrapped speckit.myfeature — extra project context added"
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-myfeature")

        # Place a core template (extension-like command) that declares argument-hint
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "myfeature.md").write_text(
            "---\n"
            "description: Core myfeature description.\n"
            f'argument-hint: "{core_arg_hint}"\n'
            "---\n\n"
            "Core myfeature body.\n",
            encoding="utf-8",
        )

        # Wrap preset: only declares description (no argument-hint)
        preset_dir = temp_dir / "wrap-hint-preset-unmapped"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.myfeature.md").write_text(
            "---\n"
            f'description: "{preset_description}"\n'
            "strategy: wrap\n"
            "---\n\n"
            "{CORE_TEMPLATE}\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "wrap-hint-preset-unmapped",
                "name": "Wrap Hint Preset Unmapped",
                "version": "1.0.0",
                "description": "Test wrap hint inheritance for an unmapped command",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.myfeature",
                        "file": "commands/speckit.myfeature.md",
                        "strategy": "wrap",
                    }
                ]
            },
        }
        import yaml as _yaml
        with open(preset_dir / "preset.yml", "w") as f:
            _yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "1.0.0")

        skill_file = skills_dir / "speckit-myfeature" / "SKILL.md"
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        # argument-hint must be inherited from core, not dropped
        assert parsed.get("argument-hint") == core_arg_hint, (
            f"argument-hint was not inherited from core; parsed={parsed}"
        )
        # description must be exactly the preset's declared value, not concatenated
        assert parsed["description"] == preset_description, (
            f"description was corrupted; parsed={parsed}"
        )

    def test_register_skills_resolves_command_refs(self, project_dir, temp_dir):
        """Preset skill overrides must resolve __SPECKIT_COMMAND_*__ tokens (issue #2717).

        ``_register_skills()`` previously ran only ``resolve_skill_placeholders()``,
        so command cross-references leaked into SKILL.md as raw placeholders
        instead of rendering as ``/speckit-<cmd>`` like the command layer.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-install",
            "speckit.specify",
            "Override specify",
            "Run `__SPECKIT_COMMAND_SPECIFY__` then `__SPECKIT_COMMAND_PLAN__`.\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked into SKILL.md"
        # Claude's invoke_separator is "-", so tokens render as /speckit-<cmd>.
        assert "/speckit-specify" in content
        assert "/speckit-plan" in content

    def test_restore_skill_resolves_command_refs(self, project_dir, temp_dir):
        """Skill restore on preset removal must also resolve command tokens (issue #2717)."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-restore",
            "speckit.specify",
            "Override specify",
            "Override body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-restore")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on restore"
        assert "/speckit-plan" in content

    def test_restore_skill_preserves_dollar_command_refs(self, project_dir, temp_dir):
        """Dollar-style core refs remain native when a preset skill is removed."""
        self._write_init_options(project_dir, ai="zcode")
        skills_dir = project_dir / ".zcode" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        raw_core = (
            "---\ndescription: Core specify\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
        )
        (core_cmds / "specify.md").write_text(raw_core)

        preset_dir = self._create_command_preset(
            temp_dir,
            "dollar-cmdref-restore",
            "speckit.specify",
            "Override specify",
            "Override body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("dollar-cmdref-restore")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "$speckit-plan" in content
        assert "/speckit-plan" not in content

    def test_reconcile_override_skill_resolves_command_refs(self, project_dir, temp_dir):
        """Reconcile's project-override restore must resolve command tokens (issue #2717).

        When a preset that overrode a command is removed and a project override
        becomes the winning layer, ``_reconcile_skills`` rewrites the skill from
        the override body — which must also render ``__SPECKIT_COMMAND_*__`` tokens.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Project override wins once the preset is removed; its body carries a
        # command cross-reference token. No core template exists for "specify",
        # so the skill is restored exclusively via the reconcile override branch.
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-reconcile",
            "speckit.specify",
            "Preset specify",
            "Preset body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-reconcile")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "override:speckit.specify" in content, "skill should be restored from the project override"
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on reconcile"
        assert "/speckit-plan" in content

    def test_extension_restore_resolves_command_refs(self, project_dir, temp_dir):
        """Extension-backed skill restore must resolve command tokens (issue #2717).

        When a preset override is removed and the skill is restored from an
        extension command body, ``__SPECKIT_COMMAND_*__`` tokens in that body
        must render as slash-command invocations like the core-template path.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
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

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-ext-restore",
            "speckit.fakeext.cmd",
            "Override fakeext cmd",
            "Override body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-ext-restore")

        content = (skills_dir / "speckit-fakeext-cmd" / "SKILL.md").read_text()
        assert "source: extension:fakeext" in content, "skill should be restored from the extension"
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on extension restore"
        assert "/speckit-plan" in content

    def test_core_command_override_skill_uses_preset_command_description(self, project_dir, temp_dir):
        """Preset skill overrides for core commands should keep preset frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        preset_dir = temp_dir / "taskstoissues-description"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.repro.taskstoissues.md").write_text(
            "---\n"
            "description: COMMAND-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "# Repro command body\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "taskstoissues-description",
                "name": "Taskstoissues Description",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.taskstoissues",
                        "file": "commands/speckit.repro.taskstoissues.md",
                        "description": "MANIFEST-DESCRIPTION",
                        "replaces": "speckit.taskstoissues",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: COMMAND-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: preset:taskstoissues-description" in content

    def test_core_skill_restore_uses_core_command_description(self, project_dir, temp_dir):
        """Core skill restore should keep core command frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "taskstoissues.md").write_text(
            "---\n"
            "description: CORE-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "core taskstoissues body\n"
        )
        preset_dir = self._create_command_preset(
            temp_dir,
            "taskstoissues-restore",
            "speckit.taskstoissues",
            "PRESET-FRONTMATTER-DESCRIPTION",
            "preset taskstoissues body\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("taskstoissues-restore")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: CORE-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: templates/commands/taskstoissues.md" in content
        assert "core taskstoissues body" in content

    def test_override_skill_reconcile_uses_override_command_description(self, project_dir, temp_dir):
        """Override skill reconciliation should keep override frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.taskstoissues.md").write_text(
            "---\n"
            "description: OVERRIDE-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "override taskstoissues body\n"
        )
        preset_dir = self._create_command_preset(
            temp_dir,
            "taskstoissues-reconcile",
            "speckit.taskstoissues",
            "PRESET-FRONTMATTER-DESCRIPTION",
            "preset taskstoissues body\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: OVERRIDE-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: override:speckit.taskstoissues" in content
        assert "override taskstoissues body" in content

    def test_skill_not_updated_when_ai_skills_disabled(self, project_dir, temp_dir):
        """When skills mode was NOT used, preset install should not touch skills."""
        self._write_init_options(project_dir, ai="qwen", ai_skills=False)
        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()
        assert "untouched" in content, "Skill should not be modified when ai_skills=False"

    def test_get_skills_dir_returns_none_for_non_string_ai(self, project_dir):
        """Corrupted init-options ai values should not crash preset skill resolution."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text('{"ai":["codex"],"ai_skills":true,"script":"sh"}')

        manager = PresetManager(project_dir)

        assert manager._get_skills_dir() is None

    def test_get_skills_dir_returns_none_for_non_dict_init_options(self, project_dir):
        """Corrupted non-dict init-options payloads should fail closed."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        manager = PresetManager(project_dir)

        assert manager._get_skills_dir() is None

    def test_skill_not_updated_without_init_options(self, project_dir, temp_dir):
        """When no init-options.json exists, preset install should not touch skills."""
        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        file_content = skill_file.read_text()
        assert "untouched" in file_content

    def test_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """When a preset is removed, skills should be restored from core templates."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        # Set up core command template in the project so restoration works
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text("---\ndescription: Core specify command\n---\n\nCore specify body\n")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        # Verify preset content is in the skill
        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:self-test" in skill_file.read_text()

        # Remove the preset
        manager.remove("self-test")

        # Skill should be restored (core specify.md template exists)
        assert skill_file.exists(), "Skill should still exist after preset removal"
        content = skill_file.read_text()
        assert "preset:self-test" not in content, "Preset content should be gone"
        assert "templates/commands/specify.md" in content, "Should reference core template"
        assert "disable-model-invocation: false" in content

    def test_skill_restored_on_preset_remove_without_project_core_templates(self, project_dir):
        """Removing a preset must restore core skills even when the project
        has no ``.specify/templates/commands`` directory of its own — which
        is the normal case, since ``specify init`` never populates it. The
        real core commands live in the bundled core_pack/repo-root templates
        tree, and restoration must fall back there instead of deleting the
        skill outright (#3928).
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # The project_dir fixture's commands dir is empty, matching a real
        # project — specify init never populates project-local overrides
        # for unmodified core commands.
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        assert core_cmds.exists() and not any(core_cmds.iterdir())

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:self-test" in skill_file.read_text(encoding="utf-8")

        manager.remove("self-test")

        assert skill_file.exists(), "Core skill must be restored, not deleted"
        content = skill_file.read_text(encoding="utf-8")
        assert "preset:self-test" not in content
        assert "templates/commands/specify.md" in content
        assert "Create or update the feature specification" in content

    def test_extension_wins_over_bundled_core_on_preset_remove(
        self, project_dir, monkeypatch
    ):
        """When an installed extension owns the same skill name as a core
        command, removing a preset that overrode that skill must restore it
        from the extension, not silently from the bundled core template.
        Extensions are resolved ahead of bundled core elsewhere, and the
        bundled-core fallback added for #3928 must not replace that
        higher-priority layer.

        The extension-command namespace rules (``speckit.<ext>.<command>``)
        make a genuine end-to-end name collision with a core command
        cumbersome to construct through real manifests, so this stubs
        ``_build_extension_skill_restore_index`` to exercise the priority
        ordering in ``_unregister_skills_in_dir`` directly -- the code path
        under test doesn't care how the index entry was produced, only that
        it wins over the bundled-core fallback when present.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # No project-local core template override — the normal case, and
        # the one that makes the bundled-core fallback kick in at all.
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        assert core_cmds.exists() and not any(core_cmds.iterdir())

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        ext_specify_file = extension_dir / "commands" / "specify.md"
        ext_specify_file.write_text(
            "---\ndescription: Extension specify command\n---\n\n"
            "extension:fakeext specify body\n"
        )

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:self-test" in skill_file.read_text(encoding="utf-8")

        fake_restore_index = {
            "speckit-specify": {
                "command_name": "speckit.fakeext.specify",
                "source_file": ext_specify_file,
                "source": "extension:fakeext",
                "extension_id": "fakeext",
                "extension_dir": extension_dir,
            }
        }
        monkeypatch.setattr(
            manager,
            "_build_extension_skill_restore_index",
            lambda: fake_restore_index,
        )

        manager.remove("self-test")

        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "preset:self-test" not in content
        assert "source: extension:fakeext" in content
        assert "extension:fakeext specify body" in content
        assert "templates/commands/specify.md" not in content

    def test_skill_restored_on_remove_resolves_script_placeholders(self, project_dir):
        """Core restore should resolve {SCRIPT}/{ARGS} placeholders like other skill paths."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True, script="sh")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="old")
        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\n"
            "description: Core specify command\n"
            "scripts:\n"
            "  sh: .specify/scripts/bash/create-new-feature.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "Run:\n"
            "{SCRIPT}\n"
        )

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        manager.remove("self-test")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert ".specify/scripts/bash/create-new-feature.sh --json \"$ARGUMENTS\"" in content

    def test_skill_not_overridden_when_skill_path_is_file(self, project_dir):
        """Preset install should skip non-directory skill targets."""
        self._write_init_options(project_dir, ai="qwen")
        skills_dir = project_dir / ".qwen" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "speckit-specify").write_text("not-a-directory")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert (skills_dir / "speckit-specify").is_file()
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" not in metadata.get("registered_skills", {}).get("qwen", [])

    def test_no_skills_registered_when_skills_mode_disabled(self, project_dir, temp_dir):
        """Skills should not be created when skills mode is disabled."""
        self._write_init_options(project_dir, ai="claude", ai_skills=False)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        metadata = manager.registry.get("self-test")
        assert metadata.get("registered_skills", {}) == {}

    def test_extension_skill_override_matches_hyphenated_multisegment_name(self, project_dir, temp_dir):
        """Preset overrides for speckit.<ext>.<cmd> should target speckit-<ext>-<cmd> skills."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="untouched")
        (project_dir / ".specify" / "extensions" / "fakeext").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "ext-skill-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-override\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-override",
                "name": "Ext Skill Override",
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
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:ext-skill-override" in content
        assert "name: speckit-fakeext-cmd" in content
        assert "# Speckit Fakeext Cmd Skill" in content

        metadata = manager.registry.get("ext-skill-override")
        assert "speckit-fakeext-cmd" in metadata.get("registered_skills", {}).get("codex", [])

    def test_extension_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """Preset removal should restore an extension-backed skill instead of deleting it."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Extension fakeext cmd\n"
            "scripts:\n"
            "  sh: ../../scripts/bash/setup-plan.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "extension:fakeext\n"
            "Run {SCRIPT}\n"
            "Read agents/control/commander.md for context.\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "author": "acme-corp",
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

        preset_dir = temp_dir / "ext-skill-restore"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-restore\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-restore",
                "name": "Ext Skill Restore",
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
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert "preset:ext-skill-restore" in skill_file.read_text()

        manager.remove("ext-skill-restore")

        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:ext-skill-restore" not in content
        assert "source: extension:fakeext" in content
        assert "extension:fakeext" in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        # Extension-relative subdir references must resolve to their
        # installed location on restore too (#2101), not just on first
        # registration.
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "# Fakeext Cmd Skill" in content

        assert yaml.safe_load(content.split("---", 2)[1])["metadata"]["author"] == "acme-corp"

    def test_skill_composed_over_extension_base_rewrites_subdir_paths(
        self, project_dir, temp_dir
    ):
        """When a preset composes (append) over an extension-provided base
        command, the resulting skill (read from the .composed output) must
        still resolve the extension's own subdir references (#2101), not
        just when the extension wins outright (replace)."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

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

        preset_dir = temp_dir / "ext-base-append-skill"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Preset overlay\n---\n\n## Extra\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-base-append-skill",
                "name": "Ext Base Append Skill",
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

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        content = skill_file.read_text()
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content

    def test_preset_remove_skips_skill_dir_without_skill_file(self, project_dir, temp_dir):
        """Preset removal should not delete arbitrary directories missing SKILL.md."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        stray_skill_dir = skills_dir / "speckit-fakeext-cmd"
        stray_skill_dir.mkdir(parents=True, exist_ok=True)
        note_file = stray_skill_dir / "notes.txt"
        note_file.write_text("user content", encoding="utf-8")

        preset_dir = temp_dir / "ext-skill-missing-file"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-missing-file\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-missing-file",
                "name": "Ext Skill Missing File",
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
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        installed_preset_dir = manager.presets_dir / "ext-skill-missing-file"
        shutil.copytree(preset_dir, installed_preset_dir)
        manager.registry.add(
            "ext-skill-missing-file",
            {
                "version": "1.0.0",
                "source": str(preset_dir),
                "provides_templates": ["speckit.fakeext.cmd"],
                "registered_skills": ["speckit-fakeext-cmd"],
                "priority": 10,
            },
        )

        manager.remove("ext-skill-missing-file")

        assert stray_skill_dir.is_dir()
        assert note_file.read_text(encoding="utf-8") == "user content"

    def test_kimi_legacy_dotted_skill_override_still_applies(self, project_dir, temp_dir):
        """Preset overrides should still target legacy dotted-named skill dirs.

        This exercises legacy *naming* (``speckit.specify``) under the current
        ``.kimi-code/`` base — distinct from the legacy ``.kimi/`` *location*.
        """
        self._write_init_options(project_dir, ai="kimi")
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit.specify", body="untouched")

        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit.specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content
        assert "name: speckit.specify" in content

        metadata = manager.registry.get("self-test")
        assert "speckit.specify" in metadata.get("registered_skills", {}).get("kimi", [])

    def test_kimi_legacy_dotted_skill_reconciles_priority_winner(
        self, project_dir, temp_dir
    ):
        """Reconciliation must carry forward recorded legacy skill names."""
        self._write_init_options(project_dir, ai="kimi")
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit.specify", body="untouched")
        (project_dir / ".kimi-code" / "commands").mkdir(
            parents=True, exist_ok=True
        )

        higher_dir = self._create_command_preset(
            temp_dir,
            "higher-kimi-preset",
            "speckit.specify",
            "Higher preset",
            "Higher body",
        )
        lower_dir = self._create_command_preset(
            temp_dir,
            "lower-kimi-preset",
            "speckit.specify",
            "Lower preset",
            "Lower body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)

        skill_file = skills_dir / "speckit.specify" / "SKILL.md"
        for preset_id in ("higher-kimi-preset", "lower-kimi-preset"):
            manager.registry.update(
                preset_id,
                {"registered_skills": {"kimi": ["speckit.specify"]}},
            )
        skill_file.write_text(
            "---\nname: speckit.specify\n---\n\nLower body\n",
            encoding="utf-8",
        )
        manager._reconcile_skills(["speckit.specify"])

        assert "Higher body" in skill_file.read_text(encoding="utf-8"), (
            "reconciliation must replace lower-priority raw content in a "
            "recorded legacy dotted skill directory"
        )

    def test_kimi_legacy_dotted_skill_receives_project_override(
        self, project_dir, temp_dir
    ):
        """Project overrides must update the recorded legacy path in place."""
        self._write_init_options(project_dir, ai="kimi")
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit.specify", body="untouched")
        (project_dir / ".kimi-code" / "commands").mkdir(
            parents=True, exist_ok=True
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "kimi-override-preset",
            "speckit.specify",
            "Preset",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.registry.update(
            "kimi-override-preset",
            {"registered_skills": {"kimi": ["speckit.specify"]}},
        )
        modern_skill_dir = skills_dir / "speckit-specify"
        if modern_skill_dir.exists():
            shutil.rmtree(modern_skill_dir)

        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Project override\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        manager._reconcile_skills(["speckit.specify"])

        legacy_file = skills_dir / "speckit.specify" / "SKILL.md"
        assert "Override body" in legacy_file.read_text(encoding="utf-8")
        assert not modern_skill_dir.exists(), (
            "legacy-only ownership must not create an untracked modern path"
        )

    def test_kimi_skill_updated_even_when_ai_skills_disabled(self, project_dir, temp_dir):
        """Kimi presets should still propagate command overrides to existing skills."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content
        assert "name: speckit-specify" in content

        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", {}).get("kimi", [])

    def test_kimi_new_skill_created_even_when_ai_skills_disabled(self, project_dir, temp_dir):
        """Kimi native skills should still receive brand-new preset commands."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = project_dir / ".kimi-code" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "kimi-new-skill"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.research.md").write_text(
            "---\n"
            "description: Kimi research workflow\n"
            "---\n\n"
            "preset:kimi-new-skill\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "kimi-new-skill",
                "name": "Kimi New Skill",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.research",
                        "file": "commands/speckit.research.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-research" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:kimi-new-skill" in content
        assert "name: speckit-research" in content

        metadata = manager.registry.get("kimi-new-skill")
        assert "speckit-research" in metadata.get("registered_skills", {}).get("kimi", [])

    def test_kimi_preset_skill_override_resolves_script_placeholders(self, project_dir, temp_dir):
        """Kimi preset skill overrides should resolve placeholders and rewrite project paths."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False, script="sh")
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")
        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "kimi-placeholder-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\n"
            "description: Kimi placeholder override\n"
            "scripts:\n"
            "  sh: scripts/bash/create-new-feature.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "Execute `{SCRIPT}` for __AGENT__\n"
            "Review templates/checklist.md and memory/constitution.md\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "kimi-placeholder-override",
                "name": "Kimi Placeholder Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "__AGENT__" not in content
        assert ".specify/scripts/bash/create-new-feature.sh --json \"$ARGUMENTS\"" in content
        assert ".specify/templates/checklist.md" in content
        assert ".specify/memory/constitution.md" in content
        assert "for kimi" in content

    def test_agy_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """Agy preset removal should restore native skills instead of deleting them."""
        self._write_init_options(project_dir, ai="agy", ai_skills=True)
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="before override")

        core_command = project_dir / ".specify" / "templates" / "commands" / "specify.md"
        core_command.write_text(
            "---\n"
            "description: Restored core specify workflow\n"
            "---\n\n"
            "restored core body\n"
        )

        preset_dir = temp_dir / "agy-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\n"
            "description: Agy override\n"
            "---\n\n"
            "preset agy body\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "agy-override",
                "name": "Agy Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset agy body" in skill_file.read_text()

        assert manager.remove("agy-override") is True
        assert skill_file.exists()
        restored = skill_file.read_text()
        assert "restored core body" in restored
        assert "name: speckit-specify" in restored

    def test_preset_skill_registration_handles_non_dict_init_options(self, project_dir, temp_dir):
        """Non-dict init-options payloads should not crash preset install/remove flows."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "untouched" in skill_content

    def test_partial_skill_registration_is_persisted_before_later_failure(
        self, project_dir, temp_dir, monkeypatch
    ):
        """A successful earlier skill write remains tracked if a later read fails."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        commands_dir = project_dir / ".github" / "agents"
        commands_dir.mkdir(parents=True)

        preset_dir = self._create_multi_command_preset(
            temp_dir,
            "partial-skill-failure-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        original_read_text = Path.read_text

        def fail_plan_source(path, *args, **kwargs):
            if (
                path.name == "speckit.plan.md"
                and path.parent.name == "commands"
                and "partial-skill-failure-preset" in path.parts
            ):
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", fail_plan_source)
        manager.register_enabled_presets_for_agent("copilot")

        metadata = manager.registry.get("partial-skill-failure-preset")
        assert "speckit-specify" in metadata["registered_skills"].get(
            "copilot", []
        ), (
            "the first successful write must be persisted before the later "
            "template failure aborts the registration call"
        )
        monkeypatch.setattr(Path, "read_text", original_read_text)
        assert manager.remove("partial-skill-failure-preset") is True
        remaining_skill = (
            project_dir
            / ".github"
            / "skills"
            / "speckit-specify"
            / "SKILL.md"
        )
        assert (
            not remaining_skill.exists()
            or "preset:partial-skill-failure-preset"
            not in remaining_skill.read_text(encoding="utf-8")
        ), "persisted partial ownership must remain removable"

    def test_remove_cleans_native_skill_missing_from_partial_skill_map(
        self, project_dir, temp_dir
    ):
        """Command cleanup must cover native skills absent from a partial map."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        (project_dir / ".claude" / "skills").mkdir(parents=True)
        preset_dir = self._create_command_preset(
            temp_dir,
            "partial-agent-skill-map-preset",
            "speckit.partial-native",
            "Partial native skill",
            "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        metadata = manager.registry.get("partial-agent-skill-map-preset")
        assert metadata["registered_skills"].get("claude")

        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        (project_dir / ".agents" / "skills").mkdir(parents=True)

        from unittest.mock import patch

        with patch.object(
            PresetManager,
            "_register_skills",
            side_effect=RuntimeError("simulated skills phase failure"),
        ):
            manager.register_enabled_presets_for_agent("codex")

        codex_skill = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-partial-native"
            / "SKILL.md"
        )
        assert codex_skill.exists()
        metadata = manager.registry.get("partial-agent-skill-map-preset")
        assert "speckit.partial-native" in metadata[
            "registered_commands"
        ].get("codex", [])
        assert not metadata["registered_skills"].get("codex")

        assert manager.remove("partial-agent-skill-map-preset") is True
        assert not codex_skill.exists(), (
            "native skill written by the commands phase must not be orphaned "
            "when another agent makes registered_skills globally non-empty"
        )

    def test_skill_switch_then_remove_restores_every_skill_agent_dir(
        self, project_dir, temp_dir
    ):
        """Switching between two skill-mode agents before removing a preset
        must restore both agents' directories, not just the currently
        active one.

        ``registered_skills`` records exactly which agent directories the
        preset wrote to (``{agent_name: [skill_name, ...]}``); switching to
        codex and re-registering adds a "codex" entry alongside the
        original "claude" entry, so removal restores both. Before the
        provenance fix, ``_unregister_skills`` only restored the currently
        active agent's skills directory; a preset used first under Claude
        and later switched to Codex would have its Claude override left
        behind permanently on removal (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        # Native skill agents only materialize a *brand-new* preset skill
        # when their skills directory already exists (mirrors every other
        # skill test in this class); pre-create both agents' directories so
        # install and the later switch both find an existing skill to
        # overwrite via _register_commands/_register_skills.
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")
        codex_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "multi-skill-agent-preset", "speckit.specify",
            "Multi skill agent test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:multi-skill-agent-preset" in claude_skill.read_text()

        # Switch the active agent to codex (a different skill-mode agent)
        # and re-register enabled presets for it, mirroring what
        # `integration use codex` does.
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")

        codex_skill = codex_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:multi-skill-agent-preset" in codex_skill.read_text(), (
            "sanity: switching to codex should rescaffold the preset there"
        )
        assert "preset:multi-skill-agent-preset" in claude_skill.read_text(), (
            "sanity: the previous agent's registration is preserved on switch"
        )

        metadata = manager.registry.get("multi-skill-agent-preset")
        registered_skills = metadata.get("registered_skills", {})
        assert set(registered_skills) == {"claude", "codex"}, (
            "registered_skills must record both agent directories this "
            "preset actually wrote to (#2948)"
        )

        assert manager.remove("multi-skill-agent-preset") is True

        for skill_file, label in ((claude_skill, "claude"), (codex_skill, "codex")):
            assert skill_file.exists(), f"{label} skill file should still exist after removal"
            content = skill_file.read_text()
            assert "preset:multi-skill-agent-preset" not in content, (
                f"{label}'s preset override must be restored on removal, "
                "not orphaned permanently (#2948)"
            )
            assert "Core specify body" in content

    def test_infer_legacy_skill_provenance_does_not_falsely_attribute_command_mode_copilot(
        self, project_dir, temp_dir
    ):
        """Broadening provenance inference to command-backed agents must not
        falsely attribute ownership to an agent's directory that has no
        preset-owned marker.

        Copilot stays in plain command mode throughout (no skills ever
        rendered there), so ``.github/skills`` never receives this
        preset's ``SKILL.md``. Probing copilot's skills directory anyway
        (now that inference isn't restricted to static ``/SKILL.md``
        agents) must find nothing there and must not invent a false
        ``"copilot"`` entry (#2948).
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
        # Copilot has never been active; its command directory holds an
        # unrelated file so the directory exists, but no skills directory
        # or SKILL.md was ever written for it.
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        preset_dir = self._create_command_preset(
            temp_dir, "no-false-attribution-preset", "speckit.specify",
            "No false attribution test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        manager.registry.update(
            "no-false-attribution-preset",
            {"registered_skills": ["speckit-specify"]},
        )

        # Rescaffold again for the same agent (claude) with unchanged
        # names, triggering the legacy migration path.
        manager.register_enabled_presets_for_agent("claude")

        metadata = manager.registry.get("no-false-attribution-preset")
        registered_skills = metadata.get("registered_skills")
        assert isinstance(registered_skills, dict)
        assert set(registered_skills) == {"claude"}, (
            "copilot must not appear in the migrated registry when it has "
            "never actually rendered this preset's skill — probing its "
            "directory for a marker match must not create a false "
            "attribution (#2948)"
        )
        assert not (project_dir / ".github" / "skills").exists(), (
            "no .github/skills directory should have been created as a "
            "side effect of probing for provenance (#2948)"
        )

    def test_infer_legacy_skill_provenance_skips_invalid_utf8(
        self, project_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skill_dir = (
            project_dir / ".claude" / "skills" / "speckit-specify"
        )
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_bytes(b"\xff")

        manager = PresetManager(project_dir)

        assert manager._infer_legacy_skill_provenance(
            ["speckit-specify"], "some-pack", "claude"
        ) == {"claude": ["speckit-specify"]}

    def test_infer_legacy_skill_provenance_excludes_home_outputs(
        self, project_dir, temp_dir, monkeypatch
    ):
        home = temp_dir / "home"
        monkeypatch.setattr(Path, "home", lambda: home)
        skill_dir = home / ".hermes" / "skills" / "speckit-specify"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "metadata:\n"
            "  source: preset:some-pack\n"
            "---\n\n"
            "Other project\n",
            encoding="utf-8",
        )

        manager = PresetManager(project_dir)
        inferred = manager._infer_legacy_skill_provenance(
            ["speckit-specify"], "some-pack", "claude"
        )

        assert inferred == {"claude": ["speckit-specify"]}
        assert skill_dir.exists()

    def test_remove_infers_legacy_flat_list_provenance_without_prior_rescaffold(
        self, project_dir, temp_dir
    ):
        """``preset remove`` on a legacy flat-list registry must restore
        every previously active agent's directory, not just the currently
        active one, even when it is the *very first* post-upgrade
        operation (no intervening ``use``/``upgrade``/rescaffold).

        Pre-#2948 registries recorded a flat ``registered_skills`` list
        because presets were rendered for every detected skill-mode agent
        at once, not just the active one. Migrating that legacy format to
        the per-agent dict form previously only happened as a side effect
        of ``register_enabled_presets_for_agent`` (i.e. a rescaffold or
        ``integration use``/``switch``). If the user's first action after
        upgrading is instead directly running ``preset remove``, the
        legacy branch of ``_unregister_skills`` restored only the
        currently active agent's directory (via ``_get_skills_dir()``),
        permanently leaving this preset's override in every other,
        previously active agent's directory (#2948).
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
            temp_dir, "remove-legacy-no-rescaffold-preset", "speckit.specify",
            "Remove legacy no rescaffold test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        claude_skill = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:remove-legacy-no-rescaffold-preset" in claude_skill.read_text(), (
            "sanity: install should have written the override under "
            "claude's skill directory"
        )
        # Simulate the pre-#2948 "register for every detected agent"
        # install behaviour by also placing the marker under codex's
        # directory directly (mirroring the old, non-active-only
        # rendering that predates this PR).
        codex_skill = codex_skills_dir / "speckit-specify" / "SKILL.md"
        codex_skill.write_text(claude_skill.read_text(), encoding="utf-8")

        # Simulate a pre-#2948 registry: a flat list with no per-agent
        # provenance, even though both directories actually hold this
        # preset's marker on disk.
        manager.registry.update(
            "remove-legacy-no-rescaffold-preset",
            {"registered_skills": ["speckit-specify"]},
        )

        # No intervening use/upgrade/rescaffold: remove() is the very
        # first operation run after the legacy registry was written.
        assert manager.remove("remove-legacy-no-rescaffold-preset") is True

        for skill_file, label in ((claude_skill, "claude"), (codex_skill, "codex")):
            assert skill_file.exists(), f"{label} skill file should still exist after removal"
            content = skill_file.read_text()
            assert "preset:remove-legacy-no-rescaffold-preset" not in content, (
                f"{label}'s preset override must be restored on removal "
                "even with no prior rescaffold to migrate the legacy "
                "flat-list format first — remove() must infer real "
                "per-agent ownership from on-disk provenance itself "
                "(#2948)"
            )
            assert "Core specify body" in content

    def test_symlinked_skills_dir_rejected_on_removal(self, project_dir, temp_dir):
        """Removal must validate a recorded skill directory before touching it.

        If an agent's skills directory is replaced with a symlink escaping
        the project root between install and removal, restoration must
        refuse to write/rmtree through it rather than trusting the
        recorded agent name blindly. The unsafe directory is skipped
        best-effort; removal still succeeds and doesn't crash (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir, "symlink-guard-preset", "speckit.specify",
            "Symlink guard test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        metadata = manager.registry.get("symlink-guard-preset")
        assert "speckit-specify" in metadata.get("registered_skills", {}).get("claude", [])

        # Simulate the claude skills directory being replaced with a symlink
        # that escapes the project root, containing an external
        # "speckit-specify" directory that must not be touched.
        outside_target = temp_dir / "outside-claude-skills"
        outside_skill_dir = outside_target / "speckit-specify"
        outside_skill_dir.mkdir(parents=True)
        sentinel = outside_skill_dir / "SKILL.md"
        sentinel.write_text("do-not-touch")
        shutil.rmtree(claude_skills_dir)
        claude_skills_dir.symlink_to(outside_target, target_is_directory=True)

        assert manager.remove("symlink-guard-preset") is True

        assert sentinel.read_text() == "do-not-touch", (
            "removal must not follow a symlinked skills directory outside "
            "the project root (#2948)"
        )
        assert outside_skill_dir.is_dir(), (
            "the external directory must not be rmtree'd through a "
            "symlinked skills path"
        )
        assert claude_skills_dir.is_symlink(), (
            "the symlink itself should be left alone, not rmtree'd through"
        )

    def test_preset_removal_does_not_touch_other_presets_skill_dir(
        self, project_dir, temp_dir
    ):
        """Removing a preset must only touch directories it actually wrote to.

        Preset A is installed while Claude is active and preset B is
        installed while Codex is active; both override the same command
        name, so both materialize a ``speckit-specify`` skill, but in
        *different* agent directories. Before the provenance fix, removing
        B enumerated every existing skill-mode directory (including
        Claude's) and restored/overwrote anything named ``speckit-specify``
        found there, corrupting A's override even though B never touched
        Claude's directory (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_skills_dir, "speckit-specify")

        preset_a_dir = self._create_command_preset(
            temp_dir, "preset-a", "speckit.specify", "Preset A", "preset A body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_a_dir, "0.1.5")

        claude_skill_file = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:preset-a" in claude_skill_file.read_text()

        # Switch to codex and install a second preset overriding the same
        # command; codex's skills directory is entirely separate.
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        codex_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_skills_dir, "speckit-specify")

        preset_b_dir = self._create_command_preset(
            temp_dir, "preset-b", "speckit.specify", "Preset B", "preset B body",
        )
        manager.install_from_directory(preset_b_dir, "0.1.5")

        metadata_b = manager.registry.get("preset-b")
        assert "claude" not in metadata_b.get("registered_skills", {}), (
            "preset B never wrote to claude's skills directory and must "
            "not record it as touched"
        )

        assert manager.remove("preset-b") is True

        assert "preset:preset-a" in claude_skill_file.read_text(), (
            "removing preset B must not disturb preset A's Claude override (#2948)"
        )

    def test_remove_does_not_recreate_empty_skill_dir(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-orphan")
        preset_dir = self._create_command_preset(
            temp_dir,
            "orphan-skill-preset",
            "speckit.orphan",
            "Orphan",
            "Preset-only body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_dir = skills_dir / "speckit-orphan"
        assert skill_dir.exists()
        assert manager.remove("orphan-skill-preset") is True
        assert not skill_dir.exists()

    def test_remove_preserves_non_owned_skill_during_reconciliation(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        lower_dir = self._create_command_preset(
            temp_dir,
            "non-owned-lower-preset",
            "speckit.specify",
            "Lower",
            "Lower preset body",
        )
        higher_dir = self._create_command_preset(
            temp_dir,
            "non-owned-higher-preset",
            "speckit.specify",
            "Higher",
            "Higher preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=10)
        manager.install_from_directory(higher_dir, "0.1.5", priority=1)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        skill_file.write_text(
            "---\nname: speckit-specify\n---\n\nUser-owned body\n",
            encoding="utf-8",
        )

        assert manager.remove("non-owned-higher-preset") is True
        assert skill_file.read_text(encoding="utf-8") == (
            "---\nname: speckit-specify\n---\n\nUser-owned body\n"
        )

    def test_shared_skills_dir_restored_once_using_active_agent(
        self, project_dir, temp_dir
    ):
        """Removal must restore a physical skills directory shared by
        multiple agents exactly once, using the active agent's renderer.

        Codex and Antigravity (agy) both resolve their skills directory to
        ``.agents/skills``. Registering a preset under codex, switching to
        agy, then switching back to codex records provenance for *both*
        agent keys even though they share one physical directory. Before
        the fix, ``_unregister_skills`` restored once per recorded agent
        key rather than once per unique directory, so the directory was
        written twice on removal with whichever agent was iterated *last*
        silently winning — regardless of which agent is actually active
        (#2948).
        """
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        shared_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(shared_skills_dir, "speckit-specify")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        preset_dir = self._create_command_preset(
            temp_dir, "shared-dir-preset", "speckit.specify",
            "Shared dir test", "preset body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Switch to agy (shares .agents/skills with codex) and back to
        # codex, mirroring `integration use agy` then `integration use
        # codex`. Both agent keys end up recorded in registered_skills even
        # though they refer to the same physical directory.
        self._write_init_options(project_dir, ai="agy", ai_skills=True)
        manager.register_enabled_presets_for_agent("agy")
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        manager.register_enabled_presets_for_agent("codex")

        metadata = manager.registry.get("shared-dir-preset")
        registered_skills = metadata.get("registered_skills", {})
        assert set(registered_skills) == {"codex", "agy"}, (
            "both agent keys must be recorded even though they share one "
            "physical directory (#2948)"
        )

        from unittest.mock import patch

        # Exercise `_unregister_skills` directly (the method this fix
        # changed) rather than the full `remove()` flow, which separately
        # triggers post-removal reconciliation that may also touch the
        # active agent's directory — an unrelated call this test isn't
        # targeting.
        with patch.object(
            manager,
            "_unregister_skills_in_dir",
            wraps=manager._unregister_skills_in_dir,
        ) as spy:
            manager._unregister_skills(registered_skills, preset_dir)

        assert spy.call_count == 1, (
            "a physical directory shared by multiple recorded agents must "
            "be restored exactly once, not once per agent key (#2948)"
        )
        (_names, called_dir, called_agent), _kwargs = spy.call_args
        assert called_dir == shared_skills_dir
        assert called_agent == "codex", (
            "the currently active agent must be used as the renderer when "
            "it shares the restored directory, not whichever agent was "
            "recorded last (#2948)"
        )

        skill_file = shared_skills_dir / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()
        assert "preset:shared-dir-preset" not in content
        assert "Core specify body" in content

    def test_remove_higher_priority_skills_only_preset_restores_lower_preset(
        self, project_dir, temp_dir
    ):
        """Removing a skills-mode preset must reconcile against the surviving
        stack, not fall back to core/extension content.

        Copilot in skills mode never populates ``registered_commands`` for
        its overrides (``_register_commands``'s ``ai_skills`` guard skips
        command-file registration entirely), so with two presets overriding
        the same command, the removed preset's command name was never added
        to ``removed_cmd_names`` and reconciliation was skipped outright.
        ``_unregister_skills`` then restored straight to core/extension
        content instead of resolving the lower-priority preset that should
        now win (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)

        preset_a_dir = self._create_command_preset(
            temp_dir, "skills-preset-a", "speckit.specify",
            "Preset A", "preset A body",
        )
        preset_b_dir = self._create_command_preset(
            temp_dir, "skills-preset-b", "speckit.specify",
            "Preset B", "preset B body",
        )

        manager = PresetManager(project_dir)
        # Lower priority number = higher precedence.
        manager.install_from_directory(preset_a_dir, "0.1.5", priority=5)
        manager.install_from_directory(preset_b_dir, "0.1.5", priority=10)

        skills_dir = project_dir / ".github" / "skills"
        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:skills-preset-a" in skill_file.read_text(), (
            "sanity: the higher-precedence preset should win initially"
        )

        assert manager.remove("skills-preset-a") is True

        content = skill_file.read_text()
        assert "preset:skills-preset-b" in content, (
            "removing the higher-precedence skills-mode preset must "
            "restore the surviving lower-precedence preset's override, "
            "not fall back to core/extension content (#2948)"
        )
        assert "preset:skills-preset-a" not in content

    def test_remove_reconciles_skill_for_every_historical_agent(
        self, project_dir, temp_dir
    ):
        """Removing a preset must reconcile every historical skills
        directory its ``registered_skills`` actually targeted, not only
        the currently active one.

        Preset B (survives) is installed while claude is active, then
        preset A (higher precedence) overrides the same command while
        claude is still active. Switching to codex and rescaffolding
        records codex too, so preset A's ``registered_skills`` spans both
        claude (now inactive) and codex (active) directories. Removing A
        restores both directories to core/extension via
        ``_unregister_skills``, but ``_reconcile_skills`` used to only
        resolve/apply the surviving winner for the currently active
        skills directory, leaving claude's directory reverted to
        core/extension content instead of preset B's override (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"

        # A core template fallback is required so unregistering the
        # top-priority preset's SKILL.md restores core content rather than
        # deleting the skill directory outright when no preset remains to
        # apply on top of it (mirrors the pre-existing skills-reconciliation
        # fixtures elsewhere in this file).
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        preset_b_dir = self._create_command_preset(
            temp_dir, "hist-skill-preset-b", "speckit.specify",
            "Preset B", "preset B body",
        )
        preset_a_dir = self._create_command_preset(
            temp_dir, "hist-skill-preset-a", "speckit.specify",
            "Preset A", "preset A body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_b_dir, "0.1.5", priority=10)
        manager.install_from_directory(preset_a_dir, "0.1.5", priority=1)

        claude_skill_file = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:hist-skill-preset-a" in claude_skill_file.read_text(), (
            "sanity: preset A (higher precedence) should win initially"
        )

        # Switch the active integration to codex (a distinct skills
        # directory) and rescaffold, mirroring `integration use codex`.
        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        codex_skills_dir = project_dir / ".agents" / "skills"
        manager.register_enabled_presets_for_agent("codex")

        metadata_a = manager.registry.get("hist-skill-preset-a")
        assert set(metadata_a.get("registered_skills", {})) == {"claude", "codex"}, (
            "sanity: preset A's registered_skills must span both the "
            "historical (claude) and currently active (codex) agents"
        )

        assert manager.remove("hist-skill-preset-a") is True

        codex_skill_file = codex_skills_dir / "speckit-specify" / "SKILL.md"
        assert claude_skill_file.exists(), "claude's skill file must still exist after removal"
        assert codex_skill_file.exists(), "codex's skill file must still exist after removal"
        assert "preset:hist-skill-preset-b" in claude_skill_file.read_text(), (
            "removing the higher-precedence preset must restore the "
            "surviving preset's override in the historical (inactive) "
            "agent's directory too, not only the active agent's (#2948)"
        )
        assert "preset:hist-skill-preset-b" in codex_skill_file.read_text(), (
            "the surviving preset's override must also be restored for "
            "the currently active agent"
        )

    def test_skill_reconciliation_preserves_per_directory_names(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_dir = project_dir / ".claude" / "skills"
        self._create_skill(claude_dir, "speckit-alpha")
        alpha_dir = self._create_command_preset(
            temp_dir, "partial-alpha", "speckit.alpha",
            "Alpha", "alpha body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(alpha_dir, "0.1.5")

        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        codex_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_dir, "speckit-beta")
        beta_dir = self._create_command_preset(
            temp_dir, "partial-beta", "speckit.beta",
            "Beta", "beta body",
        )
        manager.install_from_directory(beta_dir, "0.1.5")

        affected = manager._unregister_skills(
            {
                "claude": ["speckit-alpha"],
                "codex": ["speckit-beta"],
            },
            manager.presets_dir / "partial-alpha",
        )
        manager._reconcile_skills(
            ["speckit.alpha", "speckit.beta"],
            extra_skills_dirs=affected,
        )

        assert (claude_dir / "speckit-alpha" / "SKILL.md").exists()
        assert (codex_dir / "speckit-beta" / "SKILL.md").exists()
        assert not (claude_dir / "speckit-beta").exists()
        assert not (codex_dir / "speckit-alpha").exists()

    def test_skill_reconciliation_rejects_unsafe_managed_names(
        self, project_dir, temp_dir
    ):
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )
        absolute_escape = temp_dir / "absolute-escape"
        traversal_escape = project_dir / ".claude" / "traversal-escape"

        manager = PresetManager(project_dir)
        manager._reconcile_skills(
            ["speckit.specify"],
            extra_skills_dirs={
                skills_dir: (
                    "claude",
                    [str(absolute_escape), "../traversal-escape"],
                )
            },
        )

        assert not absolute_escape.exists()
        assert not traversal_escape.exists()

    def test_remove_reconciliation_tracks_new_historical_skill_agent_for_survivor(
        self, project_dir, temp_dir
    ):
        """Historical-agent skill reconciliation writes must be recorded in
        the surviving preset's own ``registered_skills``, mirroring
        ``test_remove_reconciliation_tracks_new_historical_agent_for_survivor``
        for the command side.

        Preset A is installed while claude is active, then survives to be
        active under codex too (so A's ``registered_skills`` spans both
        claude and codex). Preset B is installed *only* while codex is
        active — B's ``registered_skills`` is ``{"codex": [...]}`` and
        never mentions claude. Removing A triggers reconciliation that
        renders B's SKILL.md into claude's directory (an agent B never
        wrote to before) via ``extra_skills_dirs``, but if that write
        isn't merged back into B's own ``registered_skills``, a later
        ``remove('b')`` only cleans up codex, leaving claude's SKILL.md —
        rendered there entirely by side effect of removing A — untracked
        by any preset (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        # Pre-create the skill so _register_commands/_register_skills find
        # an existing skill to overwrite (mirrors every other skill test
        # in this class — native skill agents only overwrite already
        # existing skill directories, they don't materialize brand-new
        # ones outside of active-agent creation).
        self._create_skill(claude_skills_dir, "speckit-specify")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify command\n---\n\nCore specify body\n",
            encoding="utf-8",
        )

        preset_a_dir = self._create_command_preset(
            temp_dir, "orphan-skill-preset-a", "speckit.specify",
            "Preset A", "preset A body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_a_dir, "0.1.5", priority=1)

        self._write_init_options(project_dir, ai="codex", ai_skills=True)
        codex_skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(codex_skills_dir, "speckit-specify")
        manager.register_enabled_presets_for_agent("codex")

        metadata_a = manager.registry.get("orphan-skill-preset-a")
        assert set(metadata_a.get("registered_skills", {})) == {"claude", "codex"}, (
            "sanity: preset A must be tracked under both agents"
        )

        # Preset B is installed only now, while codex is the sole active
        # agent — it never writes to or tracks claude.
        preset_b_dir = self._create_command_preset(
            temp_dir, "orphan-skill-preset-b", "speckit.specify",
            "Preset B", "preset B body",
        )
        manager.install_from_directory(preset_b_dir, "0.1.5", priority=10)

        metadata_b = manager.registry.get("orphan-skill-preset-b")
        assert set(metadata_b.get("registered_skills", {})) == {"codex"}, (
            "sanity: preset B must only be tracked for codex before "
            "preset A is removed"
        )

        assert manager.remove("orphan-skill-preset-a") is True

        claude_skill_file = claude_skills_dir / "speckit-specify" / "SKILL.md"
        assert claude_skill_file.exists(), (
            "sanity: claude's skill file must have been restored by "
            "reconciliation"
        )
        assert "preset:orphan-skill-preset-b" in claude_skill_file.read_text(), (
            "sanity: claude's SKILL.md must reflect preset B's content "
            "after preset A is removed"
        )

        metadata_b = manager.registry.get("orphan-skill-preset-b")
        assert set(metadata_b.get("registered_skills", {})) == {"claude", "codex"}, (
            "preset B's own registered_skills must be updated to include "
            "claude once reconciliation actually renders content there "
            "on its behalf — otherwise B's registry entry silently lies "
            "about which directories it owns (#2948)"
        )

        assert manager.remove("orphan-skill-preset-b") is True

        # No preset is installed any more, so claude's SKILL.md must have
        # been reconciled down to the core bundled template (or removed
        # entirely) — but it must NOT still contain B's stale content,
        # which would mean B's write there was never tracked for cleanup.
        if claude_skill_file.exists():
            assert "preset:orphan-skill-preset-b" not in claude_skill_file.read_text(), (
                "removing preset B must clean up claude's directory too, "
                "since B's registered_skills was updated to include it — "
                "otherwise B's stale content is orphaned there forever "
                "with no preset left to track or clean it up (#2948)"
            )

    def test_symlinked_skill_subdir_rejected_on_restore(self, project_dir, temp_dir):
        """Restore must validate each per-skill subdirectory, not just its parent.

        ``_safe_skills_dir_for_agent`` only validates the parent skills
        directory (e.g. ``.claude/skills``); a symlink planted one level
        deeper at the individual skill's own subdirectory (e.g.
        ``.claude/skills/speckit-specify``) has a perfectly safe parent and
        would otherwise slip past that check, since ``is_dir()`` follows
        symlinks. Restoration must refuse to write/rmtree through it (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        claude_skills_dir.mkdir(parents=True)

        outside_target = temp_dir / "outside-skill-subdir"
        outside_target.mkdir()
        sentinel = outside_target / "SKILL.md"
        sentinel.write_text("do-not-touch")
        (claude_skills_dir / "speckit-specify").symlink_to(
            outside_target, target_is_directory=True
        )

        manager = PresetManager(project_dir)
        manager._unregister_skills_in_dir(
            ["speckit-specify"], claude_skills_dir, "claude"
        )

        assert sentinel.read_text() == "do-not-touch", (
            "restoration must not follow a symlinked skill subdirectory "
            "to write/delete outside the project (#2948)"
        )
        assert (claude_skills_dir / "speckit-specify").is_symlink(), (
            "the symlink itself should be left alone, not rmtree'd through"
        )

    def test_symlinked_skill_subdir_rejected_on_write(self, project_dir, temp_dir):
        """Registration must validate each per-skill subdirectory before writing.

        A symlink planted at an individual skill's own subdirectory (safe
        parent, unsafe leaf) would otherwise pass the existing
        ``skill_subdir.exists() and not skill_subdir.is_dir()`` guard
        (``is_dir()`` follows symlinks) and have ``SKILL.md`` written
        through it to an arbitrary location (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)
        skills_dir = project_dir / ".github" / "skills"
        skills_dir.mkdir(parents=True)

        outside_target = temp_dir / "outside-skill-write-target"
        outside_target.mkdir()
        (skills_dir / "speckit-specify").symlink_to(
            outside_target, target_is_directory=True
        )

        preset_dir = self._create_command_preset(
            temp_dir, "symlink-write-preset", "speckit.specify",
            "Symlink write test", "preset body",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        assert not (outside_target / "SKILL.md").exists(), (
            "registration must not follow a symlinked skill subdirectory "
            "to write outside the project (#2948)"
        )
        assert (skills_dir / "speckit-specify").is_symlink(), (
            "the symlink itself should be left alone"
        )

    def test_symlinked_skill_file_rejected_on_write(self, project_dir, temp_dir):
        """Registration must not follow a symlinked SKILL.md destination."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        (project_dir / ".github" / "agents").mkdir(parents=True)
        skill_dir = (
            project_dir / ".github" / "skills" / "speckit-specify"
        )
        skill_dir.mkdir(parents=True)
        outside_file = temp_dir / "outside-registration.md"
        outside_file.write_text("do-not-touch", encoding="utf-8")
        (skill_dir / "SKILL.md").symlink_to(outside_file)

        preset_dir = self._create_command_preset(
            temp_dir,
            "symlink-file-write-preset",
            "speckit.specify",
            "Symlink file write",
            "preset body",
        )
        manager = PresetManager(project_dir)
        with pytest.raises(ValueError):
            manager.install_from_directory(preset_dir, "0.1.5")

        assert outside_file.read_text(encoding="utf-8") == "do-not-touch"
        assert (skill_dir / "SKILL.md").is_symlink()

    def test_symlinked_skill_file_rejected_on_restore(
        self, project_dir, temp_dir
    ):
        """Restoration must not follow a symlinked SKILL.md destination."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        core_commands = project_dir / ".specify" / "templates" / "commands"
        (core_commands / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )
        skill_dir = (
            project_dir / ".claude" / "skills" / "speckit-specify"
        )
        skill_dir.mkdir(parents=True)
        outside_file = temp_dir / "outside-restoration.md"
        outside_file.write_text("do-not-touch", encoding="utf-8")
        (skill_dir / "SKILL.md").symlink_to(outside_file)

        manager = PresetManager(project_dir)
        with pytest.raises(ValueError):
            manager._unregister_skills_in_dir(
                ["speckit-specify"], skill_dir.parent, "claude"
            )

        assert outside_file.read_text(encoding="utf-8") == "do-not-touch"
        assert (skill_dir / "SKILL.md").is_symlink()

    def test_symlinked_skill_file_rejected_on_override_reconcile(
        self, project_dir, temp_dir
    ):
        """Project-override reconciliation must not follow SKILL.md symlinks."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        skill_dir = (
            project_dir / ".github" / "skills" / "speckit-specify"
        )
        skill_dir.mkdir(parents=True)
        outside_file = temp_dir / "outside-reconciliation.md"
        outside_file.write_text("do-not-touch", encoding="utf-8")
        (skill_dir / "SKILL.md").symlink_to(outside_file)

        preset_dir = self._create_command_preset(
            temp_dir,
            "symlink-override-preset",
            "speckit.specify",
            "Preset",
            "Preset body",
        )
        manager = PresetManager(project_dir)
        manager.registry.add(
            "symlink-override-preset",
            {
                "version": "1.0.0",
                "source": "local",
                "enabled": True,
                "priority": 10,
                "registered_commands": {},
                "registered_skills": {
                    "copilot": ["speckit-specify"]
                },
            },
        )
        installed_dir = (
            manager.presets_dir / "symlink-override-preset"
        )
        shutil.copytree(preset_dir, installed_dir)
        overrides_dir = (
            project_dir / ".specify" / "templates" / "overrides"
        )
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override\n---\n\nOverride body\n",
            encoding="utf-8",
        )

        manager._reconcile_skills(["speckit.specify"])

        assert outside_file.read_text(encoding="utf-8") == "do-not-touch"
        assert (skill_dir / "SKILL.md").is_symlink()

    def test_is_safe_registry_skill_name_rejects_unsafe_values(self, project_dir):
        """Unit-test the centralized registry skill-name boundary guard.

        ``registered_skills`` entries are persisted registry data, not
        manifest-derived, so every preset cleanup/provenance loop that
        joins one onto a directory must first reject: non-strings, empty
        strings, absolute paths, multi-component paths (containing ``/``),
        and the literal traversal components ``"."``/``".."`` — the last
        of which is *not* caught by a naive ``is_absolute() or
        len(parts) != 1`` check alone, since ``Path("..").parts`` is a
        single-element tuple (#2948).
        """
        manager = PresetManager(project_dir)
        is_safe = manager._is_safe_registry_skill_name

        assert is_safe("speckit-specify") is True
        assert is_safe("") is False
        assert is_safe(None) is False
        assert is_safe(123) is False
        assert is_safe(["speckit-specify"]) is False
        assert is_safe(".") is False
        assert is_safe("..") is False
        assert is_safe("/etc/passwd") is False
        assert is_safe(str(project_dir / "important-data")) is False
        assert is_safe("foo/bar") is False
        assert is_safe("foo/..") is False
        assert is_safe("../foo") is False

    def test_unregister_skills_rejects_unknown_agent_provenance(
        self, project_dir
    ):
        """Unknown registry agent keys must not fall back to shared skills."""
        shared_skills_dir = project_dir / ".agents" / "skills"
        skill_dir = self._create_skill(
            shared_skills_dir, "speckit-specify", "user-owned content"
        )
        core_commands = project_dir / ".specify" / "templates" / "commands"
        (core_commands / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )

        manager = PresetManager(project_dir)
        manager._unregister_skills(
            {"unknown": ["speckit-specify"]}, project_dir
        )

        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == (
            "---\nname: speckit-specify\n---\n\nuser-owned content\n"
        )

    def test_unregister_legacy_fallback_skips_non_owned_skill(
        self, project_dir
    ):
        """Legacy fallback provenance must not overwrite a user-owned skill."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = self._create_skill(
            skills_dir, "speckit-specify", "user-owned content"
        )
        core_commands = project_dir / ".specify" / "templates" / "commands"
        (core_commands / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )

        manager = PresetManager(project_dir)
        manager._unregister_skills(
            ["speckit-specify"], "removed-preset"
        )

        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == (
            "---\nname: speckit-specify\n---\n\nuser-owned content\n"
        )

    def test_unregister_skills_in_dir_unreadable_core_template_skips(
        self, project_dir
    ):
        """An undecodable core template must not crash `preset remove`.

        Every other failure in the restore loop — an unsafe registry name,
        a missing skill subdirectory, a foreign owner — skips the skill
        with ``continue``. The core-template read was outside that
        boundary, so one non-UTF-8 project-owned override in
        ``.specify/templates/commands/`` raised a raw ``UnicodeDecodeError``
        straight out of ``PresetManager.remove()``, which has no handler
        for it. Sibling reads of the very same directory are already
        guarded (``_substitute_core_template``, the provenance reads in
        ``_infer_legacy_skill_provenance``).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = self._create_skill(
            skills_dir, "speckit-specify", "installed content"
        )
        core_commands = project_dir / ".specify" / "templates" / "commands"
        core_commands.mkdir(parents=True, exist_ok=True)
        (core_commands / "specify.md").write_bytes(
            b"---\ndescription: \xff\xfe not utf-8\n---\n\nCore body\n"
        )

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="speckit-specify"):
            mutated = manager._unregister_skills_in_dir(
                ["speckit-specify"], skills_dir, "claude"
            )

        assert mutated == [], (
            "a skill whose restore source could not be read was not "
            "restored, so it must not be reported as mutated"
        )
        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == (
            "---\nname: speckit-specify\n---\n\ninstalled content\n"
        ), (
            "an unreadable core template must leave the skill untouched — "
            "falling through to the rmtree branch would delete it exactly "
            "when its replacement cannot be generated"
        )

    def test_unregister_skills_in_dir_unreadable_core_template_oserror_skips(
        self, project_dir, monkeypatch
    ):
        """The same boundary must cover ``OSError`` (e.g. permission denied).

        Mocked rather than chmod-based so the case also holds under
        privileged CI, where permission bits are not enforced.
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = self._create_skill(
            skills_dir, "speckit-specify", "installed content"
        )
        core_commands = project_dir / ".specify" / "templates" / "commands"
        core_commands.mkdir(parents=True, exist_ok=True)
        core_template = core_commands / "specify.md"
        core_template.write_text(
            "---\ndescription: Core specify\n---\n\nCore body\n",
            encoding="utf-8",
        )

        original_read_text = Path.read_text

        def failing_read_text(self_path, *args, **kwargs):
            if self_path == core_template:
                raise PermissionError(13, "Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", failing_read_text)

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="speckit-specify"):
            mutated = manager._unregister_skills_in_dir(
                ["speckit-specify"], skills_dir, "claude"
            )

        monkeypatch.undo()

        assert mutated == []
        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == (
            "---\nname: speckit-specify\n---\n\ninstalled content\n"
        )

    def test_unregister_skills_in_dir_unreadable_extension_source_skips(
        self, project_dir
    ):
        """The extension-restore arm needs the same boundary as the core arm.

        The two restore reads are independent branches — a skill backed by an
        installed extension never reaches the core-template read — so this
        half of the guard can regress on its own. An undecodable extension
        command file must warn, leave the skill byte-for-byte intact, and stay
        out of ``mutated_names``.
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = self._create_skill(
            skills_dir, "speckit-fakeext-cmd", "installed content"
        )

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "commands" / "cmd.md").write_bytes(
            b"---\ndescription: \xff\xfe not utf-8\n---\n\nExtension body\n"
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

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="speckit-fakeext-cmd"):
            mutated = manager._unregister_skills_in_dir(
                ["speckit-fakeext-cmd"], skills_dir, "claude"
            )

        assert mutated == [], (
            "a skill whose extension restore source could not be read was "
            "not restored, so it must not be reported as mutated"
        )
        assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == (
            "---\nname: speckit-fakeext-cmd\n---\n\ninstalled content\n"
        ), (
            "an unreadable extension source must leave the skill untouched — "
            "falling through to the rmtree branch would delete it exactly "
            "when its replacement cannot be generated"
        )

    def test_unregister_skills_in_dir_rejects_absolute_registry_name(
        self, project_dir
    ):
        """A corrupted ``registered_skills`` entry with an absolute path must not escape.

        ``Path`` join with an absolute right-hand operand discards the
        left side entirely (``skills_dir / "/abs/path"`` == ``"/abs/path"``),
        so an absolute in-project path stored in the registry would bypass
        ``skills_dir`` altogether if not rejected before the join (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        claude_skills_dir.mkdir(parents=True)

        precious_dir = project_dir / "important-data"
        precious_dir.mkdir()
        precious_file = precious_dir / "SKILL.md"
        precious_file.write_text("precious-absolute-target-marker")

        manager = PresetManager(project_dir)
        manager._unregister_skills_in_dir(
            [str(precious_dir)], claude_skills_dir, "claude"
        )

        assert precious_dir.is_dir(), (
            "an absolute registry entry must not let cleanup escape "
            "skills_dir to an unrelated project directory (#2948)"
        )
        assert precious_file.read_text() == "precious-absolute-target-marker"

    def test_infer_legacy_skill_provenance_rejects_absolute_registry_name(
        self, project_dir
    ):
        """Legacy provenance inference must reject an absolute registry name.

        ``_infer_legacy_skill_provenance`` receives its ``skill_names``
        directly from a legacy flat-list ``registered_skills`` value —
        registry data, not manifest-derived — and joins each name onto a
        candidate agent's resolved skills directory the same way
        ``_unregister_skills_in_dir`` does. An absolute in-project name
        discards the candidate directory entirely (Python's ``/`` operator
        drops the left side for an absolute right side), so it can read
        an unrelated project directory's ``SKILL.md`` and, if its
        frontmatter happens to carry a matching preset source marker,
        falsely attribute an unrelated directory as this preset's own
        skill override under whichever agent is being probed (#2948).
        """
        self._write_init_options(project_dir, ai="claude", ai_skills=True)
        claude_skills_dir = project_dir / ".claude" / "skills"
        claude_skills_dir.mkdir(parents=True)

        precious_dir = project_dir / "important-data"
        precious_dir.mkdir()
        (precious_dir / "SKILL.md").write_text(
            "---\n"
            "metadata:\n"
            "  source: preset:some-pack\n"
            "---\n\n"
            "# Unrelated directory, not a real preset skill\n"
        )

        manager = PresetManager(project_dir)
        inferred = manager._infer_legacy_skill_provenance(
            [str(precious_dir)], "some-pack", "claude"
        )

        for names in inferred.values():
            assert str(precious_dir) not in names, (
                "an absolute registry entry must not be falsely attributed "
                "as preset-owned provenance by probing outside the "
                "intended skills subtree (#2948)"
            )


class TestWrapStrategy:
    """Skill registration with inherited wrap metadata."""

    def test_register_skills_inherits_scripts_from_core_when_preset_omits_them(self, project_dir):
        """_register_skills merges scripts/agent_scripts from core when preset lacks them."""
        from specify_cli.presets import PresetManager
        import json

        # Core template with scripts
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "wrap-test.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        # Skills dir for claude
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_subdir = skills_dir / "speckit-wrap-test"
        skill_subdir.mkdir()
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-wrap-test\n---\n\nold\n")

        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        written = (skill_subdir / "SKILL.md").read_text()
        # {SCRIPT} should have been resolved (not left as a literal placeholder)
        assert "{SCRIPT}" not in written

    def test_register_skills_preset_scripts_take_precedence_over_core(self, project_dir):
        """preset-defined scripts/agent_scripts are not overwritten by core frontmatter."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: core-run.sh\n---\n\nCore body.\n"
        )

        registrar = CommandRegistrar()
        body = "{CORE_TEMPLATE}"
        _, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        # Simulate preset frontmatter that already defines scripts
        preset_fm = {"description": "preset", "strategy": "wrap", "scripts": {"sh": "preset-run.sh"}}
        for key in ("scripts", "agent_scripts"):
            if key not in preset_fm and key in core_fm:
                preset_fm[key] = core_fm[key]

        # Preset's scripts must not be overwritten by core
        assert preset_fm["scripts"] == {"sh": "preset-run.sh"}
