"""Tests for _hooks module: integration runtime hooks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from specify_cli.integrations._hooks import (
    ClaudeHookAdapter,
    CodexHookAdapter,
    CursorHookAdapter,
    DevinHookAdapter,
    GeminiHookAdapter,
    HookAdapter,
    JSONHookAdapter,
    OpencodeHookAdapter,
    QwenHookAdapter,
    TabnineHookAdapter,
    _has_marker,
    _to_camel_case,
    CANONICAL_RUNTIME_EVENTS,
    collect_extension_runtime_hooks,
    hooks_stale_exclusions,
    install_integration_hooks,
    remove_integration_hooks,
    resolve_adapter,
    resolve_hooks,
    validate_runtime_hooks,
)
from specify_cli.integrations.manifest import IntegrationManifest


# -- resolve_hooks --------------------------------------------------------

class TestResolveHooks:
    """Test the 4-layer hook resolution chain."""

    def test_layer1_disabled_returns_empty(self, tmp_path):
        """--hooks false returns empty dict."""
        result = resolve_hooks(
            "claude",
            {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate"}}},
            tmp_path,
            {"hooks": "false"},
        )
        assert result == {}

    def test_layer4_built_in_defaults(self, tmp_path):
        """Built-in config hooks are returned when no override."""
        config = {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write"}}}
        result = resolve_hooks("claude", config, tmp_path, None)
        assert "PostToolUse" in result
        assert result["PostToolUse"]["command"] == "speckit.tdd.validate"

    def test_layer3_extension_hooks_appended(self, tmp_path):
        """Extension-declared runtime_hooks are appended to built-in."""
        ext_dir = tmp_path / ".specify" / "extensions" / "myext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(yaml.dump({
            "schema_version": "1.0",
            "extension": {"id": "myext", "name": "My Ext", "version": "1.0.0",
                          "description": "test"},
            "requires": {"speckit_version": ">=0.0.80"},
            "provides": {"commands": []},
            "runtime_hooks": {
                "Stop": {"command": "speckit.myext.check", "matcher": "*"},
            },
        }))
        config = {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate"}}}
        result = resolve_hooks("claude", config, tmp_path, None)
        assert "PostToolUse" in result
        assert "Stop" in result
        assert result["Stop"]["command"] == "speckit.myext.check"

    def test_layer2_yaml_override_replaces(self, tmp_path):
        """YAML override replaces built-in and extension hooks entirely."""
        override_file = tmp_path / ".specify" / "integration-hooks.yml"
        override_file.parent.mkdir(parents=True)
        override_file.write_text(yaml.dump({
            "version": 1,
            "integrations": {
                "claude": {
                    "hooks": {
                        "PreToolUse": {"command": "speckit.protected_paths", "matcher": "Edit|Write"},
                    },
                },
            },
        }))
        config = {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate"}}}
        result = resolve_hooks("claude", config, tmp_path, None)
        assert "PreToolUse" in result
        assert "PostToolUse" not in result  # replaced, not merged

    def test_layer2_empty_hooks_disables(self, tmp_path):
        """Empty hooks: {} in YAML override disables all hooks."""
        override_file = tmp_path / ".specify" / "integration-hooks.yml"
        override_file.parent.mkdir(parents=True)
        override_file.write_text(yaml.dump({
            "version": 1,
            "integrations": {"claude": {"hooks": {}}},
        }))
        config = {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate"}}}
        result = resolve_hooks("claude", config, tmp_path, None)
        assert result == {}

    def test_no_config_no_hooks(self, tmp_path):
        """No config, no extensions, no override → empty."""
        result = resolve_hooks("gemini", None, tmp_path, None)
        assert result == {}


# -- collect_extension_runtime_hooks --------------------------------------

class TestCollectExtensionRuntimeHooks:
    """Test scanning installed extensions for runtime_hooks."""

    def test_no_extensions_dir(self, tmp_path):
        assert collect_extension_runtime_hooks(tmp_path) == {}

    def test_no_runtime_hooks_in_extension(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "myext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(yaml.dump({
            "schema_version": "1.0",
            "extension": {"id": "myext", "name": "My Ext", "version": "1.0.0",
                          "description": "test"},
            "requires": {"speckit_version": ">=0.0.80"},
            "provides": {"commands": [{"name": "speckit.myext.cmd", "file": "cmd.md"}]},
            "hooks": {"after_plan": {"command": "speckit.myext.cmd"}},
        }))
        result = collect_extension_runtime_hooks(tmp_path)
        assert result == {}

    def test_runtime_hooks_collected(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "tdd"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(yaml.dump({
            "schema_version": "1.0",
            "extension": {"id": "tdd", "name": "TDD", "version": "1.0.0",
                          "description": "test"},
            "requires": {"speckit_version": ">=0.0.80"},
            "provides": {"commands": []},
            "runtime_hooks": {
                "PostToolUse": {"command": "adlc.tdd.validate", "matcher": "Edit|Write"},
                "Stop": {"command": "adlc.tdd.validate", "matcher": "*"},
            },
        }))
        result = collect_extension_runtime_hooks(tmp_path)
        assert "PostToolUse" in result
        assert "Stop" in result
        assert result["PostToolUse"]["command"] == "adlc.tdd.validate"

    def test_invalid_yaml_skipped(self, tmp_path):
        ext_dir = tmp_path / ".specify" / "extensions" / "broken"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text("{{invalid yaml")
        result = collect_extension_runtime_hooks(tmp_path)
        assert result == {}


# -- Adapter resolution ---------------------------------------------------

class TestResolveAdapter:
    """Test adapter registry."""

    def test_claude_returns_adapter(self):
        adapter = resolve_adapter("claude")
        assert isinstance(adapter, ClaudeHookAdapter)

    def test_cursor_returns_adapter(self):
        adapter = resolve_adapter("cursor-agent")
        assert isinstance(adapter, CursorHookAdapter)

    def test_codex_returns_adapter(self):
        adapter = resolve_adapter("codex")
        assert isinstance(adapter, CodexHookAdapter)

    def test_opencode_returns_adapter(self):
        adapter = resolve_adapter("opencode")
        assert isinstance(adapter, OpencodeHookAdapter)

    def test_gemini_returns_adapter(self):
        adapter = resolve_adapter("gemini")
        assert isinstance(adapter, GeminiHookAdapter)

    def test_qwen_returns_adapter(self):
        adapter = resolve_adapter("qwen")
        assert isinstance(adapter, QwenHookAdapter)

    def test_devin_returns_adapter(self):
        adapter = resolve_adapter("devin")
        assert isinstance(adapter, DevinHookAdapter)

    def test_tabnine_returns_adapter(self):
        adapter = resolve_adapter("tabnine")
        assert isinstance(adapter, TabnineHookAdapter)

    def test_copilot_returns_none(self):
        assert resolve_adapter("copilot") is None

    def test_unknown_returns_none(self):
        assert resolve_adapter("nonexistent") is None


# -- Canonical event mapping -----------------------------------------------

class TestCanonicalEventMapping:
    """Test canonical→native event name translation per adapter."""

    def test_claude_passthrough(self):
        adapter = ClaudeHookAdapter()
        assert adapter._native_event("PreToolUse") == "PreToolUse"
        assert adapter._native_event("PostToolUse") == "PostToolUse"
        assert adapter._native_event("Stop") == "Stop"

    def test_cursor_camelcase(self):
        adapter = CursorHookAdapter()
        assert adapter._native_event("PreToolUse") == "preToolUse"
        assert adapter._native_event("PostToolUse") == "postToolUse"
        assert adapter._native_event("UserPromptSubmit") == "beforeSubmitPrompt"

    def test_opencode_limited(self):
        adapter = OpencodeHookAdapter()
        assert adapter._native_event("PreToolUse") == "tool.execute.before"
        assert adapter._native_event("PostToolUse") == "tool.execute.after"
        assert adapter._native_event("Stop") is None  # unsupported

    def test_gemini_mapping(self):
        adapter = GeminiHookAdapter()
        assert adapter._native_event("PreToolUse") == "BeforeTool"
        assert adapter._native_event("PostToolUse") == "AfterTool"
        assert adapter._native_event("Stop") == "AfterAgent"

    def test_qwen_identity(self):
        adapter = QwenHookAdapter()
        assert adapter._native_event("PreToolUse") == "PreToolUse"

    def test_devin_identity(self):
        adapter = DevinHookAdapter()
        assert adapter._native_event("PreToolUse") == "PreToolUse"

    def test_tabnine_mapping(self):
        adapter = TabnineHookAdapter()
        assert adapter._native_event("PreToolUse") == "BeforeTool"
        assert adapter._native_event("PostToolUse") == "AfterTool"
        assert adapter._native_event("Stop") is None  # not supported


class TestUnknownEventRejection:
    """Test that validate_runtime_hooks rejects unknown event names."""

    def test_unknown_event_rejected(self):
        from specify_cli.extensions import ValidationError
        data = {
            "runtime_hooks": {
                "FooBar": {"command": "speckit.test"},
            },
        }
        with pytest.raises(ValidationError, match="Unknown runtime_hook 'FooBar'"):
            validate_runtime_hooks(data)

    def test_known_event_accepted(self):
        data = {
            "runtime_hooks": {
                "PostToolUse": {"command": "speckit.test"},
            },
        }
        validate_runtime_hooks(data)  # should not raise

    def test_all_canonical_events_accepted(self):
        for event in CANONICAL_RUNTIME_EVENTS:
            data = {"runtime_hooks": {event: {"command": "speckit.test"}}}
            validate_runtime_hooks(data)  # should not raise


class TestUnsupportedEventWarning:
    """Test that adapters warn and skip unsupported events."""

    def test_opencode_skips_stop(self, tmp_path, capsys):
        from specify_cli.integrations.manifest import IntegrationManifest
        adapter = OpencodeHookAdapter()
        manifest = IntegrationManifest("opencode", tmp_path)
        hooks = {
            "PostToolUse": {"command": "speckit.test", "matcher": "Edit|Write"},
            "Stop": {"command": "speckit.test", "matcher": "*"},
        }
        adapter.install(tmp_path, manifest, hooks)
        captured = capsys.readouterr()
        assert "Stop" in captured.err
        assert "skipping" in captured.err
        # Plugin should only have PostToolUse, not Stop
        plugin = tmp_path / ".opencode" / "plugin" / "speckit-hooks.ts"
        content = plugin.read_text()
        assert "tool.execute.after" in content
        assert "tool.execute.before" not in content

    def test_tabnine_skips_stop(self, tmp_path, capsys):
        adapter = TabnineHookAdapter()
        from specify_cli.integrations.manifest import IntegrationManifest
        manifest = IntegrationManifest("tabnine", tmp_path)
        hooks = {
            "PostToolUse": {"command": "speckit.test", "matcher": "Edit|Write"},
            "Stop": {"command": "speckit.test", "matcher": "*"},
        }
        adapter.install(tmp_path, manifest, hooks)
        captured = capsys.readouterr()
        assert "Stop" in captured.err
        settings = tmp_path / ".tabnine" / "agent" / "settings.json"
        data = json.loads(settings.read_text())
        assert "AfterTool" in data.get("hooks", {})
        assert "Stop" not in data.get("hooks", {})


# -- New adapter tests -----------------------------------------------------

class TestGeminiHookAdapter:

    def test_generate_fragment_uses_native_names(self):
        adapter = GeminiHookAdapter()
        hooks = {
            "PreToolUse": {"command": "speckit.test", "matcher": "Edit|Write", "timeout": 10},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert fmt == "json"
        assert "BeforeTool" in fragment["hooks"]
        assert "PreToolUse" not in fragment["hooks"]

    def test_install_creates_settings(self, tmp_path):
        from specify_cli.integrations.manifest import IntegrationManifest
        adapter = GeminiHookAdapter()
        manifest = IntegrationManifest("gemini", tmp_path)
        hooks = {"PostToolUse": {"command": "speckit.test", "matcher": "Edit|Write", "timeout": 60}}
        created = adapter.install(tmp_path, manifest, hooks)
        settings = tmp_path / ".gemini" / "settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "AfterTool" in data["hooks"]


class TestQwenHookAdapter:

    def test_generate_fragment_identity(self):
        adapter = QwenHookAdapter()
        hooks = {
            "PreToolUse": {"command": "speckit.test", "matcher": "Edit|Write", "timeout": 10},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert "PreToolUse" in fragment["hooks"]


class TestDevinHookAdapter:

    def test_install_creates_hooks_file(self, tmp_path):
        from specify_cli.integrations.manifest import IntegrationManifest
        adapter = DevinHookAdapter()
        manifest = IntegrationManifest("devin", tmp_path)
        hooks = {"PostToolUse": {"command": "speckit.test", "matcher": "Edit|Write", "timeout": 60}}
        created = adapter.install(tmp_path, manifest, hooks)
        hooks_file = tmp_path / ".devin" / "hooks.v1.json"
        assert hooks_file.exists()
        data = json.loads(hooks_file.read_text())
        assert "PostToolUse" in data["hooks"]


class TestTabnineHookAdapter:

    def test_generate_fragment_native_names(self):
        adapter = TabnineHookAdapter()
        hooks = {
            "PreToolUse": {"command": "speckit.test", "matcher": "Edit|Write", "timeout": 10},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert "BeforeTool" in fragment["hooks"]


# -- ClaudeHookAdapter ----------------------------------------------------

class TestClaudeHookAdapter:
    """Test Claude Code native config generation and merge."""

    def test_generate_fragment_structure(self):
        adapter = ClaudeHookAdapter()
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert fmt == "json"
        assert "hooks" in fragment
        assert "PostToolUse" in fragment["hooks"]
        entry_group = fragment["hooks"]["PostToolUse"][0]
        assert entry_group["matcher"] == "Edit|Write"
        handler = entry_group["hooks"][0]
        assert handler["type"] == "command"
        assert handler["command"] == "python3"
        assert "speckit.tdd.validate" in handler["args"]
        assert "PostToolUse" in handler["args"]
        assert handler["timeout"] == 60

    def test_merge_into_empty_file(self, tmp_path):
        adapter = ClaudeHookAdapter()
        config_path = tmp_path / ".claude" / "settings.json"
        config_path.parent.mkdir(parents=True)
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        fmt, fragment = adapter.generate_fragment(hooks, tmp_path)
        adapter.merge_fragment(config_path, fragment, format=fmt)
        data = json.loads(config_path.read_text())
        assert "hooks" in data
        assert "PostToolUse" in data["hooks"]
        assert len(data["hooks"]["PostToolUse"]) == 1

    def test_merge_preserves_user_keys(self, tmp_path):
        adapter = ClaudeHookAdapter()
        config_path = tmp_path / ".claude" / "settings.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({
            "model": "claude-sonnet-4-20250514",
            "permissions": {"allow": ["Bash(git *)"]},
            "hooks": {
                "PostToolUse": [{
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "/usr/bin/my-hook.sh"}],
                }],
            },
        }))
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        fmt, fragment = adapter.generate_fragment(hooks, tmp_path)
        adapter.merge_fragment(config_path, fragment, format=fmt)
        data = json.loads(config_path.read_text())
        assert data["model"] == "claude-sonnet-4-20250514"
        assert data["permissions"]["allow"] == ["Bash(git *)"]
        assert len(data["hooks"]["PostToolUse"]) == 2  # user hook + our hook

    def test_remove_entries_preserves_user_hooks(self, tmp_path):
        adapter = ClaudeHookAdapter()
        config_path = tmp_path / ".claude" / "settings.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({
            "hooks": {
                "PostToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/usr/bin/my-hook.sh"}]},
                    {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "python3",
                        "args": [".specify/hooks/bridge.py", "speckit.tdd.validate", "PostToolUse"],
                        "__speckit_hook__": True}]},
                ],
            },
        }))
        adapter.remove_entries(config_path)
        data = json.loads(config_path.read_text())
        assert len(data["hooks"]["PostToolUse"]) == 1
        assert data["hooks"]["PostToolUse"][0]["matcher"] == "Bash"


# -- CursorHookAdapter ----------------------------------------------------

class TestCursorHookAdapter:
    """Test Cursor native config generation."""

    def test_generate_fragment_camelcase(self):
        adapter = CursorHookAdapter()
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert "postToolUse" in fragment["hooks"]
        entry = fragment["hooks"]["postToolUse"][0]
        assert "python3" in entry["command"]
        assert entry["matcher"] == "Edit|Write"


# -- CodexHookAdapter -----------------------------------------------------

class TestCodexHookAdapter:
    """Test Codex TOML config generation."""

    def test_generate_fragment_toml(self):
        adapter = CodexHookAdapter()
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        fmt, fragment = adapter.generate_fragment(hooks, Path("/tmp"))
        assert fmt == "toml"
        assert "[[hooks.PostToolUse]]" in fragment
        assert 'matcher = "Edit|Write"' in fragment
        assert "speckit.tdd.validate" in fragment
        assert "speckit_marker = true" in fragment


# -- OpencodeHookAdapter --------------------------------------------------

class TestOpencodeHookAdapter:
    """Test opencode TS plugin generation."""

    def test_install_generates_plugin_and_merges_config(self, tmp_path):
        adapter = OpencodeHookAdapter()
        manifest = MagicMock(spec=IntegrationManifest)
        manifest.files = {}
        manifest.record_file = MagicMock()
        manifest.record_existing = MagicMock()
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        created = adapter.install(tmp_path, manifest, hooks)
        plugin_path = tmp_path / ".opencode/plugin/speckit-hooks.ts"
        assert plugin_path.exists()
        content = plugin_path.read_text()
        assert "tool.execute.after" in content
        assert "speckit.tdd.validate" in content
        config_path = tmp_path / "opencode.json"
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert "./.opencode/plugin/speckit-hooks.ts" in config["plugin"]

    def test_remove_removes_plugin_ref(self, tmp_path):
        adapter = OpencodeHookAdapter()
        config_path = tmp_path / "opencode.json"
        config_path.write_text(json.dumps({
            "plugin": ["./.opencode/plugin/speckit-hooks.ts", "./other.ts"],
        }))
        adapter.remove_entries(config_path)
        config = json.loads(config_path.read_text())
        assert "./.opencode/plugin/speckit-hooks.ts" not in config["plugin"]
        assert "./other.ts" in config["plugin"]


# -- Helpers --------------------------------------------------------------

class TestHelpers:
    def test_has_marker_true(self):
        assert _has_marker({"__speckit_hook__": True, "command": "foo"})

    def test_has_marker_false(self):
        assert not _has_marker({"command": "foo"})

    def test_to_camel_case(self):
        assert _to_camel_case("PostToolUse") == "postToolUse"
        assert _to_camel_case("PreToolUse") == "preToolUse"
        assert _to_camel_case("Stop") == "stop"
        assert _to_camel_case("") == ""


# -- hooks_stale_exclusions -----------------------------------------------

class TestStaleExclusions:
    def test_claude_returns_settings_path(self):
        exclusions = hooks_stale_exclusions("claude")
        assert ".claude/settings.json" in exclusions

    def test_opencode_returns_config_and_plugin(self):
        exclusions = hooks_stale_exclusions("opencode")
        assert "opencode.json" in exclusions
        assert ".opencode/plugin/speckit-hooks.ts" in exclusions

    def test_gemini_returns_settings_path(self):
        exclusions = hooks_stale_exclusions("gemini")
        assert ".gemini/settings.json" in exclusions

    def test_copilot_returns_empty(self):
        assert hooks_stale_exclusions("copilot") == set()


# -- Integration: install + remove round-trip -----------------------------

class TestInstallRemoveRoundTrip:
    """End-to-end install → remove for Claude adapter."""

    def test_claude_install_then_remove(self, tmp_path):
        from specify_cli.integrations._hooks import HOOK_BRIDGE_REL

        manifest = IntegrationManifest("claude", tmp_path)
        adapter = ClaudeHookAdapter()
        hooks = {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }
        created = adapter.install(tmp_path, manifest, hooks)
        assert len(created) == 2  # bridge + settings.json
        bridge = tmp_path / HOOK_BRIDGE_REL
        assert bridge.exists()
        settings = tmp_path / ".claude/settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "PostToolUse" in data["hooks"]

        # Remove
        adapter.remove(tmp_path, manifest)
        data = json.loads(settings.read_text())
        # Our entries removed, but file still exists
        assert "hooks" not in data or "PostToolUse" not in data.get("hooks", {})

    def test_group_b_no_crash(self, tmp_path):
        """Installing hooks for a Group B agent (no adapter) is a no-op."""
        mock_integration = MagicMock()
        mock_integration.key = "copilot"
        mock_integration.config = {"hooks": {"PostToolUse": {"command": "speckit.tdd.validate"}}}
        manifest = IntegrationManifest("gemini", tmp_path)
        result = install_integration_hooks(mock_integration, tmp_path, manifest, None)
        assert result == []

    def test_upgrade_removes_stale_events(self, tmp_path):
        """Upgrading from hook set A to hook set B removes stale events."""
        mock_integration = MagicMock()
        mock_integration.key = "claude"
        mock_integration.config = None
        (tmp_path / ".specify").mkdir(parents=True)

        # v1: install PostToolUse only
        mock_integration.config = {"hooks": {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }}
        manifest_v1 = IntegrationManifest("claude", tmp_path)
        install_integration_hooks(mock_integration, tmp_path, manifest_v1, None)
        settings = tmp_path / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        assert "PostToolUse" in data.get("hooks", {})

        # v2: upgrade to PreToolUse + Stop (no PostToolUse)
        mock_integration.config = {"hooks": {
            "PreToolUse": {"command": "speckit.protected_paths", "matcher": "Edit|Write", "timeout": 10},
            "Stop": {"command": "speckit.tdd.validate", "matcher": "*", "timeout": 30},
        }}
        manifest_v2 = IntegrationManifest("claude", tmp_path)
        install_integration_hooks(mock_integration, tmp_path, manifest_v2, None)
        data2 = json.loads(settings.read_text())
        hooks_v2 = data2.get("hooks", {})
        assert "PostToolUse" not in hooks_v2, "Stale PostToolUse should be removed on upgrade"
        assert "PreToolUse" in hooks_v2
        assert "Stop" in hooks_v2

    def test_upgrade_preserves_user_hooks(self, tmp_path):
        """User-defined hooks survive upgrade."""
        mock_integration = MagicMock()
        mock_integration.key = "claude"
        mock_integration.config = None
        (tmp_path / ".specify").mkdir(parents=True)

        # Pre-existing user hook
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text(json.dumps({
            "hooks": {
                "PostToolUse": [{
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "/usr/bin/my-linter.sh"}],
                }],
            },
        }))

        # Install our hook
        mock_integration.config = {"hooks": {
            "PostToolUse": {"command": "speckit.tdd.validate", "matcher": "Edit|Write", "timeout": 60},
        }}
        manifest = IntegrationManifest("claude", tmp_path)
        install_integration_hooks(mock_integration, tmp_path, manifest, None)
        data = json.loads((settings_dir / "settings.json").read_text())
        post_hooks = data["hooks"]["PostToolUse"]
        assert len(post_hooks) == 2  # user hook + our hook

        # Upgrade: change our hook to PreToolUse only
        mock_integration.config = {"hooks": {
            "PreToolUse": {"command": "speckit.protected_paths", "matcher": "Edit|Write", "timeout": 10},
        }}
        manifest_v2 = IntegrationManifest("claude", tmp_path)
        install_integration_hooks(mock_integration, tmp_path, manifest_v2, None)
        data2 = json.loads((settings_dir / "settings.json").read_text())
        hooks2 = data2.get("hooks", {})
        # User's PostToolUse hook should survive
        assert "PostToolUse" in hooks2
        user_entry = hooks2["PostToolUse"][0]
        assert user_entry["matcher"] == "Bash"
        # Our new PreToolUse should be present
        assert "PreToolUse" in hooks2
