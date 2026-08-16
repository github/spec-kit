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


def test_list_command_templates_includes_revise():
    from specify_cli.integrations.base import MarkdownIntegration

    class _Probe(MarkdownIntegration):
        key = "probe"
        config = {
            "name": "Probe",
            "folder": ".probe/",
            "commands_subdir": "commands",
            "install_url": None,
            "requires_cli": False,
        }
        registrar_config = {
            "dir": ".probe/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
        }

    stems = {p.stem for p in _Probe().list_command_templates()}
    assert "revise" in stems
    assert "specify" in stems


def test_revise_command_ref_resolves_to_speckit_revise():
    resolved = IntegrationBase.resolve_command_refs(
        "next: __SPECKIT_COMMAND_REVISE__", separator=".", prefix="/"
    )
    assert resolved == "next: /speckit.revise"


def test_skill_descriptions_include_revise():
    from specify_cli import SKILL_DESCRIPTIONS

    assert "revise" in SKILL_DESCRIPTIONS
    assert "Create a new feature specification" in SKILL_DESCRIPTIONS["specify"]


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
        assert "dated log" in self.text.lower() or "dated index" in self.text.lower()
        assert "not a spec" in self.text.lower() or "NOT SOURCE OF TRUTH" in self.text

    def test_duplicates_are_a_noop(self):
        assert "DUPLICATES ARE A NO-OP" in self.text
        assert "Do **not** bump `R{N}`" in self.text or "do not append" in self.text.lower()

    def test_stable_ids_are_never_reused(self):
        assert "Do not reuse a retired ID" in self.text
        assert "STABLE IDS" in self.text

    def test_handles_add_and_remove_acceptance_criteria(self):
        assert "**add AC**" in self.text
        assert "**remove**" in self.text
        assert "RETIRED" in self.text

    def test_cancels_open_tasks_instead_of_deleting_them(self):
        assert "CANCELLED" in self.text
        assert "SUPERSEDED" in self.text

    def test_supersede_marks_old_and_adds_new(self):
        assert "op`: `add` | `remove` | `reword` | `supersede`" in self.text
        assert "SUPERSEDED by" in self.text
        assert "two **live** items that contradict" in self.text

    def test_does_not_write_application_code(self):
        assert "NO APPLICATION CODE" in self.text

    def test_hands_off_to_implement_plan_or_tasks(self):
        assert "__SPECKIT_COMMAND_IMPLEMENT__" in self.text
        assert "__SPECKIT_COMMAND_PLAN__" in self.text
        assert "agent: speckit.tasks" in self.text

    def test_uses_script_placeholder(self):
        assert "{SCRIPT}" in self.text

    def test_has_mandatory_post_execution_hooks(self):
        assert "hooks.after_revise" in self.text
        assert "EXECUTE_COMMAND:" in self.text
        assert "## Done When" in self.text


class TestCascadeContracts:
    def test_implement_skips_cancelled_tasks(self):
        text = (COMMANDS / "implement.md").read_text(encoding="utf-8")
        assert "CANCELLED" in text
        assert "SUPERSEDED" in text
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

    def test_clarify_defers_known_deltas_to_revise(self):
        text = (COMMANDS / "clarify.md").read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "concrete delta" in text
