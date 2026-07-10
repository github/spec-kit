"""Tests for post_process_command_content() hook on IntegrationBase.

Verifies that the generalized post-processing hook:
- Runs for non-skills format types (Markdown, TOML, YAML)
- Does NOT run for skills-format agents
- Default no-op returns content unchanged
- Exceptions propagate to caller
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations.base import IntegrationBase


@pytest.fixture
def registrar():
    return CommandRegistrar()


@pytest.fixture
def ext_dir(tmp_path):
    """Create a mock extension with a simple command template."""
    ext = tmp_path / "extension"
    ext.mkdir()
    cmd_dir = ext / "commands"
    cmd_dir.mkdir()
    return ext, cmd_dir


def _write_cmd(cmd_dir, name="review.md", body="Review the code.\n"):
    cmd_file = cmd_dir / name
    cmd_file.write_text(
        f"---\ndescription: Test command\n---\n\n{body}",
        encoding="utf-8",
    )
    return cmd_file


class TestDefaultNoOp:
    def test_returns_content_unchanged(self):
        base = IntegrationBase()
        content = "Some command content\nwith multiple lines."
        assert base.post_process_command_content(content) == content

    def test_empty_string(self):
        base = IntegrationBase()
        assert base.post_process_command_content("") == ""


class TestMarkdownAgentPostProcess:
    def test_opencode_post_process_applied(
        self, tmp_path, registrar, ext_dir, monkeypatch
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        opencode = get_integration("opencode")
        marker = "<!-- POST_PROCESSED -->"

        def _inject_marker(self, content):
            return content + marker

        monkeypatch.setattr(
            opencode.__class__, "post_process_command_content", _inject_marker
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        registrar.register_commands(
            "opencode", commands, "test-ext", ext, tmp_path
        )

        cmd_output = tmp_path / ".opencode" / "commands" / "speckit.test.review.md"
        assert cmd_output.exists()
        content = cmd_output.read_text(encoding="utf-8")
        assert marker in content


class TestTomlAgentPostProcess:
    def test_gemini_post_process_applied(
        self, tmp_path, registrar, ext_dir, monkeypatch
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        gemini = get_integration("gemini")
        marker = "# POST_PROCESSED"

        def _inject_marker(self, content):
            return content + f"\n{marker}\n"

        monkeypatch.setattr(
            gemini.__class__, "post_process_command_content", _inject_marker
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        registrar.register_commands(
            "gemini", commands, "test-ext", ext, tmp_path
        )

        cmd_output = tmp_path / ".gemini" / "commands" / "speckit.test.review.toml"
        assert cmd_output.exists()
        content = cmd_output.read_text(encoding="utf-8")
        assert marker in content


class TestYamlAgentPostProcess:
    def test_goose_post_process_applied(
        self, tmp_path, registrar, ext_dir, monkeypatch
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        goose = get_integration("goose")
        marker = "# POST_PROCESSED"

        def _inject_marker(self, content):
            return content + f"\n{marker}\n"

        monkeypatch.setattr(
            goose.__class__, "post_process_command_content", _inject_marker
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        registrar.register_commands(
            "goose", commands, "test-ext", ext, tmp_path
        )

        cmd_output = tmp_path / ".goose" / "recipes" / "speckit.test.review.yaml"
        assert cmd_output.exists()
        content = cmd_output.read_text(encoding="utf-8")
        assert marker in content


class TestSkillsAgentExcluded:
    def test_claude_post_process_not_called(
        self, tmp_path, registrar, ext_dir, monkeypatch
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        claude = get_integration("claude")
        marker = "<!-- SHOULD_NOT_APPEAR -->"

        def _inject_marker(self, content):
            return content + marker

        monkeypatch.setattr(
            claude.__class__, "post_process_command_content", _inject_marker
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        registrar.register_commands(
            "claude", commands, "test-ext", ext, tmp_path
        )

        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-test-review" / "SKILL.md"
        )
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert marker not in content

    def test_skills_agent_method_never_called(
        self, tmp_path, registrar, ext_dir
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        claude = get_integration("claude")
        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]

        with patch.object(
            claude.__class__, "post_process_command_content", wraps=claude.post_process_command_content
        ) as mock_method:
            registrar.register_commands(
                "claude", commands, "test-ext", ext, tmp_path
            )
            mock_method.assert_not_called()


class TestExceptionPropagation:
    def test_hook_exception_propagates(
        self, tmp_path, registrar, ext_dir, monkeypatch
    ):
        ext, cmd_dir = ext_dir
        _write_cmd(cmd_dir)

        from specify_cli.integrations import get_integration

        opencode = get_integration("opencode")

        def _raise(self, content):
            raise RuntimeError("Hook failed")

        monkeypatch.setattr(
            opencode.__class__, "post_process_command_content", _raise
        )

        commands = [{"name": "speckit.test.review", "file": "commands/review.md"}]
        with pytest.raises(RuntimeError, match="Hook failed"):
            registrar.register_commands(
                "opencode", commands, "test-ext", ext, tmp_path
            )


class TestRegressionPlainTemplate:
    @pytest.mark.parametrize(
        "agent,path_pattern",
        [
            ("claude", ".claude/skills/speckit-test-plain/SKILL.md"),
            ("opencode", ".opencode/commands/speckit.test.plain.md"),
        ],
        ids=["skills", "markdown"],
    )
    def test_plain_template_unchanged(
        self, tmp_path, registrar, ext_dir, agent, path_pattern
    ):
        ext, cmd_dir = ext_dir
        body_text = "This is a plain command with no special content.\n"
        _write_cmd(cmd_dir, name="plain.md", body=body_text)

        commands = [{"name": "speckit.test.plain", "file": "commands/plain.md"}]
        registrar.register_commands(
            agent, commands, "test-ext", ext, tmp_path
        )

        output_file = tmp_path / path_pattern
        assert output_file.exists(), f"Output file missing for {agent}"
        content = output_file.read_text(encoding="utf-8")
        assert body_text.strip() in content, f"Body text missing in {agent} output"
