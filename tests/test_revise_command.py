"""Contracts for the core ``/speckit.revise`` command.

The command file is the behavior. These checks lock the rules that make
revise a living-spec edit instead of a second specify, and lock the
cascade so implement / taskstoissues / analyze stay safe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.integrations.base import IntegrationBase


REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS = REPO_ROOT / "templates" / "commands"
REVISE = COMMANDS / "revise.md"


def test_revise_template_exists():
    assert REVISE.is_file()


def test_revise_has_scripts_frontmatter():
    text = REVISE.read_text(encoding="utf-8")
    assert "sh: scripts/bash/check-prerequisites.sh --json --paths-only" in text
    assert "ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly" in text
    assert "py: scripts/python/check_prerequisites.py --json --paths-only" in text


@pytest.mark.parametrize("script_type", ["sh", "ps", "py"])
def test_revise_template_renders(script_type: str, monkeypatch):
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.IntegrationBase._interpreter_runs",
        staticmethod(lambda path: True),
    )
    content = REVISE.read_text(encoding="utf-8")
    result = IntegrationBase.process_template(content, "agent", script_type)
    assert "{SCRIPT}" not in result
    assert "$ARGUMENTS" in result or "{{args}}" in result or result


class TestReviseInvariants:
    def setup_method(self):
        self.text = REVISE.read_text(encoding="utf-8")

    def test_does_not_create_a_new_feature_directory(self):
        assert "Do **not** create a new `specs/` folder" in self.text

    def test_edits_spec_in_place(self):
        assert "Edit `spec.md` in place" in self.text

    def test_records_revisions_changelog(self):
        assert "revisions.md" in self.text

    def test_stable_ids_are_never_reused(self):
        assert "Do not reuse a retired ID" in self.text
        assert "STABLE IDS" in self.text

    def test_handles_add_and_remove_acceptance_criteria(self):
        assert "**add AC**" in self.text
        assert "**remove AC**" in self.text

    def test_cancels_open_tasks_instead_of_deleting_them(self):
        assert "CANCELLED" in self.text
        assert "Do not delete the line" in self.text

    def test_does_not_write_application_code(self):
        assert "NO APPLICATION CODE" in self.text

    def test_hands_off_to_implement_plan_or_tasks(self):
        assert "__SPECKIT_COMMAND_IMPLEMENT__" in self.text
        assert "__SPECKIT_COMMAND_PLAN__" in self.text
        assert "agent: speckit.tasks" in self.text

    def test_uses_script_placeholder(self):
        assert "{SCRIPT}" in self.text


class TestCascadeContracts:
    def test_implement_skips_cancelled_tasks(self):
        text = (COMMANDS / "implement.md").read_text(encoding="utf-8")
        assert "CANCELLED" in text
        assert "not executable" in text

    def test_taskstoissues_skips_cancelled_tasks(self):
        text = (COMMANDS / "taskstoissues.md").read_text(encoding="utf-8")
        assert "CANCELLED" in text
        assert "must not become a GitHub issue" in text

    def test_analyze_treats_revisions_as_history(self):
        text = (COMMANDS / "analyze.md").read_text(encoding="utf-8")
        assert "revisions.md" in text
        assert "retired" in text.lower()
        assert "__SPECKIT_COMMAND_REVISE__" in text

    def test_specify_is_create_not_update(self):
        text = (COMMANDS / "specify.md").read_text(encoding="utf-8")
        assert "Create a new feature specification" in text
        assert "__SPECKIT_COMMAND_REVISE__" in text

    def test_converge_defers_to_revise_when_spec_changed(self):
        text = (COMMANDS / "converge.md").read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_REVISE__" in text
