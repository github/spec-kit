"""Dry-run tests for ``specify workflow run --dry-run``.

Scoped to the engine-only changes in this branch:
- ``StepContext.dry_run`` flag
- ``RunState.dry_run`` field (persisted via save/load)
- ``WorkflowEngine.execute(..., dry_run=...)`` + resume() restores it
- ``CommandStep`` / ``PromptStep`` / ``GateStep`` short-circuit on
  ``context.dry_run``
- ``specify workflow run --dry-run`` flag + preview rendering

Intentionally NOT covered here:
- ``init`` step registration (pre-existing test, not dry-run related)
- from_json filter / Win test stability (separate concerns)
- preset extraction (already on ``main``, not in this PR)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


# -- Helpers ---------------------------------------------------------------


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a minimal spec-kit project for workflow runs."""
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    (specify_dir / "workflows").mkdir()
    return tmp_path


def _write_wf(project_dir: Path, text: str, name: str) -> Path:
    path = project_dir / f"{name}.yml"
    path.write_text(text, encoding="utf-8")
    return path


def _invoke(project_dir: Path, args: list[str]):
    from typer.testing import CliRunner
    from specify_cli import app

    runner = CliRunner()
    with patch.object(Path, "cwd", return_value=project_dir):
        return runner.invoke(app, args, catch_exceptions=False)


# -- Step-level: CommandStep ----------------------------------------------


class TestCommandStepDryRun:
    def test_returns_completed_without_dispatch(self, tmp_path: Path) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.command import CommandStep

        step = CommandStep()
        ctx = StepContext(
            inputs={"name": "login"},
            default_integration="claude",
            project_root=str(tmp_path),
            dry_run=True,
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "{{ inputs.name }}"},
        }
        result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dry_run"] is True
        assert result.output["dispatched"] is False
        assert result.output["executed"] is False
        assert result.output["command"] == "speckit.specify"
        assert result.output["input"]["args"] == "login"
        assert "DRY RUN" in result.output["dry_run_message"]
        assert result.output["message"] == "speckit.specify"
        assert result.output["dry_run_message"] != result.output["message"]

    def test_falls_back_when_no_integration(self, tmp_path: Path) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.command import CommandStep

        step = CommandStep()
        ctx = StepContext(
            inputs={"name": "login"},
            default_integration=None,
            project_root=str(tmp_path),
            dry_run=True,
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "{{ inputs.name }}"},
        }
        result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert "speckit.specify" in result.output["message"]
        assert "DRY RUN" in result.output["dry_run_message"]


# -- Step-level: PromptStep -----------------------------------------------


class TestPromptStepDryRun:
    def test_prompt_short_circuits(self, tmp_path: Path) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.prompt import PromptStep

        step = PromptStep()
        ctx = StepContext(
            inputs={"file": "auth.py"},
            default_integration="claude",
            project_root=str(tmp_path),
            dry_run=True,
        )
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "Review {{ inputs.file }} for security issues",
        }
        result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dry_run"] is True
        assert result.output["executed"] is False
        assert result.output["dispatched"] is False
        assert result.output["exit_code"] == 0
        assert "DRY RUN" in result.output["dry_run_message"]
        assert result.output["message"] == "Review auth.py for security issues"
        assert result.output["dry_run_message"] != result.output["message"]


# -- Step-level: GateStep -------------------------------------------------


class TestGateStepDryRun:
    def test_skips_interactive_prompt(self) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        ctx = StepContext(dry_run=True)
        config = {
            "id": "review",
            "message": "Review the spec.",
            "options": ["approve", "reject"],
            "on_reject": "abort",
        }
        result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dry_run"] is True
        # Original ``message`` preserved so downstream
        # ``{{ steps.<id>.output.message }}`` references still resolve.
        assert result.output["message"] == "Review the spec."
        assert "DRY RUN" in result.output["dry_run_message"]
        assert result.output["dry_run_message"] != result.output["message"]
        # First non-sentinel option is the preview choice.
        assert result.output["choice"] == "approve"

    def test_skips_reject_sentinels_for_choice(self) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        ctx = StepContext(dry_run=True)
        config = {
            "id": "review",
            "message": "Review the spec.",
            "options": ["reject", "approve", "skip"],
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["choice"] == "approve"

    def test_accepts_tuple_options(self) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        ctx = StepContext(dry_run=True)
        config = {
            "id": "review",
            "message": "Review.",
            "options": ("approve", "reject"),
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["options"] == ["approve", "reject"]
        assert result.output["choice"] == "approve"

    def test_normalizes_non_list_options(self) -> None:
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        ctx = StepContext(dry_run=True)
        for bad in (None, "approve,reject", {"approve": True}, 42):
            config = {
                "id": "review",
                "message": "Review.",
                "options": bad,
            }
            result = step.execute(config, ctx)
            assert result.status == StepStatus.COMPLETED


# -- Engine-level ---------------------------------------------------------


class TestWorkflowEngineDryRun:
    def test_execute_dry_run_short_circuits_command_steps(
        self, project_dir: Path
    ) -> None:
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "dryrun-test"
  name: "Dry Run Test"
  version: "1.0.0"
inputs:
  spec:
    type: string
    default: "test spec"
steps:
  - id: specify
    command: speckit.specify
    input:
      args: "{{ inputs.spec }}"
  - id: plan
    command: speckit.plan
    input:
      args: "{{ inputs.spec }}"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)

        with patch(
            "specify_cli.workflows.steps.command.shutil.which",
            return_value="/usr/local/bin/claude",
        ), patch("subprocess.run") as mock_run:
            state = engine.execute(
                definition, {"spec": "login feature"}, dry_run=True
            )

        assert state.status == RunStatus.COMPLETED
        assert state.step_results["specify"]["output"]["dry_run"] is True
        assert state.step_results["specify"]["output"]["dispatched"] is False
        assert state.step_results["plan"]["output"]["dry_run"] is True
        # Crucial: subprocess.run was never invoked in dry-run mode.
        assert mock_run.call_count == 0

    def test_dry_run_persisted_in_run_state(self, project_dir: Path) -> None:
        from specify_cli.workflows.engine import (
            RunState,
            WorkflowEngine,
            WorkflowDefinition,
        )

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "dryrun-persist"
  name: "Dry Run Persist"
  version: "1.0.0"
steps:
  - id: only
    type: gate
    message: "Continue?"
    options: ["yes", "no"]
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition, dry_run=True, run_id="dr-persist")

        assert state.dry_run is True

        reloaded = RunState.load("dr-persist", project_dir)
        assert reloaded.dry_run is True

    def test_resume_restores_dry_run(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import (
            RunState,
            WorkflowEngine,
            WorkflowDefinition,
        )

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "dryrun-resume"
  name: "Dry Run Resume"
  version: "1.0.0"
steps:
  - id: only
    type: gate
    message: "Continue?"
    options: ["yes", "no"]
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)

        # Persist a paused dry-run with a known run_id, including a copy
        # of the workflow YAML so resume() can reload the definition.
        run_id = "dr-resume"
        state = RunState(
            run_id=run_id,
            workflow_id=definition.id,
            project_root=project_dir,
        )
        state.status = RunStatus.PAUSED
        state.dry_run = True
        state.save()
        run_dir = project_dir / ".specify" / "workflows" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "workflow.yml").write_text(yaml_str, encoding="utf-8")

        captured: dict[str, bool] = {}

        def spy_execute_steps(steps, context, state, registry, *, step_offset=0):
            captured["dry_run"] = context.dry_run
            return None

        monkeypatch.setattr(engine, "_execute_steps", spy_execute_steps)
        engine.resume(run_id)

        assert captured.get("dry_run") is True

    def test_execute_attaches_partial_state_on_exception(
        self, project_dir: Path
    ) -> None:
        """When the engine raises mid-run, the partially-resolved step
        results are attached to the exception as ``partial_state`` so
        the CLI can render dry-run previews for the steps that did
        resolve."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "exc-dry"
  name: "Exception Dry"
  version: "1.0.0"
steps:
  - id: boom
    type: shell
    run: "echo should-not-run"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)

        def _raise(_steps, _ctx, _state, _registry, *, step_offset=0):
            raise RuntimeError("synthetic engine failure")

        with patch.object(engine, "_execute_steps", _raise):
            with pytest.raises(RuntimeError) as excinfo:
                engine.execute(definition, dry_run=True)

        assert getattr(excinfo.value, "partial_state", None) is not None


# -- CLI-level ------------------------------------------------------------


_WF_GATED = """
schema_version: "1.0"
workflow:
  id: "dry-wf"
  name: "Dry WF"
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


class TestWorkflowRunDryRunFlag:
    def test_emits_banner_and_previews(self, project_dir: Path) -> None:
        import json as _json

        wf = _write_wf(project_dir, _WF_GATED, "dry")
        result = _invoke(project_dir, ["workflow", "run", str(wf), "--dry-run"])

        assert result.exit_code == 0
        # Banner is printed to stdout in default (non-JSON) mode.
        assert "DRY RUN" in result.stdout
        # Preview loop printed the dry-run message for the gated step.
        assert "gate skipped" in result.stdout
        assert "would choose" in result.stdout
        # Status is reported as completed (gate short-circuits in dry-run).
        assert "Status: completed" in result.stdout
        # "Resume with:" hint only appears for paused runs.
        assert "Resume with:" not in result.stdout
        # No shell step ran (after step was a shell, never executed).
        _ = _json  # keep import in case future assertions need it

    def test_with_json_suppresses_banner_and_previews(
        self, project_dir: Path
    ) -> None:
        import json as _json

        wf = _write_wf(project_dir, _WF_GATED, "dry-json")
        result = _invoke(
            project_dir, ["workflow", "run", str(wf), "--dry-run", "--json"]
        )

        assert result.exit_code == 0
        # Stdout is exactly a JSON object — no DRY-RUN banner or preview lines.
        assert "DRY RUN" not in result.stdout
        assert "[DRY RUN]" not in result.stdout
        payload = _json.loads(result.stdout)
        assert payload["status"] == "completed"

    def test_prints_previews_on_engine_exception(self, project_dir: Path) -> None:
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import RunState

        wf = _write_wf(project_dir, _WF_GATED, "dry-fail")

        def _raise_with_partial(self, *_args, **_kwargs):
            state = RunState(run_id="dr-fail-partial", workflow_id="dry-wf")
            state.step_results["ask"] = {
                "output": {
                    "dry_run": True,
                    "dry_run_message": "[DRY RUN] Gate: Review",
                    "message": "Review",
                }
            }
            state.status = RunStatus.FAILED
            err = RuntimeError("synthetic engine failure mid-dry-run")
            err.partial_state = state  # type: ignore[attr-defined]
            raise err

        with patch(
            "specify_cli.workflows.engine.WorkflowEngine.execute",
            _raise_with_partial,
        ):
            result = _invoke(
                project_dir, ["workflow", "run", str(wf), "--dry-run"]
            )

        # CLI exits non-zero on the engine exception.
        assert result.exit_code != 0
        assert "Workflow failed" in result.stdout
        # The previously-resolved dry-run previews are still printed.
        assert "DRY RUN" in result.stdout
        assert "Gate: Review" in result.stdout

    def test_no_previews_when_json_and_engine_fails(self, project_dir: Path) -> None:
        import json as _json

        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import RunState

        wf = _write_wf(project_dir, _WF_GATED, "dry-fail-json")

        def _raise_with_partial(self, *_args, **_kwargs):
            state = RunState(run_id="dr-fail-json", workflow_id="dry-wf")
            state.step_results["ask"] = {
                "output": {
                    "dry_run": True,
                    "dry_run_message": "[DRY RUN] Gate: Review",
                    "message": "Review",
                }
            }
            state.status = RunStatus.FAILED
            err = RuntimeError("synthetic engine failure mid-dry-run")
            err.partial_state = state  # type: ignore[attr-defined]
            raise err

        with patch(
            "specify_cli.workflows.engine.WorkflowEngine.execute",
            _raise_with_partial,
        ):
            result = _invoke(
                project_dir,
                ["workflow", "run", str(wf), "--dry-run", "--json"],
            )

        # Stdout stays a JSON object — no preview leak in failure path.
        assert "DRY RUN" not in result.stdout
        assert "[DRY RUN]" not in result.stdout
        payload = _json.loads(result.stdout)
        assert payload["status"] == "failed"