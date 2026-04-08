# tests/test_behavior_translator.py
import pytest
from specify_cli.behavior import translate_behavior, strip_behavior_keys, get_deployment_type, get_copilot_tools


class TestTranslateBehavior:
    def test_execution_isolated_claude(self):
        result = translate_behavior("claude", {"execution": "isolated"})
        assert result == {"context": "fork"}

    def test_execution_agent_claude_no_frontmatter_key(self):
        # 'agent' execution type is handled by routing, not frontmatter
        result = translate_behavior("claude", {"execution": "agent"})
        assert "context" not in result

    def test_capability_strong_claude(self):
        result = translate_behavior("claude", {"capability": "strong"})
        assert result == {"model": "claude-opus-4-6"}

    def test_capability_fast_claude(self):
        result = translate_behavior("claude", {"capability": "fast"})
        assert result == {"model": "claude-haiku-4-5-20251001"}

    def test_effort_high_claude(self):
        result = translate_behavior("claude", {"effort": "high"})
        assert result == {"effort": "high"}

    def test_tools_read_only_claude(self):
        result = translate_behavior("claude", {"tools": "read-only"})
        assert result == {"allowed-tools": "Read Grep Glob"}

    def test_tools_none_claude(self):
        result = translate_behavior("claude", {"tools": "none"})
        assert result == {"allowed-tools": ""}

    def test_tools_full_claude_no_injection(self):
        result = translate_behavior("claude", {"tools": "full"})
        assert "allowed-tools" not in result

    def test_invocation_explicit_claude(self):
        result = translate_behavior("claude", {"invocation": "explicit"})
        assert result == {"disable-model-invocation": True}

    def test_invocation_automatic_claude(self):
        result = translate_behavior("claude", {"invocation": "automatic"})
        assert result == {"disable-model-invocation": False}

    def test_visibility_model_claude(self):
        result = translate_behavior("claude", {"visibility": "model"})
        assert result == {"user-invocable": False}

    def test_execution_agent_copilot(self):
        result = translate_behavior("copilot", {"execution": "agent"})
        assert result == {"mode": "agent"}

    def test_unknown_key_ignored(self):
        result = translate_behavior("claude", {"unknown-key": "value"})
        assert result == {}

    def test_unsupported_agent_returns_empty(self):
        result = translate_behavior("gemini", {"execution": "isolated"})
        assert result == {}

    def test_agents_escape_hatch_applied(self):
        result = translate_behavior(
            "claude",
            {"capability": "fast"},
            agents_overrides={"claude": {"model": "claude-opus-4-6", "paths": "src/**"}},
        )
        assert result["model"] == "claude-opus-4-6"
        assert result["paths"] == "src/**"

    def test_agents_escape_hatch_other_agent_ignored(self):
        result = translate_behavior(
            "claude",
            {},
            agents_overrides={"codex": {"effort": "high"}},
        )
        assert result == {}

    def test_multiple_behavior_keys(self):
        result = translate_behavior("claude", {
            "execution": "isolated",
            "capability": "strong",
            "effort": "max",
            "invocation": "explicit",
        })
        assert result["context"] == "fork"
        assert result["model"] == "claude-opus-4-6"
        assert result["effort"] == "max"
        assert result["disable-model-invocation"] is True


class TestStripBehaviorKeys:
    def test_strips_behavior(self):
        fm = {"name": "foo", "behavior": {"execution": "isolated"}, "description": "bar"}
        result = strip_behavior_keys(fm)
        assert "behavior" not in result
        assert result["name"] == "foo"

    def test_strips_agents(self):
        fm = {"name": "foo", "agents": {"claude": {"paths": "src/**"}}}
        result = strip_behavior_keys(fm)
        assert "agents" not in result

    def test_no_behavior_keys_passthrough(self):
        fm = {"name": "foo", "description": "bar"}
        result = strip_behavior_keys(fm)
        assert result == {"name": "foo", "description": "bar"}

    def test_returns_copy_not_mutating_original(self):
        fm = {"behavior": {"execution": "isolated"}}
        result = strip_behavior_keys(fm)
        assert "behavior" in fm  # original unchanged


class TestGetDeploymentType:
    def test_behavior_execution_agent(self):
        assert get_deployment_type({"behavior": {"execution": "agent"}}) == "agent"

    def test_behavior_execution_isolated_is_command(self):
        assert get_deployment_type({"behavior": {"execution": "isolated"}}) == "command"

    def test_behavior_execution_command_is_command(self):
        assert get_deployment_type({"behavior": {"execution": "command"}}) == "command"

    def test_defaults_to_command_when_no_behavior(self):
        assert get_deployment_type({}) == "command"

    def test_defaults_to_command_when_no_execution(self):
        assert get_deployment_type({"behavior": {"capability": "strong"}}) == "command"


class TestGetCopilotTools:
    def test_read_only_returns_tools(self):
        result = get_copilot_tools({"tools": "read-only"})
        assert "read_file" in result
        assert "list_directory" in result

    def test_full_returns_empty(self):
        result = get_copilot_tools({"tools": "full"})
        assert result == []

    def test_none_returns_empty(self):
        result = get_copilot_tools({"tools": "none"})
        assert result == []

    def test_missing_tools_defaults_to_full(self):
        result = get_copilot_tools({})
        assert result == []
