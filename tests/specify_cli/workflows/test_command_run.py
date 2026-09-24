"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

from tests.specify_cli.workflows.helpers import force_gate_stdin as _force_gate_stdin


class TestWorkflowRunGateOutcomeJson:
    """CLI-level tests: the --json payload surfaces gate pauses."""

    _WF_GATE = """
schema_version: "1.0"
workflow:
  id: "gate-json"
  name: "Gate JSON"
  version: "1.0.0"
steps:
  - id: review
    type: gate
    message: "Approve the thing?"
    options: ["approve", "reject"]
"""

    _WF_PLAIN = """
schema_version: "1.0"
workflow:
  id: "plain-json"
  name: "Plain JSON"
  version: "1.0.0"
steps:
  - id: fine
    type: shell
    run: "exit 0"
"""

    def _run_json(self, tmp_path, monkeypatch, content, *, expected_exit=0):
        import json as _json
        from typer.testing import CliRunner
        from specify_cli import app

        path = tmp_path / "wf.yml"
        path.write_text(content, encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(app, ["workflow", "run", str(path), "--json"])
        # Assert the expected exit code before parsing so a real failure
        # surfaces the actual output instead of an opaque JSON decode error.
        # A terminal run still emits its JSON payload, then exits non-zero on
        # ``failed``/``aborted`` (see ``_run_outcome_exit_code``), so callers
        # pass the expected code. Use ``result.output`` for the message:
        # under ``--json`` step output is redirected off stdout, so the useful
        # diagnostics live there.
        assert result.exit_code == expected_exit, result.output
        return _json.loads(result.stdout)

    def test_gate_pause_carries_gate_block(self, tmp_path, monkeypatch):
        # CliRunner stdin is not a TTY, so the gate pauses for resume.
        payload = self._run_json(tmp_path, monkeypatch, self._WF_GATE)
        assert payload["status"] == "paused"
        assert payload["gate"] == {
            "step_id": "review",
            "message": "Approve the thing?",
            "options": ["approve", "reject"],
            "choice": None,
        }

    def test_completed_run_has_no_gate_block(self, tmp_path, monkeypatch):
        payload = self._run_json(tmp_path, monkeypatch, self._WF_PLAIN)
        assert payload["status"] == "completed"
        assert "gate" not in payload

    def test_gate_abort_carries_gate_block(self, tmp_path, monkeypatch):
        # An interactive gate the operator rejects ends the run as `aborted`
        # (on_reject defaults to abort), not `paused`. The JSON surface must
        # still carry the gate block with the recorded choice so an
        # orchestrator can see *why* the run stopped. A gate abort emits the
        # payload and then exits non-zero (aborted → exit 1), so the helper
        # is told to expect exit code 1.
        from specify_cli.workflows.step.gate import GateStep

        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr(
            GateStep, "_prompt", staticmethod(lambda _msg, _opts: "reject")
        )
        payload = self._run_json(
            tmp_path, monkeypatch, self._WF_GATE, expected_exit=1
        )
        assert payload["status"] == "aborted"
        assert payload["gate"] == {
            "step_id": "review",
            "message": "Approve the thing?",
            "options": ["approve", "reject"],
            "choice": "reject",
        }

    def test_gate_block_emitted_only_when_run_rests_at_gate(self):
        # A run rests *on* a gate only while `paused` (awaiting a decision) or
        # `aborted` (gate rejected with on_reject: abort). current_step_id is
        # not cleared afterwards, so a `completed`/`failed` run whose last
        # executed step was a gate must NOT surface a stale gate block.
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        gate_step = {
            "type": "gate",
            "output": {
                "message": "m",
                "options": ["approve", "reject"],
                "choice": "reject",
            },
        }

        def _state(status):
            return SimpleNamespace(
                status=SimpleNamespace(value=status),
                current_step_id="review",
                step_results={"review": gate_step},
            )

        assert _gate_outcome(_state("completed")) is None
        assert _gate_outcome(_state("failed")) is None
        assert _gate_outcome(_state("paused")) is not None
        assert _gate_outcome(_state("aborted")) is not None

    def test_gate_block_message_coerced_to_string(self):
        # message may be a non-string YAML literal (e.g. a number); the JSON
        # surface normalises it so the emitted schema stays stable.
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        state = SimpleNamespace(
            status=SimpleNamespace(value="paused"),
            current_step_id="review",
            step_results={
                "review": {
                    "type": "gate",
                    "output": {"message": 12.5, "options": ["ok"], "choice": None},
                }
            },
        )
        assert _gate_outcome(state)["message"] == "12.5"

    def test_gate_block_options_coerced_to_strings(self):
        # options may be non-string / non-list literals in an unvalidated
        # workflow; the JSON surface always normalises them to list[str] | None
        # so the emitted schema is stable regardless of the input shape.
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        def _options_payload(options):
            state = SimpleNamespace(
                status=SimpleNamespace(value="paused"),
                current_step_id="review",
                step_results={
                    "review": {
                        "type": "gate",
                        "output": {
                            "message": "m",
                            "options": options,
                            "choice": None,
                        },
                    }
                },
            )
            return _gate_outcome(state)["options"]

        assert _options_payload([1, 2.5]) == ["1", "2.5"]  # list
        assert _options_payload(("approve", "reject")) == ["approve", "reject"]  # tuple
        assert _options_payload("approve") == ["approve"]  # bare scalar, not iterated
        assert _options_payload(7) == ["7"]  # numeric scalar
        assert _options_payload(None) is None  # absent stays absent

    def test_gate_block_choice_coerced_to_string(self):
        # An unvalidated gate can record a non-string choice; the JSON
        # surface normalises it to str (and keeps None = no decision yet),
        # consistent with the message/options normalization.
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        def _choice_payload(choice):
            state = SimpleNamespace(
                status=SimpleNamespace(value="paused"),
                current_step_id="review",
                step_results={
                    "review": {
                        "type": "gate",
                        "output": {"message": "m", "options": ["ok"], "choice": choice},
                    }
                },
            )
            return _gate_outcome(state)["choice"]

        assert _choice_payload(None) is None  # no decision yet
        assert _choice_payload("reject") == "reject"  # normal string passes through
        assert _choice_payload(2) == "2"  # non-string coerced

    def test_gate_block_detected_without_type_field(self):
        # A run paused by an older version has no persisted step `type`. The
        # gate is still detected by its unique output signature (`on_reject`),
        # so resume surfaces the gate block instead of silently dropping it.
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        state = SimpleNamespace(
            status=SimpleNamespace(value="paused"),
            current_step_id="review",
            step_results={
                "review": {
                    # no "type" key — pre-dates the field being persisted
                    "output": {
                        "message": "Approve?",
                        "options": ["approve", "reject"],
                        "on_reject": "abort",
                        "choice": None,
                    },
                }
            },
        )
        gate = _gate_outcome(state)
        assert gate is not None
        assert gate["step_id"] == "review"
        assert gate["options"] == ["approve", "reject"]

    def test_non_gate_step_without_type_is_not_a_gate(self):
        # A typeless record lacking the gate signature must NOT be mistaken for
        # a gate (the fallback keys off `on_reject`, which only GateStep writes).
        from types import SimpleNamespace
        from specify_cli.workflows._commands import _gate_outcome

        state = SimpleNamespace(
            status=SimpleNamespace(value="paused"),
            current_step_id="run-tests",
            step_results={
                "run-tests": {"output": {"exit_code": 0, "stdout": "ok"}},
            },
        )
        assert _gate_outcome(state) is None



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

    _WF_DONE = """
schema_version: "1.0"
workflow:
  id: "json-done"
  name: "JSON Done"
  version: "1.0.0"
steps:
  - id: only
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

    def test_run_json_completed(self, project_dir):
        wf = self._write_wf(project_dir, self._WF_DONE, "done")
        result = self._invoke(project_dir, ["workflow", "run", str(wf), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["workflow_id"] == "json-done"
        assert payload["status"] == "completed"
        assert "run_id" in payload

    def test_run_json_paused(self, project_dir):
        wf = self._write_wf(project_dir, self._WF, "gated")
        result = self._invoke(project_dir, ["workflow", "run", str(wf), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "paused"
        assert payload["current_step_id"] == "ask"
        assert payload["current_step_index"] == 0

    def test_run_json_failed_includes_error(self, project_dir):
        # A run that ends in `failed` (a step failing, not an exception) must
        # carry the persisted step error in the JSON payload so external
        # callers get a reason, not a bare {"status": "failed"}.
        wf = self._write_wf(project_dir, self._WF_FAIL, "boom")
        result = self._invoke(project_dir, ["workflow", "run", str(wf), "--json"])
        assert result.exit_code != 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "failed"
        assert payload.get("error")

    def test_run_json_completed_omits_error(self, project_dir):
        # Successful runs must not carry an `error` key at all.
        wf = self._write_wf(project_dir, self._WF_DONE, "noerr")
        payload = json.loads(
            self._invoke(
                project_dir, ["workflow", "run", str(wf), "--json"]
            ).stdout
        )
        assert payload["status"] == "completed"
        assert "error" not in payload

    def test_run_json_output_has_no_markup_or_ansi(self, project_dir):
        wf = self._write_wf(project_dir, self._WF_DONE, "clean")
        out = self._invoke(
            project_dir, ["workflow", "run", str(wf), "--json"]
        ).stdout
        # Machine output must be exactly the JSON object: no Rich markup
        # tags and no ANSI escape sequences leaking in.
        assert "\x1b[" not in out
        assert "[/" not in out
        assert out.strip() == json.dumps(json.loads(out), indent=2)

    def test_run_default_output_is_human_not_json(self, project_dir):
        wf = self._write_wf(project_dir, self._WF_DONE, "done2")
        result = self._invoke(project_dir, ["workflow", "run", str(wf)])
        assert result.exit_code == 0
        assert "Running workflow" in result.stdout
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)

    def test_json_redirect_keeps_stdout_clean(self, capfd):
        # While a workflow runs under --json, steps can still write to stdout:
        # the gate step prints its prompt and the prompt step runs a
        # subprocess that inherits the stdout fd. Both must be redirected to
        # stderr so the JSON object on stdout stays parseable. capfd captures
        # at the file-descriptor level, so it sees the subprocess output too.
        import subprocess
        import sys as _sys
        from specify_cli.workflows._commands import _stdout_to_stderr_when

        print("STDOUT_BEFORE")
        with _stdout_to_stderr_when(True):
            print("PY_LEAK")  # Python-level write (gate-style)
            subprocess.run(  # inherited-fd write (prompt-style)
                [_sys.executable, "-c", "print('SUBPROC_LEAK')"],
                check=True,
            )
        print("STDOUT_AFTER")

        out, err = capfd.readouterr()
        # stdout keeps only what was written outside the guarded block.
        assert "STDOUT_BEFORE" in out and "STDOUT_AFTER" in out
        assert "PY_LEAK" not in out and "SUBPROC_LEAK" not in out
        # The step output is preserved on stderr, not discarded.
        assert "PY_LEAK" in err and "SUBPROC_LEAK" in err

    def test_json_redirect_inactive_is_noop(self, capfd):
        from specify_cli.workflows._commands import _stdout_to_stderr_when

        with _stdout_to_stderr_when(False):
            print("VISIBLE_ON_STDOUT")
        out, _ = capfd.readouterr()
        assert "VISIBLE_ON_STDOUT" in out



class TestWorkflowStepStartProgressLine:
    """The `run`/`resume` step-progress line must render the step id literally.

    The line is built as `  ▸ [<id>] <label> …`, so Rich parsed the bracketed id
    as a style tag: it silently swallowed the id (the only identifying content
    on the line), applied it as formatting when the id happened to be a real
    style like `bold`, and raised MarkupError — failing the whole run — when the
    id formed a closing tag such as `/`. `validate_workflow` places no charset
    restriction on step ids, so all of these are accepted workflows.
    """

    def _write(self, tmp_path, step_id):
        path = tmp_path / "wf.yml"
        path.write_text(
            'schema_version: "1.0"\n'
            "workflow:\n"
            '  id: "probe-wf"\n'
            '  name: "Probe"\n'
            '  version: "1.0.0"\n'
            "steps:\n"
            f'  - id: "{step_id}"\n'
            "    type: shell\n"
            '    run: "exit 0"\n',
            encoding="utf-8",
        )
        return path

    @pytest.mark.parametrize("step_id", ["greet", "bold", "a]b"])
    def test_progress_line_shows_step_id(self, tmp_path, monkeypatch, step_id):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            app, ["workflow", "run", str(self._write(tmp_path, step_id))]
        )
        assert result.exit_code == 0, result.stdout
        assert f"[{step_id}]" in result.stdout

    def test_step_id_forming_a_closing_tag_does_not_fail_the_run(
        self, tmp_path, monkeypatch
    ):
        """`id: "/"` raised MarkupError from inside the progress callback, which
        surfaced as a failed run with no step results."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            app, ["workflow", "run", str(self._write(tmp_path, "/"))]
        )
        assert result.exit_code == 0, result.stdout
        assert "Status: completed" in result.stdout
        assert "[/]" in result.stdout



class TestWorkflowRunExitCodes:
    """CLI-level tests for the run/resume process exit codes."""

    _WF_OK = """
schema_version: "1.0"
workflow:
  id: "exit-ok"
  name: "Exit OK"
  version: "1.0.0"
steps:
  - id: fine
    type: shell
    run: "exit 0"
"""

    _WF_FAIL = """
schema_version: "1.0"
workflow:
  id: "exit-fail"
  name: "Exit Fail"
  version: "1.0.0"
steps:
  - id: boom
    type: shell
    run: "exit 1"
"""

    def _write(self, tmp_path, content):
        path = tmp_path / "wf.yml"
        path.write_text(content, encoding="utf-8")
        return path

    _WF_GATE_INVALID_VERDICT = """
schema_version: "1.0"
workflow:
  id: "gate-invalid-verdict"
  name: "Gate Invalid Verdict"
  version: "1.0.0"
inputs:
  review_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Approve the review?"
    options: [approve, reject]
    on_reject: abort
    verdict_input: review_verdict
"""

    _WF_GATE_INVALID_TYPE = """
schema_version: "1.0"
workflow:
  id: "gate-invalid-type"
  name: "Gate Invalid Type"
  version: "1.0.0"
inputs:
  review_verdict:
    type: number
    default: 1
steps:
  - id: review
    type: gate
    message: "Approve the review?"
    options: [approve, reject]
    on_reject: abort
    verdict_input: review_verdict
"""

    _WF_GATE_ABORT = """
schema_version: "1.0"
workflow:
  id: "gate-abort"
  name: "Gate Abort"
  version: "1.0.0"
inputs:
  review_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Approve the review?"
    options: [approve, reject]
    on_reject: abort
    verdict_input: review_verdict
"""

    def test_run_completed_exits_zero(self, tmp_path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "run", str(self._write(tmp_path, self._WF_OK))])
        assert result.exit_code == 0
        assert "Status: completed" in result.stdout

    def test_run_failed_exits_nonzero(self, tmp_path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "run", str(self._write(tmp_path, self._WF_FAIL))])
        assert "Status: failed" in result.stdout
        assert result.exit_code == 1

    def test_run_failed_exits_nonzero_with_json(self, tmp_path, monkeypatch):
        import json as _json
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["workflow", "run", str(self._write(tmp_path, self._WF_FAIL)), "--json"],
        )
        assert result.exit_code == 1, result.stdout
        payload = _json.loads(result.stdout)
        assert payload["status"] == "failed"

    def test_run_invalid_verdict_prints_error(self, tmp_path, monkeypatch):
        """Invalid verdict value prints explanatory error in human output."""
        import re
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "workflow",
                "run",
                str(self._write(tmp_path, self._WF_GATE_INVALID_VERDICT)),
                "--input",
                "review_verdict=maybe",
            ],
        )
        assert result.exit_code == 1
        assert "Status: failed" in result.stdout
        # Normalize whitespace to handle Rich console line wrapping
        normalized = re.sub(r"\s+", " ", result.stdout)
        assert "does not match any configured option" in normalized

    def test_run_invalid_verdict_type_prints_error(self, tmp_path, monkeypatch):
        """Non-string verdict value prints explanatory error in human output."""
        import re
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["workflow", "run", str(self._write(tmp_path, self._WF_GATE_INVALID_TYPE))],
        )
        assert result.exit_code == 1
        assert "Status: failed" in result.stdout
        # Normalize whitespace to handle Rich console line wrapping
        normalized = re.sub(r"\s+", " ", result.stdout)
        assert "must be a string" in normalized

    def test_run_gate_abort_prints_status_and_error(self, tmp_path, monkeypatch):
        """Gate abort prints Status: aborted and the rejection message."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "workflow",
                "run",
                str(self._write(tmp_path, self._WF_GATE_ABORT)),
                "--input",
                "review_verdict=reject",
            ],
        )
        assert result.exit_code == 1
        assert "Status: aborted" in result.stdout
        assert "Gate rejected by user" in result.stdout

    def test_run_gate_abort_json_includes_error(self, tmp_path, monkeypatch):
        """Gate abort --json includes the rejection message in the error field."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "workflow",
                "run",
                str(self._write(tmp_path, self._WF_GATE_ABORT)),
                "--input",
                "review_verdict=reject",
                "--json",
            ],
        )
        assert result.exit_code == 1
        payload = json.loads(result.stdout)
        assert payload["status"] == "aborted"
        assert "Gate rejected by user" in (payload.get("error") or "")



class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "align-wf"
  name: "Align Workflow"
  version: "{version}"
  description: "CLI alignment test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def _write_workflow_dir(self, base, version="1.0.0"):
        d = base / "wf-src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version=version), encoding="utf-8"
        )
        return d

    def _install_dev(self, runner, app, project_dir):
        src = self._write_workflow_dir(project_dir)
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output
        return src

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

    def test_run_refuses_falsy_non_bool_enabled(self, project_dir, monkeypatch):
        """A falsy non-bool "enabled" (0) shows as disabled in list — run must agree."""
        import json as json_mod

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        registry = WorkflowRegistry(project_dir)
        registry.data["workflows"]["align-wf"]["enabled"] = 0
        registry.registry_path.write_text(json_mod.dumps(registry.data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "run", "align-wf"])
        assert result.exit_code != 0
        assert "disabled" in result.output

    def test_run_rejects_corrupted_registry_entry(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        registry = WorkflowRegistry(project_dir)
        registry.data["workflows"]["align-wf"] = "corrupted"
        registry.save()

        result = runner.invoke(app, ["workflow", "run", "align-wf"])
        assert result.exit_code != 0
        assert "corrupted" in result.output

    def test_run_rejects_corrupt_registry_file(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.write_text("not json", encoding="utf-8")

        result = runner.invoke(app, ["workflow", "run", "align-wf"])

        assert result.exit_code != 0
        assert "registry" in result.output.lower()
        assert "corrupt" in result.output.lower()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_run_refuses_symlinked_specify_dir_hiding_disabled_workflow(
        self, temp_dir, monkeypatch
    ):
        """A victim project's own .specify directory being a symlink to an
        attacker-controlled tree must not bypass the disabled-workflow guard.
        _reject_unsafe_workflow_storage only checks the *cwd's* project root
        (unrelated here); the id/leaf symlink-component loop only checks
        components from the id directory onward, missing .specify/
        .specify/workflows themselves. The ownership check must reject an
        unsafe .specify/.specify-workflows for the actual path-derived
        registry root before ever consulting the registry -- it must not
        rely on WorkflowRegistry's own symlinked-parent handling, which
        raises a generic OSError; the ownership guard should surface the
        specific unsafe-storage error before registry construction."""
        from typer.testing import CliRunner
        from specify_cli import app

        victim = temp_dir / "victim"
        victim.mkdir()
        attacker_real = temp_dir / "attacker-real"
        (attacker_real / "workflows" / "evil").mkdir(parents=True)
        (attacker_real / "workflows" / "evil" / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        (attacker_real / "workflows" / "workflow-registry.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workflows": {
                        "evil": {
                            "name": "Evil",
                            "version": "1.0.0",
                            "source": "dev",
                            "enabled": False,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (victim / ".specify").symlink_to(attacker_real)

        unrelated_cwd = temp_dir / "unrelated-cwd"
        unrelated_cwd.mkdir()
        monkeypatch.chdir(unrelated_cwd)

        runner = CliRunner()
        target = victim / ".specify" / "workflows" / "evil" / "workflow.yml"
        result = runner.invoke(app, ["workflow", "run", str(target)])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "symlink" in result.output.lower()

    def test_run_nested_installed_paths_uses_nearest_owner(
        self, temp_dir, monkeypatch
    ):
        """A direct workflow.yml path whose lexical segments contain
        .specify/workflows more than once (an unrelated nested project
        happens to live beneath an outer installed workflow's own
        directory tree, reusing the same segment names) must be attributed
        to its *nearest* (innermost) owning project/ID -- scanning from the
        start of the path and stopping at the first match would pick the
        outer project and the wrong workflow ID, gating the run on an
        unrelated workflow's disabled state instead of the real owner's."""
        from typer.testing import CliRunner
        from specify_cli import app

        def _write_registry(workflows_dir, workflow_id, enabled):
            workflows_dir.mkdir(parents=True, exist_ok=True)
            (workflows_dir / "workflow-registry.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "workflows": {
                            workflow_id: {
                                "name": workflow_id,
                                "version": "1.0.0",
                                "source": "dev",
                                "enabled": enabled,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

        outer_workflows = temp_dir / "outer-proj" / ".specify" / "workflows"
        outer_wf_dir = outer_workflows / "outer-wf"
        outer_wf_dir.mkdir(parents=True)
        (outer_wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        _write_registry(outer_workflows, "outer-wf", enabled=False)

        # An unrelated nested project lives inside the outer workflow's own
        # directory tree, with its own separate installed workflow.
        inner_workflows = outer_wf_dir / "nested-proj" / ".specify" / "workflows"
        inner_wf_dir = inner_workflows / "inner-wf"
        inner_wf_dir.mkdir(parents=True)
        (inner_wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        _write_registry(inner_workflows, "inner-wf", enabled=True)

        unrelated_cwd = temp_dir / "unrelated-cwd"
        unrelated_cwd.mkdir()
        monkeypatch.chdir(unrelated_cwd)

        runner = CliRunner()
        target = inner_wf_dir / "workflow.yml"
        result = runner.invoke(app, ["workflow", "run", str(target)])
        # inner-wf (the actual nearest owner) is enabled -- must run, not
        # be blocked by the unrelated outer-wf's disabled state.
        assert result.exit_code == 0, result.output

        # The inverse proves this isn't just ignoring nesting: disabling
        # the true (nearest) owner must actually block this exact path.
        _write_registry(inner_workflows, "inner-wf", enabled=False)
        result = runner.invoke(app, ["workflow", "run", str(target)])
        assert result.exit_code != 0
        assert "disabled" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_run_blocks_disabled_workflow_via_outward_alias_symlink(
        self, project_dir, monkeypatch
    ):
        """The inverse of the existing inward-symlink case: a path with no
        .specify/workflows segments at all (e.g. /tmp/alias.yml) that is
        itself a symlink resolving *into* installed storage must still
        receive the disabled check. Only checking the lexical path's own
        segments misses this alias entirely, since it has no such segments
        to begin with, and would let engine.load_workflow follow the
        symlink to the disabled workflow's real content unchecked."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        installed_yaml = (
            project_dir / ".specify" / "workflows" / "align-wf" / "workflow.yml"
        )
        external_dir = project_dir / "outside-alias"
        external_dir.mkdir()
        alias = external_dir / "alias.yml"
        alias.symlink_to(installed_yaml)

        result = runner.invoke(app, ["workflow", "run", str(alias)])
        assert result.exit_code != 0
        assert "disabled" in result.output

        result = runner.invoke(app, ["workflow", "enable", "align-wf"])
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, ["workflow", "run", str(alias)])
        assert result.exit_code == 0, result.output

    def test_unregistered_workflow_shaped_path_is_not_persisted_as_owner(
        self, project_dir, temp_dir, monkeypatch
    ):
        """A direct file is not installed merely because its path resembles
        installed storage; only registry membership establishes ownership."""
        from typer.testing import CliRunner
        from specify_cli import app

        standalone_root = temp_dir / "standalone-project"
        workflows_dir = standalone_root / ".specify" / "workflows"
        workflow_file = workflows_dir / "gated-wf" / "workflow.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(self._GATED_WORKFLOW_YAML, encoding="utf-8")

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_ids = []
        for _ in range(2):
            result = runner.invoke(
                app, ["workflow", "run", str(workflow_file), "--json"]
            )
            assert result.exit_code == 0, result.output
            run_ids.append(json.loads(result.stdout)["run_id"])

        for run_id in run_ids:
            state_path = (
                project_dir
                / ".specify"
                / "workflows"
                / "runs"
                / run_id
                / "state.json"
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            assert state["installed_workflow_id"] is None
            assert state["installed_registry_root"] is None

        shutil.rmtree(standalone_root)
        result = runner.invoke(
            app, ["workflow", "resume", run_ids[0], "--json"]
        )
        assert result.exit_code == 0, result.output

        workflows_dir.mkdir(parents=True)
        (workflows_dir / "workflow-registry.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workflows": {
                        "gated-wf": {
                            "name": "Unrelated workflow",
                            "version": "9.9.9",
                            "source": "dev",
                            "enabled": False,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        result = runner.invoke(
            app, ["workflow", "resume", run_ids[1], "--json"]
        )
        assert result.exit_code == 0, result.output


class TestWorkflowRunWithoutProject:
    """Tests that specify workflow run works with YAML files without .specify/ dir."""

    def test_workflow_run_yaml_without_project(self, tmp_path):
        """Running a .yml file should work without a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        # Create a minimal workflow YAML with a shell step
        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "standalone-test",
                "name": "Standalone Test",
                "version": "1.0.0",
                "description": "A workflow that runs without a project",
            },
            "steps": [
                {
                    "id": "create-marker",
                    "type": "shell",
                    "run": "echo done > marker.txt",
                },
            ],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"workflow run failed: {result.output}"
        assert "completed" in result.output
        assert (tmp_path / "marker.txt").exists()
        assert (tmp_path / ".specify" / "workflows" / "runs").is_dir()

    def test_workflow_run_yaml_with_tilde_and_uppercase_suffix(self, tmp_path, monkeypatch):
        """Running ~/file.YML should work without a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.setenv("USERPROFILE", str(home_dir))

        workflow_file = home_dir / "test-workflow.YML"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "standalone-test-uppercase",
                "name": "Standalone Test Uppercase",
                "version": "1.0.0",
                "description": "A workflow that runs from ~/ with an uppercase suffix",
            },
            "steps": [
                {
                    "id": "create-marker",
                    "type": "shell",
                    "run": "echo done > marker.txt",
                },
            ],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "~/test-workflow.YML",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"workflow run failed: {result.output}"
        assert "Status: completed" in result.output
        assert (tmp_path / "marker.txt").exists()

    def test_workflow_run_id_still_requires_project(self, tmp_path):
        """Running a workflow by ID should still require a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "some-workflow-id",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

    def test_workflow_run_missing_yaml_file(self, tmp_path):
        """Running a non-existent .yml file should still require a project."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "nonexistent.yml",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        # non-existent .yml files fall through to project check or file-not-found
        assert result.exit_code != 0

    def test_workflow_run_failing_yaml_without_project(self, tmp_path):
        """A failing workflow YAML should report failure status."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "fail-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "fail-test",
                "name": "Fail Test",
                "version": "1.0.0",
                "description": "A workflow that fails",
            },
            "steps": [
                {
                    "id": "fail-step",
                    "type": "shell",
                    "run": "exit 1",
                },
            ],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        # A failed workflow now maps to a non-zero process exit code so
        # scripts and CI can rely on $? (the CLI itself still ran fine).
        assert result.exit_code == 1, f"expected exit 1 on failed run: {result.output}"
        assert "Status: failed" in result.output

    def test_workflow_run_yaml_rejects_symlinked_specify_dir(self, tmp_path):
        """Running local YAML should fail when .specify is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-test",
                "name": "Symlink Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        target_dir = tmp_path / "real-specify-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify").symlink_to(target_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify path" in result.output

    def test_workflow_run_yaml_rejects_symlinked_workflows_dir(self, tmp_path):
        """Running local YAML should fail when .specify/workflows is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-workflows-test",
                "name": "Symlink Workflows Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        (tmp_path / ".specify").mkdir()
        target_dir = tmp_path / "real-workflows-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify" / "workflows").symlink_to(
                target_dir, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify/workflows path" in result.output

    def test_workflow_run_yaml_rejects_symlinked_runs_dir(self, tmp_path):
        """Running local YAML should fail when .specify/workflows/runs is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-runs-test",
                "name": "Symlink Runs Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        (tmp_path / ".specify" / "workflows").mkdir(parents=True)
        target_dir = tmp_path / "real-runs-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify" / "workflows" / "runs").symlink_to(
                target_dir, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify/workflows/runs path" in result.output

    def test_workflow_run_yaml_rejects_non_directory_specify_path(self, tmp_path):
        """Running local YAML should fail when .specify is not a directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "nondir-test",
                "name": "Non-directory Test",
                "version": "1.0.0",
                "description": "A workflow for non-directory guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")
        (tmp_path / ".specify").write_text("not a directory", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert ".specify path exists but is not a directory" in result.output



class TestWorkflowRunJsonErrorStream:
    """Under --json, error text must go to stderr so stdout stays parseable."""

    def _bad_workflow(self, tmp_path):
        wf = tmp_path / "bad.yml"
        wf.write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "workflow": {
                        "id": "bad-wf",
                        "name": "Bad",
                        "version": "1.0.0",
                        "description": "fails validation",
                    },
                    # shell step missing required 'run' -> validation error
                    "steps": [{"id": "s", "type": "shell"}],
                }
            ),
            encoding="utf-8",
        )
        return wf

    def test_run_json_validation_error_not_on_stdout(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        wf = self._bad_workflow(tmp_path)
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app, ["workflow", "run", str(wf), "--json"], catch_exceptions=False
            )
        finally:
            os.chdir(old)

        assert result.exit_code == 1
        # stdout must carry only JSON (here: nothing) — never human error text.
        assert "validation failed" not in result.stdout
        assert "Error" not in result.stdout
        # The message is routed to stderr instead.
        assert "validation failed" in result.stderr

    def test_run_json_invalid_input_not_on_stdout(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        # A valid single-shell workflow so we get past load/validate to
        # _parse_input_values, which rejects the malformed --input.
        wf = tmp_path / "ok.yml"
        wf.write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "workflow": {
                        "id": "ok-wf",
                        "name": "OK",
                        "version": "1.0.0",
                        "description": "x",
                    },
                    "steps": [{"id": "s", "type": "shell", "run": "echo hi"}],
                }
            ),
            encoding="utf-8",
        )
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                ["workflow", "run", str(wf), "--json", "--input", "no-equals"],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old)

        assert result.exit_code == 1
        assert "Invalid input format" not in result.stdout
        assert "Invalid input format" in result.stderr
