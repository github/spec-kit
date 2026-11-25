"""Gate behaviour in a real git repository (standalone pipe, no conductor)."""

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
      run: "{Path(sys.executable).as_posix()} check.py"
pipe:
  max_iterations: 4
  stuck_after: 2
"""


@pytest.fixture
def project(tmp_path):
    root = init_repo(tmp_path / "repo")
    install_extension(root, CONFIG)
    (root / "check.py").write_text(
        "import pathlib, sys\nsys.exit(1 if pathlib.Path('BROKEN').exists() else 0)\n", encoding="utf-8"
    )
    git(root, "add", "check.py")
    git(root, "commit", "-q", "-m", "check")
    feature = root / FEATURE
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text(SPEC_TEMPLATE, encoding="utf-8")
    (feature / "tasks.md").write_text("# Tasks\n\n## Phase 1: Build\n\n- [x] T001 Build\n", encoding="utf-8")
    return root


def _cli(root: Path, *args: str):
    result = run_cli(root, *args, env={"SPECIFY_FEATURE_DIRECTORY": FEATURE})
    return result.returncode, json.loads(result.stdout.strip().splitlines()[-1])


def _write_tests(root: Path, tags: list[str]) -> None:
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / "test_export.py").write_text(
        "".join(f"def test_{t.replace('-', '_').lower()}():\n    pass\n" for t in tags), encoding="utf-8"
    )


def _pipe(root: Path) -> dict:
    return json.loads((root / ".specify" / "autopilot" / "pipes" / "003-export" / "pipe.json").read_text())


def test_check_spec_reports_scenario_ids_and_hint(project):
    code, out = _cli(project, "check-spec")
    assert code == 0
    assert out["scenarios"] == ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"]
    assert "003_us1_as1" in out["tag_hint"]
    assert _pipe(project)["base"] == git(project, "rev-parse", "HEAD")


def test_check_spec_escalates_unresolved_clarifications(project):
    spec = project / FEATURE / "spec.md"
    spec.write_text(SPEC_TEMPLATE + "\n- FR-001: [NEEDS CLARIFICATION: which format?]\n", encoding="utf-8")
    code, out = _cli(project, "check-spec")
    assert code == 1 and "NEEDS CLARIFICATION" in out["problems"][0]
    assert _pipe(project)["status"] == "escalated"


def test_gate_failure_appends_remediation_tasks_then_passes_to_review(project):
    _cli(project, "check-spec")
    _write_tests(project, ["003-US1-AS1"])  # two scenarios untraced

    code, out = _cli(project, "gate")
    assert code == 0 and out["checks_passed"] is False and out["finished"] is False
    tasks = (project / FEATURE / "tasks.md").read_text(encoding="utf-8")
    assert "## Phase 2: Autopilot Remediation (iteration 1, gate)" in tasks
    assert "003-US1-AS2" in tasks and "003-US2-AS1" in tasks and "003-US1-AS1`" not in tasks
    report = (project / out["report"]).read_text(encoding="utf-8")
    assert "acceptance-coverage | FAIL" in report

    _, decided = _cli(project, "decide")
    assert decided["finished"] is False

    # The implementer does the remediation work.
    _write_tests(project, ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"])
    (project / FEATURE / "tasks.md").write_text(tasks.replace("- [ ]", "- [x]"), encoding="utf-8")
    _, out = _cli(project, "gate")
    assert out["checks_passed"] is True and out["finished"] is False
    args = dict(part.split("=", 1) for part in out["review_args"].split())
    assert args["feature_dir"] == FEATURE
    diff = (project / args["diff_file"]).read_text(encoding="utf-8")
    assert "tests/test_export.py" in diff and ".specify/autopilot" not in diff

    # The independent reviewer passes it.
    (project / args["review_file"]).write_text(json.dumps({"verdict": "pass", "findings": [
        {"severity": "minor", "summary": "naming"}]}), encoding="utf-8")
    _, decided = _cli(project, "decide")
    assert decided == {"finished": True, "status": "passed", "reason": decided["reason"]}
    code, result = _cli(project, "pipe-result")
    assert code == 0 and result["status"] == "passed" and result["iteration"] == 2


def test_project_check_failure_and_repeated_identical_failure_escalates(project):
    _cli(project, "check-spec")
    _write_tests(project, ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"])
    (project / "BROKEN").write_text("x", encoding="utf-8")

    _, first = _cli(project, "gate")
    assert first["finished"] is False
    tasks = project / FEATURE / "tasks.md"
    assert "Make the 'test' gate check pass" in tasks.read_text(encoding="utf-8")
    # The implementer claims the remediation is done, but the check still fails identically.
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8")
    _, second = _cli(project, "gate")
    assert second["finished"] is True and second["status"] == "escalated"
    assert "identical gate failure" in second["reason"]
    # The same remediation task is not appended twice.
    assert (project / FEATURE / "tasks.md").read_text(encoding="utf-8").count("gate check pass") == 1
    code, _ = _cli(project, "pipe-result")
    assert code == 1


def test_iteration_cap_fails_the_pipe(project):
    _cli(project, "check-spec")
    _write_tests(project, ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"])
    tasks = project / FEATURE / "tasks.md"
    for iteration in range(1, 5):
        # A different open task each time: failing, but never identically.
        tasks.write_text(tasks.read_text(encoding="utf-8") + f"- [ ] T10{iteration} more work {iteration}\n", encoding="utf-8")
        _, out = _cli(project, "gate")
    assert out["finished"] is True and out["status"] == "failed" and "iteration cap (4)" in out["reason"]


def _green_gate(project: Path) -> dict:
    _cli(project, "check-spec")
    _write_tests(project, ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"])
    _, out = _cli(project, "gate")
    assert out["checks_passed"] is True
    return dict(part.split("=", 1) for part in out["review_args"].split())


def test_blocking_review_findings_become_tasks_even_if_verdict_says_pass(project):
    args = _green_gate(project)
    (project / args["review_file"]).write_text(json.dumps({"verdict": "pass", "findings": [
        {"id": "R1", "severity": "major", "requirement": "FR-002", "file": "src/x.py",
         "summary": "empty report crashes", "fix": "emit header"}]}), encoding="utf-8")
    _, decided = _cli(project, "decide")
    assert decided["finished"] is False
    tasks = (project / FEATURE / "tasks.md").read_text(encoding="utf-8")
    assert "Autopilot Remediation (iteration 1, review)" in tasks
    assert "Review R1 (major) [FR-002] in src/x.py: empty report crashes. Fix: emit header" in tasks


def test_reviewer_that_edits_the_tree_is_escalated(project):
    args = _green_gate(project)
    (project / "src_hack.py").write_text("print('reviewer was here')\n", encoding="utf-8")
    (project / args["review_file"]).write_text(json.dumps({"verdict": "pass", "findings": []}), encoding="utf-8")
    _, decided = _cli(project, "decide")
    assert decided["finished"] is True and decided["status"] == "escalated"
    assert "reviewer changed the working tree" in decided["reason"]


@pytest.mark.parametrize(
    "content",
    ["not json", json.dumps({"verdict": "maybe"}), json.dumps({"verdict": "pass", "findings": [{"severity": "huge", "summary": "x"}]})],
)
def test_unusable_review_does_not_pass(project, content):
    args = _green_gate(project)
    (project / args["review_file"]).write_text(content, encoding="utf-8")
    _, decided = _cli(project, "decide")
    assert decided["finished"] is False and decided["status"] == "running"


def test_missing_review_does_not_pass(project):
    _green_gate(project)
    _, decided = _cli(project, "decide")
    assert decided["finished"] is False and "did not write" in decided["reason"]
