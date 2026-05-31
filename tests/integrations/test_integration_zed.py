"""Tests for ZedIntegration."""

import json

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestZedIntegration(SkillsIntegrationTests):
    KEY = "zed"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"
    CONTEXT_FILE = "AGENTS.md"

    def test_requires_cli_is_false(self):
        """Zed is IDE-based; requires_cli must remain False."""
        i = get_integration(self.KEY)
        assert i is not None
        assert i.config is not None
        assert i.config["requires_cli"] is False


class TestZedHookInvocations:
    """Zed hook messages should reference slash-invokable skills."""

    def test_hooks_render_skill_invocation(self, tmp_path):
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "zed-hooks"
        project.mkdir()
        init_options = project / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "zed", "ai_skills": True}))

        hook_executor = HookExecutor(project)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/speckit-plan`" in message
        assert "EXECUTE_COMMAND: speckit.plan" in message
        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message
