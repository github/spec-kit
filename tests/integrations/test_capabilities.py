"""Unit tests for the capability processor module.

Covers:
- resolve_tool_references (T010)
- resolve_conditionals (T011)
- validate_syntax (T012)
- resolve_capabilities (T013)
- post_process_command_content default (T026)
"""

import logging

import pytest

from specify_cli.integrations._capabilities import (
    CapabilitySyntaxError,
    resolve_capabilities,
    resolve_conditionals,
    resolve_tool_references,
    validate_syntax,
)
from specify_cli.integrations.base import IntegrationBase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_capabilities():
    """Capabilities dict with multiple entries and sub-properties."""
    return {
        "interactive_prompts": {
            "tool": "AskUserQuestion",
            "structured": True,
            "multi_select": True,
        },
        "subagents": {
            "tool": "Agent",
            "background": True,
            "worktree_isolation": True,
        },
        "process_enforcement": {
            "tool": "enforce",
            "hooks": True,
            "pre_tool_gate": True,
        },
        "context_clearing": {
            "tool": "/clear",
        },
    }


@pytest.fixture
def partial_capabilities():
    """Capabilities dict with only interactive_prompts."""
    return {
        "interactive_prompts": {
            "tool": "question",
            "structured": True,
            "multi_select": False,
        },
    }


@pytest.fixture
def empty_capabilities():
    """Empty capabilities dict (no capabilities declared)."""
    return {}


# ---------------------------------------------------------------------------
# T010: resolve_tool_references
# ---------------------------------------------------------------------------

class TestResolveToolReferences:
    """Tests for {{tool:capability_name}} substitution."""

    def test_known_capability_resolves_to_tool_name(self, full_capabilities):
        content = "Use {{tool:interactive_prompts}} to ask."
        result = resolve_tool_references(content, full_capabilities)
        assert result == "Use AskUserQuestion to ask."

    def test_multiple_tool_references(self, full_capabilities):
        content = "{{tool:interactive_prompts}} and {{tool:subagents}}"
        result = resolve_tool_references(content, full_capabilities)
        assert result == "AskUserQuestion and Agent"

    def test_unknown_capability_resolves_to_empty_string(self, full_capabilities, caplog):
        content = "Use {{tool:nonexistent}} here."
        with caplog.at_level(logging.WARNING):
            result = resolve_tool_references(content, full_capabilities)
        assert result == "Use  here."
        assert "nonexistent" in caplog.text

    def test_empty_capabilities_resolves_all_to_empty(self, empty_capabilities, caplog):
        content = "{{tool:interactive_prompts}} and {{tool:subagents}}"
        with caplog.at_level(logging.WARNING):
            result = resolve_tool_references(content, empty_capabilities)
        assert result == " and "

    def test_no_tool_references_returns_unchanged(self, full_capabilities):
        content = "No capability references here."
        result = resolve_tool_references(content, full_capabilities)
        assert result == content

    def test_context_clearing_tool(self, full_capabilities):
        content = "Run {{tool:context_clearing}} to reset."
        result = resolve_tool_references(content, full_capabilities)
        assert result == "Run /clear to reset."


# ---------------------------------------------------------------------------
# T011: resolve_conditionals
# ---------------------------------------------------------------------------

class TestResolveConditionals:
    """Tests for {{#if}}...{{else}}...{{/if}} block processing."""

    def test_simple_if_true(self, full_capabilities):
        content = "{{#if interactive_prompts}}Has prompts{{/if}}"
        result = resolve_conditionals(content, full_capabilities)
        assert result == "Has prompts"

    def test_simple_if_false(self, empty_capabilities):
        content = "{{#if interactive_prompts}}Has prompts{{/if}}"
        result = resolve_conditionals(content, empty_capabilities)
        assert result == ""

    def test_if_else_true_branch(self, full_capabilities):
        content = "{{#if subagents}}parallel{{else}}sequential{{/if}}"
        result = resolve_conditionals(content, full_capabilities)
        assert result == "parallel"

    def test_if_else_false_branch(self, empty_capabilities):
        content = "{{#if subagents}}parallel{{else}}sequential{{/if}}"
        result = resolve_conditionals(content, empty_capabilities)
        assert result == "sequential"

    def test_nested_conditionals(self, full_capabilities):
        content = (
            "{{#if interactive_prompts}}"
            "Prompts: {{#if interactive_prompts.multi_select}}multi{{else}}single{{/if}}"
            "{{/if}}"
        )
        result = resolve_conditionals(content, full_capabilities)
        assert result == "Prompts: multi"

    def test_nested_conditional_false_sub_property(self, partial_capabilities):
        content = (
            "{{#if interactive_prompts}}"
            "Prompts: {{#if interactive_prompts.multi_select}}multi{{else}}single{{/if}}"
            "{{/if}}"
        )
        result = resolve_conditionals(content, partial_capabilities)
        assert result == "Prompts: single"

    def test_dotted_sub_property_true(self, full_capabilities):
        content = "{{#if subagents.background}}bg{{/if}}"
        result = resolve_conditionals(content, full_capabilities)
        assert result == "bg"

    def test_dotted_sub_property_false(self, partial_capabilities):
        content = "{{#if subagents.background}}bg{{/if}}"
        result = resolve_conditionals(content, partial_capabilities)
        assert result == ""

    def test_missing_capability_evaluates_false(self, full_capabilities):
        content = "{{#if nonexistent}}yes{{else}}no{{/if}}"
        result = resolve_conditionals(content, full_capabilities)
        assert result == "no"

    def test_multiline_conditional(self, full_capabilities):
        content = (
            "Before\n"
            "{{#if subagents}}\n"
            "Use parallel agents\n"
            "{{else}}\n"
            "Run sequentially\n"
            "{{/if}}\n"
            "After"
        )
        result = resolve_conditionals(content, full_capabilities)
        assert "Use parallel agents" in result
        assert "Run sequentially" not in result
        assert "Before" in result
        assert "After" in result

    def test_preserves_non_capability_content(self, full_capabilities):
        content = "Regular text with no conditionals."
        result = resolve_conditionals(content, full_capabilities)
        assert result == content


# ---------------------------------------------------------------------------
# T012: validate_syntax
# ---------------------------------------------------------------------------

class TestValidateSyntax:
    """Tests for template syntax validation."""

    def test_valid_syntax_no_errors(self):
        content = "{{#if cap}}content{{else}}fallback{{/if}}"
        errors = validate_syntax(content)
        assert errors == []

    def test_valid_nested_syntax(self):
        content = "{{#if a}}{{#if b}}inner{{/if}}outer{{/if}}"
        errors = validate_syntax(content)
        assert errors == []

    def test_unmatched_if_returns_error(self):
        content = "{{#if cap}}content but no close"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "no matching {{/if}}" in errors[0]

    def test_orphaned_else_returns_error(self):
        content = "{{else}} without if"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "without matching {{#if}}" in errors[0]

    def test_missing_endif_returns_error(self):
        content = "{{#if cap}}content"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "no matching {{/if}}" in errors[0]

    def test_extra_endif_returns_error(self):
        content = "{{/if}} extra close"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "without matching {{#if}}" in errors[0]

    def test_error_messages_include_line_context(self):
        content = "line1\n{{#if cap}}\nline3"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "Line 2" in errors[0]

    def test_no_capability_syntax_is_valid(self):
        content = "Just regular text, no capability refs."
        errors = validate_syntax(content)
        assert errors == []

    def test_duplicate_else_returns_error(self):
        content = "{{#if cap}}a{{else}}b{{else}}c{{/if}}"
        errors = validate_syntax(content)
        assert len(errors) == 1
        assert "duplicate" in errors[0]


# ---------------------------------------------------------------------------
# T013: resolve_capabilities (full pipeline)
# ---------------------------------------------------------------------------

class TestResolveCapabilities:
    """Tests for the main resolve_capabilities entry point."""

    def test_full_pipeline(self, full_capabilities):
        content = (
            "Use {{tool:interactive_prompts}} for input.\n"
            "{{#if subagents}}Fan out work{{else}}Execute sequentially{{/if}}"
        )
        result = resolve_capabilities(content, full_capabilities)
        assert "AskUserQuestion" in result
        assert "Fan out work" in result
        assert "Execute sequentially" not in result

    def test_raises_on_malformed_syntax(self):
        content = "{{#if cap}}missing close"
        with pytest.raises(CapabilitySyntaxError) as exc_info:
            resolve_capabilities(content, {})
        assert len(exc_info.value.errors) > 0

    def test_empty_capabilities_produces_clean_output(self, empty_capabilities):
        content = (
            "{{#if subagents}}parallel{{else}}sequential{{/if}} "
            "with {{tool:interactive_prompts}}"
        )
        result = resolve_capabilities(content, empty_capabilities)
        assert "{{#if" not in result
        assert "{{tool:" not in result
        assert "sequential" in result

    def test_no_capability_syntax_passes_through(self, full_capabilities):
        content = "Regular content without any capability syntax."
        result = resolve_capabilities(content, full_capabilities)
        assert result == content

    def test_combined_conditionals_and_tools(self, partial_capabilities):
        content = (
            "{{#if interactive_prompts}}"
            "Ask with {{tool:interactive_prompts}}"
            "{{/if}}"
            "{{#if subagents}}"
            "Dispatch via {{tool:subagents}}"
            "{{/if}}"
        )
        result = resolve_capabilities(content, partial_capabilities)
        assert "Ask with question" in result
        assert "Dispatch" not in result


# ---------------------------------------------------------------------------
# T026: post_process_command_content default
# ---------------------------------------------------------------------------

class TestPostProcessCommandContent:
    """Tests for the generalized post-processing hook."""

    def test_default_returns_content_unchanged(self):
        """IntegrationBase.post_process_command_content() is a no-op by default."""
        from specify_cli.integrations.base import MarkdownIntegration

        class StubIntegration(MarkdownIntegration):
            key = "stub"
            config = {"name": "Stub", "folder": ".stub/", "commands_subdir": "cmds"}
            registrar_config = {"dir": ".stub/cmds", "format": "markdown",
                                "args": "$ARGUMENTS", "extension": ".md"}

        integration = StubIntegration()
        content = "Some command content here."
        assert integration.post_process_command_content(content) == content
