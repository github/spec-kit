"""Integration tests for capability resolution in the register_commands pipeline.

Covers:
- T021: Tool substitution resolves correctly per agent
- T022: Conditional blocks resolve correctly per agent capabilities
- T023: Regression test - templates without capability syntax are unchanged
"""

import pytest

from specify_cli.agents import CommandRegistrar


@pytest.fixture
def registrar():
    return CommandRegistrar()


@pytest.fixture
def ext_with_capability_template(tmp_path):
    """Create a mock extension with a command template using capability syntax."""
    ext_dir = tmp_path / "extension"
    ext_dir.mkdir()
    cmd_dir = ext_dir / "commands"
    cmd_dir.mkdir()
    return ext_dir, cmd_dir


class TestToolSubstitution:
    """T021: {{tool:capability_name}} resolves to agent-specific tool names."""

    def test_claude_resolves_interactive_prompts(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "ask.md"
        cmd_file.write_text(
            "---\n"
            "description: Ask user a question\n"
            "---\n\n"
            "Use {{tool:interactive_prompts}} to ask the user.\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.ask", "file": "commands/ask.md"}]
        registered = registrar.register_commands(
            "claude", commands, "test-ext", ext_dir, tmp_path
        )
        assert "speckit.test.ask" in registered

        # Read the generated skill file
        skill_file = tmp_path / ".claude" / "skills" / "speckit-test-ask" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "AskUserQuestion" in content
        assert "{{tool:" not in content

    def test_opencode_resolves_interactive_prompts(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "ask.md"
        cmd_file.write_text(
            "---\n"
            "description: Ask user a question\n"
            "---\n\n"
            "Use {{tool:interactive_prompts}} to ask the user.\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.ask", "file": "commands/ask.md"}]
        registered = registrar.register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )
        assert "speckit.test.ask" in registered

        # Read the generated markdown file
        cmd_output = tmp_path / ".opencode" / "commands" / "speckit.test.ask.md"
        assert cmd_output.exists()
        content = cmd_output.read_text(encoding="utf-8")
        assert "question" in content
        assert "{{tool:" not in content


class TestConditionalBlocks:
    """T022: {{#if capability}} blocks resolve based on agent capabilities."""

    def test_claude_gets_true_branch(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "dispatch.md"
        cmd_file.write_text(
            "---\n"
            "description: Dispatch work\n"
            "---\n\n"
            "{{#if subagents}}Use parallel agents{{else}}Execute sequentially{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.dispatch", "file": "commands/dispatch.md"}]
        registrar.register_commands(
            "claude", commands, "test-ext", ext_dir, tmp_path
        )

        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-test-dispatch" / "SKILL.md"
        )
        content = skill_file.read_text(encoding="utf-8")
        assert "Use parallel agents" in content
        assert "Execute sequentially" not in content

    def test_gemini_gets_false_branch(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        """Gemini has empty capabilities, so conditionals evaluate to false."""
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "dispatch.md"
        cmd_file.write_text(
            "---\n"
            "description: Dispatch work\n"
            "---\n\n"
            "{{#if subagents}}Use parallel agents{{else}}Execute sequentially{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.dispatch", "file": "commands/dispatch.md"}]
        registrar.register_commands(
            "gemini", commands, "test-ext", ext_dir, tmp_path
        )

        cmd_output = tmp_path / ".gemini" / "commands" / "speckit.test.dispatch.toml"
        content = cmd_output.read_text(encoding="utf-8")
        assert "Execute sequentially" in content
        assert "Use parallel agents" not in content

    def test_opencode_has_subagents(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        """OpenCode declares subagents, so the true branch should appear."""
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "dispatch.md"
        cmd_file.write_text(
            "---\n"
            "description: Dispatch work\n"
            "---\n\n"
            "{{#if subagents}}Use parallel agents{{else}}Execute sequentially{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.dispatch", "file": "commands/dispatch.md"}]
        registrar.register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )

        cmd_output = tmp_path / ".opencode" / "commands" / "speckit.test.dispatch.md"
        content = cmd_output.read_text(encoding="utf-8")
        assert "Use parallel agents" in content
        assert "Execute sequentially" not in content


class TestPostProcessCommandContent:
    """T027: post_process_command_content() applies for non-skill agents."""

    def test_markdown_agent_post_process_applied(
        self, tmp_path, registrar, ext_with_capability_template, monkeypatch
    ):
        """Verify post_process_command_content runs for markdown-format agents."""
        from specify_cli.integrations import get_integration

        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "review.md"
        cmd_file.write_text(
            "---\n"
            "description: Review command\n"
            "---\n\n"
            "Review the code.\n",
            encoding="utf-8",
        )

        # Monkey-patch the opencode integration's post_process_command_content
        marker = "<!-- POST_PROCESSED -->"
        opencode = get_integration("opencode")
        original = opencode.__class__.post_process_command_content

        def _inject_marker(self, content):
            return content + marker

        monkeypatch.setattr(
            opencode.__class__, "post_process_command_content", _inject_marker
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        registrar.register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )

        cmd_output = (
            tmp_path / ".opencode" / "commands" / "speckit.test.review.md"
        )
        content = cmd_output.read_text(encoding="utf-8")
        assert marker in content


class TestPluginRoot:
    """T031: __PLUGIN_ROOT__ resolves to the source_dir path."""

    def test_plugin_root_replaced_in_output(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "run.md"
        cmd_file.write_text(
            "---\n"
            "description: Run a script\n"
            "---\n\n"
            'Execute "$__PLUGIN_ROOT__/scripts/run.sh"\n',
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.run", "file": "commands/run.md"}]
        registrar.register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )

        cmd_output = tmp_path / ".opencode" / "commands" / "speckit.test.run.md"
        content = cmd_output.read_text(encoding="utf-8")
        assert "__PLUGIN_ROOT__" not in content
        # The resolved path should point to the extension source directory
        assert str(ext_dir) in content or str(ext_dir.resolve()) in content


class TestRequiresCapabilities:
    """T034-T035: Extension manifest requires_capabilities warnings."""

    def test_missing_capability_emits_warning(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        """T034: requires_capabilities triggers warning for missing capabilities."""
        ext_dir, cmd_dir = ext_with_capability_template

        # Create extension.yml with requires_capabilities
        ext_yml = ext_dir / "extension.yml"
        ext_yml.write_text(
            "schema_version: '1.0'\n"
            "extension:\n"
            "  id: test-ext\n"
            "  name: Test Extension\n"
            "  version: 1.0.0\n"
            "  description: Test\n"
            "requires_capabilities:\n"
            "  - subagents\n"
            "  - process_enforcement\n",
            encoding="utf-8",
        )

        cmd_file = cmd_dir / "review.md"
        cmd_file.write_text(
            "---\n"
            "description: Review command\n"
            "---\n\n"
            "Review the code.\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]

        # Gemini has empty capabilities, should warn about missing subagents
        # and process_enforcement
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            registrar.register_commands(
                "gemini", commands, "test-ext", ext_dir, tmp_path
            )
            cap_warnings = [
                x for x in w
                if "capability" in str(x.message).lower()
                or "requires" in str(x.message).lower()
            ]
            assert len(cap_warnings) > 0, "Expected warning about missing capabilities"
            warning_text = str(cap_warnings[0].message)
            assert "subagents" in warning_text and "process_enforcement" in warning_text

    def test_all_capabilities_present_no_warning(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        """T035: No warning when target agent has all required capabilities."""
        ext_dir, cmd_dir = ext_with_capability_template

        ext_yml = ext_dir / "extension.yml"
        ext_yml.write_text(
            "schema_version: '1.0'\n"
            "extension:\n"
            "  id: test-ext\n"
            "  name: Test Extension\n"
            "  version: 1.0.0\n"
            "  description: Test\n"
            "requires_capabilities:\n"
            "  - interactive_prompts\n"
            "  - subagents\n",
            encoding="utf-8",
        )

        cmd_file = cmd_dir / "ask.md"
        cmd_file.write_text(
            "---\n"
            "description: Ask command\n"
            "---\n\n"
            "Ask the user.\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.ask", "file": "commands/ask.md"}]

        # Claude has both interactive_prompts and subagents
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            registrar.register_commands(
                "claude", commands, "test-ext", ext_dir, tmp_path
            )
            cap_warnings = [
                x for x in w
                if "requires" in str(x.message).lower()
                and "capability" in str(x.message).lower()
            ]
            assert len(cap_warnings) == 0, (
                f"Unexpected capability warnings: {[str(x.message) for x in cap_warnings]}"
            )


class TestAllFormatTypes:
    """T039: Capability processing works for all 4 format types."""

    @pytest.mark.parametrize(
        "agent,output_path_parts,expect_true",
        [
            # Skills format (Claude) - has subagents
            ("claude", (".claude", "skills", "speckit-test-multi", "SKILL.md"), True),
            # Markdown format (OpenCode) - has subagents
            ("opencode", (".opencode", "commands", "speckit.test.multi.md"), True),
            # TOML format (Gemini) - empty capabilities
            ("gemini", (".gemini", "commands", "speckit.test.multi.toml"), False),
            # YAML format (Goose) - empty capabilities
            ("goose", (".goose", "recipes", "speckit.test.multi.yaml"), False),
        ],
        ids=["skills", "markdown", "toml", "yaml"],
    )
    def test_capability_conditionals_across_formats(
        self, tmp_path, registrar, ext_with_capability_template,
        agent, output_path_parts, expect_true,
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "multi.md"
        cmd_file.write_text(
            "---\n"
            "description: Multi-format test\n"
            "---\n\n"
            "{{#if subagents}}PARALLEL_MODE{{else}}SEQUENTIAL_MODE{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.multi", "file": "commands/multi.md"}]
        registrar.register_commands(
            agent, commands, "test-ext", ext_dir, tmp_path
        )

        output_file = tmp_path.joinpath(*output_path_parts)
        assert output_file.exists(), f"Output file missing for {agent}"
        content = output_file.read_text(encoding="utf-8")

        if expect_true:
            assert "PARALLEL_MODE" in content, f"{agent}: expected true branch"
            assert "SEQUENTIAL_MODE" not in content
        else:
            assert "SEQUENTIAL_MODE" in content, f"{agent}: expected false branch"
            assert "PARALLEL_MODE" not in content

        # No raw capability syntax should remain
        assert "{{#if" not in content
        assert "{{/if}}" not in content


class TestNestedConditionals:
    """US2-3: Nested conditionals resolve correctly through the full pipeline."""

    def test_nested_multi_select_claude_vs_opencode(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "nested.md"
        cmd_file.write_text(
            "---\n"
            "description: Nested conditional test\n"
            "---\n\n"
            "{{#if interactive_prompts}}"
            "Prompts available. "
            "{{#if interactive_prompts.multi_select}}"
            "MULTI_SELECT"
            "{{else}}"
            "SINGLE_SELECT"
            "{{/if}}"
            "{{else}}"
            "NO_PROMPTS"
            "{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.nested", "file": "commands/nested.md"}]

        # Claude has multi_select=True
        registrar.register_commands(
            "claude", commands, "test-ext", ext_dir, tmp_path
        )
        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-test-nested" / "SKILL.md"
        )
        content = skill_file.read_text(encoding="utf-8")
        assert "MULTI_SELECT" in content
        assert "SINGLE_SELECT" not in content
        assert "NO_PROMPTS" not in content

        # OpenCode has multi_select=False
        registrar.register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )
        cmd_output = (
            tmp_path / ".opencode" / "commands" / "speckit.test.nested.md"
        )
        content = cmd_output.read_text(encoding="utf-8")
        assert "SINGLE_SELECT" in content
        assert "MULTI_SELECT" not in content
        assert "NO_PROMPTS" not in content


class TestPluginRootClaude:
    """US5-1: __PLUGIN_ROOT__ resolves correctly for skills-format agents."""

    def test_plugin_root_replaced_for_claude(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "run.md"
        cmd_file.write_text(
            "---\n"
            "description: Run a script\n"
            "---\n\n"
            'Execute "$__PLUGIN_ROOT__/scripts/run.sh"\n',
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.run", "file": "commands/run.md"}]
        registrar.register_commands(
            "claude", commands, "test-ext", ext_dir, tmp_path
        )

        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-test-run" / "SKILL.md"
        )
        content = skill_file.read_text(encoding="utf-8")
        assert "__PLUGIN_ROOT__" not in content
        assert str(ext_dir) in content or str(ext_dir.resolve()) in content


class TestMalformedSyntaxSkip:
    """FR-014: Malformed capability syntax skips the command gracefully."""

    def test_malformed_command_skipped_others_registered(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template

        # Malformed command (missing {{/if}})
        bad_file = cmd_dir / "bad.md"
        bad_file.write_text(
            "---\n"
            "description: Bad command\n"
            "---\n\n"
            "{{#if subagents}}missing close\n",
            encoding="utf-8",
        )

        # Good command
        good_file = cmd_dir / "good.md"
        good_file.write_text(
            "---\n"
            "description: Good command\n"
            "---\n\n"
            "This is fine.\n",
            encoding="utf-8",
        )

        commands = [
            {"name": "speckit.test.bad", "file": "commands/bad.md"},
            {"name": "speckit.test.good", "file": "commands/good.md"},
        ]

        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            registered = registrar.register_commands(
                "claude", commands, "test-ext", ext_dir, tmp_path
            )

        assert "speckit.test.good" in registered
        assert "speckit.test.bad" not in registered
        syntax_warnings = [
            x for x in w if "malformed capability syntax" in str(x.message).lower()
        ]
        assert len(syntax_warnings) > 0


class TestPipelineOrdering:
    """Tool refs in eliminated conditional branches should NOT trigger warnings."""

    def test_tool_ref_in_false_branch_no_warning(
        self, tmp_path, registrar, ext_with_capability_template, caplog
    ):
        import logging

        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "order.md"
        cmd_file.write_text(
            "---\n"
            "description: Pipeline ordering test\n"
            "---\n\n"
            "{{#if subagents}}"
            "Use {{tool:subagents}} for dispatch"
            "{{else}}"
            "No agents, use {{tool:nonexistent_capability}}"
            "{{/if}}\n",
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.order", "file": "commands/order.md"}]
        with caplog.at_level(logging.WARNING):
            registrar.register_commands(
                "claude", commands, "test-ext", ext_dir, tmp_path
            )

        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-test-order" / "SKILL.md"
        )
        content = skill_file.read_text(encoding="utf-8")
        assert "Agent" in content
        assert "nonexistent_capability" not in content
        assert "nonexistent" not in caplog.text


class TestRegressionNoCaps:
    """T023: Templates without capability syntax produce unchanged output."""

    def test_plain_template_unchanged(
        self, tmp_path, registrar, ext_with_capability_template
    ):
        ext_dir, cmd_dir = ext_with_capability_template
        cmd_file = cmd_dir / "plain.md"
        body_text = "This is a plain command with no capability syntax.\n"
        cmd_file.write_text(
            "---\n"
            "description: Plain command\n"
            "---\n\n"
            + body_text,
            encoding="utf-8",
        )

        commands = [{"name": "speckit.test.plain", "file": "commands/plain.md"}]

        # Register for multiple agents
        for agent, path_pattern in [
            ("claude", ".claude/skills/speckit-test-plain/SKILL.md"),
            ("opencode", ".opencode/commands/speckit.test.plain.md"),
        ]:
            registrar.register_commands(
                agent, commands, "test-ext", ext_dir, tmp_path
            )
            output_file = tmp_path / path_pattern
            assert output_file.exists(), f"Output file missing for {agent}"
            content = output_file.read_text(encoding="utf-8")
            assert body_text.strip() in content, (
                f"Body text missing in {agent} output"
            )
