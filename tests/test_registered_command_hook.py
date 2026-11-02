"""Tests for the process_registered_command() hook on IntegrationBase.

The hook lets an integration rewrite a command's parsed frontmatter and body
during ``CommandRegistrar.register_commands()``, with the command's
``source_id`` available, before placeholders are resolved and the command is
rendered.
"""

from __future__ import annotations

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import get_integration
from specify_cli.integrations.base import IntegrationBase


@pytest.fixture
def ext_dir(tmp_path):
    ext = tmp_path / "extension"
    (ext / "commands").mkdir(parents=True)
    (ext / "commands" / "review.md").write_text(
        "---\ndescription: Review the code\n---\n\nReview $ARGUMENTS now.\n",
        encoding="utf-8",
    )
    return ext


COMMANDS = [{"name": "speckit.test.review", "file": "commands/review.md"}]


class TestDefault:
    def test_returns_inputs_unchanged(self):
        frontmatter = {"description": "x", "tags": ["a"]}
        body = "Body text.\n"
        result = IntegrationBase().process_registered_command(
            frontmatter, body, source_id="test-ext"
        )
        assert result == (frontmatter, body)

    def test_default_registration_output_is_unchanged(self, tmp_path, ext_dir):
        CommandRegistrar().register_commands(
            "opencode", COMMANDS, "test-ext", ext_dir, tmp_path
        )
        out = tmp_path / ".opencode" / "commands" / "speckit.test.review.md"
        text = out.read_text(encoding="utf-8")
        assert "description: Review the code" in text
        assert "Review $ARGUMENTS now." in text


class TestRegistrationUsesHook:
    def test_hook_output_is_rendered(self, tmp_path, ext_dir, monkeypatch):
        calls = []

        def hook(self, frontmatter, body, *, source_id):
            calls.append((dict(frontmatter), body, source_id))
            updated = dict(frontmatter)
            updated["description"] = f"[{source_id}] {frontmatter['description']}"
            return updated, body.replace("Review", "Inspect")

        monkeypatch.setattr(
            get_integration("opencode").__class__, "process_registered_command", hook
        )
        CommandRegistrar().register_commands(
            "opencode", COMMANDS, "test-ext", ext_dir, tmp_path
        )

        assert len(calls) == 1
        frontmatter, body, source_id = calls[0]
        assert source_id == "test-ext"
        assert frontmatter["description"] == "Review the code"
        # OpenCode keeps $ARGUMENTS unchanged, so ordering against placeholder
        # conversion is asserted by the Gemini case below.
        assert "Review $ARGUMENTS now." in body

        out = tmp_path / ".opencode" / "commands" / "speckit.test.review.md"
        text = out.read_text(encoding="utf-8")
        assert "description: '[test-ext] Review the code'" in text or (
            'description: "[test-ext] Review the code"' in text
        )
        assert "Inspect" in text
        assert "Review $ARGUMENTS" not in text

    def test_hook_runs_before_placeholder_resolution(self, tmp_path, monkeypatch):
        """Gemini rewrites ``$ARGUMENTS`` to ``{{args}}`` and resolves
        ``__SPECKIT_COMMAND_*__`` tokens, so this case fails if the hook runs
        after either conversion."""
        ext = tmp_path / "extension"
        (ext / "commands").mkdir(parents=True)
        (ext / "commands" / "review.md").write_text(
            "---\ndescription: Review the code\n---\n\n"
            "Review $ARGUMENTS, then run __SPECKIT_COMMAND_PLAN__.\n",
            encoding="utf-8",
        )
        calls = []

        def hook(self, frontmatter, body, *, source_id):
            calls.append(body)
            return frontmatter, body + "Next: __SPECKIT_COMMAND_TASKS__ $ARGUMENTS\n"

        monkeypatch.setattr(
            get_integration("gemini").__class__, "process_registered_command", hook
        )
        project = tmp_path / "project"
        project.mkdir()
        CommandRegistrar().register_commands(
            "gemini", COMMANDS, "test-ext", ext, project
        )

        assert len(calls) == 1
        assert "$ARGUMENTS" in calls[0]
        assert "__SPECKIT_COMMAND_PLAN__" in calls[0]
        assert "{{args}}" not in calls[0]
        assert "/speckit.plan" not in calls[0]

        out = project / ".gemini" / "commands" / "speckit.test.review.toml"
        text = out.read_text(encoding="utf-8")
        assert "Review {{args}}, then run /speckit.plan." in text
        assert "Next: /speckit.tasks {{args}}" in text
        assert "$ARGUMENTS" not in text
        assert "__SPECKIT_COMMAND_" not in text

    def test_hook_sees_core_source_id(self, tmp_path, ext_dir, monkeypatch):
        seen = []

        def hook(self, frontmatter, body, *, source_id):
            seen.append(source_id)
            return frontmatter, body

        monkeypatch.setattr(
            get_integration("opencode").__class__, "process_registered_command", hook
        )
        CommandRegistrar().register_commands(
            "opencode", COMMANDS, "core", ext_dir, tmp_path
        )
        assert seen == ["core"]

    def test_hook_applies_to_skills_layout(self, tmp_path, ext_dir, monkeypatch):
        def hook(self, frontmatter, body, *, source_id):
            return frontmatter, body + "\nHOOKED\n"

        integ = get_integration("claude")
        monkeypatch.setattr(integ.__class__, "process_registered_command", hook)
        CommandRegistrar().register_commands(
            "claude", COMMANDS, "test-ext", ext_dir, tmp_path
        )
        skill_files = list((tmp_path / ".claude").rglob("SKILL.md"))
        assert skill_files, "expected a skill file to be written"
        assert "HOOKED" in skill_files[0].read_text(encoding="utf-8")

    def test_hook_output_reaches_aliases(self, tmp_path, ext_dir, monkeypatch):
        def hook(self, frontmatter, body, *, source_id):
            return frontmatter, body.replace("Review", "Inspect")

        monkeypatch.setattr(
            get_integration("opencode").__class__, "process_registered_command", hook
        )
        commands = [dict(COMMANDS[0], aliases=["speckit.test.rv"])]
        CommandRegistrar().register_commands(
            "opencode", commands, "test-ext", ext_dir, tmp_path
        )
        alias = tmp_path / ".opencode" / "commands" / "speckit.test.rv.md"
        assert "Inspect" in alias.read_text(encoding="utf-8")
