"""Tests for events module: integration runtime events."""

from __future__ import annotations

import json
import os
import platform
import shlex
from pathlib import Path, PurePath
from unittest.mock import MagicMock, patch

import pytest

from specify_cli.events import (
    CANONICAL_EVENTS,
    EVENTS_DISPATCHER_REL,
    collect_extension_events,
    install_integration_events,
    remove_integration_events,
    resolve_events,
    validate_events,
    resolve_and_run_event_command,
)
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integrations.claude import ClaudeIntegration
from specify_cli.integrations.cursor_agent import CursorAgentIntegration
from specify_cli.integrations.opencode import OpencodeIntegration
from specify_cli.integrations.copilot import CopilotIntegration


# -- resolve_events --------------------------------------------------------

class TestResolveEvents:
    """Test the 4-layer event resolution chain."""

    def test_layer1_disabled_returns_empty(self, tmp_path):
        """--events false returns empty dict."""
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            {"events": "false"},
        )
        assert result == {}

    def test_layer4_built_in_defaults(self, tmp_path):
        """Returns baseline defaults when no overrides exist."""
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        assert result == {"post_tool_use": [{"command": "speckit.tdd.validate"}]}

    def test_layer3_extension_events_appended(self, tmp_path):
        """Extension-declared events are resolved and appended."""
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        ext_yml = ext_dir / "extension.yml"
        ext_yml.write_text(
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )

        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        assert "post_tool_use" in result
        assert "session_start" in result
        assert result["session_start"] == [{"command": "speckit.my-ext.boot"}]

    def test_layer3_multiple_extensions_same_event_accumulate(self, tmp_path):
        """Two extensions declaring the same event both run (#2)."""
        for ext_id, cmd in (("my-ext", "speckit.my-ext.boot"), ("other-ext", "speckit.other.boot")):
            ext_dir = tmp_path / ".specify" / "extensions" / ext_id
            ext_dir.mkdir(parents=True)
            (ext_dir / "extension.yml").write_text(
                f"events:\n  session_start:\n    command: {cmd}\n",
                encoding="utf-8",
            )
        result = resolve_events("claude", None, tmp_path, None)
        assert result["session_start"] == [
            {"command": "speckit.my-ext.boot"},
            {"command": "speckit.other.boot"},
        ]

    def test_layer2_yaml_override_replaces(self, tmp_path):
        """integration-events.yml override replaces baseline entirely."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events:\n"
            "      stop:\n"
            "        command: speckit.override.stop\n",
            encoding="utf-8",
        )

        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        assert result == {"stop": [{"command": "speckit.override.stop"}]}

    def test_layer2_empty_events_disables(self, tmp_path):
        """Empty events override disables events."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events: {}\n",
            encoding="utf-8",
        )

        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        assert result == {}

    def test_unreadable_yaml_override_keeps_prior_layers(self, tmp_path):
        """An unreadable override is ignored like malformed YAML."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_bytes(b"\xff\xfe")

        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )

        assert result == {
            "post_tool_use": [{"command": "speckit.tdd.validate"}]
        }

    def test_no_config_no_events(self, tmp_path):
        """Safe fallback with empty config/options."""
        result = resolve_events("claude", None, tmp_path, None)
        assert result == {}


# -- collect_extension_events -----------------------------------------------

class TestCollectExtensionEvents:
    """Test scanning extension.yml files for events: declarations."""

    def test_no_extensions_dir(self, tmp_path):
        assert collect_extension_events(tmp_path) == {}

    def test_no_events_in_extension(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text("extension:\n  id: my-ext\n", encoding="utf-8")
        assert collect_extension_events(tmp_path) == {}

    def test_events_collected(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "events:\n  pre_tool_use:\n    command: speckit.my-ext.check\n",
            encoding="utf-8",
        )
        result = collect_extension_events(tmp_path)
        assert result == {"pre_tool_use": [{"command": "speckit.my-ext.check"}]}

    def test_invalid_yaml_skipped(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text("invalid: - - -", encoding="utf-8")
        assert collect_extension_events(tmp_path) == {}

    def test_non_utf8_manifest_skipped(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_bytes(b"\xff\xfe")

        assert collect_extension_events(tmp_path) == {}

    def test_event_command_ref_canonicalized_via_manifest(self, tmp_path):
        """R1: events are read from a validated ExtensionManifest, so an
        obsolete command ref (e.g. my-ext.boot) is canonicalized
        (speckit.my-ext.boot) the same way hook refs are at install."""
        from specify_cli.extensions import ExtensionRegistry
        import yaml as _yaml

        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        # Manifest declares an alias-form event command ref (my-ext.boot)
        # alongside the command it resolves to; the validated manifest lifts
        # the ref to speckit.my-ext.boot (C11).
        (ext_dir / "extension.yml").write_text(
            _yaml.dump({
                "schema_version": "1.0",
                "extension": {
                    "id": "my-ext",
                    "name": "My Ext",
                    "version": "1.0.0",
                    "description": "test",
                },
                "requires": {"speckit_version": ">=0.1"},
                "provides": {
                    "commands": [
                        {"name": "speckit.my-ext.boot", "file": "commands/boot.md"}
                    ]
                },
                "events": {"session_start": {"command": "my-ext.boot"}},
            }),
            encoding="utf-8",
        )
        ExtensionRegistry(tmp_path / ".specify" / "extensions").add(
            "my-ext", {"enabled": True}
        )

        result = collect_extension_events(tmp_path)
        # The ref was canonicalized to speckit.my-ext.boot by the validated
        # manifest, so dispatch can match it (raw-YAML reading would have
        # emitted the obsolete my-ext.boot and the hook would no-op).
        assert result == {"session_start": [{"command": "speckit.my-ext.boot"}]}


# -- Class-driven mappings --------------------------------------------------

class TestCanonicalEventMapping:
    """Verify registry-driven mapping is correct on integration classes."""

    def test_claude_identity(self):
        integration = ClaudeIntegration()
        assert integration.supports_events() is True
        assert integration.CANONICAL_TO_NATIVE["pre_tool_use"] == "PreToolUse"
        assert integration.CANONICAL_TO_NATIVE["session_start"] == "SessionStart"

    def test_cursor_camelcase(self):
        integration = CursorAgentIntegration()
        assert integration.supports_events() is True
        assert integration.CANONICAL_TO_NATIVE["pre_tool_use"] == "preToolUse"
        assert integration.CANONICAL_TO_NATIVE["user_prompt_submit"] == "beforeSubmitPrompt"

    def test_opencode_limited(self):
        integration = OpencodeIntegration()
        assert integration.supports_events() is True
        assert integration.CANONICAL_TO_NATIVE["pre_tool_use"] == "tool.execute.before"
        assert integration.CANONICAL_TO_NATIVE["session_start"] == "experimental.chat.system.transform"
        assert integration.CANONICAL_TO_NATIVE["user_prompt_submit"] == "chat.message"
        assert "stop" not in integration.CANONICAL_TO_NATIVE

    def test_copilot_mapping(self):
        integration = CopilotIntegration()
        assert integration.supports_events() is True
        assert integration.CANONICAL_TO_NATIVE["session_start"] == "sessionStart"
        assert integration.CANONICAL_TO_NATIVE["user_prompt_submit"] == "userPromptSubmitted"

    def test_gemini_mapping_includes_before_agent(self):
        # S6: Gemini exposes BeforeAgent for user_prompt_submit and AfterAgent
        # for stop (verified against Gemini CLI's hooks docs).
        from specify_cli.integrations.gemini import GeminiIntegration
        integration = GeminiIntegration()
        assert integration.CANONICAL_TO_NATIVE["pre_tool_use"] == "BeforeTool"
        assert integration.CANONICAL_TO_NATIVE["user_prompt_submit"] == "BeforeAgent"
        assert integration.CANONICAL_TO_NATIVE["stop"] == "AfterAgent"

    def test_tabnine_mapping_includes_before_agent(self):
        # S7: Tabnine's Gemini-compatible schema provides BeforeAgent/AfterAgent.
        from specify_cli.integrations.tabnine import TabnineIntegration
        integration = TabnineIntegration()
        assert integration.CANONICAL_TO_NATIVE["user_prompt_submit"] == "BeforeAgent"
        assert integration.CANONICAL_TO_NATIVE["stop"] == "AfterAgent"


# -- Event-capable adapters declare --events (#8, #9) ------------------------

class TestEventCapableOptionsComposition:
    """Event-capable integrations must declare --events so the documented
    --events false opt-out is accepted."""

    def _has_option(self, opts, name):
        return any(o.name == name for o in opts)

    def test_copilot_declares_events(self):
        # #9: CopilotIntegration.options() composed with super() so --events
        # is declared alongside --skills.
        opts = CopilotIntegration().options()
        assert self._has_option(opts, "--skills")
        assert self._has_option(opts, "--events"), (
            "Copilot is event-capable but --events is not declared; "
            "--integration-options \"--events false\" would be rejected."
        )

    def test_devin_declares_events(self):
        # #8: DevinIntegration.options() composed with super() so --events
        # is declared alongside --skills.
        from specify_cli.integrations.devin import DevinIntegration
        opts = DevinIntegration().options()
        assert self._has_option(opts, "--skills")
        assert self._has_option(opts, "--events"), (
            "Devin is event-capable but --events is not declared; "
            "--integration-options \"--events false\" would be rejected."
        )

    def test_cursor_declares_events(self):
        # Cursor already composed correctly; assert it stays that way.
        opts = CursorAgentIntegration().options()
        assert self._has_option(opts, "--skills")
        assert self._has_option(opts, "--events")

    def test_codex_declares_events(self):
        # Codex already composed correctly; assert it stays that way.
        from specify_cli.integrations.codex import CodexIntegration
        opts = CodexIntegration().options()
        assert self._has_option(opts, "--skills")
        assert self._has_option(opts, "--events")


# -- validate_events --------------------------------------------------------

class TestValidateEvents:
    """Test manifest validation."""

    def test_unknown_event_rejected(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"unknown_event": {"command": "speckit.tdd.validate"}}}
        with pytest.raises(ValidationError) as exc:
            validate_events(data)
        assert "Unknown event" in str(exc.value)

    def test_known_event_accepted(self):
        data = {"events": {"pre_tool_use": {"command": "speckit.tdd.validate"}}}
        validate_events(data)  # no raise

    def test_all_canonical_events_accepted(self):
        data = {
            "events": {
                name: {"command": "speckit.test"}
                for name in CANONICAL_EVENTS
            }
        }
        validate_events(data)  # no raise


# -- Claude settings JSON merging -------------------------------------------

class TestClaudeJsonMerging:
    """Test Claude settings JSON merging and cleanup."""

    def test_merge_into_empty_file(self, tmp_path):
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "Edit|Write"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)

        config_path = tmp_path / ".claude/settings.json"
        assert config_path.is_file()
        data = json.loads(config_path.read_text())
        assert "hooks" in data
        assert "PreToolUse" in data["hooks"]
        assert data["hooks"]["PreToolUse"][0]["matcher"] == "Edit|Write"
        # #6: native schema is a single `command` string, not command+args.
        inner = data["hooks"]["PreToolUse"][0]["hooks"][0]
        assert isinstance(inner["command"], str)
        assert "args" not in inner
        assert "speckit.tdd.validate" in inner["command"]
        assert "pre_tool_use" in inner["command"]
        # The dispatcher path must be prefixed with ${CLAUDE_PROJECT_DIR}/ for
        # Claude, and double-quoted so a project path with spaces doesn't
        # word-split (C2) while the variable still expands.
        assert "${CLAUDE_PROJECT_DIR}/" in inner["command"]
        assert '"${CLAUDE_PROJECT_DIR}/.specify/events.py"' in inner["command"]

    def test_claude_emits_all_handlers_for_same_event(self, tmp_path):
        """#2: two handlers on the same event both appear in the native config."""
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [
                {"command": "speckit.tdd.validate"},
                {"command": "speckit.other.check"},
            ],
        }
        install_integration_events(integration, tmp_path, manifest, events)

        data = json.loads((tmp_path / ".claude/settings.json").read_text())
        inner_hooks = data["hooks"]["PreToolUse"][0]["hooks"]
        commands = [h["command"] for h in inner_hooks]
        assert any("speckit.tdd.validate" in c for c in commands)
        assert any("speckit.other.check" in c for c in commands)

    def test_remove_preserves_user_hooks(self, tmp_path):
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        # Pre-seed user setting
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "Bash",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "user-check",
                                    }
                                ],
                            }
                        ]
                    }
                }
            )
        )

        events = {
            "pre_tool_use": [{"command": "speckit.tdd.validate"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        remove_integration_events(integration, tmp_path, manifest)

        data = json.loads(config_path.read_text())
        assert "hooks" in data
        assert "PreToolUse" in data["hooks"]
        assert len(data["hooks"]["PreToolUse"]) == 1
        assert data["hooks"]["PreToolUse"][0]["matcher"] == "Bash"


# -- Copilot events JSON writing --------------------------------------------

class TestCopilotJsonWriting:
    """Test Copilot dedicated .github/hooks/speckit.json generation."""

    def test_copilot_json_generation(self, tmp_path):
        integration = CopilotIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "session_start": [{"command": "speckit.agent-context.update", "timeout": 60}],
        }
        install_integration_events(integration, tmp_path, manifest, events)

        config_path = tmp_path / ".github/hooks/speckit.json"
        assert config_path.is_file()
        data = json.loads(config_path.read_text())
        assert data["version"] == 1
        assert "hooks" in data
        assert "sessionStart" in data["hooks"]
        entry = data["hooks"]["sessionStart"][0]
        assert entry["type"] == "command"
        # #6: a complete shell command string (not command+args).
        assert "speckit.agent-context.update" in entry["bash"]
        assert "session_start" in entry["bash"]
        # S4: bash and powershell get independent OS-targeted interpreters so
        # a config generated on one OS works on the other. R2: command/event
        # args are shell-quoted for each target shell.
        assert "speckit.agent-context.update" in entry["powershell"]
        assert entry["bash"] != entry["powershell"]
        # bash uses POSIX interpreter python3 (shlex.quote leaves safe tokens
        # bare); powershell uses python single-quoted with the & call operator
        # so the quoted command is actually invoked (C1).
        assert entry["bash"].startswith("python3 ")
        assert entry["powershell"].startswith("& 'python' ")
        # PowerShell always single-quotes; POSIX leaves metacharacter-free
        # identifiers bare (shlex.quote only quotes when needed).
        assert "'speckit.agent-context.update'" in entry["powershell"]
        assert "speckit.agent-context.update" in entry["bash"]
        # R2: native timeout gets the buffer (60 + 5 = 65) so the agent's
        # outer cap fires after the dispatcher's inner subprocess timeout.
        assert entry["timeoutSec"] == 65


# -- Cursor hooks.json version + matcher grouping (#7, S3) -------------------

class TestCursorJsonWriting:
    """#7: .cursor/hooks.json requires top-level version:1; S3: matcher grouping."""

    def test_cursor_json_includes_version(self, tmp_path):
        integration = CursorAgentIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        data = json.loads((tmp_path / ".cursor/hooks.json").read_text())
        assert data["version"] == 1
        assert "sessionStart" in data["hooks"]

    def test_cursor_json_preserves_user_version(self, tmp_path):
        integration = CursorAgentIntegration()
        config_path = tmp_path / ".cursor/hooks.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"version": 1, "hooks": {}}))

        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        data = json.loads(config_path.read_text())
        assert data["version"] == 1

    def test_nested_matcher_grouping_per_distinct_matcher(self, tmp_path):
        """S3: two handlers with different matchers produce two matcher-groups."""
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [
                {"command": "speckit.first", "matcher": "Edit"},
                {"command": "speckit.second", "matcher": "Bash"},
            ],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        data = json.loads((tmp_path / ".claude/settings.json").read_text())
        groups = data["hooks"]["PreToolUse"]
        matchers = sorted(g["matcher"] for g in groups)
        assert matchers == ["Bash", "Edit"]
        # Each group holds exactly its own handler.
        by_matcher = {g["matcher"]: g["hooks"] for g in groups}
        assert len(by_matcher["Edit"]) == 1
        assert "speckit.first" in by_matcher["Edit"][0]["command"]
        assert len(by_matcher["Bash"]) == 1
        assert "speckit.second" in by_matcher["Bash"][0]["command"]

    def test_nested_shared_matcher_stays_one_group(self, tmp_path):
        """S3: handlers sharing a matcher stay in a single matcher-group."""
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [
                {"command": "speckit.first", "matcher": "Edit"},
                {"command": "speckit.second", "matcher": "Edit"},
            ],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        data = json.loads((tmp_path / ".claude/settings.json").read_text())
        groups = data["hooks"]["PreToolUse"]
        assert len(groups) == 1
        assert groups[0]["matcher"] == "Edit"
        assert len(groups[0]["hooks"]) == 2


# -- Gemini timeout unit (#7) ------------------------------------------------

class TestGeminiTimeoutUnit:
    """Gemini measures hook timeouts in milliseconds, not seconds."""

    def test_gemini_timeout_converted_to_ms(self, tmp_path):
        from specify_cli.integrations.gemini import GeminiIntegration
        from specify_cli.events import _native_timeout

        integration = GeminiIntegration()
        # 60 (seconds) -> 60000 (ms) for Gemini; unchanged for seconds-based agents.
        assert _native_timeout(integration, 60) == 60000
        assert _native_timeout(ClaudeIntegration(), 60) == 60

    def test_tabnine_timeout_converted_to_ms(self):
        """R5: Tabnine mirrors Gemini's ms-based hook schema."""
        from specify_cli.integrations.tabnine import TabnineIntegration
        from specify_cli.events import _native_timeout

        assert _native_timeout(TabnineIntegration(), 60) == 60000

    def test_qwen_timeout_converted_to_ms(self):
        """U1: Qwen Code command hooks use milliseconds (default 60000)."""
        from specify_cli.integrations.qwen import QwenIntegration
        from specify_cli.events import _native_timeout

        assert _native_timeout(QwenIntegration(), 60) == 60000


# -- Devin root-nested format (U2) + Copilot agentStop (U3) ------------------

class TestDevinRootNestedFormat:
    """U2: Devin's hooks.v1.json is a root event map with no 'hooks' wrapper."""

    def test_devin_events_written_at_root(self, tmp_path):
        from specify_cli.integrations.devin import DevinIntegration
        integration = DevinIntegration()
        assert integration.events_format == "json-root-nested"

        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        manifest.remove = MagicMock()

        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        data = json.loads((tmp_path / ".devin/hooks.v1.json").read_text())
        # Event keys are top-level (no "hooks" wrapper).
        assert "PreToolUse" in data
        assert "hooks" not in data

    def test_devin_teardown_removes_owned_and_preserves_user(self, tmp_path):
        from specify_cli.integrations.devin import DevinIntegration
        integration = DevinIntegration()
        config_path = tmp_path / ".devin/hooks.v1.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "PreToolUse": [{
                "matcher": "exec",
                "hooks": [{"type": "command", "command": "user-check"}],
            }]
        }))

        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        manifest.remove = MagicMock()
        install_integration_events(
            integration, tmp_path, manifest,
            {"stop": [{"command": "speckit.end"}]},
        )
        remove_integration_events(integration, tmp_path, manifest)

        data = json.loads(config_path.read_text())
        # User hook preserved at the root; Specify's Stop gone.
        assert "Stop" not in data
        assert data["PreToolUse"][0]["matcher"] == "exec"


class TestCopilotAgentStop:
    """U3: Copilot maps the canonical stop lifecycle to native agentStop."""

    def test_copilot_stop_mapping(self):
        integration = CopilotIntegration()
        assert integration.CANONICAL_TO_NATIVE.get("stop") == "agentStop"


# -- Shell quoting & matcher escaping (R2, R4) -------------------------------

class TestContextInjectionEnvelopes:
    """C13: context-injection envelope resolution and emission."""

    def test_emit_event_stdout_wrapping(self, capsys):
        from specify_cli.events import _emit_event_stdout

        _emit_event_stdout("hello ctx", "plain")
        assert capsys.readouterr().out == "hello ctx"

        # hookSpecificOutput without native_event: no hookEventName (backward
        # compat for callers that don't pass it).
        _emit_event_stdout("hello ctx", "hookSpecificOutput")
        assert json.loads(capsys.readouterr().out.strip()) == {
            "hookSpecificOutput": {"additionalContext": "hello ctx"}
        }

        # hookSpecificOutput with native_event: hookEventName included
        # (required by Qwen's hooks spec; derived from Claude Code's).
        _emit_event_stdout("hello ctx", "hookSpecificOutput", "SessionStart")
        assert json.loads(capsys.readouterr().out.strip()) == {
            "hookSpecificOutput": {
                "additionalContext": "hello ctx",
                "hookEventName": "SessionStart",
            }
        }

        _emit_event_stdout("hello ctx", "additionalContext")
        assert json.loads(capsys.readouterr().out.strip()) == {
            "additionalContext": "hello ctx"
        }

        _emit_event_stdout("hello ctx", "additional_context")
        assert json.loads(capsys.readouterr().out.strip()) == {
            "additional_context": "hello ctx"
        }

        _emit_event_stdout("hello ctx", "suppress")
        assert capsys.readouterr().out == ""

        # Empty output emits nothing under any envelope.
        _emit_event_stdout("", "additionalContext")
        assert capsys.readouterr().out == ""

    def test_envelope_resolution_and_command_formatting(self):
        from specify_cli.events import _dispatcher_command, _context_envelope_for
        from specify_cli.integrations.gemini import GeminiIntegration
        from specify_cli.integrations.qwen import QwenIntegration
        from specify_cli.integrations.copilot import CopilotIntegration
        from specify_cli.integrations.cursor_agent import CursorAgentIntegration
        from specify_cli.integrations.claude import ClaudeIntegration
        from specify_cli.integrations.codex import CodexIntegration

        gemini = GeminiIntegration()
        assert _context_envelope_for(gemini, "session_start") == "hookSpecificOutput"
        assert _context_envelope_for(gemini, "user_prompt_submit") == "hookSpecificOutput"
        assert _context_envelope_for(gemini, "pre_tool_use") == "suppress"

        # hookSpecificOutput appends the native event name as a 6th dispatcher
        # argument so the dispatcher can populate hookEventName. The default
        # timeout (60s) is always emitted as the 4th arg to keep positional
        # alignment (R3).
        cmd_gemini_start = _dispatcher_command(gemini, Path("/proj"), "speckit.boot", "session_start")
        assert cmd_gemini_start.endswith(" 60 hookSpecificOutput SessionStart")

        cmd_gemini_prompt = _dispatcher_command(gemini, Path("/proj"), "speckit.prompt", "user_prompt_submit")
        assert cmd_gemini_prompt.endswith(" 60 hookSpecificOutput BeforeAgent")

        cmd_gemini_tool = _dispatcher_command(gemini, Path("/proj"), "speckit.guard", "pre_tool_use")
        assert cmd_gemini_tool.endswith(" 60 suppress")

        # Qwen uses the same hookSpecificOutput protocol with its own native
        # event names; verify hookEventName threading for Qwen's CamelCase names.
        qwen = QwenIntegration()
        cmd_qwen_start = _dispatcher_command(qwen, Path("/proj"), "speckit.boot", "session_start")
        assert cmd_qwen_start.endswith(" 60 hookSpecificOutput SessionStart")
        cmd_qwen_prompt = _dispatcher_command(qwen, Path("/proj"), "speckit.prompt", "user_prompt_submit")
        assert cmd_qwen_prompt.endswith(" 60 hookSpecificOutput UserPromptSubmit")

        copilot = CopilotIntegration()
        assert _context_envelope_for(copilot, "session_start") == "additionalContext"
        assert _context_envelope_for(copilot, "user_prompt_submit") == "additionalContext"
        cmd_copilot_start = _dispatcher_command(copilot, Path("/proj"), "speckit.boot", "session_start")
        assert cmd_copilot_start.endswith(" 60 additionalContext")
        cmd_copilot_prompt = _dispatcher_command(copilot, Path("/proj"), "speckit.prompt", "user_prompt_submit")
        assert cmd_copilot_prompt.endswith(" 60 additionalContext")

        cursor = CursorAgentIntegration()
        assert _context_envelope_for(cursor, "session_start") == "additional_context"
        assert _context_envelope_for(cursor, "user_prompt_submit") == "suppress"
        cmd_cursor_start = _dispatcher_command(cursor, Path("/proj"), "speckit.boot", "session_start")
        assert cmd_cursor_start.endswith(" 60 additional_context")

        claude = ClaudeIntegration()
        codex = CodexIntegration()
        assert _context_envelope_for(claude, "session_start") is None
        assert _context_envelope_for(codex, "session_start") is None


class TestDispatcherCommandQuoting:
    """R2: dispatcher command components are shell-quoted so spaces and shell
    metacharacters are passed as single arguments, not reinterpreted."""

    def test_command_metacharacters_are_quoted_posix(self, tmp_path):
        from specify_cli.events import _dispatcher_command

        cmd = _dispatcher_command(
            ClaudeIntegration(), tmp_path, "speckit.x; rm -rf /", "pre_tool_use",
            target_os="posix",
        )
        # The metacharacter-bearing command is single-quoted as one argument.
        assert "'speckit.x; rm -rf /'" in cmd

    def test_interpreter_with_space_is_quoted_posix(self, tmp_path):
        import shlex
        from specify_cli.events import _dispatcher_command
        # Simulate a venv interpreter under a path with spaces.
        venv = tmp_path / ".venv" / "bin" / "python"
        venv.parent.mkdir(parents=True)
        venv.write_text("#!/bin/sh\n")
        proj = tmp_path
        cmd = _dispatcher_command(
            ClaudeIntegration(), proj, "speckit.x.y", "stop", target_os="host",
        )
        # The command must tokenize back into interpreter + dispatcher + 2 args.
        tokens = shlex.split(cmd)
        # dispatcher token carries the ${CLAUDE_PROJECT_DIR} prefix (double-
        # quoted in the raw string, but shlex.split strips the quotes).
        assert any("events.py" in t for t in tokens)
        assert "speckit.x.y" in tokens
        assert "stop" in tokens

    def test_windows_target_uses_powershell_quoting(self, tmp_path):
        from specify_cli.events import _dispatcher_command

        cmd = _dispatcher_command(
            CopilotIntegration(), tmp_path, "speckit.x.y", "session_start",
            target_os="windows",
        )
        # PowerShell single-quoted literals, and the & call operator so the
        # quoted interpreter is actually invoked (C1).
        assert cmd.startswith("& ")
        assert "'speckit.x.y'" in cmd
        assert "'session_start'" in cmd

    def test_host_target_never_emits_powershell_quotes(self, tmp_path):
        """C1: the host target uses POSIX quoting on every platform so a
        single-command-string hook (Claude/Gemini/etc.) stays invocable —
        never 'python' (which PowerShell wouldn't invoke without &)."""
        from specify_cli.events import _shell_quote
        # Safe tokens pass through bare under host (POSIX), not PS-quoted.
        assert _shell_quote("python3", "host") == "python3"
        assert _shell_quote("speckit.x.y", "host") == "speckit.x.y"

    def test_claude_dispatcher_double_quoted_for_spaces(self, tmp_path):
        """C2: Claude's ${CLAUDE_PROJECT_DIR} dispatcher path is double-quoted
        so a project path containing spaces doesn't word-split."""
        from specify_cli.events import _dispatcher_command
        cmd = _dispatcher_command(
            ClaudeIntegration(), tmp_path, "speckit.x.y", "stop", target_os="host",
        )
        assert '"${CLAUDE_PROJECT_DIR}/.specify/events.py"' in cmd


class TestTomlMatcherEscaping:
    """R4: the TOML matcher is escaped like command, not raw-interpolated."""

    def test_matcher_with_quote_stays_valid_toml(self, tmp_path):
        from specify_cli.integrations.codex import CodexIntegration

        integration = CodexIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        manifest.remove = MagicMock()

        # A matcher containing a double quote would break a raw TOML basic
        # string; it must be escaped.
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.x.y", "matcher": 'Ba"sh'}]},
        )
        content = (tmp_path / ".codex" / "config.toml").read_text()
        # Round-trips through a TOML parser without error.
        try:
            import tomllib
            parsed = tomllib.loads(content)
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore
            parsed = tomllib.loads(content)
        # The matcher value survived intact.
        group = parsed["hooks"]["PreToolUse"][0]
        assert group["matcher"] == 'Ba"sh'


class TestTomlUnreadableConfig:
    """An undecodable user config.toml must not crash install or teardown.

    Every JSON merge/remove path goes through ``_load_user_json``, which
    skips on an unreadable or malformed file to preserve user content (#22).
    The TOML merge and remove read the user's config.toml with no boundary,
    so a non-UTF-8 (or otherwise unreadable) file crashed
    ``install_integration_events``/``remove_integration_events`` with a raw
    ``UnicodeDecodeError`` — and the merge path would have regenerated the
    file, discarding the user's bytes, had it not crashed first.
    """

    def test_merge_skips_unreadable_config_and_preserves_bytes(self, tmp_path):
        from specify_cli.integrations.codex import CodexIntegration

        integration = CodexIntegration()
        manifest = _claude_manifest(tmp_path)
        config_path = tmp_path / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True)
        user_bytes = b"# codex config \xff\xfe not utf-8\n"
        config_path.write_bytes(user_bytes)

        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )

        # User bytes preserved and the skipped file is not tracked (S5).
        assert config_path.read_bytes() == user_bytes
        manifest.record_existing.assert_not_called()

    def test_teardown_skips_unreadable_config_and_preserves_bytes(self, tmp_path):
        from specify_cli.integrations.codex import CodexIntegration

        integration = CodexIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        config_path = tmp_path / ".codex" / "config.toml"
        assert config_path.is_file()

        # The user (or another tool) rewrites the config as non-UTF-8
        # between install and uninstall.
        user_bytes = b"# rewritten \xff\xfe not utf-8\n"
        config_path.write_bytes(user_bytes)

        remove_integration_events(integration, tmp_path, manifest)

        assert config_path.read_bytes() == user_bytes


# -- Opencode TS Plugin merging ---------------------------------------------

class TestOpencodePluginMerging:
    """Test Opencode typescript plugin generation."""

    def test_opencode_ts_plugin_generation(self, tmp_path):
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "Edit"}],
            "session_start": [{"command": "speckit.agent-context.update"}],
            "session_end": [{"command": "speckit.agent-context.teardown"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)

        plugin_path = tmp_path / ".opencode/plugin/speckit-events.ts"
        assert plugin_path.is_file()
        content = plugin_path.read_text()
        assert "runEvent" in content
        assert "tool.execute.before" in content
        assert "experimental.chat.system.transform" in content
        assert "speckit.tdd.validate" in content
        assert "speckit.agent-context.update" in content
        # #13: failures must propagate via throw, not process.exit(2) which
        # would kill the OpenCode host process.
        assert "process.exit(2)" not in content
        assert "throw new Error" in content
        # session_start (experimental.chat.system.transform) must be guarded
        # so canonical session-start handlers only run when a session is
        # present — OpenCode fires this hook for non-session operations
        # (e.g. agent generation) with no sessionID.
        assert "if (!input.sessionID) return;" in content
        # session_start handler output is cached per sessionID so non-idempotent
        # handlers run once per session instead of on every LLM request.
        assert "sessionStartCache" in content
        assert "sessionStartCache.get(input.sessionID)" in content
        assert "sessionStartCache.set(input.sessionID" in content
        # Cache is evicted on session.deleted (session_end).
        assert "sessionStartCache.delete(event.sessionID)" in content

    def test_opencode_ts_plugin_chat_message_part_injection(self, tmp_path):
        """user_prompt_submit emits chat.message pushing a synthetic TextPart.
        The part ID derives from output.parts[last].id (prt_ brand preserved)
        with a prt_ fallback to prevent OpenCode session schema crashes."""
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "user_prompt_submit": [{"command": "speckit.discover"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)

        plugin_path = tmp_path / ".opencode/plugin/speckit-events.ts"
        assert plugin_path.is_file()
        content = plugin_path.read_text()
        assert "chat.message" in content
        assert "output.parts.push" in content
        assert "synthetic: true" in content
        assert 'type: "text"' in content
        assert "output.parts[output.parts.length - 1]?.id" in content
        assert '?? "prt_"' in content

    def test_opencode_ts_plugin_resolves_interpreter_and_directory_at_load(self, tmp_path):
        """C8/C9: the dispatcher + interpreter are resolved per-project at
        plugin load from the `directory` OpenCode passes (not process.cwd()),
        preferring a project venv, and the dispatcher is launched via
        execFileSync (argv, no shell)."""
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        # Create a project venv so the plugin's runtime resolver prefers it.
        venv_bin = tmp_path / ".venv" / "bin" / "python"
        venv_bin.parent.mkdir(parents=True)
        venv_bin.write_text("#!/bin/sh\n")

        events = {"session_start": [{"command": "speckit.boot"}]}
        install_integration_events(integration, tmp_path, manifest, events)
        content = (tmp_path / ".opencode/plugin/speckit-events.ts").read_text()
        # Runtime venv-interpreter preference is baked into the resolver.
        assert ".venv" in content and "python" in content
        # Dispatcher is resolved from `directory`, not process.cwd() (C8).
        assert "path.join(process.cwd()" not in content
        assert "directory" in content
        # execFileSync (argv, no shell) instead of a shell command string (C9).
        assert "execFileSync" in content
        assert "execSync(`" not in content
        # R2: venv interpreter is probed for specify_cli importability before
        # selection (an unrelated project venv shouldn't shadow the fallback).
        assert "canImportSpecifyCli" in content
        # S2: the PATH fallback is python on Windows (python3 is commonly
        # absent there), python3 on POSIX.
        assert "process.platform === 'win32'" in content
        assert "'python'" in content
        assert "'python3'" in content

    def test_opencode_ts_plugin_emits_all_handlers(self, tmp_path):
        """#2: multiple handlers on the same native event all invoke runEvent."""
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "session_start": [
                {"command": "speckit.first.boot"},
                {"command": "speckit.second.boot"},
            ],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        content = (tmp_path / ".opencode/plugin/speckit-events.ts").read_text()
        assert "speckit.first.boot" in content
        assert "speckit.second.boot" in content
        # Suppressed #6: each handler call is wrapped in try/catch and errors aggregated.
        assert "try {" in content
        assert "errors.push(" in content
        assert "throw new Error(errors.join" in content

    def test_opencode_ts_plugin_forwards_output(self, tmp_path):
        """C7: tool callbacks forward both input and output to runEvent so
        pre_tool_use can inspect tool args and post_tool_use the result."""
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        events = {
            "pre_tool_use": [{"command": "speckit.tdd.validate", "matcher": "Edit"}],
            "post_tool_use": [{"command": "speckit.tdd.after"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        content = (tmp_path / ".opencode/plugin/speckit-events.ts").read_text()
        # runEvent signature carries both input and output. S1: command/event
        # are JSON string literals (double-quoted, escaped). S3: the per-
        # handler timeout (seconds) is threaded as the 5th arg.
        assert 'runEvent("speckit.tdd.validate", "pre_tool_use", input, output, 60)' in content
        assert 'runEvent("speckit.tdd.after", "post_tool_use", input, output, 60)' in content
        # Tool callbacks pass both arguments through.
        assert "_pre_tool_use(input, output)" in content
        assert "_post_tool_use(input, output)" in content

    def test_opencode_ts_plugin_escapes_metacharacters(self, tmp_path):
        """S1: command/matcher values with quotes/backticks are serialized as
        JSON string literals so they can't break the generated TypeScript or
        inject code."""
        integration = OpencodeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()

        # A command and matcher containing characters that would break a
        # single-quoted TS literal.
        events = {
            "pre_tool_use": [{"command": "speckit.x'y`code", "matcher": "Ed'it"}],
        }
        install_integration_events(integration, tmp_path, manifest, events)
        content = (tmp_path / ".opencode/plugin/speckit-events.ts").read_text()
        # The value must appear inside a JSON double-quoted literal, not a
        # single-quoted TS literal (which a quote/backtick would break).
        assert json.dumps("speckit.x'y`code") in content
        # The dangerous single-quoted form (runEvent('speckit.x'y...')) —
        # where the embedded quote would terminate the literal — is absent.
        assert "runEvent('speckit.x" not in content
        assert json.dumps("ed'it") in content


# -- Command runner test (core execution) -----------------------------------

class TestCommandRunner:
    """Test the core command/script resolution and runner."""

    def test_run_command_not_found(self, tmp_path):
        code = resolve_and_run_event_command("nonexistent.command", "session_start", "{}", tmp_path)
        assert code == 0  # no-ops gracefully

    def test_extension_command_resolves_when_file_stem_differs(self, tmp_path):
        """S8: an extension command whose declared file differs from its
        command name resolves via the manifest, not a file-stem scan."""
        from specify_cli.events import _find_command_template
        from specify_cli.extensions import ExtensionRegistry

        ext_id = "selftest"
        ext_dir = tmp_path / ".specify" / "extensions" / ext_id
        cmds_dir = ext_dir / "commands"
        cmds_dir.mkdir(parents=True)
        # Command name is speckit.selftest.extension but the file is selftest.md.
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n"
            "  id: selftest\n"
            "  name: Selftest\n"
            "  version: 1.0.0\n"
            "  description: test\n"
            "requires:\n"
            "  speckit_version: '>=0.1'\n"
            "provides:\n"
            "  commands:\n"
            "    - name: speckit.selftest.extension\n"
            "      file: commands/selftest.md\n",
            encoding="utf-8",
        )
        (cmds_dir / "selftest.md").write_text(
            "---\ndescription: \"x\"\n---\nBody\n", encoding="utf-8"
        )
        ExtensionRegistry(tmp_path / ".specify" / "extensions").add(
            ext_id, {"enabled": True}
        )

        template, resolved_ext = _find_command_template(
            "speckit.selftest.extension", tmp_path
        )
        assert template is not None
        assert template.name == "selftest.md"
        assert resolved_ext == ext_id

    def test_disabled_extension_command_not_resolved(self, tmp_path):
        """S1: a disabled extension's command is skipped by
        _find_command_template (both the manifest loop and the disk-fallback
        scan), so a stale hook can't execute a disabled extension."""
        from specify_cli.events import _find_command_template
        from specify_cli.extensions import ExtensionRegistry
        import yaml as _yaml

        # Manifest-resolvable path (step 1).
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        cmds_dir = ext_dir / "commands"
        cmds_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            _yaml.dump({
                "schema_version": "1.0",
                "extension": {"id": "my-ext", "name": "My Ext", "version": "1.0.0",
                              "description": "test"},
                "requires": {"speckit_version": ">=0.1"},
                "provides": {"commands": [{"name": "speckit.my-ext.boot",
                                           "file": "commands/boot.md"}]},
                "events": {"session_start": {"command": "speckit.my-ext.boot"}},
            }),
            encoding="utf-8",
        )
        (cmds_dir / "boot.md").write_text("---\ndescription: \"x\"\n---\nBody\n", encoding="utf-8")
        ExtensionRegistry(tmp_path / ".specify" / "extensions").add(
            "my-ext", {"enabled": False}
        )
        template, _ = _find_command_template("speckit.my-ext.boot", tmp_path)
        assert template is None, "Disabled extension's command was resolved (manifest loop)."

        # Disk-fallback path (step 2): stem == command name.
        (cmds_dir / "speckit.my-ext.boot.md").write_text("---\ndescription: \"x\"\n---\nBody\n", encoding="utf-8")
        template, _ = _find_command_template("speckit.my-ext.boot", tmp_path)
        assert template is None, "Disabled extension's command was resolved (disk fallback)."

    def test_run_command_resolves_and_executes(self, tmp_path):
        # Create a mock core command md file
        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        cmd_file = cmd_dir / "test.md"
        cmd_file.write_text(
            "---\n"
            "description: \"Test\"\n"
            "scripts:\n"
            "  sh: scripts/test.sh\n"
            "---\n"
            "Body\n",
            encoding="utf-8",
        )

        script_dir = tmp_path / ".specify" / "scripts"
        script_dir.mkdir(parents=True)
        script_file = script_dir / "test.sh"
        script_file.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        script_file.chmod(0o755)

        # Skip on Windows because sh is POSIX
        if platform.system().lower().startswith("win"):
            return

        code = resolve_and_run_event_command("speckit.test", "session_start", "{}", tmp_path)
        assert code == 0

    def test_py_variant_anchored_under_specify(self, tmp_path):
        """S2: the py variant resolves scripts/... under .specify/, not the
        project root, and prepends the resolved interpreter."""
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "boot.md").write_text(
            "---\n"
            "description: \"Boot\"\n"
            "scripts:\n"
            "  py: scripts/python/boot.py\n"
            "---\nBody\n",
            encoding="utf-8",
        )
        py_dir = tmp_path / ".specify" / "scripts" / "python"
        py_dir.mkdir(parents=True)
        (py_dir / "boot.py").write_text("import sys; sys.exit(0)\n", encoding="utf-8")

        argv = _resolve_event_command_argv(cmd_dir / "boot.md", tmp_path, None)
        assert argv is not None
        # Interpreter first, then the .specify-anchored script path. Compare in
        # POSIX form so the assertion holds on Windows (backslash paths) too.
        assert len(argv) >= 2
        assert PurePath(argv[1]).as_posix().endswith(".specify/scripts/python/boot.py")
        assert ".specify" in argv[1]

    def test_unparseable_script_command_returns_none(self, tmp_path):
        """A ``scripts:`` value shlex cannot tokenize must resolve to no argv.

        The generated dispatcher's ``_resolve_argv`` twin wraps its
        ``shlex.split`` in ``except ValueError: return None``, but the
        CLI-side resolver did not: an unclosed quote in a ``scripts:``
        frontmatter value raised a raw ``ValueError: No closing quotation``
        through ``resolve_and_run_event_command`` instead of degrading to
        "no runnable script" like every other malformed-input case here.
        """
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "boot.md").write_text(
            "---\n"
            "description: \"Boot\"\n"
            "scripts:\n"
            "  sh: scripts/bash/boot.sh \"unclosed\n"
            "---\nBody\n",
            encoding="utf-8",
        )

        argv = _resolve_event_command_argv(cmd_dir / "boot.md", tmp_path, None)

        assert argv is None

    def test_unreadable_template_returns_none(self, tmp_path):
        """A command template that cannot be read must resolve to no argv.

        Every other failure inside ``_resolve_event_command_argv`` — missing
        frontmatter, malformed YAML, absent scripts — degrades to ``None`` so
        the dispatcher treats the command as declaring no runnable script.
        The initial ``read_text`` was the one step outside that boundary: a
        non-UTF-8 template raised a raw ``UnicodeDecodeError`` through
        ``resolve_and_run_event_command`` and out of ``specify event run``.
        """
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "boot.md").write_bytes(
            b"---\ndescription: \"B\xff\xfeoot\"\n---\nBody\n"
        )

        argv = _resolve_event_command_argv(cmd_dir / "boot.md", tmp_path, None)
        assert argv is None

    def test_permission_denied_template_returns_none(self, tmp_path, monkeypatch):
        """The same boundary must cover ``OSError`` (e.g. permission denied).

        Mocked rather than chmod-based so the case also holds under
        privileged CI where permission bits are not enforced.
        """
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        template = cmd_dir / "boot.md"
        template.write_text("---\ndescription: Boot\n---\nBody\n")

        original_read_text = Path.read_text

        def failing_read_text(self_path, *args, **kwargs):
            if self_path == template:
                raise PermissionError(13, "Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", failing_read_text)

        argv = _resolve_event_command_argv(template, tmp_path, None)
        assert argv is None

    def test_ps_variant_prefixed_with_powershell_launcher(self, tmp_path):
        """S6: the ps variant prefixes argv with pwsh/powershell -File so
        subprocess.run(shell=False) can execute the .ps1 script."""
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "boot.md").write_text(
            "---\n"
            "description: \"Boot\"\n"
            "scripts:\n"
            "  ps: scripts/powershell/boot.ps1\n"
            "---\nBody\n",
            encoding="utf-8",
        )
        ps_dir = tmp_path / ".specify" / "scripts" / "powershell"
        ps_dir.mkdir(parents=True)
        (ps_dir / "boot.ps1").write_text("exit 0\n", encoding="utf-8")

        argv = _resolve_event_command_argv(cmd_dir / "boot.md", tmp_path, None)
        assert argv is not None
        # Launcher (pwsh or powershell), -File, then the .specify-anchored
        # script. shutil.which may return a full path with an .EXE suffix on
        # Windows, so match by stem (case-insensitive).
        assert PurePath(argv[0]).stem.lower() in ("pwsh", "powershell")
        assert argv[1] == "-File"
        assert PurePath(argv[2]).as_posix().endswith(".specify/scripts/powershell/boot.ps1")

    def test_run_command_executes_with_project_root_cwd(self, tmp_path):
        """R1: the event command runs with cwd set to the project root, not the
        caller's arbitrary working directory, so project-relative script logic
        resolves correctly even when the agent fires the hook elsewhere."""
        if platform.system().lower().startswith("win"):
            return
        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "cwd.md").write_text(
            "---\ndescription: \"cwd\"\nscripts:\n  sh: scripts/cwd.sh\n---\nBody\n",
            encoding="utf-8",
        )
        script_dir = tmp_path / ".specify" / "scripts"
        script_dir.mkdir(parents=True)
        out_file = tmp_path / "cwd.out"
        script = script_dir / "cwd.sh"
        # The script records its working directory.
        script.write_text(f"#!/bin/sh\npwd > {shlex.quote(str(out_file))}\nexit 0\n", encoding="utf-8")
        script.chmod(0o755)

        # Invoke from a different working directory to prove cwd is forced.
        import os as _os
        prev = _os.getcwd()
        subdir = tmp_path / "sub"
        subdir.mkdir()
        try:
            _os.chdir(subdir)
            code = resolve_and_run_event_command("speckit.cwd", "session_start", "{}", tmp_path)
        finally:
            _os.chdir(prev)
        assert code == 0
        recorded = out_file.read_text().strip()
        assert Path(recorded).resolve() == tmp_path.resolve()

    def test_dispatcher_is_self_contained(self, tmp_path):
        """R1: the generated dispatcher prefers `import specify_cli` (durable
        install) and falls back to an inline stdlib resolver so it works
        without a persistent `specify` executable (e.g. one-time uvx)."""
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        content = (tmp_path / EVENTS_DISPATCHER_REL).read_text()
        # Delegates to specify_cli when importable.
        assert "from specify_cli.events import resolve_and_run_event_command" in content
        assert "except (ImportError, TypeError):" in content
        # Inline stdlib fallback resolver for one-time/temporary installs.
        assert "_run_inline" in content
        assert "_find_command_template" in content
        # No dependency on a persistent `specify` executable.
        assert '["specify"]' not in content

    def test_dispatcher_inline_fallback_runs_script(self, tmp_path):
        """R1: with specify_cli.events NOT importable, the inline resolver
        finds the command template and runs its script (stdlib only)."""
        import subprocess as _sp
        import sys as _sys

        # Install events (generates the dispatcher + native config).
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        dispatcher = tmp_path / EVENTS_DISPATCHER_REL
        assert dispatcher.is_file()

        # Create a core command template whose script writes its payload.
        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        out_file = tmp_path / "payload.out"
        (cmd_dir / "boot.md").write_text(
            "---\ndescription: \"Boot\"\nscripts:\n  sh: scripts/boot.sh\n---\nBody\n",
            encoding="utf-8",
        )
        script_dir = tmp_path / ".specify" / "scripts"
        script_dir.mkdir(parents=True)
        script = script_dir / "boot.sh"
        script.write_text(f"#!/bin/sh\ncat > {shlex.quote(str(out_file))}\nexit 0\n", encoding="utf-8")
        script.chmod(0o755)

        if platform.system().lower().startswith("win"):
            return  # sh is POSIX

        # Force the inline fallback: shadow `specify_cli` with an empty package
        # (no `events` submodule) so `from specify_cli.events import ...` raises
        # ModuleNotFoundError (an ImportError subclass), simulating a one-time
        # install where the package is unavailable at runtime.
        fake_dir = tmp_path / "_fake"
        (fake_dir / "specify_cli").mkdir(parents=True)
        (fake_dir / "specify_cli" / "__init__.py").write_text("", encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(fake_dir)
        result = _sp.run(
            [_sys.executable, str(dispatcher), "speckit.boot", "session_start", "60"],
            input='{"tool_name":"x"}',
            capture_output=True,
            text=True,
            env=env,
            cwd=str(tmp_path),
        )
        # The inline resolver ran the script with the payload.
        assert out_file.exists(), f"inline fallback did not run script; stderr={result.stderr!r} rc={result.returncode}"
        assert out_file.read_text() == '{"tool_name":"x"}'

    def test_dispatcher_threads_per_handler_timeout(self, tmp_path):
        """S4: the generated dispatcher reads an optional 4th timeout arg and
        uses it for the inner subprocess, instead of a fixed 120s cap that
        would kill a handler configured for longer."""
        integration = ClaudeIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate", "timeout": 300}]},
        )
        content = (tmp_path / EVENTS_DISPATCHER_REL).read_text()
        # The dispatcher accepts a 4th argv element as the timeout.
        assert "sys.argv[3]" in content
        assert "timeout=timeout" in content

    def test_native_command_carries_resolved_timeout(self, tmp_path):
        """S4: the generated native hook command appends the resolved timeout
        so the dispatcher receives it. Claude uses seconds (default unit)."""
        from specify_cli.events import _dispatcher_command
        cmd = _dispatcher_command(
            ClaudeIntegration(), tmp_path, "speckit.x.y", "stop",
            timeout_seconds=300,
        )
        # R2: the raw seconds (no conversion, no buffer) are appended as the
        # 4th arg; the buffer goes on the native hook timeout field instead.
        assert " 300" in cmd

    def test_dispatcher_timeout_not_unit_converted_for_ms_adapters(self, tmp_path):
        """R2: the dispatcher arg is always seconds — for Gemini/Qwen/Tabnine
        (ms adapters) the timeout must NOT be converted to milliseconds
        (which previously yielded 60000 seconds)."""
        from specify_cli.events import _dispatcher_command
        from specify_cli.integrations.gemini import GeminiIntegration
        cmd = _dispatcher_command(
            GeminiIntegration(), tmp_path, "speckit.x.y", "pre_tool_use",
            timeout_seconds=60,
        )
        # 60 seconds (not 60000) is passed to the dispatcher.
        assert " 60" in cmd
        assert " 60000" not in cmd

    def test_sh_variant_uses_launcher_on_windows(self, tmp_path):
        """S5: on Windows the sh variant prefixes a bash/sh launcher so
        subprocess.run(shell=False) can execute the .sh script."""
        from specify_cli.events import _resolve_event_command_argv

        cmd_dir = tmp_path / ".specify" / "templates" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "boot.md").write_text(
            "---\ndescription: \"Boot\"\nscripts:\n  sh: scripts/bash/boot.sh\n---\nBody\n",
            encoding="utf-8",
        )
        sh_dir = tmp_path / ".specify" / "scripts" / "bash"
        sh_dir.mkdir(parents=True)
        (sh_dir / "boot.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        argv = _resolve_event_command_argv(cmd_dir / "boot.md", tmp_path, None)
        assert argv is not None
        # On POSIX the script runs directly; on Windows a launcher prefixes it.
        if platform.system().lower().startswith("win"):
            assert PurePath(argv[0]).stem.lower() in ("bash", "sh")
            assert PurePath(argv[1]).as_posix().endswith(".specify/scripts/bash/boot.sh")
        else:
            assert PurePath(argv[0]).as_posix().endswith(".specify/scripts/bash/boot.sh")


# -- Merge/teardown idempotency & safety (Tier 3) ----------------------------

def _claude_manifest(tmp_path):
    manifest = MagicMock(spec=IntegrationManifest)
    manifest.files = {}
    manifest.record_file = MagicMock()
    manifest.record_existing = MagicMock()
    manifest.remove = MagicMock()
    return manifest


class TestMergeIdempotency:
    """#9/#11: marker recursion and full-clean-before-add."""

    def test_upgrade_does_not_duplicate_nested_hooks(self, tmp_path):
        """#9: re-running install replaces prior Specify inner hooks instead of
        appending a second matcher-group on every upgrade."""
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        events = {"pre_tool_use": [{"command": "speckit.tdd.validate"}]}
        for _ in range(2):
            manifest = _claude_manifest(tmp_path)
            install_integration_events(integration, tmp_path, manifest, events)

        data = json.loads(config_path.read_text())
        groups = data["hooks"]["PreToolUse"]
        # Exactly one matcher-group for Specify (no duplication).
        assert len(groups) == 1
        inner = groups[0]["hooks"]
        assert len(inner) == 1
        assert "speckit.tdd.validate" in inner[0]["command"]

    def test_override_change_removes_stale_event(self, tmp_path):
        """#11: when the resolved set changes from pre_tool_use to stop, the
        old marked pre_tool_use entry is removed, not left active."""
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"stop": [{"command": "speckit.end"}]},
        )

        data = json.loads(config_path.read_text())
        assert "PreToolUse" not in data["hooks"]
        assert "Stop" in data["hooks"]


class TestEmptyMapRemoval:
    """#3: --events false / empty resolved map strips prior hooks."""

    def test_empty_events_removes_prior_hooks(self, tmp_path):
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        assert config_path.is_file()

        # Now resolve to empty (--events false): prior hooks must be removed.
        install_integration_events(integration, tmp_path, _claude_manifest(tmp_path), {})

        # The dispatcher is shared and left in place (#10); only native hooks
        # are stripped. The settings file had no user content → deleted (#14).
        assert not config_path.exists() or "hooks" not in json.loads(config_path.read_text())


class TestTeardownDataSafety:
    """#14/#22/#23: preserve user content, delete Spec-Kit-created empties."""

    def test_remove_deletes_spec_kit_created_config(self, tmp_path):
        """#14: a config Spec Kit created from scratch is deleted (not left as
        ``{}``) so manifest.uninstall() doesn't preserve an empty stub."""
        integration = ClaudeIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        config_path = tmp_path / ".claude/settings.json"
        assert config_path.is_file()

        remove_integration_events(integration, tmp_path, manifest)
        assert not config_path.exists()

    def test_remove_preserves_user_content_in_config(self, tmp_path):
        """#14: a pre-existing config with user content is kept (user hooks
        survive teardown)."""
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [{
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "user-check"}],
                }]
            },
            "userSetting": True,
        }))

        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"stop": [{"command": "speckit.end"}]},
        )
        remove_integration_events(integration, tmp_path, manifest)

        data = json.loads(config_path.read_text())
        # User hook and setting preserved; Specify hook gone.
        assert data["userSetting"] is True
        assert "Stop" not in data.get("hooks", {})
        assert data["hooks"]["PreToolUse"][0]["matcher"] == "Bash"

    def test_forced_full_teardown_preserves_user_config(self, tmp_path):
        """S9: a full teardown(force=True) — which runs manifest.uninstall(
        force=True) after remove_events — must not delete a pre-existing user
        settings file whose owned entries were cleaned but user content kept.
        Uses a real manifest to exercise the uninstall path."""
        from specify_cli.integrations.manifest import IntegrationManifest

        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [{
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "user-check"}],
                }]
            },
            "userSetting": True,
        }))

        manifest = IntegrationManifest(integration.key, tmp_path, version="test")
        install_integration_events(
            integration, tmp_path, manifest,
            {"stop": [{"command": "speckit.end"}]},
        )
        manifest.save()

        # Full teardown: remove_events + manifest.uninstall(force=True).
        integration.teardown(tmp_path, manifest, force=True)

        assert config_path.exists(), (
            "Forced teardown deleted the user's settings file (S9)."
        )
        data = json.loads(config_path.read_text())
        assert data["userSetting"] is True
        assert data["hooks"]["PreToolUse"][0]["matcher"] == "Bash"

    def test_jsonc_config_not_reset_on_merge(self, tmp_path):
        """#22: a JSONC/unparseable native config is left untouched on merge."""
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        jsonc = '{\n  // my comment\n  "hooks": {}\n}\n'
        config_path.write_text(jsonc)

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        # User content preserved verbatim — not reset to {}.
        assert config_path.read_text() == jsonc

    def test_unreadable_config_not_overwritten_on_merge(self, tmp_path):
        """An unreadable user config aborts the merge instead of crashing."""
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.mkdir(parents=True)

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )

        assert config_path.is_dir()

    def test_jsonc_opencode_config_not_reset(self, tmp_path):
        """#23: a malformed opencode.json is preserved, not reset to {}."""
        integration = OpencodeIntegration()
        config_path = tmp_path / "opencode.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        malformed = "{ not valid json"
        config_path.write_text(malformed)

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"session_start": [{"command": "speckit.boot"}]},
        )
        assert config_path.read_text() == malformed


class TestCopilotMergeTeardown:
    """#8: Copilot dedicated hooks JSON merges owned entries / teardown
    removes only owned entries."""

    def test_copilot_merge_preserves_user_hooks(self, tmp_path):
        integration = CopilotIntegration()
        config_path = tmp_path / ".github/hooks/speckit.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "version": 1,
            "hooks": {
                "sessionStart": [{"type": "command", "bash": "user-hook"}],
            },
        }))

        install_integration_events(
            integration, tmp_path, _claude_manifest(tmp_path),
            {"session_start": [{"command": "speckit.boot"}]},
        )
        data = json.loads(config_path.read_text())
        entries = data["hooks"]["sessionStart"]
        bash_cmds = [e.get("bash") for e in entries]
        assert "user-hook" in bash_cmds
        assert any("speckit.boot" in c for c in bash_cmds)

    def test_copilot_teardown_removes_only_owned_entries(self, tmp_path):
        integration = CopilotIntegration()
        config_path = tmp_path / ".github/hooks/speckit.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "version": 1,
            "hooks": {
                "sessionStart": [{"type": "command", "bash": "user-hook"}],
            },
        }))

        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        remove_integration_events(integration, tmp_path, manifest)

        data = json.loads(config_path.read_text())
        # User hook preserved; Spec-Kit entry gone.
        assert data["hooks"]["sessionStart"][0]["bash"] == "user-hook"

    def test_copilot_teardown_deletes_spec_kit_only_file(self, tmp_path):
        """#8/#14: when the file held only Spec-Kit entries, teardown deletes it."""
        integration = CopilotIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        config_path = tmp_path / ".github/hooks/speckit.json"
        assert config_path.is_file()
        remove_integration_events(integration, tmp_path, manifest)
        assert not config_path.exists()


class TestSharedDispatcherRefcount:
    """#10: the shared .specify/events.py dispatcher is not deleted while
    another installed event-capable integration still references it."""

    def test_dispatcher_kept_when_other_integration_references_it(self, tmp_path):
        # Simulate two event-capable integrations installed: claude (the one
        # being uninstalled) and codex (still installed). The codex manifest
        # lists the dispatcher, so removing claude must not delete it.
        from specify_cli.integrations.codex import CodexIntegration

        claude = ClaudeIntegration()
        codex = CodexIntegration()

        # Install claude's events (writes dispatcher + claude config).
        claude_manifest = _claude_manifest(tmp_path)
        install_integration_events(
            claude, tmp_path, claude_manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        # Install codex's events (re-writes shared dispatcher + codex config).
        codex_manifest = MagicMock(spec=IntegrationManifest)
        codex_manifest.files = {}
        codex_manifest.record_file = MagicMock()
        codex_manifest.record_existing = MagicMock()
        codex_manifest.remove = MagicMock()
        install_integration_events(
            codex, tmp_path, codex_manifest,
            {"pre_tool_use": [{"command": "speckit.codex.check"}]},
        )

        # Persist a codex manifest on disk so the refcount check finds it.
        codex_disk = IntegrationManifest(codex.key, tmp_path, version="test")
        codex_disk._files = {EVENTS_DISPATCHER_REL: "x"}
        codex_disk.save()

        # Write the integration-state JSON so installed_integration_keys sees codex.
        import json as _json
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(_json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude", "codex"],
        }))

        dispatcher_path = tmp_path / EVENTS_DISPATCHER_REL
        assert dispatcher_path.exists()

        # Removing claude should leave the dispatcher (codex still uses it).
        remove_integration_events(claude, tmp_path, claude_manifest)
        assert dispatcher_path.exists()


class TestSafeWriteDestination:
    """#12: write targets are validated before any bytes are written."""

    def test_symlinked_config_dir_rejected(self, tmp_path):
        integration = ClaudeIntegration()
        # Create a symlinked .claude directory pointing outside the project.
        outside = tmp_path / "outside"
        outside.mkdir()
        linked = tmp_path / ".claude"
        os.symlink(outside, linked)

        with pytest.raises(ValueError, match="(?i)symlink|escapes|outside"):
            install_integration_events(
                integration, tmp_path, _claude_manifest(tmp_path),
                {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
            )
        # No content written through the symlink.
        assert not (outside / "settings.json").exists()

    def test_toml_teardown_rejects_symlinked_config(self, tmp_path):
        """R3: TOML teardown validates the destination before read/write, so a
        symlink swap after install can't make uninstall overwrite an external
        file."""
        from specify_cli.integrations.codex import CodexIntegration

        integration = CodexIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        config_path = tmp_path / ".codex" / "config.toml"
        assert config_path.is_file()

        # Swap the config for a symlink pointing outside the project.
        outside = tmp_path / "outside.toml"
        outside.write_text("external = true\n")
        config_path.unlink()
        os.symlink(outside, config_path)

        with pytest.raises(ValueError, match="(?i)symlink|escapes|outside"):
            remove_integration_events(integration, tmp_path, manifest)
        # External file untouched.
        assert outside.read_text() == "external = true\n"

    def test_json_remover_rejects_symlinked_config(self, tmp_path):
        """Removers validate destination before reading or unlinking."""
        integration = ClaudeIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        config_path = tmp_path / ".claude" / "settings.json"
        assert config_path.is_file()

        outside = tmp_path / "outside.json"
        outside.write_text('{"external": true}')
        config_path.unlink()
        os.symlink(outside, config_path)

        with pytest.raises(ValueError, match="(?i)symlink|escapes|outside"):
            remove_integration_events(integration, tmp_path, manifest)
        assert outside.read_text() == '{"external": true}'

    def test_plugin_remover_rejects_symlinked_plugin(self, tmp_path):
        """OpenCode plugin cleanup validates destination before unlinking."""
        integration = OpencodeIntegration()
        manifest = _claude_manifest(tmp_path)
        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        plugin_path = tmp_path / ".opencode" / "plugin" / "speckit-events.ts"
        assert plugin_path.is_file()

        outside = tmp_path / "outside.ts"
        outside.write_text("// external")
        plugin_path.unlink()
        os.symlink(outside, plugin_path)

        manifest.files[".opencode/plugin/speckit-events.ts"] = "hash"
        with pytest.raises(ValueError, match="(?i)symlink|escapes|outside"):
            remove_integration_events(integration, tmp_path, manifest)
        assert outside.read_text() == "// external"


# -- Validation & lifecycle (Tier 4) -----------------------------------------

class TestValidateEventsCommandType:
    """#17: command must be a non-empty string, not just truthy."""

    def test_non_string_command_rejected(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": ["speckit.tdd.validate"]}}}
        with pytest.raises(ValidationError, match="(?i)command.*string"):
            validate_events(data)

    def test_empty_string_command_rejected(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": "  "}}}
        with pytest.raises(ValidationError, match="(?i)command.*string"):
            validate_events(data)


class TestCollectExtensionEventsEnabledFlag:
    """#1: collect_extension_events honors the registry's enabled flag."""

    def test_disabled_extension_events_skipped(self, tmp_path):
        from specify_cli.extensions import ExtensionRegistry

        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "extension:\n  id: my-ext\n  name: My Ext\n  version: 1.0.0\n"
            "  description: test\n"
            "schema_version: '1.0'\n"
            "requires:\n  speckit_version: '>=0.1'\n"
            "provides:\n  commands: []\n"
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )
        registry = ExtensionRegistry(tmp_path / ".specify" / "extensions")
        registry.add("my-ext", {"enabled": False})

        result = collect_extension_events(tmp_path)
        assert result == {}

    def test_enabled_extension_events_collected(self, tmp_path):
        from specify_cli.extensions import ExtensionRegistry

        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "extension:\n  id: my-ext\n  name: My Ext\n  version: 1.0.0\n"
            "  description: test\n"
            "schema_version: '1.0'\n"
            "requires:\n  speckit_version: '>=0.1'\n"
            "provides:\n  commands: []\n"
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )
        registry = ExtensionRegistry(tmp_path / ".specify" / "extensions")
        registry.add("my-ext", {"enabled": True})

        result = collect_extension_events(tmp_path)
        assert result == {"session_start": [{"command": "speckit.my-ext.boot"}]}


class TestRefreshIntegrationEvents:
    """#1: refresh_integration_events regenerates native config after
    extension state changes."""

    def test_refresh_strips_removed_extension_events(self, tmp_path):
        from specify_cli.events import refresh_integration_events
        from specify_cli.integrations.manifest import IntegrationManifest

        # Install claude with an event sourced from a (simulated) extension.
        integration = ClaudeIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path, version="test")
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.my-ext.check"}]},
        )
        manifest.save()
        config_path = tmp_path / ".claude/settings.json"
        assert config_path.is_file()

        # Record claude as installed so refresh finds it.
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude"],
        }))
        # No extension declares events now → refresh should strip the prior hook
        # (the config is deleted when no user content remains, #14).
        refresh_integration_events(tmp_path)

        if config_path.exists():
            data = json.loads(config_path.read_text())
            assert "PreToolUse" not in data.get("hooks", {})
        # If the file is gone, the hooks were stripped (and the empty config
        # deleted) — also correct.

    def test_refresh_emits_newly_declared_extension_events(self, tmp_path):
        from specify_cli.events import refresh_integration_events
        from specify_cli.integrations.manifest import IntegrationManifest

        integration = ClaudeIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path, version="test")
        # Initially no events.
        manifest.save()
        config_path = tmp_path / ".claude/settings.json"

        # Declare an extension event on disk.
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude"],
        }))

        refresh_integration_events(tmp_path)

        data = json.loads(config_path.read_text())
        assert "SessionStart" in data["hooks"]

    def test_refresh_honors_stored_events_false(self, tmp_path):
        """S7: a stored --events false must be honored across extension
        lifecycle refresh; passing None would re-enable events."""
        from specify_cli.events import refresh_integration_events
        from specify_cli.integrations.manifest import IntegrationManifest

        integration = ClaudeIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path, version="test")
        manifest.save()
        config_path = tmp_path / ".claude/settings.json"

        # Declare an extension event on disk.
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )
        # Store the integration with --events false in parsed_options.
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude"],
            "integration_settings": {
                "claude": {"parsed_options": {"events": "false"}},
            },
        }))

        refresh_integration_events(tmp_path)

        # No hooks should have been re-created (CLI gate honored).
        if config_path.exists():
            assert "hooks" not in json.loads(config_path.read_text())


# -- Override preserve-layers (#10) ------------------------------------------

class TestOverridePreserveLayers:
    """#10: an invalid override entry abandons the whole override and keeps
    the accumulated built-in + extension layers, instead of disabling all
    hooks."""

    def test_invalid_override_entry_keeps_prior_layers(self, tmp_path):
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        # One valid entry, one invalid (non-string command) — the whole
        # override is ignored, built-in defaults survive.
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events:\n"
            "      stop:\n"
            "        command: speckit.valid.stop\n"
            "      pre_tool_use:\n"
            "        command: [not-a-string]\n",
            encoding="utf-8",
        )
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        # Built-in default survived (override was abandoned on the invalid entry).
        assert "post_tool_use" in result
        assert result["post_tool_use"] == [{"command": "speckit.tdd.validate"}]

    def test_explicit_empty_override_disables(self, tmp_path):
        """A fully-valid explicit `events: {}` override still disables."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events: {}\n",
            encoding="utf-8",
        )
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        assert result == {}

    def test_empty_handler_override_abandons_override(self, tmp_path):
        """C4: a malformed handler (`stop: []` or `stop: bad-value`) abandons
        the whole override and keeps prior layers, rather than disabling."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events:\n"
            "      stop: []\n",
            encoding="utf-8",
        )
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        # Built-in default survived (override abandoned on the empty handler).
        assert "post_tool_use" in result

    def test_non_mapping_integration_entry_abandons_override(self, tmp_path):
        """C6: a non-mapping integration entry (`claude: bad`) is ignored as
        malformed, not treated as a valid explicit disable."""
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "integrations:\n"
            "  claude: bad\n",
            encoding="utf-8",
        )
        result = resolve_events(
            "claude",
            {"events": {"post_tool_use": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            None,
        )
        # Built-in default survived (override ignored as malformed).
        assert "post_tool_use" in result


# -- Matcher string validation (C10) -----------------------------------------

class TestMatcherValidation:
    """C10: matcher must be a string; a non-string matcher is rejected at
    validation time so it can't crash by_matcher.setdefault later."""

    def test_non_string_matcher_rejected_in_manifest(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": "speckit.x.y", "matcher": []}}}
        with pytest.raises(ValidationError, match="(?i)matcher.*string"):
            validate_events(data)

    def test_non_string_matcher_rejected_in_override(self, tmp_path):
        override_file = tmp_path / ".specify" / "integration-events.yml"
        override_file.parent.mkdir(parents=True, exist_ok=True)
        # A matcher of [] would crash by_matcher.setdefault; the override must
        # be abandoned (built-in defaults survive) rather than crash.
        override_file.write_text(
            "integrations:\n"
            "  claude:\n"
            "    events:\n"
            "      pre_tool_use:\n"
            "        command: speckit.x.y\n"
            "        matcher: []\n",
            encoding="utf-8",
        )
        result = resolve_events(
            "claude",
            {"events": {"stop": {"command": "speckit.end"}}},
            tmp_path,
            None,
        )
        # Built-in default survived (override abandoned on the bad matcher).
        assert "stop" in result


class TestTimeoutValidation:
    """Validate that non-integer, boolean, or non-positive timeouts are rejected."""

    def test_non_int_timeout_rejected_in_manifest(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": "speckit.x.y", "timeout": "60"}}}
        with pytest.raises(ValidationError, match="(?i)timeout.*positive integer"):
            validate_events(data)

    def test_boolean_timeout_rejected_in_manifest(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": "speckit.x.y", "timeout": True}}}
        with pytest.raises(ValidationError, match="(?i)timeout.*positive integer"):
            validate_events(data)

    def test_zero_or_negative_timeout_rejected_in_manifest(self):
        from specify_cli.extensions import ValidationError
        data = {"events": {"pre_tool_use": {"command": "speckit.x.y", "timeout": 0}}}
        with pytest.raises(ValidationError, match="(?i)timeout.*positive integer"):
            validate_events(data)


# -- Event command-ref canonicalization (C11) --------------------------------

class TestEventCommandRefCanonicalization:
    """C11: an event referencing a command that was auto-corrected is itself
    rewritten to the canonical name (mirrors hook reference rewriting)."""

    def test_event_command_ref_lifted_to_canonical(self, tmp_path):
        from specify_cli.extensions import ExtensionManifest
        import yaml as _yaml

        manifest_path = tmp_path / "extension.yml"
        manifest_path.write_text(
            _yaml.dump({
                "schema_version": "1.0",
                "extension": {
                    "id": "my-ext",
                    "name": "My Ext",
                    "version": "1.0.0",
                    "description": "test",
                },
                "requires": {"speckit_version": ">=0.1"},
                "provides": {
                    "commands": [
                        {"name": "speckit.my-ext.boot", "file": "commands/boot.md"}
                    ]
                },
                "events": {
                    "session_start": {"command": "my-ext.boot"},
                },
            }),
            encoding="utf-8",
        )
        manifest = ExtensionManifest(manifest_path)
        assert manifest.data["events"]["session_start"]["command"] == "speckit.my-ext.boot"
        assert any(
            "Event 'session_start' referenced command 'my-ext.boot'" in w
            for w in manifest.warnings
        )


# -- Skipped-merge not tracked (S5) ------------------------------------------

class TestSkippedMergeNotTracked:
    """S5: when a merge is skipped on parse failure, the untouched file is
    not recorded in the manifest, so uninstall() won't later delete it."""

    def test_jsonc_native_config_not_tracked(self, tmp_path):
        integration = ClaudeIntegration()
        config_path = tmp_path / ".claude/settings.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        jsonc = '{\n  // my comment\n  "hooks": {}\n}\n'
        config_path.write_text(jsonc)

        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        manifest.remove = MagicMock()

        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        # The JSONC file must NOT have been recorded (would cause uninstall()
        # to delete it later). Only the dispatcher (which we wrote) is tracked.
        recorded_rels = [c.args[0] for c in manifest.record_existing.call_args_list]
        assert str(config_path.relative_to(tmp_path)) not in recorded_rels
        # User content preserved verbatim.
        assert config_path.read_text() == jsonc


# -- Dispatcher manifest claim dropped on retain (S1) ------------------------

class TestDispatcherManifestClaimDroppedOnRetain:
    """S1: when the dispatcher is retained (another integration references
    it), this integration's manifest still drops its claim so the subsequent
    manifest.uninstall() in teardown() doesn't delete the shared file."""

    def test_full_teardown_keeps_dispatcher_when_other_references_it(self, tmp_path):
        from specify_cli.integrations.codex import CodexIntegration
        from specify_cli.integrations.manifest import IntegrationManifest

        claude = ClaudeIntegration()
        codex = CodexIntegration()

        # Install claude's events (writes dispatcher + claude config).
        claude_manifest = IntegrationManifest(claude.key, tmp_path, version="test")
        install_integration_events(
            claude, tmp_path, claude_manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        claude_manifest.save()

        # Install codex's events (re-writes shared dispatcher + codex config).
        codex_manifest = IntegrationManifest(codex.key, tmp_path, version="test")
        install_integration_events(
            codex, tmp_path, codex_manifest,
            {"pre_tool_use": [{"command": "speckit.codex.check"}]},
        )
        codex_manifest.save()

        # integration.json: both installed, codex is default.
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "codex",
            "installed_integrations": ["claude", "codex"],
        }))

        dispatcher_path = tmp_path / EVENTS_DISPATCHER_REL
        assert dispatcher_path.exists()

        # Full teardown of claude (remove + manifest.uninstall): the dispatcher
        # must survive because codex's manifest still references it.
        remove_integration_events(claude, tmp_path, claude_manifest)
        claude_manifest.uninstall(tmp_path, force=True)

        assert dispatcher_path.exists(), (
            "Shared dispatcher was deleted by teardown() despite another "
            "integration referencing it (S1)."
        )

    def test_empty_map_upgrade_deletes_dispatcher_for_last_integration(self, tmp_path):
        """S3: an --events false upgrade (empty resolved map) of the last
        event-capable integration deletes the shared dispatcher instead of
        orphaning it (the new manifest wouldn't claim it and stale cleanup
        excludes it)."""
        from specify_cli.integrations.codex import CodexIntegration
        from specify_cli.integrations.manifest import IntegrationManifest

        claude = ClaudeIntegration()
        codex = CodexIntegration()
        # Install both so the dispatcher is shared.
        cm = IntegrationManifest(claude.key, tmp_path, version="test")
        install_integration_events(claude, tmp_path, cm, {"pre_tool_use": [{"command": "speckit.x"}]})
        cm.save()
        xm = IntegrationManifest(codex.key, tmp_path, version="test")
        install_integration_events(codex, tmp_path, xm, {"pre_tool_use": [{"command": "speckit.y"}]})
        xm.save()
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "codex",
            "installed_integrations": ["claude", "codex"],
        }))
        dispatcher_path = tmp_path / EVENTS_DISPATCHER_REL
        assert dispatcher_path.exists()

        # Codex upgrades to --events false (empty map): claude still references
        # the dispatcher, so it must be retained.
        install_integration_events(codex, tmp_path, xm, {})
        xm.save()
        assert dispatcher_path.exists(), "Dispatcher deleted while claude still references it."

        # Now claude also goes --events false: no integration references the
        # dispatcher, so it must be deleted (not orphaned).
        install_integration_events(claude, tmp_path, cm, {})
        cm.save()
        assert not dispatcher_path.exists(), (
            "Dispatcher orphaned after the last event integration disabled events (S3)."
        )

    def test_fresh_manifest_upgrade_deletes_dispatcher_when_last(self, tmp_path):
        """S2: an upgrade passing a *fresh* manifest (that never recorded the
        dispatcher) still deletes the shared dispatcher when no other
        integration references it — the deletion isn't gated on the new
        manifest's claim."""
        from specify_cli.integrations.manifest import IntegrationManifest

        claude = ClaudeIntegration()
        # Install claude with an old manifest that records the dispatcher.
        old = IntegrationManifest(claude.key, tmp_path, version="test")
        install_integration_events(claude, tmp_path, old, {"pre_tool_use": [{"command": "speckit.x"}]})
        old.save()
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude"],
        }))
        dispatcher_path = tmp_path / EVENTS_DISPATCHER_REL
        assert dispatcher_path.exists()

        # Simulate the upgrade path: a fresh manifest (like
        # IntegrationManifest(key, project_root, version=...) in
        # _migrate_commands) that never recorded the dispatcher.
        fresh = IntegrationManifest(claude.key, tmp_path, version="test")
        assert EVENTS_DISPATCHER_REL not in fresh.files
        install_integration_events(claude, tmp_path, fresh, {})

        # The dispatcher must be deleted (no other integration references it),
        # not orphaned just because the fresh manifest didn't claim it.
        assert not dispatcher_path.exists(), (
            "Dispatcher orphaned after upgrade with a fresh manifest (S2)."
        )


# -- Dispatcher stale-cleanup exclusion (C3) ---------------------------------

class TestDispatcherStaleExclusion:
    """C3: the shared dispatcher is excluded from the generic upgrade stale
    pass so an --events false upgrade doesn't delete it and break other
    installed event-capable integrations."""

    def test_dispatcher_in_stale_exclusions(self):
        from specify_cli.events import events_stale_exclusions
        exclusions = events_stale_exclusions("claude")
        assert EVENTS_DISPATCHER_REL in exclusions


# -- Cursor version-only stub deletion (C5) ----------------------------------

class TestCursorVersionOnlyStubDeletion:
    """C5: a Spec-Kit-created Cursor file retaining only {"version": 1} after
    all owned hooks are removed is deleted, not left as a generated stub."""

    def test_version_only_cursor_file_deleted_on_teardown(self, tmp_path):
        integration = CursorAgentIntegration()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        manifest.remove = MagicMock()

        install_integration_events(
            integration, tmp_path, manifest,
            {"session_start": [{"command": "speckit.boot"}]},
        )
        config_path = tmp_path / ".cursor/hooks.json"
        assert config_path.is_file()
        assert json.loads(config_path.read_text()).get("version") == 1

        remove_integration_events(integration, tmp_path, manifest)
        # No user content remained (only the Spec-Kit-managed version field) →
        # the file is deleted for a clean teardown, not left as a stub.
        assert not config_path.exists()


# -- Non-destructive refresh (C12) -------------------------------------------

class TestNonDestructiveRefresh:
    """C12: refresh resolves first then installs once; a failure during install
    no longer destroys the working native config before the new one is written."""

    def test_refresh_failure_preserves_existing_config(self, tmp_path):
        from specify_cli.events import refresh_integration_events
        from specify_cli.integrations.manifest import IntegrationManifest

        integration = ClaudeIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path, version="test")
        install_integration_events(
            integration, tmp_path, manifest,
            {"pre_tool_use": [{"command": "speckit.tdd.validate"}]},
        )
        manifest.save()
        config_path = tmp_path / ".claude/settings.json"
        original = config_path.read_text()

        # Declare an extension event so refresh would try to re-emit.
        ext_dir = tmp_path / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(
            "events:\n  session_start:\n    command: speckit.my-ext.boot\n",
            encoding="utf-8",
        )
        state_path = tmp_path / ".specify" / "integration.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "default_integration": "claude",
            "installed_integrations": ["claude"],
        }))

        # Force install_integration_events to fail mid-refresh. R3: the
        # failure is now surfaced as EventRefreshError (aggregated) rather
        # than silently swallowed.
        from specify_cli.events import EventRefreshError
        with patch(
            "specify_cli.events.install_integration_events",
            side_effect=RuntimeError("simulated write failure"),
        ):
            with pytest.raises(EventRefreshError, match="simulated write failure"):
                refresh_integration_events(tmp_path)

        # The pre-existing config was NOT destroyed before the failure
        # (install handles cleanup atomically; refresh no longer pre-strips).
        assert config_path.read_text() == original
