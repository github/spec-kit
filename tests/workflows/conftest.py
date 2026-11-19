"""Shared fixtures for workflow tests."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=(sys.platform == "win32"))


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project with ``.specify/workflows/`` directory."""
    workflows_dir = temp_dir / ".specify" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


@pytest.fixture
def bundled_review(monkeypatch, project_dir):
    """Run a canonical workflow up to a review, without invoking an agent."""
    from specify_cli.workflows.base import RunStatus, StepResult, StepStatus
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
    from specify_cli.workflows.step import gate as gate_module
    from specify_cli.workflows.step.command import CommandStep

    def start(workflow_id: str, gate_id: str):
        commands: list[str] = []
        tty = gate_id == "review-plan"

        def execute_command(self, config, context):
            commands.append(config["command"])
            return StepResult(status=StepStatus.COMPLETED)

        def approve_previous_review(message, options):
            nonlocal tty
            assert tty
            tty = False
            return "approve"

        monkeypatch.setattr(CommandStep, "execute", execute_command)
        monkeypatch.setattr(
            gate_module, "sys",
            SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: tty)),
        )
        monkeypatch.setattr(
            gate_module.GateStep, "_prompt", staticmethod(approve_previous_review)
        )
        definition = WorkflowDefinition.from_yaml(
            Path(__file__).resolve().parents[2]
            / "workflows" / workflow_id / "workflow.yml"
        )
        engine = WorkflowEngine(project_dir)
        assert engine.validate(definition) == []
        inputs = (
            {"spec": "Test feature"}
            if workflow_id == "speckit"
            else {"report": "Test bug report", "slug": "test-bug"}
        )
        state = engine.execute(definition, inputs={**inputs, "integration": "copilot"})
        assert state.status is RunStatus.PAUSED
        assert state.current_step_id == gate_id
        monkeypatch.setattr(
            gate_module.GateStep, "_prompt",
            staticmethod(lambda *_: pytest.fail("Unexpected review prompt")),
        )
        return engine, state, commands

    return start


@pytest.fixture
def resume_bundled_review(monkeypatch, project_dir):
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.workflows.engine import RunState

    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project_dir))

    def resume(state, input_name: str, value: str):
        result = CliRunner().invoke(
            app, ["workflow", "resume", state.run_id, "--input", f"{input_name}={value}"]
        )
        return result, RunState.load(state.run_id, project_dir)

    return resume
