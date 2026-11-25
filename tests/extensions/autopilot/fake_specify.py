"""Stand-in for ``specify workflow run autopilot-epic`` used by the driver tests.

It plays the agents (developer, team lead, reviewer): writes spec.md, tasks.md,
code and tests, checks tasks off, answers questions and writes the reviewer's
verdict. It calls the real deterministic steps (``consult``, ``record``,
``check-spec``, ``gate``, ``decide``, ``pipe-result``) in the same order as
``workflows/autopilot-epic/workflow.yml``.

Markers in the epic brief select behaviour:
  MISSING-TEST   never write the acceptance tests (the gate keeps failing)
  REVIEW-ONCE    the first review reports a major finding, later ones pass
  SHARED:<text>  also write <text> into shared.txt (to provoke merge conflicts)
  SPEC-MARKER    leave a [NEEDS CLARIFICATION] marker in spec.md for the lead
  ASK-LEAD       the developer asks the lead a question during the first build
  ASK-HUMAN      like ASK-LEAD, but the lead hands it to the product owner
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

CLI = Path(".specify/extensions/autopilot/scripts/python/autopilot.py")


def step(*args: str) -> dict:
    result = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, encoding="utf-8")
    sys.stderr.write(result.stderr)
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        payload = {}
    payload["_exit"] = result.returncode
    return payload


def lead(brief: str, consult: dict) -> None:
    """The team lead answers every open question (or hands it to the product owner)."""
    if not consult.get("open"):
        return
    args = dict(part.split("=", 1) for part in consult["lead_args"].split())
    for qid in args["ids"].split(","):
        target = Path(args["questions_dir"]) / f"{qid}.answer.json"
        if "ASK-HUMAN" in brief and "-Q" in qid:
            body = {"needs_human": True, "why": "scope decision", "options": ["CSV", "XLSX"], "recommendation": "CSV"}
        else:
            body = {"answer": "Use ISO-8601 UTC timestamps everywhere", "rationale": "program convention", "applies_to": "program"}
        target.write_text(json.dumps(body), encoding="utf-8")


def consult_round(brief: str, stage: str) -> dict:
    lead(brief, step("consult", "--stage", stage))
    return step("record", "--stage", stage)


def main(argv: list[str]) -> int:
    inputs = dict(arg.split("=", 1) for arg in argv if "=" in arg and not arg.startswith("-"))
    brief = inputs.get("brief", "")
    phase = inputs.get("phase", "full")
    feature = Path(os.environ["SPECIFY_FEATURE_DIRECTORY"])
    slug = re.sub(r"^\d+-", "", feature.name)
    run_id = uuid.uuid4().hex[:8]
    runs = Path(".specify/workflows/runs") / run_id
    runs.mkdir(parents=True)
    context = Path(".specify/autopilot/context")
    (runs / "context-seen.txt").write_text(
        "\n".join(sorted(p.name for p in context.glob("*.md"))) if context.is_dir() else "", encoding="utf-8"
    )

    def finish(status: str) -> int:
        (runs / "state.json").write_text(json.dumps({"run_id": run_id, "workflow_id": "autopilot-epic", "status": status}))
        print(json.dumps({"run_id": run_id, "workflow_id": "autopilot-epic", "status": status}))
        return 0 if status == "completed" else 1

    if phase == "full":
        feature.mkdir(parents=True, exist_ok=True)
        marker = "\n- FR-001: [NEEDS CLARIFICATION: timestamp format?]\n" if "SPEC-MARKER" in brief else ""
        (feature / "spec.md").write_text(
            f"# {slug}\n\n### User Story 1 - Do it (Priority: P1)\n\n**Acceptance Scenarios**:\n\n"
            "1. **Given** x, **When** y, **Then** z\n" + marker,
            encoding="utf-8",
        )
    consult_round(brief, "spec")
    spec = step("check-spec")
    if spec["_exit"]:
        return finish("failed")
    tags = spec["scenarios"]
    if phase != "build":
        (feature / "tasks.md").write_text("# Tasks\n\n## Phase 1: Build\n\n- [ ] T001 Build it\n", encoding="utf-8")
    if consult_round(brief, "design").get("finished"):
        return finish("completed" if step("pipe-result")["_exit"] == 0 else "failed")

    reviews = 0
    for iteration in range(25):
        # "implement": do the work and check every open task off.
        Path("src").mkdir(exist_ok=True)
        (Path("src") / f"{slug}.txt").write_text(f"{slug} implemented\n", encoding="utf-8")
        if "SHARED:" in brief:
            Path("shared.txt").write_text(brief.split("SHARED:", 1)[1].split()[0] + "\n", encoding="utf-8")
        if "MISSING-TEST" not in brief:
            Path("tests").mkdir(exist_ok=True)
            (Path("tests") / f"test_{slug.replace('-', '_')}.py").write_text(
                "".join(f"def test_{t.replace('-', '_').lower()}():\n    assert True\n" for t in tags), encoding="utf-8"
            )
        tasks = feature / "tasks.md"
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ]", "- [X]"), encoding="utf-8")
        asked = any(Path(".specify/autopilot/pipes").glob("*/questions/*-Q*.json"))
        if iteration == 0 and ("ASK-LEAD" in brief or "ASK-HUMAN" in brief) and not asked:
            inbox = Path(".specify/autopilot/inbox/questions")
            inbox.mkdir(parents=True, exist_ok=True)
            (inbox / "format.json").write_text(json.dumps({
                "question": "Which export format?" if "ASK-HUMAN" in brief else "Which timestamp format?",
                "context": "writing the exporter", "options": ["A", "B"], "recommendation": "A", "blocking": True,
            }), encoding="utf-8")

        consult_round(brief, "build")
        gate = step("gate")
        if gate.get("checks_passed") and not gate.get("finished"):
            reviews += 1
            args = dict(part.split("=", 1) for part in gate["review_args"].split())
            findings = []
            if "REVIEW-ONCE" in brief and reviews == 1:
                findings = [{"id": "R1", "severity": "major", "summary": "edge case unhandled", "fix": "handle it"}]
            Path(args["review_file"]).write_text(
                json.dumps({"verdict": "fail" if findings else "pass", "summary": "ok", "findings": findings}),
                encoding="utf-8",
            )
        if step("decide").get("finished"):
            break
    return finish("completed" if step("pipe-result")["_exit"] == 0 else "failed")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:2] == ["workflow", "run"]:
        sys.exit(main(args[2:]))
    print(json.dumps({"error": f"fake specify does not support {args}"}))
    sys.exit(2)
