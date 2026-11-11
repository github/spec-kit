"""Bundled gates can be answered when a workflow has no terminal (#5389)."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("workflow_id", "gate_id", "verdict_input"),
    [
        ("speckit", "review-spec", "spec_verdict"),
        ("speckit", "review-plan", "plan_verdict"),
        ("bugfix", "review-assessment", "assessment_verdict"),
    ],
)
def test_bundled_gate_resumes_without_tty(
    tmp_path, monkeypatch, workflow_id, gate_id, verdict_input
):
    source = yaml.safe_load(
        (ROOT / "workflows" / workflow_id / "workflow.yml").read_text()
    )
    gate = next(step for step in source["steps"] if step["id"] == gate_id)
    assert gate["verdict_input"] == verdict_input
    assert source["inputs"][verdict_input] == {
        "type": "string",
        "enum": ["", "approve", "reject"],
        "default": "",
    }

    # Keep the shipped gate and input schema, replacing agent commands with a
    # local shell step so this exercises CLI run/resume without an agent.
    source["steps"] = [gate, {"id": "after", "type": "shell", "run": "true"}]
    source["inputs"] = {verdict_input: source["inputs"][verdict_input]}
    source["workflow"]["id"] = f"gate-{gate_id}"
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(yaml.safe_dump(source), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    started = runner.invoke(app, ["workflow", "run", str(workflow), "--json"])
    assert started.exit_code == 0, started.output
    run_id = json.loads(started.stdout)["run_id"]
    assert json.loads(started.stdout)["status"] == "paused"

    empty = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
    assert empty.exit_code == 0, empty.output
    assert json.loads(empty.stdout)["status"] == "paused"

    explicit_empty = runner.invoke(
        app,
        ["workflow", "resume", run_id, "--json", "--input", f"{verdict_input}="],
    )
    assert explicit_empty.exit_code == 0, explicit_empty.output
    assert json.loads(explicit_empty.stdout)["status"] == "paused"

    approved = runner.invoke(
        app,
        ["workflow", "resume", run_id, "--json", "--input", f"{verdict_input}=approve"],
    )
    assert approved.exit_code == 0, approved.output
    assert json.loads(approved.stdout)["status"] == "completed"
