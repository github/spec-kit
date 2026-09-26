"""Command-focused workflow tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer



class TestWorkflowJsonOutput:
    """Test the --json machine-readable output for run/resume/status."""

    _WF = """
schema_version: "1.0"
workflow:
  id: "json-wf"
  name: "JSON WF"
  version: "1.0.0"
steps:
  - id: ask
    type: gate
    message: "Review"
    options: [approve, reject]
  - id: after
    type: shell
    run: "echo done"
"""

    _WF_FAIL = """
schema_version: "1.0"
workflow:
  id: "json-fail"
  name: "JSON Fail"
  version: "1.0.0"
steps:
  - id: boom
    type: shell
    run: "exit 3"
"""

    def _write_wf(self, project_dir, text, name):
        path = project_dir / f"{name}.yml"
        path.write_text(text, encoding="utf-8")
        return path

    def _invoke(self, project_dir, args):
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            return runner.invoke(app, args, catch_exceptions=False)

    def test_status_json_failed_includes_error(self, project_dir):
        # `status --json` reuses the shared payload, so a failed run inspected
        # after the fact surfaces the same error text as `run`/`resume`.
        wf = self._write_wf(project_dir, self._WF_FAIL, "boom2")
        rid = json.loads(
            self._invoke(
                project_dir, ["workflow", "run", str(wf), "--json"]
            ).stdout
        )["run_id"]
        status = json.loads(
            self._invoke(
                project_dir, ["workflow", "status", rid, "--json"]
            ).stdout
        )
        assert status["status"] == "failed"
        assert status.get("error")

    def test_status_json_single_and_list(self, project_dir):
        wf = self._write_wf(project_dir, self._WF, "gated2")
        run = json.loads(
            self._invoke(project_dir, ["workflow", "run", str(wf), "--json"]).stdout
        )
        rid = run["run_id"]

        single = json.loads(
            self._invoke(project_dir, ["workflow", "status", rid, "--json"]).stdout
        )
        assert single["run_id"] == rid
        assert single["status"] == "paused"
        assert single["steps"]["ask"] == "paused"
        # status --json carries the same step-position fields as run/resume
        # so automation never has to branch on which command produced it.
        assert single["current_step_id"] == run["current_step_id"]
        assert single["current_step_index"] == run["current_step_index"]

        listing = json.loads(
            self._invoke(project_dir, ["workflow", "status", "--json"]).stdout
        )
        assert any(r["run_id"] == rid for r in listing["runs"])

    def test_composed_gate_status_and_resume(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        child_dir = project_dir / ".specify" / "workflows" / "child"
        child_dir.mkdir(parents=True)
        (child_dir / "workflow.yml").write_text(
            "workflow: {id: child, name: Child}\n"
            "inputs:\n  verdict: {type: string, default: ''}\n"
            "steps:\n  - {id: review, type: gate, message: Review, verdict_input: verdict}\n",
            encoding="utf-8",
        )
        WorkflowRegistry(project_dir).add("child", {"enabled": True})
        root = self._write_wf(
            project_dir,
            "workflow: {id: parent, name: Parent}\n"
            "inputs:\n  verdict: {type: string, default: ''}\n"
            "steps:\n  - id: call\n    type: workflow\n    workflow: child\n"
            "    input: {verdict: '{{ inputs.verdict }}'}\n",
            "parent",
        )
        run = json.loads(self._invoke(project_dir, ["workflow", "run", str(root), "--json"]).stdout)
        assert run["status"] == "paused", run
        status = json.loads(self._invoke(project_dir, ["workflow", "status", run["run_id"], "--json"]).stdout)
        assert status["gate"] == run["gate"]
        assert status["gate"]["scope_path"] == ["call"]
        assert status["workflow_scopes"] == [{"scope_path": ["call"], "workflow_id": "child", "status": "paused"}]
        human = self._invoke(project_dir, ["workflow", "status", run["run_id"]])
        assert "child: paused" in human.stdout
        resumed = self._invoke(project_dir, ["workflow", "resume", run["run_id"], "--input", "verdict=approve", "--json"])
        assert resumed.exit_code == 0
        assert json.loads(resumed.stdout)["status"] == "completed"



class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    _GATED_WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "gated-wf"
  name: "Gated Workflow"
  version: "1.0.0"
steps:
  - id: ask
    type: gate
    message: "Review"
    options: [approve, reject]
"""

    def _install_and_run_gated(self, runner, app, project_dir):
        """Install a gate-step workflow and run it to a paused state.

        Returns the run_id. The gate step pauses without any interactive
        input, giving a resumable run tied to an installed workflow ID.
        """
        src = project_dir / "gated-src"
        src.mkdir(exist_ok=True)
        (src / "workflow.yml").write_text(self._GATED_WORKFLOW_YAML, encoding="utf-8")
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["workflow", "run", "gated-wf", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert payload["status"] == "paused"
        return payload["run_id"]

    @pytest.mark.parametrize(
        "field, bad_value",
        [
            ("installed_workflow_id", 123),
            ("installed_workflow_id", ["gated-wf"]),
            ("installed_registry_root", 123),
            ("installed_registry_root", ["."]),
        ],
    )
    def test_status_rejects_malformed_run_state_origin_fields(
        self, project_dir, monkeypatch, field, bad_value
    ):
        """`workflow status <run_id>` calls RunState.load() same as resume,
        but only caught FileNotFoundError -- the new type validation there
        (int/list instead of str-or-null) raises ValueError, which leaked
        as a raw unhandled traceback instead of `workflow resume`'s clean
        `[red]Error:[/red] {exc}` + exit 1. Must get the identical clean
        boundary, leaving the no-run-id list path (and FileNotFoundError
        behavior) unchanged."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        data[field] = bad_value
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "status", run_id])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Error" in result.output

    def test_status_run_not_found_unchanged(self, project_dir, monkeypatch):
        """FileNotFoundError behavior for a nonexistent run_id must remain
        exactly as before this fix."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        (project_dir / ".specify" / "workflows").mkdir(parents=True, exist_ok=True)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "status", "nonexistent-run"])
        assert result.exit_code != 0
        assert "Run not found: nonexistent-run" in result.output

    def test_status_json_not_found_error_goes_to_stderr(
        self, project_dir, monkeypatch, capsys
    ):
        """Under --json, the not-found/invalid-run error must go to stderr so the
        stdout JSON stream stays parseable (empty on the error path) — mirroring
        `workflow run`/`workflow resume`. Before this fix both handlers used the
        stdout console, corrupting a consumer's json.loads(stdout)."""
        from specify_cli.workflows import _commands

        (project_dir / ".specify" / "workflows").mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(
            _commands, "_require_specify_project", lambda: project_dir
        )
        with pytest.raises(typer.Exit) as exc:
            _commands.workflow_status("does-not-exist", json_output=True)
        assert exc.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Run not found" in captured.err
        assert "Run not found" not in captured.out
        # stdout carries no partial/corrupt JSON on the error path.
        assert captured.out.strip() == ""

    def test_status_json_invalid_run_error_goes_to_stderr(
        self, project_dir, monkeypatch, capsys
    ):
        """The ValueError handler (a malformed/invalid run state) must ALSO route
        to stderr under --json, not just the FileNotFoundError one — otherwise a
        regression there would silently corrupt the JSON stream and this suite
        wouldn't catch it."""
        from specify_cli.workflows import _commands
        from specify_cli.workflows.engine import RunState

        (project_dir / ".specify" / "workflows").mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(
            _commands, "_require_specify_project", lambda: project_dir
        )

        def _raise_value_error(*args, **kwargs):
            raise ValueError("corrupt run state: bad status")

        monkeypatch.setattr(RunState, "load", _raise_value_error)

        with pytest.raises(typer.Exit) as exc:
            _commands.workflow_status("some-run", json_output=True)
        assert exc.value.exit_code == 1
        captured = capsys.readouterr()
        assert "corrupt run state" in captured.err
        assert "corrupt run state" not in captured.out
        assert captured.out.strip() == ""

    def test_status_unreadable_run_state_exits_cleanly(
        self, project_dir, monkeypatch
    ):
        """`workflow status <run_id>` gained a ValueError boundary to match
        `workflow resume`, but not resume's OSError one -- so an unreadable
        state.json (bad permissions, a directory in its place, an I/O error)
        still leaked a raw traceback. exists() is True for a directory, so
        the guard passes and open() raises OSError."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runs_dir = project_dir / ".specify" / "workflows" / "runs" / "abc123"
        runs_dir.mkdir(parents=True, exist_ok=True)
        # A directory where state.json should be: exists() passes, open() fails.
        (runs_dir / "state.json").mkdir(exist_ok=True)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "status", "abc123"])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Error" in result.output

    def test_status_json_unreadable_run_state_error_goes_to_stderr(
        self, project_dir, monkeypatch, capsys
    ):
        """The OSError handler must route to stderr under --json too, so the
        stdout JSON stream stays parseable -- mirroring the sibling
        FileNotFoundError/ValueError handlers."""
        from specify_cli.workflows import _commands
        from specify_cli.workflows.engine import RunState

        (project_dir / ".specify" / "workflows").mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(
            _commands, "_require_specify_project", lambda: project_dir
        )

        def _raise_os_error(*args, **kwargs):
            raise PermissionError(13, "Permission denied")

        monkeypatch.setattr(RunState, "load", _raise_os_error)

        with pytest.raises(typer.Exit) as exc:
            _commands.workflow_status("some-run", json_output=True)
        assert exc.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Permission denied" in captured.err
        assert "Permission denied" not in captured.out
        assert captured.out.strip() == ""

    def test_status_no_run_id_list_path_unaffected(self, project_dir, monkeypatch):
        """The no-run-id list-all-runs path must remain unaffected by the
        new single-run ValueError boundary."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        (project_dir / ".specify" / "workflows").mkdir(parents=True, exist_ok=True)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "status"])
        assert result.exit_code == 0, result.output
