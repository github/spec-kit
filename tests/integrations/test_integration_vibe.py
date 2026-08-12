"""Tests for VibeIntegration."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import IntegrationBase, SkillsIntegration
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integrations.vibe import ARGUMENT_HINTS, FORK_CONTEXT_COMMANDS

from .test_integration_base_skills import SkillsIntegrationTests


class TestVibeIntegration:
    def test_registered(self):
        assert "vibe" in INTEGRATION_REGISTRY
        assert get_integration("vibe") is not None

    def test_is_base_integration(self):
        assert isinstance(get_integration("vibe"), IntegrationBase)

    def test_is_skills_integration(self):
        assert isinstance(get_integration("vibe"), SkillsIntegration)

    def test_config_uses_skills(self):
        integration = get_integration("vibe")
        assert integration.config["folder"] == ".vibe/"
        assert integration.config["commands_subdir"] == "skills"

    def test_registrar_config_uses_skill_layout(self):
        integration = get_integration("vibe")
        assert integration.registrar_config["dir"] == ".vibe/skills"
        assert integration.registrar_config["format"] == "markdown"
        assert integration.registrar_config["args"] == "$ARGUMENTS"
        assert integration.registrar_config["extension"] == "/SKILL.md"

    def test_multi_install_safe(self):
        integration = get_integration("vibe")
        assert integration.multi_install_safe is True

    def test_canonical_to_native_events(self):
        integration = get_integration("vibe")
        assert integration.CANONICAL_TO_NATIVE is not None
        assert integration.CANONICAL_TO_NATIVE.get("session_start") == "SessionStart"
        assert integration.CANONICAL_TO_NATIVE.get("pre_tool_use") == "PreToolUse"
        assert integration.CANONICAL_TO_NATIVE.get("post_tool_use") == "PostToolUse"
        assert integration.CANONICAL_TO_NATIVE.get("session_end") == "SessionEnd"
        assert integration.CANONICAL_TO_NATIVE.get("user_prompt_submit") == "UserPromptSubmit"
        assert integration.CANONICAL_TO_NATIVE.get("stop") == "Stop"

    def test_events_config(self):
        integration = get_integration("vibe")
        assert integration.events_config_file == ".vibe/settings.json"
        assert integration.events_format == "json-nested"

    def test_setup_creates_skill_files(self, tmp_path):
        integration = get_integration("vibe")
        manifest = IntegrationManifest("vibe", tmp_path)
        created = integration.setup(tmp_path, manifest, script_type="sh")

        skill_files = [path for path in created if path.name == "SKILL.md"]
        assert skill_files

        skills_dir = tmp_path / ".vibe" / "skills"
        assert skills_dir.is_dir()

        plan_skill = skills_dir / "speckit-plan" / "SKILL.md"
        assert plan_skill.exists()

        content = plan_skill.read_text(encoding="utf-8")
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert "__AGENT__" not in content
        assert "__SPECKIT_COMMAND_" not in content, "unprocessed __SPECKIT_COMMAND_*__"
        assert "/speckit." not in content, "skills agent must use /speckit-<name> not /speckit.<name>"

        parts = content.split("---", 2)
        parsed = yaml.safe_load(parts[1])
        assert parsed["name"] == "speckit-plan"
        assert parsed["user-invocable"] is True
        assert parsed["disable-model-invocation"] is False
        assert parsed["metadata"]["source"] == "templates/commands/plan.md"

    def test_render_skill_unicode(self):
        """Test rendering a skill preserves non-ASCII characters."""
        integration = get_integration("vibe")
        rendered = integration._render_skill(
            "constitution",
            {"description": "Prüfe Konformität der Implementierung"},
            "Body",
        )
        assert "Prüfe Konformität" in rendered

    def test_setup_does_not_write_context_section(self, tmp_path):
        """The CLI no longer manages the agent context file — that is owned by
        the opt-in agent-context extension. Setup must not create or touch it."""
        integration = get_integration("vibe")
        manifest = IntegrationManifest("vibe", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        for path in tmp_path.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "<!-- SPECKIT START -->" not in text

    def test_teardown_does_not_touch_existing_context_file(self, tmp_path):
        """A user-authored context file is left intact on teardown."""
        integration = get_integration("vibe")
        ctx_path = tmp_path / "AGENTS.md"
        original = "# AGENTS.md\n\nUser content.\n"
        ctx_path.write_text(original, encoding="utf-8")

        manifest = IntegrationManifest("vibe", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")
        integration.teardown(tmp_path, manifest)

        assert ctx_path.read_text(encoding="utf-8") == original


class TestVibeArgumentHints:
    """Verify that argument-hint frontmatter is injected for Vibe skills."""

    def test_converge_has_no_argument_hint(self):
        """Converge should not advertise unsupported feature-name arguments."""
        assert "converge" not in ARGUMENT_HINTS

    def test_all_skills_have_hints(self, tmp_path):
        """Every skill with a configured hint must contain an argument-hint line."""
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-"):]
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
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            # Extract stem: speckit-plan -> plan
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-"):]
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
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
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
                stem = stem[len("speckit-"):]
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
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()
            stem = f.parent.name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-"):]
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
        from specify_cli.integrations.vibe import VibeIntegration

        content = (
            "---\n"
            "description: My command\n"
            "---\n"
            "\n"
            "description: this is body text\n"
        )
        result = VibeIntegration.inject_argument_hint(content, "Test hint")
        lines = result.splitlines()
        hint_count = sum(1 for ln in lines if ln.startswith("argument-hint:"))
        assert hint_count == 1, (
            f"Expected exactly 1 argument-hint line, found {hint_count}"
        )

    def test_inject_argument_hint_skips_if_already_present(self):
        """inject_argument_hint must not duplicate if argument-hint already exists."""
        from specify_cli.integrations.vibe import VibeIntegration

        content = (
            "---\n"
            "description: My command\n"
            'argument-hint: "Existing hint"\n'
            "---\n"
            "\n"
            "Body text\n"
        )
        result = VibeIntegration.inject_argument_hint(content, "New hint")
        assert result == content, "Content should be unchanged when hint already exists"


class TestVibeUserInvocable:
    def test_all_skills_have_user_invocable(self, tmp_path):
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert content.startswith("---"), (
                f"{f.parent.name}/SKILL.md is missing the opening frontmatter delimiter '---'"
            )
            parts = content.split("---", 2)
            assert len(parts) >= 3, (
                f"{f.parent.name}/SKILL.md has malformed frontmatter; expected a '--- ... ---' block"
            )
            parsed = yaml.safe_load(parts[1])
            assert parsed.get("user-invocable") is True, (
                f"{f.parent.name}/SKILL.md is missing user-invocable: true in frontmatter"
            )

    def test_all_skills_have_disable_model_invocation(self, tmp_path):
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            parsed = yaml.safe_load(parts[1])
            assert parsed.get("disable-model-invocation") is False, (
                f"{f.parent.name}/SKILL.md is missing disable-model-invocation: false in frontmatter"
            )
