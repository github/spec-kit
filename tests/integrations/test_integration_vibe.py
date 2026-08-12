"""Tests for VibeIntegration."""

import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestVibeIntegration(SkillsIntegrationTests):
    KEY = "vibe"
    FOLDER = ".vibe/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".vibe/skills"

    def test_is_base_integration(self):
        assert isinstance(get_integration("vibe"), IntegrationBase)

    def test_multi_install_safe(self):
        integration = get_integration("vibe")
        assert integration.multi_install_safe is True

    def test_canonical_to_native_events(self):
        integration = get_integration("vibe")
        assert integration.CANONICAL_TO_NATIVE is not None
        assert integration.CANONICAL_TO_NATIVE.get("session_start") == "session_start"
        assert integration.CANONICAL_TO_NATIVE.get("pre_tool_use") == "pre_tool"
        assert integration.CANONICAL_TO_NATIVE.get("post_tool_use") == "post_tool"
        assert integration.CANONICAL_TO_NATIVE.get("session_end") == "session_end"
        assert integration.CANONICAL_TO_NATIVE.get("user_prompt_submit") == "user_prompt_submit"
        assert integration.CANONICAL_TO_NATIVE.get("stop") == "post_agent"

    def test_events_config(self):
        integration = get_integration("vibe")
        assert integration.events_config_file == ".vibe/hooks.toml"
        assert integration.events_format == "toml-vibe"

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

    def test_skills_do_not_have_argument_hint(self, tmp_path):
        """Vibe does not support argument-hint in skill frontmatter, so it must not be injected."""
        integration = get_integration("vibe")
        manifest = IntegrationManifest("vibe", tmp_path)
        created = integration.setup(tmp_path, manifest, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert "argument-hint:" not in content, (
                f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
            )


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
