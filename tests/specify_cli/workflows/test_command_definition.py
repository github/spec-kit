"""Tests for ``specify workflow definition``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.catalog import WorkflowRegistry
from tests.specify_cli.workflows import helpers


def _invoke(project_dir, args):
    from unittest.mock import patch

    from typer.testing import CliRunner

    from specify_cli import app

    with patch.object(Path, "cwd", return_value=project_dir):
        return CliRunner().invoke(app, args, catch_exceptions=False)


def _run(project_dir, text, name="root"):
    path = project_dir / f"{name}.yml"
    path.write_text(text, encoding="utf-8")
    result = _invoke(project_dir, ["workflow", "run", str(path), "--json"])
    return json.loads(result.stdout)


def _definition(project_dir, run_id, *extra):
    return _invoke(project_dir, ["workflow", "definition", run_id, "--json", *extra])


def _status(project_dir, run_id):
    return json.loads(
        _invoke(project_dir, ["workflow", "status", run_id, "--json"]).stdout
    )


def _install(project_dir, workflow_id, body):
    wf_dir = project_dir / ".specify" / "workflows" / workflow_id
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "workflow.yml").write_text(body, encoding="utf-8")
    WorkflowRegistry(project_dir).add(workflow_id, {"enabled": True})


def _snapshot(project_dir, run_id) -> Path:
    return project_dir / ".specify" / "workflows" / "runs" / run_id / "workflow.yml"


def _assert_json_error(result, fragment):
    assert result.exit_code == 1, result.output
    assert result.stdout == ""
    error = json.loads(result.stderr)
    assert list(error) == ["error"]
    assert fragment in error["error"]


GATE_WF = """
schema_version: "1.0"
workflow:
  id: "gate-wf"
  name: "Gate WF"
  version: "1.0.0"
steps:
  - id: approve
    type: gate
    message: "Review"
    options: [approve, reject]
    on_reject: abort
  - id: after
    type: shell
    run: "echo done"
"""

CHILD = (
    "workflow: {id: child, name: Child}\n"
    "inputs:\n  verdict: {type: string, default: ''}\n"
    "steps:\n  - {id: review, type: gate, message: Review, verdict_input: verdict}\n"
)

PARENT = (
    "workflow: {id: parent, name: Parent}\n"
    "inputs:\n  verdict: {type: string, default: ''}\n"
    "steps:\n  - id: call\n    type: workflow\n    workflow: child\n"
    "    input: {verdict: '{{ inputs.verdict }}'}\n"
)


def _gate_scope(definition, scopes, gate):
    """Join rule from the contract: longest-prefix scope, then step_id."""
    path = gate.get("scope_path", [])
    best = None
    for scope in scopes:
        n = len(scope["scope_path"])
        if path[:n] == scope["scope_path"] and (best is None or n > len(best["scope_path"])):
            best = scope
    root = best["definition"] if best else definition
    step_id = gate["step_id"]
    if step_id.count(":") >= 2:
        step_id = step_id.split(":")[-2]

    def find(steps):
        for step in steps:
            if step.get("id") == step_id:
                return step
            for key in ("then", "else", "steps", "default"):
                if isinstance(step.get(key), list) and (found := find(step[key])):
                    return found
            for case in (step.get("cases") or {}).values():
                if found := find(case):
                    return found
            if isinstance(step.get("step"), dict) and (found := find([step["step"]])):
                return found
        return None

    return find(root["steps"])


class TestPositive:
    def test_metadata_and_gate_fields(self, project_dir):
        run = _run(project_dir, GATE_WF)
        result = _definition(project_dir, run["run_id"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        # 14. exactly the contracted envelope
        assert list(payload) == ["run_id", "definition", "workflow_scopes"]
        assert payload["run_id"] == run["run_id"]
        definition = payload["definition"]
        assert definition["schema_version"] == "1.0"
        assert definition["workflow"] == {
            "id": "gate-wf", "name": "Gate WF", "version": "1.0.0",
        }
        gate = definition["steps"][0]
        assert gate["message"] == "Review"
        assert gate["options"] == ["approve", "reject"]
        assert gate["on_reject"] == "abort"
        assert payload["workflow_scopes"] == []

    def test_nested_steps_preserved(self, project_dir):
        text = """
workflow: {id: nested, name: Nested}
steps:
  - {id: g, type: gate, message: first}
  - id: branch
    type: if
    condition: "{{ true }}"
    then: [{id: t1, type: shell, run: "echo t"}]
    else: [{id: e1, type: shell, run: "echo e"}]
  - id: pick
    type: switch
    expression: "{{ 'a' }}"
    cases:
      a: [{id: ca, type: shell, run: "echo a"}]
    default: [{id: dflt, type: shell, run: "echo d"}]
  - id: w
    type: while
    condition: "{{ false }}"
    max_iterations: 2
    steps: [{id: wbody, type: shell, run: "echo w"}]
  - id: dw
    type: do-while
    condition: "{{ false }}"
    max_iterations: 2
    steps: [{id: dwbody, type: shell, run: "echo dw"}]
  - id: fan
    type: fan-out
    items: "{{ ['a'] }}"
    step: {id: item, type: shell, run: "echo item"}
"""
        run = _run(project_dir, text)
        definition = json.loads(_definition(project_dir, run["run_id"]).stdout)["definition"]
        steps = {s["id"]: s for s in definition["steps"]}
        assert steps["branch"]["then"][0]["id"] == "t1"
        assert steps["branch"]["else"][0]["id"] == "e1"
        assert steps["pick"]["cases"]["a"][0]["id"] == "ca"
        assert steps["pick"]["default"][0]["id"] == "dflt"
        assert steps["w"]["steps"][0]["id"] == "wbody"
        assert steps["dw"]["steps"][0]["id"] == "dwbody"
        assert steps["fan"]["step"]["id"] == "item"

    def test_verbatim_no_defaults_and_unknown_keys_kept(self, project_dir):
        text = (
            "workflow: {id: bare, name: Bare}\n"
            "custom_key: {a: 1}\n"
            "requires: {speckit_version: '>=0.1.0'}\n"
            "steps:\n  - {id: g, type: gate, message: hi}\n"
        )
        run = _run(project_dir, text)
        definition = json.loads(_definition(project_dir, run["run_id"]).stdout)["definition"]
        assert definition["steps"] == [{"id": "g", "type": "gate", "message": "hi"}]
        assert definition["custom_key"] == {"a": 1}
        assert definition["requires"] == {"speckit_version": ">=0.1.0"}
        assert "schema_version" not in definition

    def test_plain_json_dates_are_strings(self, project_dir):
        # An unknown top-level key is passed through verbatim (C3), so an
        # unquoted date reaches the JSON boundary as a datetime.date.
        text = (
            "workflow: {id: dated, name: Dated}\n"
            "released: 2026-01-01\n"
            "steps:\n  - {id: g, type: gate, message: hi}\n"
        )
        run = _run(project_dir, text)
        snapshot = yaml.safe_load(_snapshot(project_dir, run["run_id"]).read_text())
        assert str(snapshot["released"]) == "2026-01-01"
        assert not isinstance(snapshot["released"], str)  # snapshot keeps YAML type
        result = _definition(project_dir, run["run_id"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["definition"]["released"] == "2026-01-01"

    def test_plain_json_date_mapping_keys_are_strings(self, project_dir):
        text = (
            "workflow: {id: dated-key, name: Dated Key}\n"
            "steps:\n"
            "  - id: route\n"
            "    type: switch\n"
            "    expression: '{{ 1 }}'\n"
            "    cases:\n"
            "      2026-01-01: [{id: g, type: gate, message: hi}]\n"
        )
        run = _run(project_dir, text)
        result = _definition(project_dir, run["run_id"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["definition"]["steps"][0]["cases"] == {
            "2026-01-01": [{"id": "g", "type": "gate", "message": "hi"}],
        }

    @pytest.mark.parametrize("value", [".nan", ".inf"])
    def test_plain_json_non_finite_floats_are_strings(self, project_dir, value):
        text = (
            "workflow: {id: non-finite, name: Non Finite}\n"
            f"x: {value}\n"
            "steps:\n  - {id: g, type: gate, message: hi}\n"
        )
        run = _run(project_dir, text)
        result = _definition(project_dir, run["run_id"])
        assert result.exit_code == 0, result.output

        def reject_constant(constant):
            raise ValueError(constant)

        assert json.loads(result.stdout, parse_constant=reject_constant)["definition"]["x"] == value[1:]

    def test_installed_workflow_modified_does_not_change_output(self, project_dir):
        _install(project_dir, "gate-wf", GATE_WF)
        run = json.loads(
            _invoke(project_dir, ["workflow", "run", "gate-wf", "--json"]).stdout
        )
        before = _definition(project_dir, run["run_id"]).stdout
        wf = project_dir / ".specify" / "workflows" / "gate-wf" / "workflow.yml"
        wf.write_text(
            GATE_WF.replace("approve\n    type", "renamed\n    type").replace(
                'message: "Review"', 'message: "Changed"'
            ),
            encoding="utf-8",
        )
        after = _definition(project_dir, run["run_id"])
        assert after.exit_code == 0
        assert after.stdout == before
        assert "Changed" not in after.stdout

    def test_installed_workflow_removed_still_returns_definition(self, project_dir):
        _install(project_dir, "gate-wf", GATE_WF)
        run = json.loads(
            _invoke(project_dir, ["workflow", "run", "gate-wf", "--json"]).stdout
        )
        removed = _invoke(project_dir, ["workflow", "remove", "gate-wf"])
        assert removed.exit_code == 0, removed.output
        result = _definition(project_dir, run["run_id"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["definition"]["workflow"]["id"] == "gate-wf"

    def test_overlay_applied(self, project_dir):
        _install(project_dir, "gate-wf", GATE_WF)
        helpers.write_overlay(
            project_dir, "gate-wf", "ov1", {
                "id": "ov1",
                "extends": "gate-wf",
                "priority": 10,
                "edits": [{
                    "operation": "insert_after",
                    "anchor": "approve",
                    "step": {"id": "added", "type": "shell", "run": "echo added"},
                }],
            },
        )
        run = json.loads(
            _invoke(project_dir, ["workflow", "run", "gate-wf", "--json"]).stdout
        )
        steps = json.loads(_definition(project_dir, run["run_id"]).stdout)["definition"]["steps"]
        assert [s["id"] for s in steps] == ["approve", "added", "after"]


class TestContract:
    def test_json_flag_required(self, project_dir):
        run = _run(project_dir, GATE_WF)
        for rid in (run["run_id"], "does-not-exist"):
            result = _invoke(project_dir, ["workflow", "definition", rid])
            assert result.exit_code == 2
            assert result.stdout == ""
            assert "--json" in result.stderr

    def test_json_usage_error_uses_json_contract(self, project_dir):
        result = _invoke(project_dir, ["workflow", "definition", "--json"])
        assert result.exit_code == 2
        assert result.stdout == ""
        assert list(json.loads(result.stderr)) == ["error"]


class TestComposition:
    def _call_run(self, project_dir, parent=PARENT):
        _install(project_dir, "child", CHILD)
        return _run(project_dir, parent, "parent")

    def test_bound_call_matches_status(self, project_dir):
        run = self._call_run(project_dir)
        assert run["status"] == "paused"
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        status = _status(project_dir, run["run_id"])
        # the root keeps the call step as authored; nothing is injected
        assert payload["definition"]["steps"] == [{
            "id": "call", "type": "workflow", "workflow": "child",
            "input": {"verdict": "{{ inputs.verdict }}"},
        }]
        [scope] = payload["workflow_scopes"]
        assert (scope["scope_path"], scope["workflow_id"]) == (
            status["workflow_scopes"][0]["scope_path"],
            status["workflow_scopes"][0]["workflow_id"],
        )
        assert scope["scope_path"] == ["call"]
        assert scope["definition"]["steps"][0]["message"] == "Review"
        gate = _gate_scope(payload["definition"], payload["workflow_scopes"], status["gate"])
        assert gate["id"] == "review"

    def test_nested_gate_join_uses_prefix_not_exact_match(self, project_dir):
        _install(
            project_dir, "child",
            "workflow: {id: child, name: Child}\n"
            "steps:\n"
            "  - id: wrap\n    type: if\n    condition: '{{ true }}'\n"
            "    then: [{id: review, type: gate, message: Review}]\n",
        )
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "steps:\n"
            "  - id: route\n    type: if\n    condition: '{{ true }}'\n"
            "    then: [{id: call, type: workflow, workflow: child}]\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        gate = _status(project_dir, run["run_id"])["gate"]
        assert gate["scope_path"] == ["route", "call", "wrap"]
        assert [s["scope_path"] for s in payload["workflow_scopes"]] == [["route", "call"]]
        found = _gate_scope(payload["definition"], payload["workflow_scopes"], gate)
        assert found["message"] == "Review"

    def test_root_gate_inside_if_has_no_scope(self, project_dir):
        text = (
            "workflow: {id: r, name: R}\n"
            "steps:\n  - id: route\n    type: if\n    condition: '{{ true }}'\n"
            "    then: [{id: g, type: gate, message: Hello}]\n"
        )
        run = _run(project_dir, text)
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        gate = _status(project_dir, run["run_id"])["gate"]
        assert gate["scope_path"] == ["route"]
        assert payload["workflow_scopes"] == []
        assert _gate_scope(payload["definition"], [], gate)["message"] == "Hello"

    def test_nested_calls_longest_prefix_wins(self, project_dir):
        _install(project_dir, "inner", CHILD.replace("id: child", "id: inner"))
        _install(
            project_dir, "outer",
            "workflow: {id: outer, name: Outer}\n"
            "inputs:\n  verdict: {type: string, default: ''}\n"
            "steps:\n  - id: inner\n    type: workflow\n    workflow: inner\n"
            "    input: {verdict: '{{ inputs.verdict }}'}\n",
        )
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "inputs:\n  verdict: {type: string, default: ''}\n"
            "steps:\n  - id: outer\n    type: workflow\n    workflow: outer\n"
            "    input: {verdict: '{{ inputs.verdict }}'}\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        assert [(s["scope_path"], s["workflow_id"]) for s in payload["workflow_scopes"]] == [
            (["outer"], "outer"), (["outer", "inner"], "inner"),
        ]
        gate = _status(project_dir, run["run_id"])["gate"]
        assert _gate_scope(
            payload["definition"], payload["workflow_scopes"], gate
        )["id"] == "review"

    def test_call_inside_loop_scope_path(self, project_dir):
        _install(project_dir, "child", CHILD)
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "inputs:\n  verdict: {type: string, default: ''}\n"
            "steps:\n  - id: loop\n    type: do-while\n    condition: '{{ false }}'\n"
            "    max_iterations: 1\n"
            "    steps:\n      - id: call\n        type: workflow\n        workflow: child\n"
            "        input: {verdict: '{{ inputs.verdict }}'}\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        assert [s["scope_path"] for s in payload["workflow_scopes"]] == [["loop", "0", "call"]]

    def test_callee_drift_frozen(self, project_dir):
        run = self._call_run(project_dir)
        before = _definition(project_dir, run["run_id"]).stdout
        child = project_dir / ".specify" / "workflows" / "child" / "workflow.yml"
        child.write_text(CHILD.replace("message: Review", "message: Changed"), encoding="utf-8")
        assert _definition(project_dir, run["run_id"]).stdout == before
        removed = _invoke(project_dir, ["workflow", "remove", "child"])
        assert removed.exit_code == 0, removed.output
        after = _definition(project_dir, run["run_id"])
        assert after.exit_code == 0, after.output
        assert after.stdout == before
        assert "Changed" not in after.stdout

    def test_unbound_call_is_absent(self, project_dir):
        _install(project_dir, "child", CHILD)
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "steps:\n"
            "  - {id: first, type: gate, message: Wait}\n"
            "  - {id: call, type: workflow, workflow: child}\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        assert payload["workflow_scopes"] == []
        assert payload["definition"]["steps"][1] == {
            "id": "call", "type": "workflow", "workflow": "child",
        }

    def test_failed_binding_is_absent(self, project_dir):
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "steps:\n  - {id: call, type: workflow, workflow: missing}\n"
        )
        run = _run(project_dir, parent, "parent")
        assert run["status"] == "failed"
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        assert payload["workflow_scopes"] == []
        assert payload["definition"]["steps"][0]["workflow"] == "missing"

    def test_same_call_bound_per_fan_out_item(self, project_dir):
        _install(
            project_dir,
            "child",
            "workflow: {id: child, name: Child}\n"
            "steps: [{id: noop, type: shell, run: 'true'}]\n",
        )
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "steps:\n  - id: fan\n    type: fan-out\n    items: \"{{ ['a', 'b'] }}\"\n"
            "    max_concurrency: 1\n"
            "    step: {id: call, type: workflow, workflow: child}\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        paths = [s["scope_path"] for s in payload["workflow_scopes"]]
        assert paths == [["fan", "0", "call"], ["fan", "1", "call"]]
        assert paths == [s["scope_path"] for s in _status(project_dir, run["run_id"])["workflow_scopes"]]

    def test_same_call_bound_per_loop_iteration(self, project_dir):
        _install(
            project_dir,
            "child",
            "workflow: {id: child, name: Child}\n"
            "steps: [{id: noop, type: shell, run: 'true'}]\n",
        )
        parent = (
            "workflow: {id: parent, name: Parent}\n"
            "steps:\n  - id: loop\n    type: do-while\n"
            "    condition: '{{ true }}'\n    max_iterations: 2\n"
            "    steps:\n      - {id: call, type: workflow, workflow: child}\n"
        )
        run = _run(project_dir, parent, "parent")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        paths = [s["scope_path"] for s in payload["workflow_scopes"]]
        assert paths == [["loop", "0", "call"], ["loop", "1", "call"]]
        assert paths == [s["scope_path"] for s in _status(project_dir, run["run_id"])["workflow_scopes"]]

    def test_overlaid_callee(self, project_dir):
        _install(project_dir, "child", CHILD)
        helpers.write_overlay(
            project_dir, "child", "ov1", {
                "id": "ov1", "extends": "child", "priority": 10,
                "edits": [{
                    "operation": "insert_before", "anchor": "review",
                    "step": {"id": "prep", "type": "shell", "run": "echo prep"},
                }],
            },
        )
        run = _run(project_dir, PARENT, "parent")
        [scope] = json.loads(_definition(project_dir, run["run_id"]).stdout)["workflow_scopes"]
        assert [s["id"] for s in scope["definition"]["steps"]] == ["prep", "review"]

    def test_legacy_run_without_execution_tree(self, project_dir):
        run = self._call_run(project_dir)
        state_path = project_dir / ".specify" / "workflows" / "runs" / run["run_id"] / "state.json"
        state = json.loads(state_path.read_text())
        state.pop("execution", None)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        payload = json.loads(_definition(project_dir, run["run_id"]).stdout)
        assert payload["workflow_scopes"] == []
        assert payload["definition"]["steps"][0]["id"] == "call"


class TestNegative:
    def test_unknown_run(self, project_dir):
        _assert_json_error(_definition(project_dir, "nope"), "Run not found: nope")

    def test_invalid_run_id(self, project_dir):
        _assert_json_error(_definition(project_dir, "../escape"), "Invalid run_id")

    def test_not_a_project(self, temp_dir):
        _assert_json_error(_definition(temp_dir, "x"), "Not a Spec Kit project")

    def test_symlinked_workflow_runs_storage(self, project_dir, tmp_path):
        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        runs_dir.mkdir(parents=True)
        runs_dir.rmdir()
        runs_dir.symlink_to(tmp_path, target_is_directory=True)
        result = _definition(project_dir, "run")
        _assert_json_error(result, "Refusing to use symlinked .specify/workflows/runs path")

    def test_invalid_specify_init_dir(self, project_dir, tmp_path, monkeypatch):
        invalid_root = tmp_path / "not-a-project"
        invalid_root.mkdir()
        monkeypatch.setenv("SPECIFY_INIT_DIR", str(invalid_root))
        result = _definition(project_dir, "run")
        _assert_json_error(
            result,
            f"SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): {invalid_root}",
        )

    def test_missing_snapshot_does_not_fall_back(self, project_dir):
        _install(project_dir, "gate-wf", GATE_WF)
        run = json.loads(
            _invoke(project_dir, ["workflow", "run", "gate-wf", "--json"]).stdout
        )
        _snapshot(project_dir, run["run_id"]).unlink()
        result = _definition(project_dir, run["run_id"])
        _assert_json_error(result, "has no persisted workflow definition")
        assert "approve" not in result.stderr

    def test_recursive_yaml_alias_returns_json_error(self, project_dir):
        recursive_workflow = GATE_WF + "\nmetadata: &loop\n  self: *loop\n"
        run = _run(project_dir, recursive_workflow)

        result = _definition(project_dir, run["run_id"])

        _assert_json_error(result, "cannot represent recursive YAML aliases")

    @pytest.mark.parametrize("content", [": : :\n  - [", "- a\n- b\n"])
    def test_corrupt_snapshot(self, project_dir, content):
        run = _run(project_dir, GATE_WF)
        _snapshot(project_dir, run["run_id"]).write_text(content, encoding="utf-8")
        _assert_json_error(
            _definition(project_dir, run["run_id"]), "Invalid workflow definition"
        )

    def _mutate_state(self, project_dir, run_id, mutate):
        path = project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        state = json.loads(path.read_text())
        mutate(state["execution"])
        path.write_text(json.dumps(state), encoding="utf-8")

    def test_unsupported_execution_version(self, project_dir):
        _install(project_dir, "child", CHILD)
        run = _run(project_dir, PARENT, "parent")
        self._mutate_state(project_dir, run["run_id"], lambda e: e.update(version=999))
        _assert_json_error(
            _definition(project_dir, run["run_id"]), "Unsupported execution version"
        )

    def test_malformed_execution_tree(self, project_dir):
        _install(project_dir, "child", CHILD)
        run = _run(project_dir, PARENT, "parent")
        self._mutate_state(project_dir, run["run_id"], lambda e: e.pop("sequence"))
        _assert_json_error(
            _definition(project_dir, run["run_id"]), "Invalid execution state"
        )

    def test_invalid_bound_callee_definition(self, project_dir):
        _install(project_dir, "child", CHILD)
        run = _run(project_dir, PARENT, "parent")

        def corrupt(execution):
            execution["sequence"]["nodes"][0]["binding"]["definition"] = "- a\n- b\n"

        self._mutate_state(project_dir, run["run_id"], corrupt)
        _assert_json_error(
            _definition(project_dir, run["run_id"]), "Invalid bound workflow definition"
        )
