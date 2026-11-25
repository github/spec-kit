"""Questions to the team lead and the decision log, in one standalone checkout."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tests.extensions.autopilot.helpers import SPEC_TEMPLATE, git, init_repo, install_extension, run_cli

FEATURE = "specs/003-export"
CONFIG = f"""gate:
  checks:
    - name: test
      run: "{Path(sys.executable).as_posix()} -c pass"
pipe:
  max_questions: 3
"""


@pytest.fixture
def project(tmp_path):
    root = init_repo(tmp_path / "repo")
    install_extension(root, CONFIG)
    feature = root / FEATURE
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text(
        SPEC_TEMPLATE + "\n- FR-001: [NEEDS CLARIFICATION: CSV or XLSX?]\n", encoding="utf-8"
    )
    (feature / "tasks.md").write_text("# Tasks\n\n## Phase 1: Build\n\n- [x] T001 Build\n", encoding="utf-8")
    return root


def _cli(root: Path, *args: str):
    result = run_cli(root, *args, env={"SPECIFY_FEATURE_DIRECTORY": FEATURE})
    return result.returncode, json.loads(result.stdout.strip().splitlines()[-1])


def _ask(root: Path, name: str, question: str, **extra) -> None:
    inbox = root / ".specify" / "autopilot" / "inbox" / "questions"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / f"{name}.json").write_text(json.dumps({"question": question, **extra}), encoding="utf-8")


def _answer(root: Path, consult: dict, body: dict) -> None:
    args = dict(part.split("=", 1) for part in consult["lead_args"].split())
    for qid in args["ids"].split(","):
        (root / args["questions_dir"] / f"{qid}.answer.json").write_text(json.dumps(body), encoding="utf-8")


def _pipe(root: Path) -> dict:
    return json.loads((root / ".specify/autopilot/pipes/003-export/pipe.json").read_text())


def test_spec_markers_and_inbox_questions_are_filed_for_the_lead(project):
    _ask(project, "a", "Which timestamp format?", options=["ISO", "epoch"], recommendation="ISO")
    _ask(project, "bad", "")
    _, out = _cli(project, "consult", "--stage", "build")
    assert out["open"] == 2
    assert sorted(out["open_ids"])[0] == "003-Q1" and any(i.startswith("003-S") for i in out["open_ids"])
    assert "bad.json" in out["problems"][0]
    assert not (project / ".specify/autopilot/inbox/questions/a.json").exists()
    filed = json.loads((project / ".specify/autopilot/pipes/003-export/questions/003-Q1.json").read_text())
    assert filed["options"] == ["ISO", "epoch"] and filed["blocking"] is True
    # The standalone checkout still gets a brief with the asking protocol.
    assert "Asking the team lead" in (project / ".specify/autopilot/context/epic-context.md").read_text()


def test_answers_become_decisions_spec_edits_and_tasks(project):
    _ask(project, "a", "Which timestamp format?")
    _, consult = _cli(project, "consult", "--stage", "build")
    _answer(project, consult, {"answer": "ISO-8601 UTC", "rationale": "convention", "applies_to": "program"})
    _, out = _cli(project, "record", "--stage", "build")
    assert out["finished"] is False and len(out["applied"]) == 2

    spec = (project / FEATURE / "spec.md").read_text()
    assert "[NEEDS CLARIFICATION" not in spec and "CSV or XLSX? — **Decided (D-003-S" in spec
    tasks = (project / FEATURE / "tasks.md").read_text()
    assert "## Phase 2: Team Decisions (build)" in tasks
    assert "Apply team decision D-003-Q1 to your work (your question 003-Q1: Which timestamp format?): ISO-8601 UTC" in tasks
    decisions = (project / ".specify/autopilot/decisions.md").read_text()
    assert decisions.count("**Decision:** ISO-8601 UTC") == 2
    # Answers are applied once.
    _, again = _cli(project, "record", "--stage", "build")
    assert again["applied"] == []


def test_a_repeated_question_is_answered_from_the_decision_log_without_the_lead(project):
    _ask(project, "a", "Which timestamp format?")
    _, consult = _cli(project, "consult", "--stage", "build")
    _answer(project, consult, {"answer": "ISO-8601 UTC"})
    _cli(project, "record", "--stage", "build")
    _ask(project, "b", "which TIMESTAMP format")
    _, consult = _cli(project, "consult", "--stage", "build")
    assert consult["open"] == 0
    _, out = _cli(project, "record", "--stage", "build")
    assert out["applied"] == ["003-Q2"]
    assert "D-003-Q1" in (project / FEATURE / "tasks.md").read_text().splitlines()[-1]


def test_product_owner_question_pauses_the_pipe(project):
    _, consult = _cli(project, "consult", "--stage", "spec")
    _answer(project, consult, {"needs_human": True, "why": "scope", "options": ["CSV", "XLSX"], "recommendation": "CSV"})
    _, out = _cli(project, "record", "--stage", "spec")
    assert out["finished"] is True and out["status"] == "awaiting-human"
    code, spec = _cli(project, "check-spec")
    assert code == 1 and "product owner" in spec["problems"][0]
    _, gate = _cli(project, "gate")
    assert gate["finished"] is True and _pipe(project)["iteration"] == 0

    [qid] = out["awaiting_human"]
    code, answered = _cli(project, "answer", qid, "--text", "CSV")
    assert code == 0 and answered["still_open"] == []
    code, _ = _cli(project, "answer", qid, "--text", "again")
    assert code == 1


def test_lead_that_edits_files_is_escalated(project):
    _, consult = _cli(project, "consult", "--stage", "build")
    _answer(project, consult, {"answer": "CSV"})
    (project / "lead_was_here.py").write_text("x = 1\n", encoding="utf-8")
    _, out = _cli(project, "record", "--stage", "build")
    assert out["status"] == "escalated" and "team lead changed the working tree" in out["reason"]


def test_lead_that_does_not_answer_twice_hands_the_question_to_a_human(project):
    _cli(project, "consult", "--stage", "build")
    assert _cli(project, "record", "--stage", "build")[1]["status"] == "running"
    _cli(project, "consult", "--stage", "build")
    _, out = _cli(project, "record", "--stage", "build")
    assert out["status"] == "awaiting-human" and len(out["awaiting_human"]) == 1


def test_too_many_questions_escalate(project):
    for index in range(4):
        _ask(project, f"q{index}", f"Question number {'x' * index}?")
    _, out = _cli(project, "consult", "--stage", "build")
    assert out["finished"] is True and _pipe(project)["status"] == "escalated"


def test_decisions_before_tasks_exist_are_handed_over_once_tasks_do(project):
    (project / FEATURE / "tasks.md").unlink()
    _ask(project, "a", "Which timestamp format?")
    _, consult = _cli(project, "consult", "--stage", "spec")
    _answer(project, consult, {"answer": "ISO-8601 UTC"})
    _cli(project, "record", "--stage", "spec")
    (project / FEATURE / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Build\n", encoding="utf-8")
    _cli(project, "consult", "--stage", "design")
    tasks = (project / FEATURE / "tasks.md").read_text()
    assert "Team Decisions (before tasks)" in tasks and "ISO-8601 UTC" in tasks
