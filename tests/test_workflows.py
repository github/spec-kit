"""Tests for the workflow engine subsystem.

Covers:
- Step registry & auto-discovery
- Base classes (StepBase, StepContext, StepResult)
- Expression engine
- All 10 built-in step types
- Workflow definition loading & validation
- Workflow engine execution & state persistence
- Workflow catalog & registry
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project with .specify/ directory."""
    specify_dir = temp_dir / ".specify"
    specify_dir.mkdir()
    (specify_dir / "workflows").mkdir()
    return temp_dir


@pytest.fixture
def sample_workflow_yaml():
    """Return a valid minimal workflow YAML string."""
    return """
schema_version: "1.0"
workflow:
  id: "test-workflow"
  name: "Test Workflow"
  version: "1.0.0"
  description: "A test workflow"

inputs:
  spec:
    type: string
    required: true
  scope:
    type: string
    default: "full"

steps:
  - id: step-one
    command: speckit.specify
    input:
      args: "{{ inputs.spec }}"

  - id: step-two
    command: speckit.plan
    input:
      args: "{{ steps.step-one.output.command }}"
"""


@pytest.fixture
def sample_workflow_file(project_dir, sample_workflow_yaml):
    """Write a sample workflow YAML to a file and return its path."""
    wf_dir = project_dir / ".specify" / "workflows" / "test-workflow"
    wf_dir.mkdir(parents=True, exist_ok=True)
    wf_path = wf_dir / "workflow.yml"
    wf_path.write_text(sample_workflow_yaml, encoding="utf-8")
    return wf_path


# ===== Step Registry Tests =====

class TestStepRegistry:
    """Test STEP_REGISTRY and auto-discovery."""

    def test_registry_populated(self):
        from specify_cli.workflows import STEP_REGISTRY

        assert len(STEP_REGISTRY) >= 10

    def test_all_step_types_registered(self):
        from specify_cli.workflows import STEP_REGISTRY

        expected = {
            "command", "shell", "prompt", "gate", "if", "switch",
            "while", "do-while", "fan-out", "fan-in",
        }
        assert expected.issubset(set(STEP_REGISTRY.keys()))

    def test_get_step_type(self):
        from specify_cli.workflows import get_step_type

        step = get_step_type("command")
        assert step is not None
        assert step.type_key == "command"

    def test_get_step_type_missing(self):
        from specify_cli.workflows import get_step_type

        assert get_step_type("nonexistent") is None

    def test_register_step_duplicate_raises(self):
        from specify_cli.workflows import _register_step
        from specify_cli.workflows.steps.command import CommandStep

        with pytest.raises(KeyError, match="already registered"):
            _register_step(CommandStep())

    def test_register_step_empty_key_raises(self):
        from specify_cli.workflows import _register_step
        from specify_cli.workflows.base import StepBase, StepResult

        class EmptyStep(StepBase):
            type_key = ""
            def execute(self, config, context):
                return StepResult()

        with pytest.raises(ValueError, match="empty type_key"):
            _register_step(EmptyStep())


# ===== Base Classes Tests =====

class TestBaseClasses:
    """Test StepBase, StepContext, StepResult."""

    def test_step_context_defaults(self):
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert ctx.inputs == {}
        assert ctx.steps == {}
        assert ctx.item is None
        assert ctx.fan_in == {}
        assert ctx.default_integration is None

    def test_step_context_with_data(self):
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            inputs={"name": "test"},
            default_integration="claude",
            default_model="sonnet-4",
        )
        assert ctx.inputs == {"name": "test"}
        assert ctx.default_integration == "claude"
        assert ctx.default_model == "sonnet-4"

    def test_step_result_defaults(self):
        from specify_cli.workflows.base import StepResult, StepStatus

        result = StepResult()
        assert result.status == StepStatus.COMPLETED
        assert result.output == {}
        assert result.next_steps == []
        assert result.error is None

    def test_step_status_values(self):
        from specify_cli.workflows.base import StepStatus

        assert StepStatus.PENDING == "pending"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.COMPLETED == "completed"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.SKIPPED == "skipped"
        assert StepStatus.PAUSED == "paused"

    def test_run_status_values(self):
        from specify_cli.workflows.base import RunStatus

        assert RunStatus.CREATED == "created"
        assert RunStatus.RUNNING == "running"
        assert RunStatus.PAUSED == "paused"
        assert RunStatus.COMPLETED == "completed"
        assert RunStatus.FAILED == "failed"
        assert RunStatus.ABORTED == "aborted"


# ===== Expression Engine Tests =====

class TestExpressions:
    """Test sandboxed expression evaluator."""

    def test_simple_variable(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"name": "login"})
        assert evaluate_expression("{{ inputs.name }}", ctx) == "login"

    def test_step_output_reference(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            steps={"specify": {"output": {"file": "spec.md"}}}
        )
        assert evaluate_expression("{{ steps.specify.output.file }}", ctx) == "spec.md"

    def test_string_interpolation(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"name": "login"})
        result = evaluate_expression("Feature: {{ inputs.name }} done", ctx)
        assert result == "Feature: login done"

    def test_comparison_equals(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"scope": "full"})
        assert evaluate_expression("{{ inputs.scope == 'full' }}", ctx) is True
        assert evaluate_expression("{{ inputs.scope == 'partial' }}", ctx) is False

    def test_comparison_not_equals(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            steps={"run-tests": {"output": {"exit_code": 1}}}
        )
        result = evaluate_expression("{{ steps.run-tests.output.exit_code != 0 }}", ctx)
        assert result is True

    def test_numeric_comparison(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            steps={"plan": {"output": {"task_count": 7}}}
        )
        assert evaluate_expression("{{ steps.plan.output.task_count > 5 }}", ctx) is True
        assert evaluate_expression("{{ steps.plan.output.task_count < 5 }}", ctx) is False

    def test_boolean_and(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"a": True, "b": True})
        assert evaluate_expression("{{ inputs.a and inputs.b }}", ctx) is True

    def test_boolean_or(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"a": False, "b": True})
        assert evaluate_expression("{{ inputs.a or inputs.b }}", ctx) is True

    def test_filter_default(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression("{{ inputs.missing | default('fallback') }}", ctx) == "fallback"

    def test_filter_join(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"tags": ["a", "b", "c"]})
        assert evaluate_expression("{{ inputs.tags | join(', ') }}", ctx) == "a, b, c"

    def test_filter_contains(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"text": "hello world"})
        assert evaluate_expression("{{ inputs.text | contains('world') }}", ctx) is True

    def test_condition_evaluation(self):
        from specify_cli.workflows.expressions import evaluate_condition
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"ready": True})
        assert evaluate_condition("{{ inputs.ready }}", ctx) is True
        assert evaluate_condition("{{ inputs.missing }}", ctx) is False

    def test_non_string_passthrough(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression(42, ctx) == 42
        assert evaluate_expression(None, ctx) is None

    def test_string_literal(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression("{{ 'hello' }}", ctx) == "hello"

    def test_numeric_literal(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression("{{ 42 }}", ctx) == 42

    def test_boolean_literal(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression("{{ true }}", ctx) is True
        assert evaluate_expression("{{ false }}", ctx) is False

    def test_list_indexing(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            steps={"tasks": {"output": {"task_list": [{"file": "a.md"}, {"file": "b.md"}]}}}
        )
        result = evaluate_expression("{{ steps.tasks.output.task_list[0].file }}", ctx)
        assert result == "a.md"


# ===== Integration Dispatch Tests =====

class TestBuildExecArgs:
    """Test build_exec_args for CLI-based integrations."""

    def test_claude_exec_args(self):
        from specify_cli.integrations.claude import ClaudeIntegration
        impl = ClaudeIntegration()
        args = impl.build_exec_args("do stuff", model="sonnet-4")
        assert args[0] == "claude"
        assert args[1] == "-p"
        assert args[2] == "do stuff"
        assert "--model" in args
        assert "sonnet-4" in args
        assert "--output-format" in args

    def test_gemini_exec_args(self):
        from specify_cli.integrations.gemini import GeminiIntegration
        impl = GeminiIntegration()
        args = impl.build_exec_args("do stuff", model="gemini-2.5-pro")
        assert args[0] == "gemini"
        assert args[1] == "-p"
        assert "-m" in args
        assert "gemini-2.5-pro" in args

    def test_codex_exec_args(self):
        from specify_cli.integrations.codex import CodexIntegration
        impl = CodexIntegration()
        args = impl.build_exec_args("do stuff")
        assert args[0] == "codex"
        assert args[1] == "exec"
        assert args[2] == "do stuff"
        assert "--json" in args

    def test_copilot_exec_args(self, monkeypatch):
        monkeypatch.delenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", raising=False)
        monkeypatch.delenv("SPECKIT_ALLOW_ALL_TOOLS", raising=False)
        from specify_cli.integrations.copilot import CopilotIntegration
        impl = CopilotIntegration()
        args = impl.build_exec_args("do stuff", model="claude-sonnet-4-20250514")
        assert args[0] == "copilot"
        assert "-p" in args
        assert "--yolo" in args
        assert "--model" in args

    def test_copilot_new_env_var_disables_yolo(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
        monkeypatch.delenv("SPECKIT_ALLOW_ALL_TOOLS", raising=False)
        from specify_cli.integrations.copilot import CopilotIntegration
        impl = CopilotIntegration()
        args = impl.build_exec_args("do stuff")
        assert "--yolo" not in args

    def test_copilot_deprecated_env_var_still_honoured(self, monkeypatch):
        monkeypatch.delenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", raising=False)
        monkeypatch.setenv("SPECKIT_ALLOW_ALL_TOOLS", "0")
        import warnings
        from specify_cli.integrations.copilot import CopilotIntegration
        impl = CopilotIntegration()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            args = impl.build_exec_args("do stuff")
        assert "--yolo" not in args
        assert any(
            "SPECKIT_ALLOW_ALL_TOOLS is deprecated" in str(x.message)
            and issubclass(x.category, UserWarning)
            for x in w
        )

    def test_copilot_new_env_var_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "1")
        monkeypatch.setenv("SPECKIT_ALLOW_ALL_TOOLS", "0")
        from specify_cli.integrations.copilot import CopilotIntegration
        impl = CopilotIntegration()
        args = impl.build_exec_args("do stuff")
        assert "--yolo" in args

    def test_ide_only_returns_none(self):
        from specify_cli.integrations.windsurf import WindsurfIntegration
        impl = WindsurfIntegration()
        assert impl.build_exec_args("test") is None

    def test_no_model_omits_flag(self):
        from specify_cli.integrations.claude import ClaudeIntegration
        impl = ClaudeIntegration()
        args = impl.build_exec_args("do stuff", model=None)
        assert "--model" not in args

    def test_no_json_omits_flag(self):
        from specify_cli.integrations.claude import ClaudeIntegration
        impl = ClaudeIntegration()
        args = impl.build_exec_args("do stuff", output_json=False)
        assert "--output-format" not in args


# ===== Step Type Tests =====

class TestCommandStep:
    """Test the command step type."""

    def test_execute_basic(self):
        from unittest.mock import patch
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(
            inputs={"name": "login"},
            default_integration="claude",
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "{{ inputs.name }}"},
        }
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["command"] == "speckit.specify"
        assert result.output["integration"] == "claude"
        assert result.output["input"]["args"] == "login"

    def test_validate_missing_command(self):
        from specify_cli.workflows.steps.command import CommandStep

        step = CommandStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'command'" in e for e in errors)

    def test_step_override_integration(self):
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_integration="claude")
        config = {
            "id": "test",
            "command": "speckit.plan",
            "integration": "gemini",
            "input": {},
        }
        result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_step_override_model(self):
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_model="sonnet-4")
        config = {
            "id": "test",
            "command": "speckit.implement",
            "model": "opus-4",
            "input": {},
        }
        result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_options_merge(self):
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_options={"max-tokens": 8000})
        config = {
            "id": "test",
            "command": "speckit.plan",
            "options": {"thinking-budget": 32768},
            "input": {},
        }
        result = step.execute(config, ctx)
        assert result.output["options"]["max-tokens"] == 8000
        assert result.output["options"]["thinking-budget"] == 32768

    def test_dispatch_not_attempted_without_cli(self):
        """When the CLI tool is not installed, step should fail."""
        from unittest.mock import patch
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(
            inputs={"name": "login"},
            default_integration="claude",
            project_root="/tmp",
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "{{ inputs.name }}"},
        }
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert result.error is not None

    def test_dispatch_with_mock_cli(self, tmp_path, monkeypatch):
        """When the CLI is installed, dispatch invokes the command by name."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(
            inputs={"name": "login"},
            default_integration="claude",
            project_root=str(tmp_path),
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "{{ inputs.name }}"},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"result": "done"}'
        mock_result.stderr = ""

        with patch("specify_cli.workflows.steps.command.shutil.which", return_value="/usr/local/bin/claude"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0
        # Verify the CLI was called with -p and the skill invocation
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "claude"
        assert call_args[0][0][1] == "-p"
        # Claude is a SkillsIntegration so uses /speckit-specify
        assert "/speckit-specify login" in call_args[0][0][2]

    def test_dispatch_failure_returns_failed_status(self, tmp_path):
        """When the CLI exits non-zero, the step should fail."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(
            inputs={},
            default_integration="claude",
            project_root=str(tmp_path),
        )
        config = {
            "id": "test",
            "command": "speckit.specify",
            "input": {"args": "test"},
        }

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "API error"

        with patch("specify_cli.workflows.steps.command.shutil.which", return_value="/usr/local/bin/claude"), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 1


class TestPromptStep:
    """Test the prompt step type."""

    def test_execute_basic(self):
        from unittest.mock import patch
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        ctx = StepContext(
            inputs={"file": "auth.py"},
            default_integration="claude",
        )
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "Review {{ inputs.file }} for security issues",
        }
        with patch("specify_cli.workflows.steps.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["prompt"] == "Review auth.py for security issues"
        assert result.output["integration"] == "claude"
        assert result.output["dispatched"] is False

    def test_execute_with_step_integration(self):
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext

        step = PromptStep()
        ctx = StepContext(default_integration="claude")
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "Summarize the codebase",
            "integration": "gemini",
        }
        result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_execute_with_model(self):
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext

        step = PromptStep()
        ctx = StepContext(default_integration="claude", default_model="sonnet-4")
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "hello",
            "model": "opus-4",
        }
        result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_dispatch_with_mock_cli(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        ctx = StepContext(
            default_integration="claude",
            project_root=str(tmp_path),
        )
        config = {
            "id": "ask",
            "type": "prompt",
            "prompt": "Explain this code",
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Here is the explanation"
        mock_result.stderr = ""

        with patch("specify_cli.workflows.steps.prompt.shutil.which", return_value="/usr/local/bin/claude"), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

    def test_validate_missing_prompt(self):
        from specify_cli.workflows.steps.prompt import PromptStep

        step = PromptStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'prompt'" in e for e in errors)

    def test_validate_valid(self):
        from specify_cli.workflows.steps.prompt import PromptStep

        step = PromptStep()
        errors = step.validate({"id": "test", "prompt": "do something"})
        assert errors == []


class TestShellStep:
    """Test the shell step type."""

    def test_execute_echo(self):
        from specify_cli.workflows.steps.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext()
        config = {"id": "test", "run": "echo hello"}
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["exit_code"] == 0
        assert "hello" in result.output["stdout"]

    def test_execute_failure(self):
        from specify_cli.workflows.steps.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext()
        config = {"id": "test", "run": "exit 1"}
        result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["exit_code"] == 1
        assert result.error is not None

    def test_validate_missing_run(self):
        from specify_cli.workflows.steps.shell import ShellStep

        step = ShellStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'run'" in e for e in errors)


class TestGateStep:
    """Test the gate step type."""

    def test_execute_returns_paused(self):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = GateStep()
        ctx = StepContext()
        config = {
            "id": "review",
            "message": "Review the spec.",
            "options": ["approve", "reject"],
            "on_reject": "abort",
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.PAUSED
        assert result.output["message"] == "Review the spec."
        assert result.output["options"] == ["approve", "reject"]

    def test_validate_missing_message(self):
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        errors = step.validate({"id": "test", "options": ["approve"]})
        assert any("missing 'message'" in e for e in errors)

    def test_validate_invalid_on_reject(self):
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        errors = step.validate({
            "id": "test",
            "message": "Review",
            "on_reject": "invalid",
        })
        assert any("on_reject" in e for e in errors)


class TestIfThenStep:
    """Test the if/then/else step type."""

    def test_execute_then_branch(self):
        from specify_cli.workflows.steps.if_then import IfThenStep
        from specify_cli.workflows.base import StepContext

        step = IfThenStep()
        ctx = StepContext(inputs={"scope": "full"})
        config = {
            "id": "check",
            "condition": "{{ inputs.scope == 'full' }}",
            "then": [{"id": "a", "command": "speckit.tasks"}],
            "else": [{"id": "b", "command": "speckit.plan"}],
        }
        result = step.execute(config, ctx)
        assert result.output["condition_result"] is True
        assert len(result.next_steps) == 1
        assert result.next_steps[0]["id"] == "a"

    def test_execute_else_branch(self):
        from specify_cli.workflows.steps.if_then import IfThenStep
        from specify_cli.workflows.base import StepContext

        step = IfThenStep()
        ctx = StepContext(inputs={"scope": "backend"})
        config = {
            "id": "check",
            "condition": "{{ inputs.scope == 'full' }}",
            "then": [{"id": "a", "command": "speckit.tasks"}],
            "else": [{"id": "b", "command": "speckit.plan"}],
        }
        result = step.execute(config, ctx)
        assert result.output["condition_result"] is False
        assert result.next_steps[0]["id"] == "b"

    def test_validate_missing_condition(self):
        from specify_cli.workflows.steps.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate({"id": "test", "then": []})
        assert any("missing 'condition'" in e for e in errors)


class TestSwitchStep:
    """Test the switch step type."""

    def test_execute_matches_case(self):
        from specify_cli.workflows.steps.switch import SwitchStep
        from specify_cli.workflows.base import StepContext

        step = SwitchStep()
        ctx = StepContext(
            steps={"review": {"output": {"choice": "approve"}}}
        )
        config = {
            "id": "route",
            "expression": "{{ steps.review.output.choice }}",
            "cases": {
                "approve": [{"id": "plan", "command": "speckit.plan"}],
                "reject": [{"id": "log", "type": "shell", "run": "echo rejected"}],
            },
            "default": [{"id": "abort", "type": "gate", "message": "Unknown"}],
        }
        result = step.execute(config, ctx)
        assert result.output["matched_case"] == "approve"
        assert result.next_steps[0]["id"] == "plan"

    def test_execute_falls_to_default(self):
        from specify_cli.workflows.steps.switch import SwitchStep
        from specify_cli.workflows.base import StepContext

        step = SwitchStep()
        ctx = StepContext(
            steps={"review": {"output": {"choice": "unknown"}}}
        )
        config = {
            "id": "route",
            "expression": "{{ steps.review.output.choice }}",
            "cases": {
                "approve": [{"id": "plan", "command": "speckit.plan"}],
            },
            "default": [{"id": "fallback", "type": "gate", "message": "Fallback"}],
        }
        result = step.execute(config, ctx)
        assert result.output["matched_case"] == "__default__"
        assert result.next_steps[0]["id"] == "fallback"

    def test_execute_no_default_no_match(self):
        from specify_cli.workflows.steps.switch import SwitchStep
        from specify_cli.workflows.base import StepContext

        step = SwitchStep()
        ctx = StepContext(
            steps={"review": {"output": {"choice": "other"}}}
        )
        config = {
            "id": "route",
            "expression": "{{ steps.review.output.choice }}",
            "cases": {
                "approve": [{"id": "plan", "command": "speckit.plan"}],
            },
        }
        result = step.execute(config, ctx)
        assert result.output["matched_case"] == "__default__"
        assert result.next_steps == []

    def test_validate_missing_expression(self):
        from specify_cli.workflows.steps.switch import SwitchStep

        step = SwitchStep()
        errors = step.validate({"id": "test", "cases": {}})
        assert any("missing 'expression'" in e for e in errors)

    def test_validate_invalid_cases_and_default(self):
        from specify_cli.workflows.steps.switch import SwitchStep

        step = SwitchStep()
        errors = step.validate({
            "id": "test",
            "expression": "{{ x }}",
            "cases": {"a": "not-a-list"},
            "default": "also-bad",
        })
        assert any("case 'a' must be a list" in e for e in errors)
        assert any("'default' must be a list" in e for e in errors)


class TestWhileStep:
    """Test the while loop step type."""

    def test_execute_condition_true(self):
        from specify_cli.workflows.steps.while_loop import WhileStep
        from specify_cli.workflows.base import StepContext

        step = WhileStep()
        ctx = StepContext(
            steps={"run-tests": {"output": {"exit_code": 1}}}
        )
        config = {
            "id": "retry",
            "condition": "{{ steps.run-tests.output.exit_code != 0 }}",
            "max_iterations": 5,
            "steps": [{"id": "fix", "command": "speckit.implement"}],
        }
        result = step.execute(config, ctx)
        assert result.output["condition_result"] is True
        assert len(result.next_steps) == 1

    def test_execute_condition_false(self):
        from specify_cli.workflows.steps.while_loop import WhileStep
        from specify_cli.workflows.base import StepContext

        step = WhileStep()
        ctx = StepContext(
            steps={"run-tests": {"output": {"exit_code": 0}}}
        )
        config = {
            "id": "retry",
            "condition": "{{ steps.run-tests.output.exit_code != 0 }}",
            "max_iterations": 5,
            "steps": [{"id": "fix", "command": "speckit.implement"}],
        }
        result = step.execute(config, ctx)
        assert result.output["condition_result"] is False
        assert result.next_steps == []

    def test_validate_missing_fields(self):
        from specify_cli.workflows.steps.while_loop import WhileStep

        step = WhileStep()
        errors = step.validate({"id": "test", "steps": []})
        assert any("missing 'condition'" in e for e in errors)
        # max_iterations is optional (defaults to 10)

    def test_validate_invalid_max_iterations(self):
        from specify_cli.workflows.steps.while_loop import WhileStep

        step = WhileStep()
        errors = step.validate({"id": "test", "condition": "{{ true }}", "max_iterations": 0, "steps": []})
        assert any("must be an integer >= 1" in e for e in errors)


class TestDoWhileStep:
    """Test the do-while loop step type."""

    def test_execute_always_runs_once(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep
        from specify_cli.workflows.base import StepContext

        step = DoWhileStep()
        ctx = StepContext()
        config = {
            "id": "cycle",
            "condition": "{{ false }}",
            "max_iterations": 3,
            "steps": [{"id": "refine", "command": "speckit.specify"}],
        }
        result = step.execute(config, ctx)
        assert len(result.next_steps) == 1
        assert result.output["loop_type"] == "do-while"
        assert result.output["condition"] == "{{ false }}"

    def test_execute_with_true_condition(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep
        from specify_cli.workflows.base import StepContext

        step = DoWhileStep()
        ctx = StepContext()
        config = {
            "id": "cycle",
            "condition": "{{ true }}",
            "max_iterations": 5,
            "steps": [{"id": "work", "command": "speckit.plan"}],
        }
        result = step.execute(config, ctx)
        # Body always executes on first call regardless of condition
        assert len(result.next_steps) == 1
        assert result.output["max_iterations"] == 5

    def test_execute_empty_steps(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep
        from specify_cli.workflows.base import StepContext

        step = DoWhileStep()
        ctx = StepContext()
        config = {
            "id": "empty",
            "condition": "{{ false }}",
            "max_iterations": 1,
            "steps": [],
        }
        result = step.execute(config, ctx)
        assert result.next_steps == []
        assert result.status.value == "completed"

    def test_validate_missing_fields(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep

        step = DoWhileStep()
        errors = step.validate({"id": "test", "steps": []})
        assert any("missing 'condition'" in e for e in errors)
        # max_iterations is optional (defaults to 10)

    def test_validate_steps_not_list(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep

        step = DoWhileStep()
        errors = step.validate({
            "id": "test",
            "condition": "{{ true }}",
            "max_iterations": 3,
            "steps": "not-a-list",
        })
        assert any("'steps' must be a list" in e for e in errors)


class TestFanOutStep:
    """Test the fan-out step type."""

    def test_execute_with_items(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep
        from specify_cli.workflows.base import StepContext

        step = FanOutStep()
        ctx = StepContext(
            steps={"tasks": {"output": {"task_list": [
                {"file": "a.md"},
                {"file": "b.md"},
            ]}}}
        )
        config = {
            "id": "parallel",
            "items": "{{ steps.tasks.output.task_list }}",
            "max_concurrency": 3,
            "step": {"id": "impl", "command": "speckit.implement"},
        }
        result = step.execute(config, ctx)
        assert result.output["item_count"] == 2
        assert result.output["max_concurrency"] == 3

    def test_execute_non_list_items_resolves_empty(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep
        from specify_cli.workflows.base import StepContext

        step = FanOutStep()
        ctx = StepContext()
        config = {
            "id": "parallel",
            "items": "{{ undefined_var }}",
            "step": {"id": "impl", "command": "speckit.implement"},
        }
        result = step.execute(config, ctx)
        assert result.output["item_count"] == 0
        assert result.output["items"] == []

    def test_validate_missing_fields(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep

        step = FanOutStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'items'" in e for e in errors)
        assert any("missing 'step'" in e for e in errors)

    def test_validate_step_not_mapping(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep

        step = FanOutStep()
        errors = step.validate({
            "id": "test",
            "items": "{{ x }}",
            "step": "not-a-dict",
        })
        assert any("'step' must be a mapping" in e for e in errors)


class TestFanInStep:
    """Test the fan-in step type."""

    def test_execute_collects_results(self):
        from specify_cli.workflows.steps.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext

        step = FanInStep()
        ctx = StepContext(
            steps={
                "parallel": {"output": {"item_count": 2, "status": "done"}}
            }
        )
        config = {
            "id": "collect",
            "wait_for": ["parallel"],
            "output": {},
        }
        result = step.execute(config, ctx)
        assert len(result.output["results"]) == 1
        assert result.output["results"][0]["item_count"] == 2

    def test_execute_multiple_wait_for(self):
        from specify_cli.workflows.steps.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext

        step = FanInStep()
        ctx = StepContext(
            steps={
                "task-a": {"output": {"file": "a.md"}},
                "task-b": {"output": {"file": "b.md"}},
            }
        )
        config = {
            "id": "collect",
            "wait_for": ["task-a", "task-b"],
            "output": {},
        }
        result = step.execute(config, ctx)
        assert len(result.output["results"]) == 2
        assert result.output["results"][0]["file"] == "a.md"
        assert result.output["results"][1]["file"] == "b.md"

    def test_execute_missing_wait_for_step(self):
        from specify_cli.workflows.steps.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext

        step = FanInStep()
        ctx = StepContext(steps={})
        config = {
            "id": "collect",
            "wait_for": ["nonexistent"],
            "output": {},
        }
        result = step.execute(config, ctx)
        assert result.output["results"] == [{}]

    def test_validate_empty_wait_for(self):
        from specify_cli.workflows.steps.fan_in import FanInStep

        step = FanInStep()
        errors = step.validate({"id": "test", "wait_for": []})
        assert any("non-empty list" in e for e in errors)

    def test_validate_wait_for_not_list(self):
        from specify_cli.workflows.steps.fan_in import FanInStep

        step = FanInStep()
        errors = step.validate({"id": "test", "wait_for": "not-a-list"})
        assert any("non-empty list" in e for e in errors)


# ===== Workflow Definition Tests =====

class TestWorkflowDefinition:
    """Test WorkflowDefinition loading and parsing."""

    def test_from_yaml(self, sample_workflow_file):
        from specify_cli.workflows.engine import WorkflowDefinition

        definition = WorkflowDefinition.from_yaml(sample_workflow_file)
        assert definition.id == "test-workflow"
        assert definition.name == "Test Workflow"
        assert definition.version == "1.0.0"
        assert len(definition.steps) == 2

    def test_from_string(self, sample_workflow_yaml):
        from specify_cli.workflows.engine import WorkflowDefinition

        definition = WorkflowDefinition.from_string(sample_workflow_yaml)
        assert definition.id == "test-workflow"
        assert len(definition.inputs) == 2

    def test_from_string_invalid(self):
        from specify_cli.workflows.engine import WorkflowDefinition

        with pytest.raises(ValueError, match="must be a mapping"):
            WorkflowDefinition.from_string("- just a list")

    def test_inputs_parsed(self, sample_workflow_yaml):
        from specify_cli.workflows.engine import WorkflowDefinition

        definition = WorkflowDefinition.from_string(sample_workflow_yaml)
        assert "spec" in definition.inputs
        assert definition.inputs["spec"]["required"] is True
        assert definition.inputs["scope"]["default"] == "full"


# ===== Workflow Validation Tests =====

class TestWorkflowValidation:
    """Test workflow validation."""

    def test_valid_workflow(self, sample_workflow_yaml):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string(sample_workflow_yaml)
        errors = validate_workflow(definition)
        assert errors == []

    def test_missing_id(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("workflow.id" in e for e in errors)

    def test_invalid_id_format(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "Invalid ID!"
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("lowercase alphanumeric" in e for e in errors)

    def test_no_steps(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps: []
""")
        errors = validate_workflow(definition)
        assert any("no steps" in e.lower() for e in errors)

    def test_duplicate_step_ids(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: same-id
    command: speckit.specify
  - id: same-id
    command: speckit.plan
""")
        errors = validate_workflow(definition)
        assert any("Duplicate" in e for e in errors)

    def test_invalid_step_type(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: bad
    type: nonexistent
""")
        errors = validate_workflow(definition)
        assert any("invalid type" in e.lower() for e in errors)

    def test_nested_step_validation(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: branch
    type: if
    condition: "{{ true }}"
    then:
      - id: nested-a
        command: speckit.specify
    else:
      - id: nested-b
        command: speckit.plan
""")
        errors = validate_workflow(definition)
        assert errors == []

    def test_invalid_input_type(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
inputs:
  bad:
    type: array
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("invalid type" in e.lower() for e in errors)


# ===== Workflow Engine Tests =====

class TestWorkflowEngine:
    """Test WorkflowEngine execution."""

    def test_load_from_file(self, sample_workflow_file, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(project_dir)
        definition = engine.load_workflow(str(sample_workflow_file))
        assert definition.id == "test-workflow"

    def test_load_from_installed_id(self, sample_workflow_file, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(project_dir)
        definition = engine.load_workflow("test-workflow")
        assert definition.id == "test-workflow"

    def test_load_not_found(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(project_dir)
        with pytest.raises(FileNotFoundError):
            engine.load_workflow("nonexistent")

    def test_execute_simple_workflow(self, project_dir):
        from unittest.mock import patch
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "simple"
  name: "Simple"
  version: "1.0.0"
  integration: claude
inputs:
  name:
    type: string
    default: "test"
steps:
  - id: step-one
    command: speckit.specify
    input:
      args: "{{ inputs.name }}"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
            state = engine.execute(definition, {"name": "login"})

        assert state.status == RunStatus.FAILED
        assert "step-one" in state.step_results
        assert state.step_results["step-one"]["output"]["command"] == "speckit.specify"
        assert state.step_results["step-one"]["output"]["input"]["args"] == "login"

    def test_execute_with_gate_pauses(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "gated"
  name: "Gated"
  version: "1.0.0"
steps:
  - id: step-one
    type: shell
    run: "echo test"
  - id: gate
    type: gate
    message: "Review?"
    options: [approve, reject]
    on_reject: abort
  - id: step-two
    type: shell
    run: "echo done"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.PAUSED
        assert "gate" in state.step_results
        assert state.step_results["gate"]["status"] == "paused"

    def test_execute_with_shell_step(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "shell-test"
  name: "Shell Test"
  version: "1.0.0"
steps:
  - id: echo
    type: shell
    run: "echo workflow-output"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert "workflow-output" in state.step_results["echo"]["output"]["stdout"]

    def test_execute_with_if_then(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "branching"
  name: "Branching"
  version: "1.0.0"
inputs:
  scope:
    type: string
    default: "full"
steps:
  - id: check
    type: if
    condition: "{{ inputs.scope == 'full' }}"
    then:
      - id: full-tasks
        type: shell
        run: "echo full"
    else:
      - id: partial-tasks
        type: shell
        run: "echo partial"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition, {"scope": "full"})

        assert state.status == RunStatus.COMPLETED
        assert "full-tasks" in state.step_results
        assert "partial-tasks" not in state.step_results

    def test_execute_missing_required_input(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "needs-input"
  name: "Needs Input"
  version: "1.0.0"
inputs:
  name:
    type: string
    required: true
steps:
  - id: step-one
    command: speckit.specify
    input:
      args: "{{ inputs.name }}"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)

        with pytest.raises(ValueError, match="Required input"):
            engine.execute(definition, {})


# ===== State Persistence Tests =====

class TestRunState:
    """Test RunState persistence and loading."""

    def test_save_and_load(self, project_dir):
        from specify_cli.workflows.engine import RunState
        from specify_cli.workflows.base import RunStatus

        state = RunState(
            run_id="test-run",
            workflow_id="test-workflow",
            project_root=project_dir,
        )
        state.status = RunStatus.RUNNING
        state.inputs = {"name": "login"}
        state.step_results = {
            "step-one": {
                "output": {"file": "spec.md"},
                "status": "completed",
            }
        }
        state.save()

        loaded = RunState.load("test-run", project_dir)
        assert loaded.run_id == "test-run"
        assert loaded.workflow_id == "test-workflow"
        assert loaded.status == RunStatus.RUNNING
        assert loaded.inputs == {"name": "login"}
        assert "step-one" in loaded.step_results

    def test_load_not_found(self, project_dir):
        from specify_cli.workflows.engine import RunState

        with pytest.raises(FileNotFoundError):
            RunState.load("nonexistent", project_dir)

    def test_append_log(self, project_dir):
        from specify_cli.workflows.engine import RunState

        state = RunState(
            run_id="log-test",
            workflow_id="test",
            project_root=project_dir,
        )
        state.append_log({"event": "test_event", "data": "hello"})

        log_file = state.runs_dir / "log.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["event"] == "test_event"
        assert "timestamp" in entry


class TestListRuns:
    """Test listing workflow runs."""

    def test_list_empty(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        engine = WorkflowEngine(project_dir)
        assert engine.list_runs() == []

    def test_list_after_execution(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "list-test"
  name: "List Test"
  version: "1.0.0"
steps:
  - id: step-one
    type: shell
    run: "echo test"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        engine.execute(definition)

        runs = engine.list_runs()
        assert len(runs) == 1
        assert runs[0]["workflow_id"] == "list-test"


# ===== Workflow Registry Tests =====

class TestWorkflowRegistry:
    """Test WorkflowRegistry operations."""

    def test_add_and_get(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})

        entry = registry.get("test-wf")
        assert entry is not None
        assert entry["name"] == "Test"
        assert "installed_at" in entry

    def test_remove(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test"})
        assert registry.is_installed("test-wf")

        registry.remove("test-wf")
        assert not registry.is_installed("test-wf")

    def test_list(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("wf-a", {"name": "A"})
        registry.add("wf-b", {"name": "B"})

        installed = registry.list()
        assert "wf-a" in installed
        assert "wf-b" in installed

    def test_is_installed(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        assert not registry.is_installed("missing")

        registry.add("exists", {"name": "Exists"})
        assert registry.is_installed("exists")

    def test_persistence(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry1 = WorkflowRegistry(project_dir)
        registry1.add("test-wf", {"name": "Test"})

        # Load fresh
        registry2 = WorkflowRegistry(project_dir)
        assert registry2.is_installed("test-wf")

    def test_update(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})

        original_entry = registry.get("test-wf")
        original_installed_at = original_entry["installed_at"]

        registry.update("test-wf", {"version": "2.0.0", "enabled": False})

        entry = registry.get("test-wf")
        assert entry["version"] == "2.0.0"
        assert entry["enabled"] is False
        # Original fields preserved
        assert entry["name"] == "Test"
        # installed_at preserved, updated_at set
        assert entry["installed_at"] == original_installed_at
        assert "updated_at" in entry

    def test_update_nonexistent(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry
        import pytest

        registry = WorkflowRegistry(project_dir)
        with pytest.raises(KeyError):
            registry.update("missing", {"version": "2.0.0"})
        assert registry.get("missing") is None

    def test_enable_disable_via_update(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})

        # Disable
        registry.update("test-wf", {"enabled": False})
        entry = registry.get("test-wf")
        assert entry["enabled"] is False

        # Enable
        registry.update("test-wf", {"enabled": True})
        entry = registry.get("test-wf")
        assert entry["enabled"] is True


# ===== Workflow Catalog Tests =====

class TestWorkflowCatalog:
    """Test WorkflowCatalog catalog resolution."""

    def test_default_catalogs(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 2
        assert entries[0].name == "default"
        assert entries[1].name == "community"

    def test_env_var_override(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.setenv("SPECKIT_WORKFLOW_CATALOG_URL", "https://example.com/catalog.json")
        catalog = WorkflowCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 1
        assert entries[0].name == "env-override"
        assert entries[0].url == "https://example.com/catalog.json"

    def test_project_level_config(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "custom",
                "url": "https://example.com/wf-catalog.json",
                "priority": 1,
                "install_allowed": True,
            }]
        }))

        catalog = WorkflowCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 1
        assert entries[0].name == "custom"

    def test_validate_url_http_rejected(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="HTTPS"):
            catalog._validate_catalog_url("http://evil.com/catalog.json")

    def test_validate_url_localhost_http_allowed(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        # Should not raise
        catalog._validate_catalog_url("http://localhost:8080/catalog.json")

    def test_add_catalog(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/new-catalog.json", "my-catalog")

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/new-catalog.json"

    def test_add_catalog_duplicate_rejected(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/catalog.json")

        with pytest.raises(WorkflowValidationError, match="already configured"):
            catalog.add_catalog("https://example.com/catalog.json")

    def test_remove_catalog(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/c1.json", "first")
        catalog.add_catalog("https://example.com/c2.json", "second")

        removed = catalog.remove_catalog(0)
        assert removed == "first"

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1

    def test_remove_catalog_invalid_index(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/c1.json")

        with pytest.raises(WorkflowValidationError, match="out of range"):
            catalog.remove_catalog(5)

    def test_get_catalog_configs(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        configs = catalog.get_catalog_configs()
        assert len(configs) == 2
        assert configs[0]["name"] == "default"
        assert isinstance(configs[0]["install_allowed"], bool)

    def test_search_author_filter(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)

        # Mock _get_merged_workflows to return test data
        def mock_merged(force_refresh=False):
            return {
                "wf-a": {"id": "wf-a", "name": "Alpha", "author": "Alice", "tags": []},
                "wf-b": {"id": "wf-b", "name": "Beta", "author": "Bob", "tags": ["sdd"]},
                "wf-c": {"id": "wf-c", "name": "Charlie", "author": "Alice", "tags": ["deploy"]},
            }

        monkeypatch.setattr(catalog, "_get_merged_workflows", mock_merged)

        # Filter by author
        results = catalog.search(author="Alice")
        assert len(results) == 2
        assert all(r["author"] == "Alice" for r in results)

        # Filter by author (case-insensitive)
        results = catalog.search(author="alice")
        assert len(results) == 2

        # Filter by author + tag
        results = catalog.search(author="Alice", tag="deploy")
        assert len(results) == 1
        assert results[0]["id"] == "wf-c"

        # No match
        results = catalog.search(author="Nobody")
        assert len(results) == 0


# ===== Integration Test =====

class TestWorkflowIntegration:
    """End-to-end workflow execution tests."""

    def test_full_sequential_workflow(self, project_dir):
        """Execute a multi-step sequential workflow end to end."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "e2e-test"
  name: "E2E Test"
  version: "1.0.0"
  integration: claude
inputs:
  feature:
    type: string
    default: "login"
steps:
  - id: specify
    type: shell
    run: "echo speckit.specify {{ inputs.feature }}"

  - id: check-scope
    type: if
    condition: "{{ inputs.feature == 'login' }}"
    then:
      - id: echo-full
        type: shell
        run: "echo full scope"
    else:
      - id: echo-partial
        type: shell
        run: "echo partial scope"

  - id: plan
    type: shell
    run: "echo speckit.plan"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert "specify" in state.step_results
        assert "check-scope" in state.step_results
        assert "echo-full" in state.step_results
        assert "echo-partial" not in state.step_results
        assert "plan" in state.step_results

    def test_switch_workflow(self, project_dir):
        """Test switch step type in a workflow."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "switch-test"
  name: "Switch Test"
  version: "1.0.0"
inputs:
  action:
    type: string
    default: "plan"
steps:
  - id: route
    type: switch
    expression: "{{ inputs.action }}"
    cases:
      specify:
        - id: do-specify
          type: shell
          run: "echo specify"
      plan:
        - id: do-plan
          type: shell
          run: "echo plan"
    default:
      - id: do-default
        type: shell
        run: "echo default"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert "do-plan" in state.step_results
        assert "do-specify" not in state.step_results


# ===== CLI Integration Tests =====


class TestWorkflowCLI:
    """CLI integration tests for workflow commands via CliRunner."""

    def test_enable_not_installed(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "enable", "nonexistent"])
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_disable_not_installed(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "disable", "nonexistent"])
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_enable_disable_roundtrip(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        runner = CliRunner()
        monkeypatch.chdir(project_dir)

        # Pre-install a workflow in the registry
        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})

        # Disable
        result = runner.invoke(app, ["workflow", "disable", "test-wf"])
        assert result.exit_code == 0
        assert "disabled" in result.output

        # Already disabled
        result = runner.invoke(app, ["workflow", "disable", "test-wf"])
        assert result.exit_code == 0
        assert "already disabled" in result.output

        # Enable
        result = runner.invoke(app, ["workflow", "enable", "test-wf"])
        assert result.exit_code == 0
        assert "enabled" in result.output

        # Already enabled
        result = runner.invoke(app, ["workflow", "enable", "test-wf"])
        assert result.exit_code == 0
        assert "already enabled" in result.output

    def test_update_no_project(self, tmp_path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_update_not_installed(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "update", "nonexistent"])
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_add_no_source(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "add"])
        assert result.exit_code != 0

    def test_add_from_url_without_source(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        # --from with non-HTTPS should be rejected with URL scheme error, not missing source
        result = runner.invoke(app, ["workflow", "add", "--from", "http://evil.example.com/wf.yml"])
        assert result.exit_code != 0
        assert "HTTPS" in result.output

    def test_add_dev_missing_path(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "add", "--dev", "/nonexistent/path"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_list_shows_disabled(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        runner = CliRunner()
        monkeypatch.chdir(project_dir)

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test WF", "version": "1.0.0", "enabled": False})

        result = runner.invoke(app, ["workflow", "list"])
        assert result.exit_code == 0
        assert "disabled" in result.output

    def test_add_dev_and_from_mutually_exclusive(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "add", "--dev", "--from", "https://example.com/wf.yml", "./local"])
        assert result.exit_code != 0
        assert "cannot be combined" in result.output

    def test_add_dev_requires_source(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        monkeypatch.chdir(project_dir)
        result = runner.invoke(app, ["workflow", "add", "--dev"])
        assert result.exit_code != 0
        assert "--dev requires" in result.output or "path" in result.output.lower()

    def test_update_success_path(self, project_dir, monkeypatch):
        """Test workflow update happy path: download, validate, swap, registry update."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        runner = CliRunner()
        monkeypatch.chdir(project_dir)

        # Pre-install a workflow
        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test WF", "version": "1.0.0", "source": "catalog"})

        # Create the existing workflow directory
        wf_dir = project_dir / ".specify" / "workflows" / "test-wf"
        wf_dir.mkdir(parents=True, exist_ok=True)
        (wf_dir / "workflow.yml").write_text(
            'schema_version: "1.0"\nworkflow:\n  id: test-wf\n  name: Test WF\n  version: "1.0.0"\nsteps:\n  - id: step1\n    type: shell\n    run: "echo hello"\n'
        )

        # Prepare updated workflow YAML
        updated_yaml = (
            'schema_version: "1.0"\nworkflow:\n  id: test-wf\n  name: Test WF Updated\n  version: "2.0.0"\n'
            'steps:\n  - id: step1\n    type: shell\n    run: "echo hello"\n'
        )

        # Mock catalog to report v2.0.0 available
        mock_cat_info = {
            "name": "Test WF",
            "version": "2.0.0",
            "url": "https://example.com/test-wf/workflow.yml",
            "_install_allowed": True,
            "_catalog_name": "default",
        }

        with patch("specify_cli.workflows.catalog.WorkflowCatalog") as MockCatalog, \
             patch("specify_cli._download_validated") as mock_download:

            mock_instance = MagicMock()
            mock_instance.get_workflow_info.return_value = mock_cat_info
            MockCatalog.return_value = mock_instance

            def fake_download(url, dest):
                dest.write_text(updated_yaml)
            mock_download.side_effect = fake_download

            result = runner.invoke(app, ["workflow", "update", "test-wf"], input="y\n")

        assert result.exit_code == 0, result.output
        assert "2.0.0" in result.output

        # Verify registry was updated
        registry2 = WorkflowRegistry(project_dir)
        entry = registry2.get("test-wf")
        assert entry["version"] == "2.0.0"

        # Verify workflow file was swapped
        new_content = (wf_dir / "workflow.yml").read_text()
        assert "2.0.0" in new_content
