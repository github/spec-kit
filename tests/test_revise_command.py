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
    assert "Create or update feature specifications" in SKILL_DESCRIPTIONS["specify"]


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
    assert "$ARGUMENTS" in result or "{{args}}" in result


class TestReviseInvariants:
    def setup_method(self):
        self.text = REVISE.read_text(encoding="utf-8")

    def test_does_not_create_a_new_feature_directory(self):
        assert "after `plan.md`, `tasks.md`, or implementation exist" in self.text

    def test_edits_spec_in_place(self):
        assert "in place" in self.text
        assert "spec.md" in self.text

    def test_records_revisions_changelog(self):
        assert "revisions.md" in self.text
        assert "dated log" in self.text
        assert "not a spec" in self.text

    def test_duplicates_are_a_noop(self):
        assert "duplicate" in self.text
        assert "don't bump `R{N}`" in self.text or "don't append" in self.text

    def test_stable_ids_are_never_reused(self):
        assert "Don't reuse" in self.text or "Don't renumber" in self.text

    def test_handles_add_and_remove_acceptance_criteria(self):
        assert "Brand new" in self.text or "add" in self.text
        assert "RETIRED" in self.text

    def test_cancels_open_tasks_instead_of_deleting_them(self):
        assert "CANCELLED" in self.text
        assert "SUPERSEDED" in self.text

    def test_supersede_marks_old_and_adds_new(self):
        assert "supersede" in self.text
        assert "SUPERSEDED by" in self.text
        assert "contradict" in self.text

    def test_does_not_write_application_code(self):
        assert "application code" in self.text

    def test_never_rewrites_artifacts(self):
        assert "Never regenerate" in self.text or "never regenerate" in self.text.lower() or "Do **not** rewrite" in self.text
        assert "the old code" in self.text

    def test_implemented_is_per_id_not_any_checked_task(self):
        assert "references that ID" in self.text
        assert "not a blanket remove-code trigger" in self.text

    def test_reports_named_plan_status(self):
        assert "plan_status:" in self.text
        assert "needs-rebuild" in self.text
        assert "patched" in self.text
        assert "missing" in self.text
        assert "- plan_status:" in self.text
        assert "Persist that same value" in self.text

    def test_tasks_handoff_refuses_to_regenerate(self):
        assert "agent: speckit.tasks" in self.text
        assert "Never regenerate an existing task list" in self.text

    def test_hands_off_to_implement_plan_or_tasks(self):
        assert "__SPECKIT_COMMAND_IMPLEMENT__" in self.text
        assert "__SPECKIT_COMMAND_PLAN__" in self.text
        assert "agent: speckit.tasks" in self.text
        assert "agent: speckit.plan" in self.text
        assert "plan_status: needs-rebuild" in self.text

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
        assert "only when `tasks.md` is **absent**" in text
        assert "Do not regenerate" in text

    def test_taskstoissues_skips_cancelled_tasks(self):
        text = (COMMANDS / "taskstoissues.md").read_text(encoding="utf-8")
        assert "CANCELLED" in text
        assert "must not become a GitHub issue" in text

    def test_analyze_treats_revisions_as_history(self):
        text = (COMMANDS / "analyze.md").read_text(encoding="utf-8")
        assert "revisions.md" in text
        assert "retired" in text.lower()
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "Only **live**" in text
        assert "Do not create keys for `SUPERSEDED` or `RETIRED` IDs" in text
        assert "Skip plan bullets marked `SUPERSEDED` or `RETIRED`" in text

    def test_specify_defers_to_revise_after_plan_tasks_or_impl(self):
        text = (COMMANDS / "specify.md").read_text(encoding="utf-8")
        assert "Create or update the feature specification" in text
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "`plan.md`, `tasks.md`, or implemented work" in text
        assert "this command can still **update** that spec" in text

    def test_converge_defers_to_revise_when_spec_changed(self):
        text = (COMMANDS / "converge.md").read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "SUPERSEDED" in text
        assert "RETIRED" in text
        assert "Only **live**" in text
        assert "Do not create keys for `SUPERSEDED` or `RETIRED` IDs" in text
        assert "Revision R#" in text
        assert "__SPECKIT_COMMAND_IMPLEMENT__" in text

    def test_tasks_refuses_to_regenerate_after_revise(self):
        text = (COMMANDS / "tasks.md").read_text(encoding="utf-8")
        assert "do **not** regenerate the file" in text
        assert "Revision R#" in text
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "Inventory only **live**" in text
        assert "even on first generation" in text

    def test_lean_implement_skips_cancelled_tasks(self):
        text = (
            REPO_ROOT
            / "presets"
            / "lean"
            / "commands"
            / "speckit.implement.md"
        ).read_text(encoding="utf-8")
        assert "CANCELLED" in text
        assert "SUPERSEDED" in text
        assert "not count them as remaining work" in text

    def test_plan_inventories_only_live_ids(self):
        text = (COMMANDS / "plan.md").read_text(encoding="utf-8")
        assert "SUPERSEDED" in text
        assert "RETIRED" in text
        assert "do not restore them" in text
        assert "plan_status: needs-rebuild" in text

    def test_lean_specify_defers_to_revise_after_plan_or_tasks(self):
        text = (
            REPO_ROOT / "presets" / "lean" / "commands" / "speckit.specify.md"
        ).read_text(encoding="utf-8")
        assert "/speckit.revise" in text
        assert "`plan.md`, `tasks.md`, or implementation already exist" in text
        assert "this command may **update** it" in text

    def test_lean_plan_skips_retired_ids(self):
        text = (
            REPO_ROOT / "presets" / "lean" / "commands" / "speckit.plan.md"
        ).read_text(encoding="utf-8")
        assert "SUPERSEDED" in text
        assert "RETIRED" in text
        assert "do not restore them" in text
        assert "plan_status: needs-rebuild" in text

    def test_lean_tasks_refuses_to_overwrite_revision_list(self):
        text = (
            REPO_ROOT / "presets" / "lean" / "commands" / "speckit.tasks.md"
        ).read_text(encoding="utf-8")
        assert "do **not** overwrite it" in text
        assert "Revision R#" in text
        assert "Never emit tasks for `SUPERSEDED` or `RETIRED` lines" in text

    def test_clarify_defers_known_deltas_to_revise(self):
        text = (COMMANDS / "clarify.md").read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_REVISE__" in text
        assert "concrete delta" in text
        assert "do **not** replace or delete live FR/AC/SC lines" in text
        assert "do **not** drop `SUPERSEDED` / `RETIRED` history" in text
        assert "do not remove the old live line" in text

    def test_checklist_inventories_only_live_ids(self):
        text = (COMMANDS / "checklist.md").read_text(encoding="utf-8")
        assert "only **live**" in text
        assert "SUPERSEDED" in text
        assert "__SPECKIT_COMMAND_REVISE__" in text
