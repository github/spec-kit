"""Tests for VibeIntegration."""

from unittest.mock import MagicMock

import yaml

from specify_cli.events import install_integration_events, remove_integration_events
from specify_cli.integrations import get_integration
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore


def _vibe_manifest() -> MagicMock:
    manifest = MagicMock(spec=IntegrationManifest)
    manifest.files = {}
    manifest.record_file = MagicMock()
    manifest.record_existing = MagicMock()
    return manifest


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
        """Vibe supports exactly three hook types: pre_tool, post_tool, post_agent."""
        integration = get_integration("vibe")
        assert integration.CANONICAL_TO_NATIVE == {
            "pre_tool_use": "pre_tool",
            "post_tool_use": "post_tool",
            "stop": "post_agent",
        }

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


class TestVibeTomlMerging:
    """Behavioral tests for the toml-vibe hooks.toml generation and cleanup."""

    def _install(self, tmp_path, events):
        integration = get_integration("vibe")
        manifest = _vibe_manifest()
        install_integration_events(integration, tmp_path, manifest, events)
        return integration, manifest

    def _parse(self, tmp_path):
        return tomllib.loads((tmp_path / ".vibe" / "hooks.toml").read_text(encoding="utf-8"))

    def test_generated_toml_is_valid_and_schema_conformant(self, tmp_path):
        self._install(tmp_path, {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "Edit|Write"}],
            "stop": [{"command": "speckit.session.finish"}],
        })
        data = self._parse(tmp_path)
        hooks = data["hooks"]
        assert len(hooks) == 2
        by_type = {h["type"]: h for h in hooks}
        assert set(by_type) == {"pre_tool", "post_agent"}
        for h in hooks:
            assert h["name"].startswith("speckit-")
            assert isinstance(h["command"], str) and h["command"]
            assert isinstance(h["timeout"], int)
        # Canonical Claude-style regex matcher lands in Vibe's `match`
        # field with the `re:` escape — never in a `matcher` field.
        assert by_type["pre_tool"]["match"] == "re:Edit|Write"
        assert "matcher" not in by_type["pre_tool"]
        # HookConfig rejects `match` on post_agent hooks.
        assert "match" not in by_type["post_agent"]

    def test_wildcard_matcher_omitted(self, tmp_path):
        self._install(tmp_path, {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "*"}],
        })
        (hook,) = self._parse(tmp_path)["hooks"]
        assert "match" not in hook

    def test_unsupported_events_are_skipped(self, tmp_path, capsys):
        self._install(tmp_path, {
            "session_start": [{"command": "speckit.agent-context.update"}],
            "pre_tool_use": [{"command": "speckit.tdd.validate"}],
        })
        hooks = self._parse(tmp_path)["hooks"]
        assert [h["type"] for h in hooks] == ["pre_tool"]
        assert "does not support 'session_start'" in capsys.readouterr().err

    def test_multiple_handlers_get_unique_names(self, tmp_path):
        """Vibe drops duplicate hook names, so shared command stems must not collide."""
        self._install(tmp_path, {
            "pre_tool_use": [
                {"command": "speckit.tdd.validate"},
                {"command": "speckit.other.validate"},
            ],
        })
        hooks = self._parse(tmp_path)["hooks"]
        assert len(hooks) == 2
        names = [h["name"] for h in hooks]
        assert len(set(names)) == 2
        commands = " ".join(h["command"] for h in hooks)
        assert "speckit.tdd.validate" in commands
        assert "speckit.other.validate" in commands

    def test_reinstall_is_idempotent(self, tmp_path):
        events = {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "Bash"}],
            "stop": [{"command": "speckit.session.finish"}],
        }
        self._install(tmp_path, events)
        first = self._parse(tmp_path)["hooks"]
        self._install(tmp_path, events)
        second = self._parse(tmp_path)["hooks"]
        assert second == first

    def test_merge_and_teardown_preserve_user_hooks(self, tmp_path):
        config_path = tmp_path / ".vibe" / "hooks.toml"
        config_path.parent.mkdir(parents=True)
        user_block = (
            '[[hooks]]\n'
            'name = "deny-rm-rf"\n'
            'type = "pre_tool"\n'
            'match = "bash"\n'
            'command = "guard-bash"\n'
        )
        config_path.write_text(user_block, encoding="utf-8")

        integration, manifest = self._install(tmp_path, {
            "pre_tool_use": [{"command": "speckit.tdd.validate"}],
        })
        merged = self._parse(tmp_path)["hooks"]
        assert len(merged) == 2
        assert any(h["name"] == "deny-rm-rf" for h in merged)

        remove_integration_events(integration, tmp_path, manifest)
        remaining = self._parse(tmp_path)["hooks"]
        assert [h["name"] for h in remaining] == ["deny-rm-rf"]

    def test_commands_carry_structured_output_envelope(self, tmp_path):
        """Vibe parses non-empty hook stdout as JSON (HookStructuredResponse);
        plain text is reported as a hook failure. Every generated hook command
        must therefore pass the hook_specific_output envelope to the dispatcher."""
        self._install(tmp_path, {
            "pre_tool_use": [{"command": "speckit.tdd.validate"}],
            "stop": [{"command": "speckit.session.finish"}],
        })
        for hook in self._parse(tmp_path)["hooks"]:
            assert hook["command"].endswith(" hook_specific_output"), hook["name"]

    def test_windows_host_uses_cmd_quoting(self, tmp_path, monkeypatch):
        """Vibe runs hooks via create_subprocess_shell — cmd.exe on Windows,
        where POSIX single quotes don't quote. A host interpreter path with
        spaces must be double-quoted, never shlex-quoted."""
        import specify_cli.events as events_mod

        monkeypatch.setattr(events_mod, "_vibe_target_os", lambda: "cmd")
        monkeypatch.setattr(
            events_mod, "_resolve_interpreter",
            lambda root: r"C:\Program Files\Python\python.exe",
        )
        self._install(tmp_path, {"pre_tool_use": [{"command": "speckit.tdd.validate"}]})
        (hook,) = self._parse(tmp_path)["hooks"]
        assert hook["command"].startswith('"C:\\Program Files\\Python\\python.exe" ')
        assert "'" not in hook["command"]

    def test_posix_host_keeps_shlex_quoting(self, tmp_path, monkeypatch):
        import specify_cli.events as events_mod

        # Pin the target: on a Windows CI runner _vibe_target_os() would
        # return "cmd" and this test asserts the POSIX-host quoting path.
        monkeypatch.setattr(events_mod, "_vibe_target_os", lambda: "host")
        monkeypatch.setattr(
            events_mod, "_resolve_interpreter",
            lambda root: "/opt/my venv/bin/python3",
        )
        self._install(tmp_path, {"pre_tool_use": [{"command": "speckit.tdd.validate"}]})
        (hook,) = self._parse(tmp_path)["hooks"]
        assert hook["command"].startswith("'/opt/my venv/bin/python3' ")

    def test_envelope_resolution(self):
        from specify_cli.events import _context_envelope_for
        integration = get_integration("vibe")
        for event in ("pre_tool_use", "post_tool_use", "stop"):
            assert _context_envelope_for(integration, event) == "hook_specific_output"

    def test_emit_wraps_stdout_as_structured_response(self, capsys):
        import json

        from specify_cli.events import _emit_event_stdout

        _emit_event_stdout("context line", "hook_specific_output")
        data = json.loads(capsys.readouterr().out)
        assert data == {
            "decision": "allow",
            "hook_specific_output": {"additional_context": "context line"},
        }

        # Empty stdout stays empty — Vibe treats it as "no response".
        _emit_event_stdout("", "hook_specific_output")
        assert capsys.readouterr().out == ""

    def test_teardown_deletes_file_without_user_content(self, tmp_path):
        integration, manifest = self._install(tmp_path, {
            "pre_tool_use": [{"command": "speckit.tdd.validate"}],
        })
        assert (tmp_path / ".vibe" / "hooks.toml").is_file()
        remove_integration_events(integration, tmp_path, manifest)
        assert not (tmp_path / ".vibe" / "hooks.toml").exists()


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
