"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest



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

    def test_resume_json(self, project_dir):
        wf = self._write_wf(project_dir, self._WF, "gated3")
        rid = json.loads(
            self._invoke(project_dir, ["workflow", "run", str(wf), "--json"]).stdout
        )["run_id"]
        # Non-interactive resume re-runs the gate, which pauses again.
        resumed = json.loads(
            self._invoke(project_dir, ["workflow", "resume", rid, "--json"]).stdout
        )
        assert resumed["run_id"] == rid
        assert resumed["status"] == "paused"



class TestResumeWithInputs:
    """Test that `workflow resume` can accept updated workflow inputs."""

    _WF_NUM = """
schema_version: "1.0"
workflow:
  id: "resume-num-wf"
  name: "Resume Num WF"
  version: "1.0.0"
inputs:
  count:
    type: number
    default: 1
steps:
  - id: gate
    type: gate
    message: "Review"
    options: [approve, reject]
"""

    def _engine(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine
        return WorkflowEngine(project_dir)

    def test_cli_resume_input_invalid_format_errors(self, project_dir):
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowDefinition

        definition = WorkflowDefinition.from_string(self._WF_NUM)
        state = self._engine(project_dir).execute(definition)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["workflow", "resume", state.run_id, "--input", "bogus"]
            )
        assert result.exit_code == 1
        assert "Invalid input format" in result.stdout



class TestWorkflowStepStartProgressLine:
    """The `run`/`resume` step-progress line must render the step id literally.

    The line is built as `  ▸ [<id>] <label> …`, so Rich parsed the bracketed id
    as a style tag: it silently swallowed the id (the only identifying content
    on the line), applied it as formatting when the id happened to be a real
    style like `bold`, and raised MarkupError — failing the whole run — when the
    id formed a closing tag such as `/`. `validate_workflow` places no charset
    restriction on step ids, so all of these are accepted workflows.
    """

    def test_resume_progress_line_shows_step_id(self, tmp_path, monkeypatch):
        """`workflow resume` installs its own copy of the same callback, so it
        needs independent coverage — a one-line fix would miss the twin."""
        import json as _json

        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        path = tmp_path / "wf.yml"
        path.write_text(
            'schema_version: "1.0"\n'
            "workflow:\n"
            '  id: "probe-resume"\n'
            '  name: "Probe"\n'
            '  version: "1.0.0"\n'
            "steps:\n"
            "  - id: boom\n"
            "    type: shell\n"
            '    run: "exit 1"\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        first = runner.invoke(app, ["workflow", "run", str(path), "--json"])
        run_id = _json.loads(first.stdout).get("run_id")
        assert run_id

        resumed = runner.invoke(app, ["workflow", "resume", run_id])
        assert "[boom]" in resumed.stdout



class TestWorkflowRunExitCodes:
    """CLI-level tests for the run/resume process exit codes."""

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

    def test_resume_failed_run_exits_nonzero(self, tmp_path, monkeypatch):
        # End-to-end coverage for the `workflow resume` exit-code mapping:
        # resuming a run whose outcome is still `failed` must exit non-zero,
        # mirroring `workflow run`. Resume re-executes the failed step, which
        # fails again, so the resumed outcome stays `failed`.
        import json as _json
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".specify").mkdir()  # `workflow resume` requires a project
        runner = CliRunner()
        run = runner.invoke(
            app,
            ["workflow", "run", str(self._write(tmp_path, self._WF_FAIL)), "--json"],
        )
        assert run.exit_code == 1, run.stdout
        run_id = _json.loads(run.stdout)["run_id"]

        resumed = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert resumed.exit_code == 1, resumed.stdout
        payload = _json.loads(resumed.stdout)
        assert payload["status"] == "failed"



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

    def test_resume_blocks_when_installed_workflow_disabled(
        self, project_dir, monkeypatch
    ):
        """A run started from an installed workflow must not resume once
        that workflow is disabled. engine.resume() replays the persisted
        run directly from disk with no registry awareness at all, so the
        installed workflow's origin (id + owning registry root) is
        persisted at run start and re-checked against the registry's
        *current* state before resuming, mirroring `workflow run`'s
        disabled guard."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "gated-wf"])
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert "disabled" in result.output

        # Re-enabling must unblock the exact same run.
        result = runner.invoke(app, ["workflow", "enable", "gated-wf"])
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert result.exit_code == 0, result.output
        resumed = json.loads(result.stdout)
        assert resumed["run_id"] == run_id

    def test_resume_rejects_corrupted_registry_entry(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        registry = WorkflowRegistry(project_dir)
        registry.data["workflows"]["gated-wf"] = "corrupted"
        registry.save()

        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert "corrupted" in result.output

    def test_resume_preload_io_error_is_reported_cleanly(
        self, project_dir, monkeypatch
    ):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import RunState

        monkeypatch.chdir(project_dir)
        with patch.object(
            RunState, "load", side_effect=OSError("permission [denied]")
        ):
            result = CliRunner().invoke(
                app, ["workflow", "resume", "unreadable-run"]
            )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Resume failed" in result.output
        assert "permission [denied]" in result.output

    @pytest.mark.parametrize("malformation", ["non-object", "missing-run-id"])
    def test_resume_preload_rejects_malformed_state_cleanly(
        self, project_dir, monkeypatch, malformation
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)
        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )

        if malformation == "non-object":
            state_path.write_text("[]", encoding="utf-8")
        else:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            data.pop("run_id")
            state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "resume", run_id])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Invalid run state" in result.output

    def test_resume_rejects_out_of_range_current_step_index(
        self, project_dir, monkeypatch
    ):
        """An out-of-range positive index must fail cleanly, not silently
        complete the run with no steps executed.

        ``resume()`` slices ``definition.steps[state.current_step_index:]``;
        for any index >= len(steps) that slice is an empty list, so the run
        would otherwise finish with status "completed" having executed
        nothing.
        """
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)
        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        data["current_step_index"] = 5
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "resume", run_id])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Invalid run state" in result.output
        assert "out of range" in result.output

        reloaded = json.loads(state_path.read_text(encoding="utf-8"))
        assert reloaded["status"] == "paused"

    def test_resume_legacy_run_respects_current_disabled_state(
        self, project_dir, monkeypatch
    ):
        """Legacy runs infer same-project registry ownership before resume."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        data.pop("installed_workflow_id", None)
        data.pop("installed_registry_root", None)
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "disable", "gated-wf"])
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert result.exit_code != 0
        assert "disabled" in result.output

    def test_resume_migrates_legacy_installed_origin_metadata(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        data.pop("installed_workflow_id", None)
        data.pop("installed_registry_root", None)
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert result.exit_code == 0, result.output

        migrated = json.loads(state_path.read_text(encoding="utf-8"))
        assert migrated["installed_workflow_id"] == "gated-wf"
        assert migrated["installed_registry_root"] is None

    def test_resume_blocks_after_project_moved_following_disable(
        self, temp_dir, monkeypatch
    ):
        """Renaming/moving the entire project after starting a run must not
        let a subsequent disable-then-resume bypass the guard. Persisting
        the run's *creation-time absolute* project path would make resume
        open a now-nonexistent old root (WorkflowRegistry falls back to an
        empty default there), missing the disabled entry that actually
        lives in the *current* (moved) project's registry. The common,
        same-project case must instead re-derive the owning root from the
        project's current location on every resume."""
        from typer.testing import CliRunner
        from specify_cli import app

        project_v1 = temp_dir / "project-v1"
        (project_v1 / ".specify" / "workflows").mkdir(parents=True)
        monkeypatch.chdir(project_v1)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_v1)

        project_v2 = temp_dir / "project-v2"
        monkeypatch.chdir(temp_dir)
        shutil.move(str(project_v1), str(project_v2))
        monkeypatch.chdir(project_v2)

        result = runner.invoke(app, ["workflow", "disable", "gated-wf"])
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert "disabled" in result.output

    def test_resume_after_project_moved_still_works_when_enabled(
        self, temp_dir, monkeypatch
    ):
        """The inverse of the move regression: an enabled workflow's run
        must still resume normally after the project is moved -- the
        current-project fallback must not itself block legitimate
        resumes."""
        from typer.testing import CliRunner
        from specify_cli import app

        project_v1 = temp_dir / "project-v1-ok"
        (project_v1 / ".specify" / "workflows").mkdir(parents=True)
        monkeypatch.chdir(project_v1)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_v1)

        project_v2 = temp_dir / "project-v2-ok"
        monkeypatch.chdir(temp_dir)
        shutil.move(str(project_v1), str(project_v2))
        monkeypatch.chdir(project_v2)

        result = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert result.exit_code == 0, result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_resume_respects_cross_project_registry_root(
        self, temp_dir, monkeypatch
    ):
        """A run started via a direct workflow.yml path belonging to a
        different project than the cwd used for `workflow run`/`workflow
        resume` must still gate resuming on *that* owning project's
        registry, not the cwd project's (which has no entry for this ID
        at all). This is the genuine cross-project case that must remain
        unaffected by only special-casing the common same-project one."""
        from typer.testing import CliRunner
        from specify_cli import app

        owner_project = temp_dir / "owner-project"
        (owner_project / ".specify" / "workflows").mkdir(parents=True)
        monkeypatch.chdir(owner_project)
        runner = CliRunner()
        src = owner_project / "gated-src"
        src.mkdir()
        (src / "workflow.yml").write_text(self._GATED_WORKFLOW_YAML, encoding="utf-8")
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output

        unrelated_cwd = temp_dir / "unrelated-cwd"
        unrelated_cwd.mkdir()
        monkeypatch.chdir(unrelated_cwd)

        owner_alias = temp_dir / "owner-project-alias"
        owner_alias.symlink_to(owner_project, target_is_directory=True)
        target = owner_alias / ".specify" / "workflows" / "gated-wf" / "workflow.yml"
        result = runner.invoke(app, ["workflow", "run", str(target), "--json"])
        assert result.exit_code == 0, result.output
        run_id = json.loads(result.stdout)["run_id"]
        state_path = (
            unrelated_cwd
            / ".specify"
            / "workflows"
            / "runs"
            / run_id
            / "state.json"
        )
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["installed_registry_root"] == str(owner_project.resolve())

        monkeypatch.chdir(owner_project)
        result = runner.invoke(app, ["workflow", "disable", "gated-wf"])
        assert result.exit_code == 0, result.output

        # Resume must run from unrelated_cwd (where this run's own
        # state.json actually lives) yet still be blocked by the owner
        # project's disabled entry.
        monkeypatch.chdir(unrelated_cwd)
        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert "disabled" in result.output

    def test_resume_rejects_missing_cross_project_owner_root(
        self, temp_dir, monkeypatch
    ):
        """A vanished explicit cross-project owner cannot be safely
        rediscovered, so resume must fail closed instead of consulting the
        unrelated project that stores the run state."""
        from typer.testing import CliRunner
        from specify_cli import app

        owner_project = temp_dir / "owner-project-2"
        (owner_project / ".specify" / "workflows").mkdir(parents=True)
        monkeypatch.chdir(owner_project)
        runner = CliRunner()
        src = owner_project / "gated-src"
        src.mkdir()
        (src / "workflow.yml").write_text(self._GATED_WORKFLOW_YAML, encoding="utf-8")
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output

        unrelated_cwd = temp_dir / "unrelated-cwd-2"
        unrelated_cwd.mkdir()
        monkeypatch.chdir(unrelated_cwd)

        target = owner_project / ".specify" / "workflows" / "gated-wf" / "workflow.yml"
        result = runner.invoke(app, ["workflow", "run", str(target), "--json"])
        assert result.exit_code == 0, result.output
        run_id = json.loads(result.stdout)["run_id"]

        # owner_project vanishes entirely -- its persisted absolute root
        # is now dangling.
        shutil.rmtree(owner_project)

        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert "owner" in result.output.lower()
        assert "unavailable" in result.output.lower()

    @pytest.mark.parametrize(
        "field, bad_value",
        [
            ("installed_workflow_id", 123),
            ("installed_workflow_id", ["gated-wf"]),
            ("installed_workflow_id", {"id": "gated-wf"}),
            ("installed_workflow_id", True),
            ("installed_workflow_id", ""),
            ("installed_workflow_id", "gated-wf\n"),
            ("installed_registry_root", 123),
            ("installed_registry_root", ["."]),
            ("installed_registry_root", {"root": "."}),
            ("installed_registry_root", False),
            ("installed_registry_root", ""),
            ("installed_registry_root", "relative-owner"),
        ],
    )
    def test_resume_rejects_malformed_run_state_origin_fields(
        self, project_dir, monkeypatch, field, bad_value
    ):
        """RunState.load() rejects malformed or unsafe origin metadata
        before registry/path lookups and reports a clean CLI error."""
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

        result = runner.invoke(app, ["workflow", "resume", run_id])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Error" in result.output

    @pytest.mark.parametrize("command", ["resume", "status"])
    def test_state_load_errors_escape_rich_markup(
        self, project_dir, monkeypatch, command
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        malicious_status = "[bold red]forged[/bold red]"
        data["status"] = malicious_status
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", command, run_id])

        assert result.exit_code != 0
        assert malicious_status in result.output

    @pytest.mark.parametrize(
        "installed_workflow_id, installed_registry_root",
        [
            (None, None),
            ("gated-wf", None),
        ],
    )
    def test_resume_accepts_valid_run_state_origin_fields(
        self, project_dir, monkeypatch, installed_workflow_id, installed_registry_root
    ):
        """Valid installed-origin values continue to load and resume."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        run_id = self._install_and_run_gated(runner, app, project_dir)

        state_path = (
            project_dir / ".specify" / "workflows" / "runs" / run_id / "state.json"
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        data["installed_workflow_id"] = installed_workflow_id
        data["installed_registry_root"] = installed_registry_root
        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = runner.invoke(app, ["workflow", "resume", run_id, "--json"])
        assert result.exit_code == 0, result.output
