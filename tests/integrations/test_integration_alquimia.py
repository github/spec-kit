"""Tests for AlquimiaAIIntegration."""

import json
import os
from unittest.mock import patch

import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import IntegrationBase, SkillsIntegration
from specify_cli.integrations.alquimia import ARGUMENT_HINTS
from specify_cli.integrations.manifest import IntegrationManifest


class TestAlquimiaAIIntegration:
    def test_registered(self):
        assert "alquimia" in INTEGRATION_REGISTRY
        assert get_integration("alquimia") is not None

    def test_is_base_integration(self):
        assert isinstance(get_integration("alquimia"), IntegrationBase)

    def test_config_uses_skills(self):
        integration = get_integration("alquimia")
        assert integration.config["folder"] == ".alquimia/"
        assert integration.config["commands_subdir"] == "skills"

    def test_registrar_config_uses_skill_layout(self):
        integration = get_integration("alquimia")
        assert integration.registrar_config["dir"] == ".alquimia/skills"
        assert integration.registrar_config["format"] == "markdown"
        assert integration.registrar_config["args"] == "$ARGUMENTS"
        assert integration.registrar_config["extension"] == "/SKILL.md"

    def test_setup_creates_skill_files(self, tmp_path):
        integration = get_integration("alquimia")
        manifest = IntegrationManifest("alquimia", tmp_path)
        created = integration.setup(tmp_path, manifest, script_type="sh")

        skill_files = [path for path in created if path.name == "SKILL.md"]
        assert skill_files

        skills_dir = tmp_path / ".alquimia" / "skills"
        assert skills_dir.is_dir()

        plan_skill = skills_dir / "speckit-plan" / "SKILL.md"
        assert plan_skill.exists()

        content = plan_skill.read_text(encoding="utf-8")
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert "__AGENT__" not in content
        assert "__SPECKIT_COMMAND_" not in content, "unprocessed __SPECKIT_COMMAND_*__"
        assert "/speckit." not in content, (
            "skills agent must use /speckit-<name> not /speckit.<name>"
        )

        parts = content.split("---", 2)
        parsed = yaml.safe_load(parts[1])
        assert parsed["name"] == "speckit-plan"
        assert parsed["user-invocable"] is True
        assert parsed["disable-model-invocation"] is False
        assert parsed["metadata"]["source"] == "templates/commands/plan.md"

    def test_render_skill_unicode(self):
        """Test rendering a skill preserves non-ASCII characters."""
        integration = get_integration("alquimia")
        rendered = integration._render_skill(
            "constitution",
            {"description": "Prüfe Konformität der Implementierung"},
            "Body",
        )
        assert "Prüfe Konformität" in rendered

    def test_setup_does_not_write_context_section(self, tmp_path):
        """The CLI no longer manages the agent context file — that is owned by
        the opt-in agent-context extension. Setup must not create or touch it."""
        integration = get_integration("alquimia")
        manifest = IntegrationManifest("alquimia", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        for path in tmp_path.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "<!-- SPECKIT START -->" not in text

    def test_teardown_does_not_touch_existing_context_file(self, tmp_path):
        """A user-authored context file is left intact on teardown."""
        integration = get_integration("alquimia")
        ctx_path = tmp_path / "ALQUIMIA.md"
        original = "# ALQUIMIA.md\n\nUser content.\n"
        ctx_path.write_text(original, encoding="utf-8")

        manifest = IntegrationManifest("alquimia", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")
        integration.teardown(tmp_path, manifest)

        assert ctx_path.read_text(encoding="utf-8") == original

    def test_integration_flag_creates_skill_files_cli(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "alquimia-promote"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "alquimia",
                    "--script",
                    "sh",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        assert (project / ".alquimia" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert not (project / ".alquimia" / "commands").exists()

        init_options = json.loads(
            (project / ".specify" / "init-options.json").read_text(encoding="utf-8")
        )
        assert init_options["ai"] == "alquimia"
        assert init_options["ai_skills"] is True
        assert init_options["integration"] == "alquimia"

    def test_integration_flag_creates_skill_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "alquimia-integration"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "alquimia",
                    "--script",
                    "sh",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        assert (
            project / ".alquimia" / "skills" / "speckit-specify" / "SKILL.md"
        ).exists()
        assert (
            project / ".specify" / "integrations" / "alquimia.manifest.json"
        ).exists()

    def test_interactive_alquimia_selection_uses_integration_path(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "alquimia-interactive"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            with (
                patch(
                    "specify_cli.commands.init._stdin_is_interactive", return_value=True
                ),
                patch(
                    "specify_cli.commands.init.select_with_arrows",
                    return_value="alquimia",
                ),
            ):
                result = runner.invoke(
                    app,
                    [
                        "init",
                        "--here",
                        "--script",
                        "sh",
                        "--ignore-agent-tools",
                    ],
                    catch_exceptions=False,
                )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        assert (project / ".specify" / "integration.json").exists()
        assert (
            project / ".specify" / "integrations" / "alquimia.manifest.json"
        ).exists()

        skill_file = project / ".alquimia" / "skills" / "speckit-plan" / "SKILL.md"
        assert skill_file.exists()
        skill_content = skill_file.read_text(encoding="utf-8")
        assert "user-invocable: true" in skill_content
        assert "disable-model-invocation: false" in skill_content

        init_options = json.loads(
            (project / ".specify" / "init-options.json").read_text(encoding="utf-8")
        )
        assert init_options["ai"] == "alquimia"
        assert init_options["ai_skills"] is True
        assert init_options["integration"] == "alquimia"

    def test_alquimia_init_remains_usable_when_converter_fails(self, tmp_path):
        """Alquimia init should succeed even without install_skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "fail-proj"

        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "alquimia",
                "--script",
                "sh",
                "--ignore-agent-tools",
            ],
        )

        assert result.exit_code == 0
        assert (
            target / ".alquimia" / "skills" / "speckit-specify" / "SKILL.md"
        ).exists()

    def test_alquimia_preset_creates_new_skill_without_commands_dir(self, tmp_path):
        from specify_cli import save_init_options
        from specify_cli.presets import PresetManager

        project = tmp_path / "alquimia-preset-skill"
        project.mkdir()
        save_init_options(
            project, {"ai": "alquimia", "ai_skills": True, "script": "sh"}
        )

        skills_dir = project / ".alquimia" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        preset_dir = tmp_path / "alquimia-skill-command"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.research.md").write_text(
            "---\n"
            "description: Research workflow\n"
            "---\n\n"
            "preset:alquimia-skill-command\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "alquimia-skill-command",
                "name": "Alquimia Skill Command",
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

        manager = PresetManager(project)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-research" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "preset:alquimia-skill-command" in content
        assert "name: speckit-research" in content
        assert "user-invocable: true" in content
        assert "disable-model-invocation: false" in content

        metadata = manager.registry.get("alquimia-skill-command")
        assert "speckit-research" in metadata.get("registered_skills", [])


class TestAlquimiaArgumentHints:
    """Verify that argument-hint frontmatter is injected for Alquimia skills."""

    def test_converge_has_no_argument_hint(self):
        """Converge should not advertise unsupported feature-name arguments."""
        assert "converge" not in ARGUMENT_HINTS

    def test_all_skills_have_hints(self, tmp_path):
        """Every skill with a configured hint must contain an argument-hint line."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-") :]
            content = f.read_text(encoding="utf-8")
            if stem in ARGUMENT_HINTS:
                assert "argument-hint:" in content, (
                    f"{f.parent.name}/SKILL.md is missing argument-hint frontmatter"
                )
            else:
                assert "argument-hint:" not in content, (
                    f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
                )

    def test_hints_match_expected_values(self, tmp_path):
        """Each skill's argument-hint must match the expected text."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            # Extract stem: speckit-plan -> plan
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-") :]
            expected_hint = ARGUMENT_HINTS.get(stem)
            content = f.read_text(encoding="utf-8")
            if expected_hint is None:
                assert "argument-hint:" not in content, (
                    f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
                )
            else:
                assert f'argument-hint: "{expected_hint}"' in content, (
                    f"{f.parent.name}/SKILL.md: expected hint '{expected_hint}' not found"
                )

    def test_hint_is_inside_frontmatter(self, tmp_path):
        """argument-hint must appear between the --- delimiters, not in the body."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"No frontmatter in {f.parent.name}/SKILL.md"
            frontmatter = parts[1]
            body = parts[2]
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-") :]
            if stem in ARGUMENT_HINTS:
                assert "argument-hint:" in frontmatter, (
                    f"{f.parent.name}/SKILL.md: argument-hint not in frontmatter section"
                )
                assert "argument-hint:" not in body, (
                    f"{f.parent.name}/SKILL.md: argument-hint leaked into body"
                )
            else:
                assert "argument-hint:" not in content, (
                    f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
                )

    def test_hint_appears_after_description(self, tmp_path):
        """argument-hint must immediately follow the description line."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-") :]
            if stem not in ARGUMENT_HINTS:
                assert "argument-hint:" not in content, (
                    f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
                )
                continue
            found_description = False
            for idx, line in enumerate(lines):
                if line.startswith("description:"):
                    found_description = True
                    assert idx + 1 < len(lines), (
                        f"{f.parent.name}/SKILL.md: description is last line"
                    )
                    assert lines[idx + 1].startswith("argument-hint:"), (
                        f"{f.parent.name}/SKILL.md: argument-hint does not follow description"
                    )
                    break
            assert found_description, (
                f"{f.parent.name}/SKILL.md: no description: line found in output"
            )

    def test_inject_argument_hint_only_in_frontmatter(self):
        """inject_argument_hint must not modify description: lines in the body."""
        from specify_cli.integrations.alquimia import AlquimiaAIIntegration

        content = (
            "---\ndescription: My command\n---\n\ndescription: this is body text\n"
        )
        result = AlquimiaAIIntegration.inject_argument_hint(content, "Test hint")
        lines = result.splitlines()
        hint_count = sum(1 for ln in lines if ln.startswith("argument-hint:"))
        assert hint_count == 1, (
            f"Expected exactly 1 argument-hint line, found {hint_count}"
        )

    def test_inject_argument_hint_skips_if_already_present(self):
        """inject_argument_hint must not duplicate if argument-hint already exists."""
        from specify_cli.integrations.alquimia import AlquimiaAIIntegration

        content = (
            "---\n"
            "description: My command\n"
            'argument-hint: "Existing hint"\n'
            "---\n"
            "\n"
            "Body text\n"
        )
        result = AlquimiaAIIntegration.inject_argument_hint(content, "New hint")
        assert result == content, "Content should be unchanged when hint already exists"
        lines = result.splitlines()
        hint_count = sum(1 for ln in lines if ln.startswith("argument-hint:"))
        assert hint_count == 1


class TestAlquimiaDisableModelInvocation:
    """Verify disable-model-invocation is false for Alquimia skills."""

    def test_setup_sets_disable_model_invocation_false(self, tmp_path):
        """Generated SKILL.md files must have disable-model-invocation: false."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            parsed = yaml.safe_load(parts[1])
            assert parsed["disable-model-invocation"] is False, (
                f"{f.parent.name}: expected disable-model-invocation: false"
            )

    def test_disable_model_invocation_not_true(self, tmp_path):
        """No Alquimia skill should have disable-model-invocation: true."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        for f in created:
            if f.name != "SKILL.md":
                continue
            content = f.read_text(encoding="utf-8")
            assert "disable-model-invocation: true" not in content, (
                f"{f.parent.name}: must not have disable-model-invocation: true"
            )

    def test_non_alquimia_agents_lack_disable_model_invocation(self, tmp_path):
        """Non-Alquimia skill agents should not get disable-model-invocation."""
        from specify_cli.agents import CommandRegistrar

        fm = CommandRegistrar.build_skill_frontmatter(
            "codex", "speckit-plan", "desc", "templates/commands/plan.md"
        )
        assert "disable-model-invocation" not in fm
        assert "user-invocable" not in fm

    def test_skills_default_post_process_preserves_content_without_hooks(
        self, tmp_path
    ):
        """SkillsIntegration agents without an override preserve non-hook content."""
        # ``agy`` is a plain SkillsIntegration with no post-process override,
        # so it stands in for the base-class default behavior.
        agy = get_integration("agy")
        if agy is None:
            return  # agy not registered in this build
        content = "---\nname: test\n---\nBody"
        assert agy.post_process_skill_content(content) == content


class TestAlquimiaHookCommandNote:
    """Verify dot-to-hyphen normalization note is injected in hook sections."""

    def test_hook_note_injected_in_skills_with_hooks(self, tmp_path):
        """Skills that have hook sections should get the normalization note."""
        i = get_integration("alquimia")
        m = IntegrationManifest("alquimia", tmp_path)
        i.setup(tmp_path, m, script_type="sh")
        specify_skill = tmp_path / ".alquimia/skills/speckit-specify/SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        # specify.md has hook sections
        assert "replace dots" in content, (
            "speckit-specify should have dot-to-hyphen hook note"
        )

    def test_hook_note_not_in_skills_without_hooks(self, tmp_path):
        """Skills without hook sections should not get the note."""
        content = "---\nname: test\ndescription: test\n---\n\nNo hooks here.\n"
        result = SkillsIntegration._inject_hook_command_note(content)
        assert "replace dots" not in result

    def test_hook_note_idempotent(self, tmp_path):
        """Injecting the note twice should not duplicate it."""
        content = (
            "---\nname: test\n---\n\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        once = SkillsIntegration._inject_hook_command_note(content)
        twice = SkillsIntegration._inject_hook_command_note(once)
        assert once == twice, "Hook note injection should be idempotent"

    def test_hook_note_fills_missing_repeated_instructions(self, tmp_path):
        """Already-noted hook sections should not suppress later sections."""
        from specify_cli.integrations.base import _HOOK_COMMAND_NOTE

        content = (
            "---\nname: test\n---\n\n"
            f"{_HOOK_COMMAND_NOTE}"
            "- For each executable hook, output the following based on its flag:\n"
            "\n"
            "  - For each executable hook, output the following based on its flag:\n"
        )
        result = SkillsIntegration._inject_hook_command_note(content)
        assert result.count("replace dots (`.`) with hyphens") == 2

    def test_hook_note_not_suppressed_by_unrelated_phrase(self, tmp_path):
        """Unrelated text should not trip the hook-note idempotence guard."""
        content = (
            "---\nname: test\n---\n\n"
            "This paragraph says replace dots in a different context.\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        result = SkillsIntegration._inject_hook_command_note(content)
        assert "This paragraph says replace dots in a different context." in result
        assert result.count("replace dots (`.`) with hyphens") == 1

    def test_hook_note_preserves_indentation(self, tmp_path):
        """The injected note should match the indentation of the target line."""
        content = (
            "---\nname: test\n---\n\n"
            "   - For each executable hook, output the following\n"
        )
        result = SkillsIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line = [line for line in lines if "replace dots" in line][0]
        assert note_line.startswith("   "), "Note should preserve indentation"

    def test_post_process_injects_all_alquimia_flags(self):
        """post_process_skill_content should inject all Alquimia-specific fields."""
        i = get_integration("alquimia")
        content = (
            "---\nname: test\ndescription: test\n---\n\n"
            "- For each executable hook, output the following\n"
        )
        result = i.post_process_skill_content(content)
        assert "user-invocable: true" in result
        assert "disable-model-invocation: false" in result
        assert "replace dots" in result
