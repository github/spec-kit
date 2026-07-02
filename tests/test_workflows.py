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
import os
import shutil
import sys
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
    # On Windows, file handles from dynamic imports or registry access may
    # still be held briefly after the test. Use ignore_errors to avoid
    # flaky teardown failures (WinError 32).
    shutil.rmtree(tmpdir, ignore_errors=(sys.platform == "win32"))


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
            "while", "do-while", "fan-out", "fan-in", "init",
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

    def test_multi_expression_no_surrounding_text(self):
        """Two expressions with no surrounding literal text must interpolate each,
        not collapse to None via the fullmatch fast path (#3208)."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"issue": "23"}, run_id="47c5eb4b")
        result = evaluate_expression(
            "{{ context.run_id }} {{ inputs.issue }}", ctx
        )
        assert result == "47c5eb4b 23"

    def test_multi_expression_adjacent_no_separator(self):
        """Back-to-back expressions with no separator still interpolate (#3208)."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"a": "foo", "b": "bar"})
        result = evaluate_expression("{{ inputs.a }}{{ inputs.b }}", ctx)
        assert result == "foobar"

    def test_single_expression_with_literal_braces_preserves_type(self):
        """A lone expression whose string argument contains a literal ``{{`` or ``}}``
        must still take the typed fast path and return a bool, not a string
        (the fix for #3208 must not coerce it to ``\"True\"``)."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"text": "uses {{ jinja }} syntax"})
        assert evaluate_expression("{{ inputs.text | contains('{{') }}", ctx) is True

        ctx = StepContext(inputs={"text": "uses }} syntax"})
        assert evaluate_expression("{{ inputs.text | contains('}}') }}", ctx) is True

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

    def test_list_literal_preserves_quoted_commas(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        # commas inside a double-quoted element must not split it
        assert evaluate_expression('{{ ["a, b", "c"] }}', ctx) == ["a, b", "c"]
        assert evaluate_expression('{{ ["x, y, z"] }}', ctx) == ["x, y, z"]
        # single-quoted elements are handled the same way
        assert evaluate_expression("{{ ['a, b', 'c'] }}", ctx) == ["a, b", "c"]
        assert evaluate_expression("{{ ['p, q, r'] }}", ctx) == ["p, q, r"]
        # plain and empty lists still parse correctly
        assert evaluate_expression("{{ [1, 2, 3] }}", ctx) == [1, 2, 3]
        assert evaluate_expression("{{ [] }}", ctx) == []
        # nested lists (commas inside the inner brackets) stay intact
        assert evaluate_expression('{{ [["a", "b"], "c"] }}', ctx) == [["a", "b"], "c"]
        assert evaluate_expression("{{ [[1, 2], [3, 4]] }}", ctx) == [[1, 2], [3, 4]]

    def test_operator_splitting_is_quote_aware(self):
        from specify_cli.workflows.expressions import (
            evaluate_condition,
            evaluate_expression,
        )
        from specify_cli.workflows.base import StepContext

        # An 'and'/'or'/'in' keyword INSIDE a quoted operand must not be treated
        # as a boolean/membership operator: the comparison applies to the whole
        # string literal.
        ctx = StepContext(inputs={"mode": "read and write"})
        assert evaluate_expression("{{ inputs.mode == 'read and write' }}", ctx) is True
        assert evaluate_expression("{{ inputs.mode == 'read or write' }}", ctx) is False
        # ...also when the quoted literal is on the left of the operator.
        left_ctx = StepContext(inputs={"x": "approve or reject"})
        assert evaluate_expression("{{ 'approve or reject' == inputs.x }}", left_ctx) is True
        # membership against a literal that contains a keyword
        assert evaluate_expression("{{ 'cat' in 'cat and dog' }}", StepContext()) is True

        # Literal-vs-literal equality no longer mis-strips to a garbage string
        # (previously `'done' == 'failed'` short-circuited to the truthy string
        # "done' == 'failed").
        assert evaluate_condition("{{ 'done' == 'failed' }}", StepContext()) is False
        assert evaluate_condition("{{ 'done' == 'done' }}", StepContext()) is True

        # A single quoted literal that itself contains operator text is preserved.
        assert evaluate_expression("{{ 'a == b' }}", StepContext()) == "a == b"
        assert evaluate_expression("{{ 'x and y' }}", StepContext()) == "x and y"

        # Regression: ordinary (unquoted-keyword) parsing still works.
        plain = StepContext(inputs={"a": 1, "b": 2, "mode": "read"})
        assert evaluate_expression("{{ inputs.mode == 'read' }}", plain) is True
        assert evaluate_expression("{{ inputs.a == 1 and inputs.b == 2 }}", plain) is True
        assert evaluate_expression("{{ inputs.a == 9 or inputs.b == 2 }}", plain) is True
        assert evaluate_expression("{{ inputs.missing | default('a and b') }}", plain) == "a and b"

    def test_pipe_detection_is_quote_aware(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        # A literal '|' inside a quoted operand must not be treated as a filter
        # pipe: the comparison applies to the whole string.
        ctx = StepContext(inputs={"x": "a|b"})
        assert evaluate_expression("{{ inputs.x == 'a|b' }}", ctx) is True
        assert evaluate_expression("{{ inputs.x == 'a|b' }}", StepContext(inputs={"x": "z"})) is False
        # membership against a literal containing a pipe
        assert evaluate_expression("{{ 'a|b' in inputs.s }}", StepContext(inputs={"s": "x a|b y"})) is True
        # a single quoted literal containing pipes is preserved
        assert evaluate_expression("{{ 'a|b|c' }}", StepContext()) == "a|b|c"

        # Regression: real filters still work, including a pipe inside a filter arg.
        ctx2 = StepContext(inputs={"items": ["a", "b"], "s": "xabz"})
        assert evaluate_expression("{{ inputs.missing | default('y') }}", ctx2) == "y"
        assert evaluate_expression('{{ inputs.items | join("-") }}', ctx2) == "a-b"
        assert evaluate_expression("{{ inputs.s | contains('ab') }}", ctx2) is True
        assert evaluate_expression("{{ inputs.missing | default('a|b') }}", ctx2) == "a|b"

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

    def test_filter_from_json_parses_object(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            steps={"emit": {"output": {"stdout": '{"items": [1, 2, 3]}'}}}
        )
        result = evaluate_expression("{{ steps.emit.output.stdout | from_json }}", ctx)
        assert result == {"items": [1, 2, 3]}

    def test_filter_from_json_invalid_json_raises(self):
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(steps={"emit": {"output": {"stdout": "not json"}}})
        with pytest.raises(ValueError, match="from_json: invalid JSON"):
            evaluate_expression("{{ steps.emit.output.stdout | from_json }}", ctx)

    def test_filter_from_json_non_string_raises(self):
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(steps={"emit": {"output": {"exit_code": 0}}})
        with pytest.raises(ValueError, match="expected a JSON string"):
            evaluate_expression("{{ steps.emit.output.exit_code | from_json }}", ctx)

    def test_filter_from_json_rejects_malformed_forms(self):
        # `from_json` is strict: no arguments and no trailing tokens. Every
        # mis-wired form — parenthesized, accidental arg, or trailing
        # garbage — must raise rather than silently fall through to the
        # unknown-filter path and return the unparsed value.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(steps={"emit": {"output": {"stdout": '{"a": 1}'}}})
        bad_forms = (
            "from_json()",
            "from_json('x')",
            "from_json ()",
            "from_json ('x')",
            "from_json)",
            "from_json extra",
            "from_json 'x'",
        )
        for bad in bad_forms:
            with pytest.raises(ValueError, match="from_json: expected"):
                evaluate_expression(
                    "{{ steps.emit.output.stdout | " + bad + " }}", ctx
                )

    def test_filter_unknown_name_raises(self):
        # An unregistered filter name must fail loudly rather than silently
        # returning the unfiltered value (which hides a typo / unsupported
        # filter as a wrong result).
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"items": [1, 2, 3]})
        with pytest.raises(ValueError, match="unknown filter 'length'"):
            evaluate_expression("{{ inputs.items | length }}", ctx)

    def test_filter_unknown_name_with_args_raises(self):
        # The unknown-filter path must also catch the `name(arg)` form, which
        # otherwise falls through the recognized-args branch silently.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"text": "hello"})
        with pytest.raises(ValueError, match="unknown filter 'upper'"):
            evaluate_expression("{{ inputs.text | upper('x') }}", ctx)

    def test_registered_filters_unaffected(self):
        # Regression: all five registered filters keep working unchanged.
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            inputs={
                "tags": ["a", "b", "c"],
                "text": "hello world",
                "missing": "",
                "rows": [{"id": "a"}, {"id": "b"}],
            },
            steps={"emit": {"output": {"stdout": '{"n": 1}'}}},
        )
        assert (
            evaluate_expression("{{ inputs.missing | default('fb') }}", ctx) == "fb"
        )
        assert evaluate_expression("{{ inputs.tags | join(', ') }}", ctx) == "a, b, c"
        assert evaluate_expression("{{ inputs.rows | map('id') }}", ctx) == ["a", "b"]
        assert (
            evaluate_expression("{{ inputs.text | contains('world') }}", ctx) is True
        )
        assert evaluate_expression(
            "{{ steps.emit.output.stdout | from_json }}", ctx
        ) == {"n": 1}

    def test_registered_filter_unsupported_form_raises(self):
        # A *registered* filter used in an unsupported form (e.g. `| join` with
        # no argument) must fail loudly with a message that names it as a known
        # filter misused, not as an "unknown filter".
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"tags": ["a", "b", "c"]})
        with pytest.raises(
            ValueError, match="filter 'join' used in an unsupported form"
        ):
            evaluate_expression("{{ inputs.tags | join }}", ctx)
        with pytest.raises(
            ValueError, match="filter 'map' used in an unsupported form"
        ):
            evaluate_expression("{{ inputs.tags | map }}", ctx)

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

    def test_context_run_id_resolves(self):
        """``{{ context.run_id }}`` resolves to ``StepContext.run_id``.

        Locks the contract from issue #2590: workflow templates can
        reference the engine-assigned run id for telemetry, artifact
        metadata, or per-run scratch isolation.
        """
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(run_id="a1b2c3d4")
        assert evaluate_expression("{{ context.run_id }}", ctx) == "a1b2c3d4"

    def test_context_run_id_defaults_to_empty_when_unset(self):
        """``{{ context.run_id }}`` resolves to ``""`` when no run is
        active (dry-run, validation, ad-hoc evaluator usage) rather
        than raising — workflows referencing the variable never error
        outside a run context.
        """
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        # No run_id set on the context.
        ctx = StepContext()
        assert evaluate_expression("{{ context.run_id }}", ctx) == ""

    def test_context_run_id_string_interpolation(self):
        """Run id interpolates inside a larger template string — the
        common pattern for stamping shell commands and artifact paths
        with the run id.
        """
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(run_id="deadbeef")
        result = evaluate_expression("RUN_ID={{ context.run_id }}", ctx)
        assert result == "RUN_ID=deadbeef"


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
        expected_exec = "copilot.cmd" if os.name == "nt" else "copilot"
        assert args[0] == expected_exec
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
        from specify_cli.integrations.kilocode import KilocodeIntegration
        impl = KilocodeIntegration()
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

    def test_rovodev_exec_args(self):
        from specify_cli.integrations.rovodev import RovodevIntegration

        impl = RovodevIntegration()
        args = impl.build_exec_args("/speckit.plan add OAuth")
        assert args[0:3] == ["acli", "rovodev", "run"]
        assert args[3] == "/speckit.plan add OAuth"
        assert "--output-schema" in args


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

    def test_try_dispatch_resolves_rovodev_via_acli(self, tmp_path):
        """When acli is installed, rovodev dispatch succeeds via acli."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(
            default_integration="rovodev",
            project_root=str(tmp_path),
        )
        config = {
            "id": "test",
            "command": "speckit.plan",
            "input": {"args": "add OAuth"},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("specify_cli.workflows.steps.command.shutil.which",
                    lambda name: "/usr/bin/acli" if name == "acli" else None), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

    def test_validate_missing_command(self):
        from specify_cli.workflows.steps.command import CommandStep

        step = CommandStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'command'" in e for e in errors)

    def test_step_override_integration(self):
        from unittest.mock import patch
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
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_step_override_model(self):
        from unittest.mock import patch
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
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_options_merge(self):
        from unittest.mock import patch
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
        with patch("specify_cli.workflows.steps.command.shutil.which", return_value=None):
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
             patch("specify_cli.integrations.base.shutil.which", return_value="/usr/local/bin/claude"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0
        # Verify the CLI was called with the resolved path (via shutil.which,
        # which honors PATHEXT for ``.cmd``/``.bat`` shims on Windows), then
        # ``-p`` and the skill invocation.
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "/usr/local/bin/claude"
        assert call_args[0][0][1] == "-p"
        # Claude is a SkillsIntegration so uses /speckit-specify
        assert "/speckit-specify login" in call_args[0][0][2]

    def test_dispatch_uses_executable_override_for_fallback_preflight(self, tmp_path, monkeypatch):
        """Command preflight falls back to build_exec_args() argv[0]."""
        from unittest.mock import MagicMock, patch
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXECUTABLE", "/opt/claude")
        seen_which: list[str] = []

        def fake_which(name: str) -> str | None:
            seen_which.append(name)
            return name if name == "/opt/claude" else None

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

        with patch("specify_cli.workflows.steps.command.shutil.which", side_effect=fake_which), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert seen_which[:2] == ["claude", "/opt/claude"]
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "/opt/claude"
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
             patch("specify_cli.integrations.base.shutil.which", return_value="/usr/local/bin/claude"), \
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
        from unittest.mock import patch
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
        with patch("specify_cli.workflows.steps.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_execute_with_model(self):
        from unittest.mock import patch
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
        with patch("specify_cli.workflows.steps.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_try_dispatch_resolves_rovodev_via_acli(self, tmp_path):
        """When acli is installed, rovodev prompt dispatch succeeds via acli."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        ctx = StepContext(
            default_integration="rovodev",
            project_root=str(tmp_path),
        )
        config = {
            "id": "test",
            "type": "prompt",
            "prompt": "Explain this code",
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("specify_cli.workflows.steps.prompt.shutil.which",
                    lambda name: "/usr/bin/acli" if name == "acli" else None), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

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

    def test_dispatch_uses_executable_override_for_fallback_preflight(self, tmp_path, monkeypatch):
        """Prompt preflight falls back to build_exec_args() argv[0]."""
        from unittest.mock import MagicMock, patch
        from specify_cli.workflows.steps.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXECUTABLE", "/opt/claude")
        seen_which: list[str] = []

        def fake_which(name: str) -> str | None:
            seen_which.append(name)
            return name if name == "/opt/claude" else None

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

        with patch("specify_cli.workflows.steps.prompt.shutil.which", side_effect=fake_which), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert seen_which[:2] == ["claude", "/opt/claude"]
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "/opt/claude"
        assert call_args[0][0][2] == "Explain this code"

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

    @staticmethod
    def _python_run(tmp_path, body):
        """A portable shell ``run`` that executes ``body`` with the current
        interpreter, avoiding non-portable shell quoting (e.g. Windows
        ``cmd.exe`` keeping single quotes) in the output_format tests."""
        import sys

        script = tmp_path / "emit.py"
        script.write_text(body, encoding="utf-8")
        return f'"{sys.executable}" "{script}"'

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


    def test_output_format_json_exposes_data(self, tmp_path):
        from specify_cli.workflows.steps.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext(project_root=str(tmp_path))
        config = {
            "id": "emit",
            "run": self._python_run(
                tmp_path, 'import json; print(json.dumps({"items": [1, 2]}))\n'
            ),
            "output_format": "json",
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["data"] == {"items": [1, 2]}
        assert result.output["exit_code"] == 0  # raw keys still present

    def test_output_format_json_invalid_stdout_fails(self, tmp_path):
        from specify_cli.workflows.steps.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext(project_root=str(tmp_path))
        config = {
            "id": "emit",
            "run": self._python_run(tmp_path, "print('not-json')\n"),
            "output_format": "json",
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert "output_format: json" in (result.error or "")

    def test_no_output_format_keeps_raw_output_only(self, tmp_path):
        from specify_cli.workflows.steps.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext(project_root=str(tmp_path))
        config = {
            "id": "emit",
            "run": self._python_run(
                tmp_path, 'import json; print(json.dumps({"items": []}))\n'
            ),
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert "data" not in result.output

    def test_validate_rejects_unknown_output_format(self):
        from specify_cli.workflows.steps.shell import ShellStep

        step = ShellStep()
        errors = step.validate({"id": "emit", "run": "exit 0", "output_format": "yaml"})
        assert any("'output_format' must be 'json'" in e for e in errors)

class _StubStdin:
    """Stdin stub exposing only a fixed ``isatty`` result.

    A real ``TextIOWrapper.isatty`` is not assignable under some runners
    (e.g. pytest with capture disabled), so the gate tests force the value
    through this stub to stay deterministic regardless of how the suite is
    run.
    """

    def __init__(self, tty: bool):
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


class _FakeSys:
    """Stand-in for the gate module's ``sys`` with a fixed-``isatty`` stdin.

    Every other attribute delegates to the real ``sys``. Rebinding the gate
    module's ``sys`` name (rather than mutating the process-wide
    ``sys.stdin``) keeps the patch local to the gate module and leaves the
    real stdin untouched.
    """

    def __init__(self, tty: bool):
        self.stdin = _StubStdin(tty)

    def __getattr__(self, name):
        return getattr(sys, name)


def _force_gate_stdin(monkeypatch, *, tty: bool):
    from specify_cli.workflows.steps import gate as gate_module

    monkeypatch.setattr(gate_module, "sys", _FakeSys(tty=tty))


class TestInitStep:
    """Test the init step type."""

    def test_builds_here_argv_and_bootstraps(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        config = {"id": "bootstrap", "here": True, "script": "sh"}
        result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["exit_code"] == 0
        argv = result.output["argv"]
        assert argv[0] == "init"
        assert "--here" in argv
        assert "--integration" in argv and "copilot" in argv
        assert "--ignore-agent-tools" in argv
        assert (tmp_path / ".specify").is_dir()

    def test_default_integration_falls_back_to_workflow_default(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {"id": "bootstrap", "here": True, "script": "sh"}, ctx
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["integration"] == "copilot"

    def test_project_name_creates_subdirectory(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {
                "id": "bootstrap",
                "project": "demo",
                "script": "sh",
            },
            ctx,
        )
        assert result.status == StepStatus.COMPLETED
        assert (tmp_path / "demo" / ".specify").is_dir()

    def test_invalid_integration_fails(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        ctx = StepContext(project_root=str(tmp_path))
        result = step.execute(
            {
                "id": "bootstrap",
                "here": True,
                "integration": "no-such-agent",
                "script": "sh",
            },
            ctx,
        )
        assert result.status == StepStatus.FAILED
        assert result.output["exit_code"] != 0
        assert result.error is not None

    def test_non_empty_current_dir_without_force_fails_fast(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        (tmp_path / "existing.txt").write_text("data")

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {"id": "bootstrap", "here": True, "script": "sh"},
            ctx,
        )
        assert result.status == StepStatus.FAILED
        assert "force: true" in (result.error or "")
        assert not (tmp_path / ".specify").exists()

    def test_engine_owned_dirs_do_not_trigger_non_empty_check(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        # Simulate the engine creating its run-state directory before steps run
        (tmp_path / ".specify" / "workflows" / "runs" / "abc123").mkdir(
            parents=True
        )

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {"id": "bootstrap", "here": True, "script": "sh"},
            ctx,
        )
        assert result.status == StepStatus.COMPLETED
        # Verify --force was implicitly added
        assert "--force" in result.output["argv"]

    def test_default_integration_when_none_provided(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        # No default_integration on context either
        ctx = StepContext(project_root=str(tmp_path))
        result = step.execute(
            {"id": "bootstrap", "here": True, "script": "sh"},
            ctx,
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["integration"] == "copilot"

    def test_integration_options_passed_through(self, tmp_path):
        from specify_cli.workflows.steps.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {
                "id": "bootstrap",
                "here": True,
                "script": "sh",
                "integration": "copilot",
                "integration_options": "--skills",
            },
            ctx,
        )
        assert result.status == StepStatus.COMPLETED
        assert "--integration-options" in result.output["argv"]
        assert "--skills" in result.output["argv"]
        assert result.output["integration_options"] == "--skills"

    def test_validate_rejects_bad_script(self):
        from specify_cli.workflows.steps.init import InitStep

        step = InitStep()
        errors = step.validate({"id": "bootstrap", "script": "bogus"})
        assert any("'script' must be 'sh' or 'ps'" in e for e in errors)

    def test_validate_accepts_valid(self):
        from specify_cli.workflows.steps.init import InitStep

        step = InitStep()
        assert step.validate({"id": "bootstrap", "script": "sh"}) == []


class TestGateStep:
    """Test the gate step type."""

    @pytest.fixture(autouse=True)
    def _non_tty_stdin_by_default(self, monkeypatch):
        # Default every gate test to a non-TTY stdin so none can drop into
        # the interactive prompt and block on input() when the suite runs
        # with a real TTY. Interactive tests opt back in with
        # _force_gate_stdin(monkeypatch, tty=True).
        _force_gate_stdin(monkeypatch, tty=False)

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

    def test_validate_non_string_options_does_not_raise(self):
        """Non-string options with on_reject=abort/retry must be REPORTED as an
        error, not crash: the reject-choice check calls o.lower() on each option,
        which previously raised AttributeError on a non-string option and broke
        validate_workflow's 'return errors, never raise' contract."""
        from specify_cli.workflows.steps.gate import GateStep

        step = GateStep()
        # on_reject defaults to "abort", which triggers the option-text check.
        errors = step.validate({"id": "test", "message": "Review", "options": [123]})
        assert any("must be strings" in e for e in errors)
        # also with an explicit retry on_reject
        errors = step.validate(
            {"id": "test", "message": "Review", "options": [True], "on_reject": "retry"}
        )
        assert any("must be strings" in e for e in errors)

    def test_interactive_prompt_renders_show_file(self, tmp_path, monkeypatch, capsys):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        review = tmp_path / "spec.md"
        review.write_text("LINE-ONE\nLINE-TWO\n", encoding="utf-8")

        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

        step = GateStep()
        config = {
            "id": "review",
            "message": "Review the spec.",
            "show_file": str(review),
            "options": ["approve", "reject"],
        }
        result = step.execute(config, StepContext())
        out = capsys.readouterr().out

        assert "LINE-ONE" in out and "LINE-TWO" in out
        assert str(review) in out
        assert result.status == StepStatus.COMPLETED
        assert result.output["choice"] == "approve"

    def test_interactive_prompt_missing_show_file_does_not_crash(
        self, tmp_path, monkeypatch, capsys
    ):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        missing = tmp_path / "does-not-exist.md"

        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

        step = GateStep()
        config = {
            "id": "review",
            "message": "Review.",
            "show_file": str(missing),
            "options": ["approve", "reject"],
        }
        result = step.execute(config, StepContext())
        out = capsys.readouterr().out

        assert "could not read file" in out
        assert result.status == StepStatus.COMPLETED

    def test_non_interactive_show_file_still_pauses_without_reading(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        review = tmp_path / "spec.md"
        review.write_text("CONTENT\n", encoding="utf-8")

        # stdin defaults to non-TTY via the autouse fixture.
        # The non-interactive path must not read the file; hard-fail if it does.
        monkeypatch.setattr(
            GateStep,
            "_read_show_file",
            staticmethod(
                lambda _p: (_ for _ in ()).throw(
                    AssertionError("show_file read on the non-interactive path")
                )
            ),
        )

        step = GateStep()
        config = {
            "id": "review",
            "message": "Review.",
            "show_file": str(review),
            "options": ["approve", "reject"],
        }
        result = step.execute(config, StepContext())
        assert result.status == StepStatus.PAUSED
        assert result.output["show_file"] == str(review)

    def test_read_show_file_empty(self, tmp_path):
        from specify_cli.workflows.steps.gate import GateStep

        empty = tmp_path / "empty.md"
        empty.write_text("", encoding="utf-8")
        assert GateStep._read_show_file(str(empty)) == ["(file is empty)"]

    def test_read_show_file_truncates_large_file(self, tmp_path):
        from specify_cli.workflows.steps.gate import GateStep

        big = tmp_path / "big.md"
        big.write_text(
            "\n".join(f"line{i}" for i in range(GateStep.MAX_SHOW_FILE_LINES + 50)),
            encoding="utf-8",
        )
        rendered = GateStep._read_show_file(str(big))
        # MAX_SHOW_FILE_LINES content lines + one truncation notice line.
        assert len(rendered) == GateStep.MAX_SHOW_FILE_LINES + 1
        assert "truncated" in rendered[-1]

    def test_read_show_file_invalid_path_does_not_raise(self):
        from specify_cli.workflows.steps.gate import GateStep

        # An embedded NUL byte makes the OS reject the path with ValueError
        # before any I/O; it must degrade to a notice, not crash the prompt.
        rendered = GateStep._read_show_file("bad\x00path.md")
        assert len(rendered) == 1
        assert rendered[0].startswith("(could not read file:")

    def test_read_show_file_strips_control_chars(self, tmp_path):
        from specify_cli.workflows.steps.gate import GateStep

        # A file with ANSI/control bytes must not inject escapes into the
        # terminal; ESC and other C0 controls are stripped, tab is kept.
        f = tmp_path / "ansi.md"
        f.write_text("a\x1b[2Jb\tc\x07d\n", encoding="utf-8")
        rendered = GateStep._read_show_file(str(f))
        assert rendered == ["a[2Jb\tcd"]
        assert "\x1b" not in rendered[0] and "\x07" not in rendered[0]

    def test_compose_prompt_sanitizes_show_file_path(self):
        from specify_cli.workflows.steps.gate import GateStep

        # The displayed path header (and the read-error notice it produces)
        # must not carry escapes even when the path string itself contains
        # control characters — ESC, LF, and C1 CSI (\x9b); the file is still
        # opened with the raw value.
        out = GateStep._compose_prompt("Review.", "ev\x1bil\x9b[2J\npath.md")
        assert "\x1b" not in out and "\x9b" not in out
        assert "evil[2Jpath.md:" in out

    def test_interactive_non_string_message_renders(self, monkeypatch, capsys):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        # A YAML numeric literal reaches the prompt as a non-string; it must
        # render rather than crash on the multi-line split.
        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

        step = GateStep()
        config = {"id": "review", "message": 123, "options": ["approve", "reject"]}
        result = step.execute(config, StepContext())
        out = capsys.readouterr().out
        assert "123" in out
        assert result.status == StepStatus.COMPLETED

    def test_templated_show_file_resolving_to_non_string_is_coerced(self):
        from specify_cli.workflows.steps.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        # A single-expression template can resolve to a non-string (e.g. a
        # number from a prior step); it must be coerced to str, not skipped.
        # stdin defaults to non-TTY via the autouse fixture, so the path
        # stays non-interactive (-> PAUSED) and cannot block on input.
        step = GateStep()
        ctx = StepContext(steps={"prev": {"output": {"ref": 123}}})
        config = {
            "id": "review",
            "message": "Review.",
            "show_file": "{{ steps.prev.output.ref }}",
            "options": ["approve", "reject"],
        }
        result = step.execute(config, ctx)  # non-interactive -> PAUSED
        assert result.status == StepStatus.PAUSED
        assert result.output["show_file"] == "123"


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
        # bool is an int subclass; `max_iterations: true` must be rejected, not
        # silently treated as a single iteration.
        bool_errors = step.validate(
            {"id": "test", "condition": "{{ true }}", "max_iterations": True, "steps": []}
        )
        assert any("must be an integer >= 1" in e for e in bool_errors)


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

    def test_validate_rejects_bool_max_iterations(self):
        from specify_cli.workflows.steps.do_while import DoWhileStep

        step = DoWhileStep()
        # bool is an int subclass; `max_iterations: true` must be rejected.
        errors = step.validate(
            {"id": "test", "condition": "{{ true }}", "max_iterations": True, "steps": []}
        )
        assert any("must be an integer >= 1" in e for e in errors)
        # a real positive integer is fully valid (no errors at all).
        ok = step.validate(
            {"id": "test", "condition": "{{ true }}", "max_iterations": 3, "steps": []}
        )
        assert ok == [], ok

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

    def test_execute_non_list_items_fails_loudly(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanOutStep()
        ctx = StepContext()
        config = {
            "id": "parallel",
            "items": "{{ undefined_var }}",
            "step": {"id": "impl", "command": "speckit.implement"},
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert "'items' must resolve to a list" in (result.error or "")
        assert result.output["item_count"] == 0

    def test_execute_empty_list_items_is_valid(self):
        from specify_cli.workflows.steps.fan_out import FanOutStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanOutStep()
        ctx = StepContext(steps={"tasks": {"output": {"task_list": []}}})
        config = {
            "id": "parallel",
            "items": "{{ steps.tasks.output.task_list }}",
            "step": {"id": "impl", "command": "speckit.implement"},
        }
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["item_count"] == 0

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


class TestFanOutConcurrency:
    """Fan-out honors max_concurrency (WorkflowEngine._run_fan_out)."""

    @staticmethod
    def _build(tmp_path, on_item=None):
        """Wire an engine + run state to a probe step that echoes context.item.

        Per-item output is ``{"seen": <item>}`` so order and per-thread item
        isolation are checkable. ``on_item(item)`` may run a side effect and
        optionally return a StepStatus to override COMPLETED (or raise).
        """
        from specify_cli.workflows.base import (
            RunStatus,
            StepBase,
            StepContext,
            StepResult,
            StepStatus,
        )
        from specify_cli.workflows.engine import RunState, WorkflowEngine

        class _ProbeStep(StepBase):
            type_key = "probe"

            def execute(self, config, context):
                status = StepStatus.COMPLETED
                if on_item is not None:
                    override = on_item(context.item)
                    if override is not None:
                        status = override
                return StepResult(status=status, output={"seen": context.item})

        engine = WorkflowEngine(project_root=tmp_path)
        context = StepContext()
        state = RunState(run_id="r", workflow_id="w", project_root=tmp_path)
        state.status = RunStatus.RUNNING
        template = {"id": "impl", "type": "probe"}
        return engine, context, state, {"probe": _ProbeStep()}, template

    def _run(self, tmp_path, items, max_concurrency, on_item=None):
        engine, context, state, registry, template = self._build(tmp_path, on_item)
        results = engine._run_fan_out(
            items, template, "fan", context, state, registry, max_concurrency
        )
        return results, state

    def test_sequential_default_preserves_order(self, tmp_path):
        results, _ = self._run(tmp_path, list(range(5)), 1)
        assert results == [{"seen": i} for i in range(5)]

    def test_concurrent_runs_all_items_in_item_order(self, tmp_path):
        results, _ = self._run(tmp_path, list(range(10)), 4)
        assert results == [{"seen": i} for i in range(10)]

    def test_sequential_and_concurrent_agree(self, tmp_path):
        items = [{"n": i} for i in range(8)]
        seq, _ = self._run(tmp_path, items, 1)
        con, _ = self._run(tmp_path, items, 4)
        assert seq == con == [{"seen": {"n": i}} for i in range(8)]

    def test_shuffled_completion_preserves_item_order(self, tmp_path):
        # Determinism keystone: completion order is forced to the exact REVERSE of
        # item order by an event chain (no sleeps) — item i blocks until item i+1
        # has finished, so item 0 completes LAST — yet results must still be in
        # item order. K == len(items) so all workers are in flight together.
        import threading

        n = 4
        done = [threading.Event() for _ in range(n)]
        completion: list[int] = []
        clock = threading.Lock()

        def on_item(item):
            if item + 1 < n:
                assert done[item + 1].wait(2.0), f"item {item + 1} never finished"
            with clock:
                completion.append(item)
            done[item].set()
            return None

        results, _ = self._run(tmp_path, list(range(n)), n, on_item)
        assert results == [{"seen": i} for i in range(n)]
        assert completion == list(reversed(range(n)))

    def test_concurrency_is_real(self, tmp_path):
        import threading

        # Deterministic proof of real parallelism (no wall-clock threshold to
        # tune or flake): every item must reach the barrier before any may pass.
        # Sequential execution would block the first item forever — the barrier
        # times out, raises BrokenBarrierError, and fails the test.
        n = 4
        barrier = threading.Barrier(n, timeout=5)

        def on_item(item):
            barrier.wait()
            return None

        results, _ = self._run(tmp_path, list(range(n)), n, on_item)
        assert results == [{"seen": i} for i in range(n)]

    @pytest.mark.parametrize("bad", [0, -1, None, "abc", 1.0])
    def test_invalid_max_concurrency_coerces_to_sequential(self, tmp_path, bad):
        results, _ = self._run(tmp_path, list(range(4)), bad)
        assert results == [{"seen": i} for i in range(4)]

    def test_string_max_concurrency_is_honored(self, tmp_path):
        results, _ = self._run(tmp_path, list(range(4)), "2")
        assert results == [{"seen": i} for i in range(4)]

    def test_context_item_isolation_across_threads(self, tmp_path):
        items = [{"id": f"x{i}"} for i in range(6)]
        results, _ = self._run(tmp_path, items, 6)
        assert [r["seen"]["id"] for r in results] == [f"x{i}" for i in range(6)]

    def test_empty_items(self, tmp_path):
        results, _ = self._run(tmp_path, [], 4)
        assert results == []

    def test_concurrent_halt_status_not_clobbered_by_later_item(self, tmp_path):
        # Item 1 PAUSES (first halting item in order); item 3 FAILS while in
        # flight. The final run status must be the halting item's (PAUSED), never
        # a later item's (FAILED) that raced after it — matching sequential.
        from specify_cli.workflows.base import RunStatus, StepStatus

        def on_item(item):
            if item == 1:
                return StepStatus.PAUSED
            if item == 3:
                return StepStatus.FAILED
            return None

        results, state = self._run(tmp_path, list(range(4)), 4, on_item)
        assert results == [{"seen": 0}, {"seen": 1}]
        assert state.status == RunStatus.PAUSED

    def test_halt_on_failure_sequential_returns_prefix(self, tmp_path):
        from specify_cli.workflows.base import RunStatus, StepStatus

        def on_item(item):
            return StepStatus.FAILED if item == 2 else None

        results, state = self._run(tmp_path, list(range(5)), 1, on_item)
        assert len(results) == 3  # items 0,1,2 ran; 3,4 never dispatched
        assert results[2] == {"seen": 2}
        assert state.status == RunStatus.FAILED

    def test_halt_on_failure_concurrent_includes_halting_item(self, tmp_path):
        # The concurrent prefix must match the sequential one: items up to and
        # INCLUDING the failing item (2), never a short prefix that drops it just
        # because a later in-flight item flipped the shared run status first.
        from specify_cli.workflows.base import RunStatus, StepStatus

        def on_item(item):
            return StepStatus.FAILED if item == 2 else None

        results, state = self._run(tmp_path, list(range(6)), 4, on_item)
        assert results == [{"seen": 0}, {"seen": 1}, {"seen": 2}]
        assert state.status == RunStatus.FAILED

    def test_continue_on_error_item_does_not_halt_concurrent(self, tmp_path):
        # A failing item whose template sets continue_on_error must NOT truncate
        # the fan-out: every item still runs and is returned in order.
        from specify_cli.workflows.base import StepStatus

        def on_item(item):
            return StepStatus.FAILED if item == 2 else None

        engine, context, state, registry, template = self._build(tmp_path, on_item)
        template["continue_on_error"] = True
        results = engine._run_fan_out(
            list(range(5)), template, "fan", context, state, registry, 4
        )
        assert results == [{"seen": i} for i in range(5)]

    def test_unknown_template_type_halts_concurrent_like_sequential(self, tmp_path):
        # A template whose type isn't registered fails fast and records no result;
        # the concurrent path must still attribute the halt to the first item and
        # return the same prefix as sequential — never run on as if completed.
        from specify_cli.workflows.base import RunStatus, StepContext
        from specify_cli.workflows.engine import RunState, WorkflowEngine

        def fresh():
            state = RunState(run_id="r", workflow_id="w", project_root=tmp_path)
            state.status = RunStatus.RUNNING
            return WorkflowEngine(project_root=tmp_path), StepContext(), state

        template = {"id": "impl", "type": "does-not-exist"}
        e1, c1, s1 = fresh()
        seq = e1._run_fan_out(list(range(5)), template, "fan", c1, s1, {}, 1)
        e2, c2, s2 = fresh()
        con = e2._run_fan_out(list(range(5)), template, "fan", c2, s2, {}, 4)
        assert seq == con == [{}]  # halted at the first item; rest never returned
        assert s1.status == s2.status == RunStatus.FAILED

    def test_first_exception_cancels_and_reraises(self, tmp_path):
        def on_item(item):
            if item == 0:
                raise ValueError("boom")
            return None

        with pytest.raises(ValueError, match="boom"):
            self._run(tmp_path, list(range(4)), 2, on_item)


class TestFanInWaitForValidation:
    """fan-in wait_for must reference a declared step (no silent empty join)."""

    @staticmethod
    def _errors(yaml_text):
        from specify_cli.workflows.engine import (
            WorkflowDefinition,
            validate_workflow,
        )

        return validate_workflow(WorkflowDefinition.from_string(yaml_text))

    def test_unknown_wait_for_id_is_rejected(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: collect
    type: fan-in
    wait_for: [ghost]
""")
        assert any(
            "unknown or not-yet-declared step id 'ghost'" in e for e in errors
        )

    def test_wait_for_declared_earlier_step_passes(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: produce
    type: command
    command: speckit.implement
  - id: collect
    type: fan-in
    wait_for: [produce]
""")
        assert not any("wait_for" in e for e in errors)

    def test_wait_for_conditionally_declared_step_passes(self):
        # A step declared inside an if-branch may be skipped at runtime, but it is
        # still "declared", so referencing it must validate — a legitimately-empty
        # runtime join stays valid.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: maybe
    type: if
    condition: "{{ inputs.flag }}"
    then:
      - id: branch_task
        type: command
        command: speckit.implement
  - id: collect
    type: fan-in
    wait_for: [branch_task]
""")
        assert not any("wait_for" in e for e in errors)

    def test_forward_reference_is_rejected(self):
        # wait_for points at a step declared AFTER the fan-in; its results cannot
        # exist when the fan-in runs, so it is flagged.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: collect
    type: fan-in
    wait_for: [later]
  - id: later
    type: command
    command: speckit.implement
""")
        assert any(
            "unknown or not-yet-declared step id 'later'" in e for e in errors
        )

    def test_self_reference_is_rejected(self):
        # A fan-in's own id is in scope by the time it is validated, so a
        # self-reference slips past the membership check while still producing
        # an empty join at runtime.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: collect
    type: fan-in
    wait_for: [collect]
""")
        assert any(
            "references itself" in e and "collect" in e for e in errors
        )

    def test_non_string_wait_for_entry_is_rejected(self):
        # A non-string entry (e.g. YAML `wait_for: [123]`) can never match a
        # real step id, so it must be flagged rather than silently ignored.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: collect
    type: fan-in
    wait_for: [123]
""")
        assert any(
            "must be step-id strings" in e and "int" in e for e in errors
        )


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

    def test_requires_with_recognized_keys_is_valid(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires:
  speckit_version: ">=0.7.2"
  integrations:
    any: ["claude", "gemini"]
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert errors == []

    def test_requires_must_be_mapping(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires: "claude"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("'requires' must be a mapping" in e for e in errors)

    def test_requires_unknown_key_is_rejected(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires:
  speckit_version: ">=0.7.2"
  typo_key: true
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("typo_key" in e and "requires" in e for e in errors)

    def test_requires_permissions_is_rejected_as_not_enforced(self):
        """A `requires.permissions` block looks like a runtime capability gate
        but no such gate exists — shell steps always run with the user's
        privileges. Reject it explicitly so authors are not misled into
        believing the declaration sandboxes execution.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires:
  permissions:
    shell: true
steps:
  - id: run
    type: shell
    run: "echo hi"
""")
        errors = validate_workflow(definition)
        # Assert on specific markers from the intended message (the offending
        # key and the `gate` remediation) so the test fails if the validation
        # path or wording drifts, rather than passing on any error that merely
        # happens to contain "permissions" and "not".
        assert any("requires.permissions" in e and "gate" in e for e in errors)

    def test_requires_empty_sequence_is_rejected_as_non_mapping(self):
        """A non-mapping ``requires`` (e.g. an empty list) is an authoring
        error. Mirroring ``inputs``, validation checks ``isinstance(..., dict)``
        so ``requires: []`` surfaces instead of silently passing.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires: []
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("'requires' must be a mapping" in e for e in errors)

    def test_requires_yaml_null_is_rejected_as_non_mapping(self):
        """A bare ``requires:`` parses as YAML null. Like ``inputs``, a present
        block must be a mapping, so YAML null is rejected as an authoring error
        rather than being silently treated as an omitted block. (A truly
        omitted ``requires`` defaults to ``{}`` and stays valid.)
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
requires:
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("'requires' must be a mapping" in e for e in errors)

    def test_requires_omitted_is_valid(self):
        """A workflow with no ``requires`` block at all defaults to ``{}`` and
        must validate cleanly — only a present-but-non-mapping value is an
        error (guards against over-correcting YAML-null rejection into also
        flagging the omitted case).
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert not any("requires" in e for e in errors)


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

    def test_integration_auto_default_uses_project_integration(self, project_dir):
        """`integration: auto` should resolve to .specify/integration.json's integration."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text(
            json.dumps({"integration": "opencode", "version": "0.7.4"}),
            encoding="utf-8",
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-default"
  name: "Auto Default"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "opencode"

    def test_integration_auto_default_falls_back_when_no_integration_json(self, project_dir):
        """`integration: auto` should keep the literal "auto" when project state is missing.

        The engine itself must not invent an integration when
        ``.specify/integration.json`` is absent; any later validation or
        command resolution will handle an unresolved ``"auto"`` value.
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-fallback"
  name: "Auto Fallback"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "auto"

    def test_integration_explicit_input_overrides_auto(self, project_dir):
        """An explicit --input integration=X must win over `auto` even when integration.json exists."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text(
            json.dumps({"integration": "opencode"}),
            encoding="utf-8",
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "explicit-wins"
  name: "Explicit Wins"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {"integration": "claude"})
        assert resolved["integration"] == "claude"

    def test_integration_explicit_auto_resolves_like_default(self, project_dir):
        """Passing ``integration=auto`` explicitly must resolve the sentinel,
        not pass it through as a literal — the workflow prompt advertises
        ``auto`` as a valid value, so the dispatch path must never see it.
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text(
            json.dumps({"integration": "opencode"}),
            encoding="utf-8",
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "explicit-auto"
  name: "Explicit Auto"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {"integration": "auto"})
        assert resolved["integration"] == "opencode"

    def test_integration_auto_ignores_malformed_integration_json(self, project_dir):
        """A malformed integration.json must not crash — fall back to the literal default."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text("{not json", encoding="utf-8")

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-malformed"
  name: "Auto Malformed"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "auto"

    def test_integration_auto_ignores_non_utf8_integration_json(self, project_dir):
        """A non-UTF8 integration.json must not crash — fall back to the literal default."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        # 0xFF is invalid as the leading byte of a UTF-8 sequence, so
        # ``Path.read_text(encoding="utf-8")`` raises UnicodeDecodeError.
        (specify_dir / "integration.json").write_bytes(b"\xff\xfe\x00\x00")

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-non-utf8"
  name: "Auto Non UTF-8"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "auto"

    def test_integration_auto_resolves_modern_normalized_state(self, project_dir):
        """`integration: auto` must resolve modern state files that record
        ``default_integration`` / ``installed_integrations`` and omit the
        legacy ``integration`` field."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text(
            json.dumps(
                {
                    "version": "0.8.3",
                    "integration_state_schema": 1,
                    "default_integration": "claude",
                    "installed_integrations": ["claude", "copilot"],
                    "integration_settings": {},
                }
            ),
            encoding="utf-8",
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-modern"
  name: "Auto Modern"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "claude"

    def test_integration_auto_rejects_future_state_schema(self, project_dir):
        """`integration: auto` must not silently use a state file written by a newer
        CLI (``integration_state_schema`` greater than the current supported value);
        the resolver falls back to the literal default rather than guessing."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.integration_state import INTEGRATION_STATE_SCHEMA

        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "integration.json").write_text(
            json.dumps(
                {
                    "version": "99.0.0",
                    "integration_state_schema": INTEGRATION_STATE_SCHEMA + 1,
                    "default_integration": "claude",
                    "installed_integrations": ["claude"],
                    "integration_settings": {},
                }
            ),
            encoding="utf-8",
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-future-schema"
  name: "Auto Future Schema"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["integration"] == "auto"

    def test_default_value_is_validated_against_enum(self, project_dir):
        """Defaults must run through the same coercion/enum check as provided inputs."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "default-enum"
  name: "Default Enum"
  version: "1.0.0"
inputs:
  scope:
    type: string
    default: "not-in-enum"
    enum: ["full", "backend-only", "frontend-only"]
""")
        engine = WorkflowEngine(project_dir)
        with pytest.raises(ValueError, match="not in allowed values"):
            engine._resolve_inputs(definition, {})

    def test_default_value_is_coerced_to_declared_type(self, project_dir):
        """A numeric default declared as a string should still be coerced like a provided input."""
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "default-coerce"
  name: "Default Coerce"
  version: "1.0.0"
inputs:
  retries:
    type: number
    default: "3"
""")
        engine = WorkflowEngine(project_dir)
        resolved = engine._resolve_inputs(definition, {})
        assert resolved["retries"] == 3
        assert isinstance(resolved["retries"], int)

    def test_validate_workflow_rejects_invalid_default(self):
        """Authoring-time validation should reject defaults that violate enum."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "bad-default"
  name: "Bad Default"
  version: "1.0.0"
inputs:
  scope:
    type: string
    default: "not-in-enum"
    enum: ["full", "backend-only", "frontend-only"]
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid default" in e for e in errors), errors

    def test_validate_workflow_exempts_integration_auto_sentinel(self):
        """``integration: auto`` is a runtime-resolved sentinel and must not fail validation."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-ok"
  name: "Auto OK"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
    enum: ["copilot", "claude", "gemini"]
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert not any("invalid default" in e for e in errors), errors

    def test_validate_workflow_still_checks_type_for_auto_sentinel(self):
        """The ``auto`` exemption only skips enum-membership; declared type is still enforced."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-bad-type"
  name: "Auto Bad Type"
  version: "1.0.0"
inputs:
  integration:
    type: number
    default: "auto"
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid default" in e for e in errors), errors

    def test_validate_workflow_rejects_bool_default_for_number_type(self):
        """``type: number`` paired with a bool default must fail — bool is a
        subclass of int so ``float(True)`` would otherwise silently coerce
        ``true`` to ``1``.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "bool-as-number"
  name: "Bool As Number"
  version: "1.0.0"
inputs:
  count:
    type: number
    default: true
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid default" in e for e in errors), errors

    def test_coerce_number_input_rejects_infinity_cleanly(self):
        """An infinite float must surface as a clean ValueError (like NaN), not
        let ``int(inf)``'s OverflowError escape: ``int()`` of an infinity raises
        OverflowError, which is not ValueError/TypeError.
        """
        from specify_cli.workflows.engine import WorkflowEngine

        for value in (float("inf"), float("-inf"), "inf", "Infinity", "-inf"):
            with pytest.raises(ValueError, match="expected a number"):
                WorkflowEngine._coerce_input("count", value, {"type": "number"})
        # Finite values still coerce (whole floats normalize to int).
        assert WorkflowEngine._coerce_input("count", 5.0, {"type": "number"}) == 5
        assert WorkflowEngine._coerce_input("count", 3.5, {"type": "number"}) == 3.5

    def test_validate_workflow_rejects_infinite_default_for_number_type(self):
        """``type: number`` with an infinite default (YAML ``.inf``) must be
        reported as an error, not raise. ``int(inf)`` raises OverflowError during
        coercion, which previously escaped validate_workflow's ValueError handler
        and broke its "return a list of errors" contract.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "inf-as-number"
  name: "Inf As Number"
  version: "1.0.0"
inputs:
  count:
    type: number
    default: .inf
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid default" in e for e in errors), errors

    def test_validate_workflow_rejects_non_string_default_for_string_type(self):
        """``type: string`` must require an actual string — a numeric YAML
        default like ``5`` would otherwise slip through unvalidated.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "number-as-string"
  name: "Number As String"
  version: "1.0.0"
inputs:
  label:
    type: string
    default: 5
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid default" in e for e in errors), errors

    def test_while_loop_condition_reads_latest_iteration(self, project_dir):
        """Regression: while-loop condition must see updated step output
        from the most recent iteration, not stale iteration-0 data.

        See https://github.com/github/spec-kit/issues/2592
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        # Shell step echoes a counter via a file.
        # Condition: exit_code != 0 means "keep looping" — but a non-zero
        # exit code would mark the step FAILED and abort the run, so we
        # use stdout-based comparison instead.
        #
        # Iteration 0: counter=1, echoes "1" → not "done" → loop continues
        # Iteration 1: counter=2, echoes "done" → condition false → stop
        # Without the fix, condition always reads iteration-0 stdout,
        # so the loop runs all max_iterations.
        import sys

        counter_file = project_dir / ".counter"
        counter_file.write_text("0", encoding="utf-8")
        py = sys.executable
        script_file = project_dir / "_tick.py"
        script_file.write_text(
            f"import pathlib; p = pathlib.Path(r'{counter_file}')\n"
            "n = int(p.read_text()) + 1; p.write_text(str(n))\n"
            "print('done' if n >= 2 else str(n), end='')\n",
            encoding="utf-8",
        )

        yaml_str = f"""
schema_version: "1.0"
workflow:
  id: "while-condition-update"
  name: "While Condition Update"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: while
    condition: "{{{{ 'done' not in steps.attempt.output.stdout }}}}"
    max_iterations: 5
    steps:
      - id: attempt
        type: shell
        run: '"{py}" "{script_file}"'
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        # The unprefixed key should reflect the latest iteration's result.
        assert state.step_results["attempt"]["output"]["stdout"] == "done"
        # Namespaced iteration-1 result should also exist.
        assert "retry-loop:attempt:1" in state.step_results
        # Counter should be 2 (iteration 0 + iteration 1), not 5.
        assert counter_file.read_text(encoding="utf-8").strip() == "2"

    def test_do_while_loop_condition_reads_latest_iteration(self, project_dir):
        """Regression: do-while loop condition must also see updated output.

        See https://github.com/github/spec-kit/issues/2592
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        import sys

        counter_file = project_dir / ".counter"
        counter_file.write_text("0", encoding="utf-8")
        py = sys.executable
        script_file = project_dir / "_tick.py"
        script_file.write_text(
            f"import pathlib; p = pathlib.Path(r'{counter_file}')\n"
            "n = int(p.read_text()) + 1; p.write_text(str(n))\n"
            "print('done' if n >= 2 else str(n), end='')\n",
            encoding="utf-8",
        )

        yaml_str = f"""
schema_version: "1.0"
workflow:
  id: "do-while-condition-update"
  name: "Do While Condition Update"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: do-while
    condition: "{{{{ 'done' not in steps.attempt.output.stdout }}}}"
    max_iterations: 5
    steps:
      - id: attempt
        type: shell
        run: '"{py}" "{script_file}"'
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert state.step_results["attempt"]["output"]["stdout"] == "done"
        assert counter_file.read_text(encoding="utf-8").strip() == "2"

    def test_while_loop_runs_to_max_when_condition_stays_true(self, project_dir):
        """While loop must still run to max_iterations when the condition
        never becomes false — copy-back must not break this path.

        See https://github.com/github/spec-kit/issues/2592
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        import sys

        counter_file = project_dir / ".counter"
        counter_file.write_text("0", encoding="utf-8")
        py = sys.executable
        script_file = project_dir / "_tick.py"
        script_file.write_text(
            f"import pathlib; p = pathlib.Path(r'{counter_file}')\n"
            "n = int(p.read_text()) + 1; p.write_text(str(n))\n"
            "print('pending', end='')\n",
            encoding="utf-8",
        )

        yaml_str = f"""
schema_version: "1.0"
workflow:
  id: "while-max-iterations"
  name: "While Max Iterations"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: while
    condition: "{{{{ 'done' not in steps.tick.output.stdout }}}}"
    max_iterations: 3
    steps:
      - id: tick
        type: shell
        run: '"{py}" "{script_file}"'
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        # All 3 iterations ran (iteration 0 + 2 loop iterations).
        assert counter_file.read_text(encoding="utf-8").strip() == "3"
        # Unprefixed key holds the last iteration's result.
        assert state.step_results["tick"]["output"]["stdout"] == "pending"
        # Namespaced keys for loop iterations exist.
        assert "retry-loop:tick:1" in state.step_results
        assert "retry-loop:tick:2" in state.step_results

    def test_do_while_loop_runs_to_max_when_condition_stays_true(self, project_dir):
        """Do-while loop must still run to max_iterations when the condition
        never becomes false.

        See https://github.com/github/spec-kit/issues/2592
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        import sys

        counter_file = project_dir / ".counter"
        counter_file.write_text("0", encoding="utf-8")
        py = sys.executable
        script_file = project_dir / "_tick.py"
        script_file.write_text(
            f"import pathlib; p = pathlib.Path(r'{counter_file}')\n"
            "n = int(p.read_text()) + 1; p.write_text(str(n))\n"
            "print('pending', end='')\n",
            encoding="utf-8",
        )

        yaml_str = f"""
schema_version: "1.0"
workflow:
  id: "do-while-max-iterations"
  name: "Do While Max Iterations"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: do-while
    condition: "{{{{ 'done' not in steps.tick.output.stdout }}}}"
    max_iterations: 3
    steps:
      - id: tick
        type: shell
        run: '"{py}" "{script_file}"'
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert counter_file.read_text(encoding="utf-8").strip() == "3"
        assert state.step_results["tick"]["output"]["stdout"] == "pending"

    def test_while_loop_multi_step_body_inter_step_refs(self, project_dir):
        """Multi-step loop body: step B must see step A's output from the
        current iteration, not a stale previous one.

        See https://github.com/github/spec-kit/issues/2592
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        import sys

        counter_file = project_dir / ".counter"
        counter_file.write_text("0", encoding="utf-8")
        py = sys.executable

        # Step A: increments counter file, echoes the value.
        step_a_file = project_dir / "_step_a.py"
        step_a_file.write_text(
            f"import pathlib; p = pathlib.Path(r'{counter_file}')\n"
            "n = int(p.read_text()) + 1; p.write_text(str(n))\n"
            "print(str(n), end='')\n",
            encoding="utf-8",
        )

        # Step B uses {{ steps.step-a.output.stdout }} expression
        # substitution in its run command so the engine resolves the
        # aliased unprefixed key — this is the real inter-step test.
        yaml_str = f"""
schema_version: "1.0"
workflow:
  id: "while-multi-step"
  name: "While Multi Step"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: while
    condition: "{{{{ 'done' not in steps.step-a.output.stdout }}}}"
    max_iterations: 3
    steps:
      - id: step-a
        type: shell
        run: '"{py}" "{step_a_file}"'
      - id: step-b
        type: shell
        run: "echo b-saw-{{{{ steps.step-a.output.stdout }}}}"
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        # Both unprefixed keys reflect the latest iteration's results.
        assert state.step_results["step-a"]["output"]["stdout"] == "3"
        # Step B saw step A's output via expression substitution.
        assert "b-saw-3" in state.step_results["step-b"]["output"]["stdout"]
        # Namespaced keys exist for loop iterations.
        assert "retry-loop:step-a:1" in state.step_results
        assert "retry-loop:step-b:1" in state.step_results
        assert "retry-loop:step-a:2" in state.step_results
        assert "retry-loop:step-b:2" in state.step_results


# ===== context.run_id Tests =====
#
# End-to-end coverage for the `{{ context.run_id }}` template
# variable introduced in issue #2590. Locks resolution inside the
# three step types the acceptance criteria called out — shell `run:`,
# command `input.args:`, and switch `expression:` — plus the
# "workflow doesn't reference it" backward-compat path.


class TestContextRunId:
    """End-to-end tests for `{{ context.run_id }}` in workflow YAML."""

    def test_shell_run_resolves_run_id(self, project_dir):
        """`run: "echo {{ context.run_id }}"` substitutes the
        engine-assigned run id into the spawned shell, and the
        same value appears on `state.run_id`.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "stamp-run-id"
  name: "Stamp Run Id"
  version: "1.0.0"
steps:
  - id: stamp
    type: shell
    run: "echo RUN_ID={{ context.run_id }}"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition, run_id="abc12345")

        assert state.run_id == "abc12345"
        stdout = state.step_results["stamp"]["output"]["stdout"]
        assert stdout.strip() == "RUN_ID=abc12345"

    def test_command_input_args_resolves_run_id(self, project_dir):
        """`input.args: "{{ context.run_id }}"` is resolved by
        `CommandStep` and recorded in step output, even when CLI
        dispatch is unavailable (no integration installed). Covers
        the artifact-metadata use case from the issue.
        """
        from unittest.mock import patch
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "command-stamp"
  name: "Command Stamp"
  version: "1.0.0"
  integration: claude
steps:
  - id: tag-artifact
    command: speckit.specify
    input:
      args: "{{ context.run_id }}"
""")
        engine = WorkflowEngine(project_dir)
        with patch(
            "specify_cli.workflows.steps.command.shutil.which",
            return_value=None,
        ):
            state = engine.execute(definition, run_id="cafef00d")

        # Even when dispatch fails (no CLI), the resolved input is
        # recorded so downstream observers see the run id in artifact
        # metadata.
        assert state.step_results["tag-artifact"]["output"]["input"]["args"] == "cafef00d"

    def test_switch_expression_matches_on_run_id(self, project_dir):
        """`switch` over `{{ context.run_id }}` matches against case
        keys, and the nested branch can ALSO reference
        `{{ context.run_id }}`. Demonstrates the run id is a
        first-class value in the expression engine (not just a
        string-interpolation token) AND that it propagates into
        nested step execution via the recursive `_execute_steps`
        traversal.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "switch-on-run-id"
  name: "Switch On Run Id"
  version: "1.0.0"
steps:
  - id: route
    type: switch
    expression: "{{ context.run_id }}"
    cases:
      target-run:
        - id: matched-branch
          type: shell
          run: "echo nested-run-id={{ context.run_id }}"
    default:
      - id: default-branch
        type: shell
        run: "echo defaulted"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition, run_id="target-run")

        assert state.status == RunStatus.COMPLETED
        assert state.step_results["route"]["output"]["matched_case"] == "target-run"
        assert "matched-branch" in state.step_results
        assert "default-branch" not in state.step_results
        # The nested branch sees the same run id — propagation through
        # recursive `_execute_steps` is intact.
        nested_stdout = state.step_results["matched-branch"]["output"]["stdout"]
        assert nested_stdout.strip() == "nested-run-id=target-run"

    def test_workflow_without_context_reference_unchanged(self, project_dir):
        """Workflows that do not reference `{{ context.run_id }}`
        continue to run exactly as before. Locks the byte-equivalent
        default required by the issue's acceptance criteria.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "no-context-ref"
  name: "No Context Ref"
  version: "1.0.0"
steps:
  - id: only-step
    type: shell
    run: "echo hello"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert state.step_results["only-step"]["output"]["stdout"].strip() == "hello"

    def test_run_id_uses_speckit_workflow_run_id_env_override(self, project_dir, monkeypatch):
        """When no run_id argument is provided, SPECKIT_WORKFLOW_RUN_ID overrides the auto-generated run ID."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        monkeypatch.setenv("SPECKIT_WORKFLOW_RUN_ID", "env-run-123")
        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "env-run-id"
  name: "Env Run Id"
  version: "1.0.0"
steps:
  - id: stamp
    type: shell
    run: "echo {{ context.run_id }}"
""")
        state = WorkflowEngine(project_dir).execute(definition)

        assert state.run_id == "env-run-123"
        assert state.step_results["stamp"]["output"]["stdout"].strip() == "env-run-123"

    def test_run_id_arg_takes_precedence_over_env_override(self, project_dir, monkeypatch):
        """Explicit run_id keeps existing precedence over SPECKIT_WORKFLOW_RUN_ID."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        monkeypatch.setenv("SPECKIT_WORKFLOW_RUN_ID", "env-run-123")
        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "explicit-run-id"
  name: "Explicit Run Id"
  version: "1.0.0"
steps:
  - id: stamp
    type: shell
    run: "echo {{ context.run_id }}"
""")
        state = WorkflowEngine(project_dir).execute(definition, run_id="explicit-456")

        assert state.run_id == "explicit-456"
        assert state.step_results["stamp"]["output"]["stdout"].strip() == "explicit-456"


# ===== continue_on_error Tests =====
#
# Locks the contract documented in workflows/README.md "Error Handling"
# section: when a step returns `StepResult(status=StepStatus.FAILED, ...)` and
# `continue_on_error: true` is declared, the engine records the step's
# `output` (with `exit_code` and `stderr` from the failure) and its
# `status` (sibling key on `steps.<id>`, not nested under `output`)
# and continues to the next sibling step instead of halting the run.
# Gate aborts (`output.aborted`) still halt regardless of the flag.
# Unhandled exceptions raised out of `step_impl.execute()` are out of
# scope for this flag — they propagate to `WorkflowEngine.execute()`
# and abort the run.


class TestContinueOnError:
    """Test the `continue_on_error` step-level field."""

    def test_undeclared_failure_halts_run(self, project_dir):
        """Default behaviour (no `continue_on_error`): a failing step
        halts the workflow run with `status == StepStatus.FAILED`.

        Locks the byte-equivalent default — workflows that do not
        declare the flag must behave exactly as before this feature.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "halt-on-fail"
  name: "Halt On Fail"
  version: "1.0.0"
steps:
  - id: fail-step
    type: shell
    run: "exit 7"
  - id: after
    type: shell
    run: "echo should-not-run"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.FAILED
        assert "fail-step" in state.step_results
        assert state.step_results["fail-step"]["output"]["exit_code"] == 7
        # Subsequent step never executes when the flag is absent.
        assert "after" not in state.step_results

    def test_declared_and_fired_continues_run(self, project_dir):
        """`continue_on_error: true` + failing step: the run keeps
        going, the failed step's result is recorded, and the
        downstream step runs.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "continue-past-fail"
  name: "Continue Past Fail"
  version: "1.0.0"
steps:
  - id: flaky-step
    type: shell
    run: "exit 42"
    continue_on_error: true
  - id: after
    type: shell
    run: "echo did-run"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        # Failed step's exit_code is preserved so downstream branching
        # can inspect it.
        assert state.step_results["flaky-step"]["output"]["exit_code"] == 42
        assert state.step_results["flaky-step"]["status"] == "failed"
        # Downstream step ran successfully.
        assert state.step_results["after"]["output"]["exit_code"] == 0

    def test_declared_but_step_succeeded_is_noop(self, project_dir):
        """`continue_on_error: true` on a step that succeeds is a
        no-op — the flag only changes behaviour on StepStatus.FAILED status.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "flag-but-success"
  name: "Flag But Success"
  version: "1.0.0"
steps:
  - id: ok-step
    type: shell
    run: "echo ok"
    continue_on_error: true
  - id: after
    type: shell
    run: "echo done"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert state.step_results["ok-step"]["status"] == "completed"
        assert state.step_results["ok-step"]["output"]["exit_code"] == 0
        assert state.step_results["after"]["output"]["exit_code"] == 0

    def test_if_branch_routes_around_failure(self, project_dir):
        """End-to-end: `continue_on_error` + `if` cleanly routes around
        a failure. The recovery branch runs; the success branch does
        not.

        Mirrors the canonical usage pattern from the original feature
        discussion in issue #2591.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "route-around"
  name: "Route Around Failure"
  version: "1.0.0"
steps:
  - id: heavy-thing
    type: shell
    run: "exit 1"
    continue_on_error: true
  - id: check-result
    type: if
    condition: "{{ steps.heavy-thing.output.exit_code != 0 }}"
    then:
      - id: recovery
        type: shell
        run: "echo recovery-ran"
    else:
      - id: happy-path
        type: shell
        run: "echo happy-path-ran"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert "recovery" in state.step_results
        assert "happy-path" not in state.step_results

    def test_gate_abort_still_halts_with_continue_on_error(
        self, project_dir, monkeypatch
    ):
        """`continue_on_error` does NOT override a deliberate gate
        abort. `output.aborted` always halts the run with
        `status == ABORTED`.

        Aborts are explicit operator decisions; continue_on_error
        is for transient/expected step failures only.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.steps.gate import GateStep

        # Force the gate step into interactive mode and feed a "reject"
        # choice so the abort path actually runs in the test env (default
        # behaviour returns StepStatus.PAUSED when stdin is not a TTY).
        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr(
            GateStep, "_prompt", staticmethod(lambda _msg, _opts: "reject")
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "gate-abort-halts"
  name: "Gate Abort Halts"
  version: "1.0.0"
steps:
  - id: gate-step
    type: gate
    message: "Approve?"
    options: [approve, reject]
    on_reject: abort
    continue_on_error: true
  - id: should-not-run
    type: shell
    run: "echo nope"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.ABORTED
        assert "should-not-run" not in state.step_results

    def test_validation_rejects_non_bool_continue_on_error(self):
        """`continue_on_error` must be a literal boolean; coerced
        strings like `"true"` are rejected at validation time so
        authoring mistakes surface before execution.
        """
        from specify_cli.workflows.engine import (
            WorkflowDefinition,
            validate_workflow,
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "bad-coe"
  name: "Bad COE"
  version: "1.0.0"
steps:
  - id: step-one
    type: shell
    run: "true"
    continue_on_error: "true"
""")
        errors = validate_workflow(definition)
        assert any(
            "continue_on_error" in e and "boolean" in e for e in errors
        ), errors

    def test_validation_accepts_bool_continue_on_error(self):
        """Boolean values pass validation cleanly."""
        from specify_cli.workflows.engine import (
            WorkflowDefinition,
            validate_workflow,
        )

        for value in (True, False):
            yaml_value = "true" if value else "false"
            definition = WorkflowDefinition.from_string(f"""
schema_version: "1.0"
workflow:
  id: "good-coe"
  name: "Good COE"
  version: "1.0.0"
steps:
  - id: step-one
    type: shell
    run: "true"
    continue_on_error: {yaml_value}
""")
            errors = validate_workflow(definition)
            assert errors == [], errors

    def test_engine_ignores_truthy_non_bool_continue_on_error(self, project_dir):
        """Defense-in-depth: even if a caller bypasses
        `validate_workflow()` and feeds the engine a definition with
        `continue_on_error: "true"` (a string), the engine must NOT
        honour the flag — only a literal boolean enables the
        behaviour. `WorkflowEngine.execute()` does not auto-validate
        (the `WorkflowEngine.load_workflow` docstring explicitly
        notes the definition is "not yet validated; call
        `validate_workflow()` or `engine.validate()` separately"),
        so the engine guards against truthy non-bool values itself
        via an identity check rather than truthiness.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        # Bypass `validate_workflow()` — execute() is what would
        # be called by a caller that skipped validation.
        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "string-coe"
  name: "String COE"
  version: "1.0.0"
steps:
  - id: fail-step
    type: shell
    run: "exit 1"
    continue_on_error: "true"
  - id: should-not-run
    type: shell
    run: "echo should-not-run"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        # String "true" is truthy but not a literal boolean, so the
        # engine must treat the step as a halting failure.
        assert state.status == RunStatus.FAILED
        assert "should-not-run" not in state.step_results


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

    @pytest.mark.parametrize(
        "malicious_run_id",
        [
            # Parent-directory traversal — the classic path-escape vector.
            "../escape",
            "..",
            "../../etc/passwd",
            # Embedded path separators — both POSIX and Windows.
            "foo/bar",
            "foo\\bar",
            # Leading non-alphanumeric characters that the existing
            # pattern's anchor blocks (would be mistaken for CLI flags
            # or hidden files in shell completions / error messages).
            ".hidden",
            "-flag",
            # NUL byte — some filesystems treat the prefix as a valid
            # path and silently truncate at the NUL.
            "foo\x00bar",
            # Empty string — degenerate case, matches no file but the
            # validator should reject it before any I/O.
            "",
        ],
    )
    def test_load_rejects_path_traversal(self, project_dir, malicious_run_id):
        """``RunState.load`` validates ``run_id`` before touching the
        filesystem.

        Without this guard, a value like ``../escape`` passed via
        ``specify workflow resume`` would interpolate path-traversal
        segments into the lookup path. ``state_path.exists()`` would
        probe arbitrary paths the process can read (a file-existence
        oracle) and ``json.load`` would happily parse attacker-planted
        JSON from outside ``.specify/workflows/runs/``. The check must
        fire *before* the path is built — ``__init__``'s identical
        regex on ``state_data["run_id"]`` fires too late.
        """
        from specify_cli.workflows.engine import RunState

        # Plant a state.json *outside* the legitimate ``runs/`` directory
        # at the location ``../escape`` would traverse to, so a missing
        # guard would surface as a successful load rather than a
        # ``FileNotFoundError`` (which would be ambiguous with the
        # not-found case).
        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        attacker_dir = project_dir / ".specify" / "workflows" / "escape"
        attacker_dir.mkdir(exist_ok=True)
        (attacker_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "pwned",
                    "workflow_id": "attacker-owned",
                    "status": "created",
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Invalid run_id"):
            RunState.load(malicious_run_id, project_dir)

    @pytest.mark.parametrize(
        "bad_run_id",
        [
            # One vector per category from ``test_load_rejects_path_traversal``
            # — enough to prove both entry points agree without re-running
            # the full attack matrix here.
            "../escape",    # parent-directory traversal
            "foo/bar",      # embedded path separator
            ".hidden",      # leading non-alphanumeric
            "",             # empty / degenerate
        ],
    )
    def test_init_and_load_share_validation(self, project_dir, bad_run_id):
        """``__init__`` *and* ``load`` reject the same malformed IDs.

        The two entry points must stay in sync — drift would let an ID
        slip in via one path that the other would reject, producing
        confusing crashes mid-workflow. The previous version of this
        test only exercised ``__init__`` and ``_validate_run_id`` (the
        shared helper), so a regression in ``load`` — e.g. someone
        deleting the ``cls._validate_run_id(run_id)`` call there — could
        slip through despite ``__init__`` and the helper staying
        aligned. We now hit ``load`` directly with the same vector so
        any drift between the two call sites is caught by this test.
        """
        from specify_cli.workflows.engine import RunState

        # ``__init__`` rejects up front.
        with pytest.raises(ValueError, match="Invalid run_id"):
            RunState(run_id=bad_run_id)

        # The shared helper rejects the value too (sanity check that the
        # ``__init__`` rejection came from the validator, not some
        # unrelated constructor failure).
        with pytest.raises(ValueError, match="Invalid run_id"):
            RunState._validate_run_id(bad_run_id)

        # And ``load`` rejects it *before* touching the filesystem. This
        # is the assertion the previous version was missing: without it,
        # a regression in ``load`` (e.g. forgetting to call the
        # validator before building the path) would not be caught even
        # though ``__init__`` and the helper still agreed.
        with pytest.raises(ValueError, match="Invalid run_id"):
            RunState.load(bad_run_id, project_dir)

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


# ===== Workflow Catalog Tests =====

class TestWorkflowCatalog:
    """Test WorkflowCatalog catalog resolution."""

    def test_default_catalogs(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.setattr(Path, "home", lambda: project_dir)
        monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
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

    def test_load_catalog_config_non_dict_yaml_raises(self, project_dir):
        """A YAML catalog config that is a list (not a mapping) must raise WorkflowValidationError."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text("- item1\n- item2\n", encoding="utf-8")

        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="expected a mapping"):
            catalog.get_active_catalogs()

    def test_add_catalog_malformed_yaml_raises(self, project_dir):
        """A malformed YAML config file must raise WorkflowValidationError when adding a catalog."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(": invalid: yaml: {\n", encoding="utf-8")

        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="unreadable or malformed"):
            catalog.add_catalog("https://example.com/new.json")

    def test_remove_catalog_malformed_yaml_raises(self, project_dir):
        """A malformed YAML config file must raise WorkflowValidationError when removing a catalog."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/c1.json", "first")

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(": bad: yaml: {\n", encoding="utf-8")

        with pytest.raises(WorkflowValidationError, match="unreadable or malformed"):
            catalog.remove_catalog(0)

    def test_add_catalog_wraps_write_oserror(self, project_dir, monkeypatch):
        """An OSError on write must be wrapped as WorkflowValidationError."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError
        import builtins

        catalog = WorkflowCatalog(project_dir)
        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == config_path and "w" in mode:
                raise OSError("simulated write failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(WorkflowValidationError, match="Failed to write catalog config"):
            catalog.add_catalog("https://example.com/new-catalog.json", "my-catalog")

    def test_remove_catalog_wraps_write_oserror(self, project_dir, monkeypatch):
        """An OSError on write must be wrapped as WorkflowValidationError."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError
        import builtins

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/c1.json", "first")
        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == config_path and "w" in mode:
                raise OSError("simulated write failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(WorkflowValidationError, match="Failed to write catalog config"):
            catalog.remove_catalog(0)


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


# ===== Step Registry Tests =====

class TestStepRegistryCustom:
    """Test StepRegistry operations for custom step types."""

    def test_add_and_get(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("deploy", {"name": "Deploy", "version": "1.0.0", "type_key": "deploy"})

        entry = registry.get("deploy")
        assert entry is not None
        assert entry["name"] == "Deploy"
        assert "installed_at" in entry

    def test_add_does_not_mutate_input_metadata(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        metadata = {
            "name": "Deploy",
            "type_key": "deploy",
            "nested": {"key": "original"},
        }

        registry.add("deploy", metadata)

        assert "installed_at" not in metadata
        assert "updated_at" not in metadata
        metadata["nested"]["key"] = "changed-after-add"
        assert registry.get("deploy")["nested"]["key"] == "original"

    def test_remove(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("deploy", {"name": "Deploy", "type_key": "deploy"})
        assert registry.is_installed("deploy")

        registry.remove("deploy")
        assert not registry.is_installed("deploy")

    def test_remove_missing_returns_false(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        removed = registry.remove("nonexistent")
        assert removed is False

    def test_list(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("step-a", {"name": "A", "type_key": "step-a"})
        registry.add("step-b", {"name": "B", "type_key": "step-b"})

        installed = registry.list()
        assert "step-a" in installed
        assert "step-b" in installed

    def test_is_installed(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        assert not registry.is_installed("missing")

        registry.add("exists", {"name": "Exists", "type_key": "exists"})
        assert registry.is_installed("exists")

    def test_persistence(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry1 = StepRegistry(project_dir)
        registry1.add("deploy", {"name": "Deploy", "type_key": "deploy"})

        registry2 = StepRegistry(project_dir)
        assert registry2.is_installed("deploy")

    def test_corrupted_registry_resets(self, project_dir):
        from specify_cli.workflows.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.steps_dir.mkdir(parents=True, exist_ok=True)
        registry.registry_path.write_text("not json", encoding="utf-8")

        # Loading again should reset
        registry2 = StepRegistry(project_dir)
        assert registry2.list() == {}

    def test_registry_missing_steps_key_resets(self, project_dir):
        """Valid JSON but missing 'steps' key should not crash add/get."""
        from specify_cli.workflows.catalog import StepRegistry
        import json as _json

        registry = StepRegistry(project_dir)
        registry.steps_dir.mkdir(parents=True, exist_ok=True)
        # Valid JSON but 'steps' is not a dict
        registry.registry_path.write_text(
            _json.dumps({"schema_version": "1.0", "steps": "bad"}),
            encoding="utf-8",
        )

        registry2 = StepRegistry(project_dir)
        # Should be safe to call add/get without KeyError
        assert registry2.list() == {}
        registry2.add("deploy", {"name": "Deploy", "type_key": "deploy"})
        assert registry2.is_installed("deploy")

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod not reliable on Windows")
    def test_registry_unreadable_file_resets(self, project_dir):
        """OSError reading the registry file should fall back to default."""
        from specify_cli.workflows.catalog import StepRegistry
        import json as _json

        registry = StepRegistry(project_dir)
        registry.steps_dir.mkdir(parents=True, exist_ok=True)
        # Write valid registry first
        registry.registry_path.write_text(
            _json.dumps({"schema_version": "1.0", "steps": {"existing": {}}}),
            encoding="utf-8",
        )
        # Make it unreadable
        registry.registry_path.chmod(0o000)
        try:
            registry2 = StepRegistry(project_dir)
            assert registry2.list() == {}
        finally:
            registry.registry_path.chmod(0o644)

        # After restoring permissions the registry is fully functional
        registry2.add("deploy", {"name": "Deploy", "type_key": "deploy"})
        assert registry2.is_installed("deploy")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_registry_load_refuses_symlinked_steps_dir(self, project_dir):
        """A symlinked steps directory must not be read from (defense-in-depth)."""
        from specify_cli.workflows.catalog import StepRegistry
        import json as _json

        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        (outside / "step-registry.json").write_text(
            _json.dumps({"schema_version": "1.0", "steps": {"evil": {}}}),
            encoding="utf-8",
        )
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        registry = StepRegistry(project_dir)
        assert registry.list() == {}

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_registry_save_refuses_symlinked_steps_dir(self, project_dir):
        """save() must refuse symlinked registry paths (defense-in-depth)."""
        from specify_cli.workflows.catalog import StepRegistry, StepValidationError

        outside = project_dir.parent / "outside-steps-save"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        registry = StepRegistry(project_dir)
        with pytest.raises(StepValidationError, match="symlinked path"):
            registry.save()


# ===== Step Catalog Tests =====

class TestStepCatalog:
    """Test StepCatalog catalog resolution."""

    def test_default_catalogs(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import StepCatalog

        monkeypatch.setattr(Path, "home", lambda: project_dir)
        monkeypatch.delenv("SPECKIT_STEP_CATALOG_URL", raising=False)
        catalog = StepCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 2
        assert entries[0].name == "default"
        assert entries[1].name == "community"

    def test_env_var_override(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import StepCatalog

        monkeypatch.setenv("SPECKIT_STEP_CATALOG_URL", "https://example.com/step-catalog.json")
        catalog = StepCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 1
        assert entries[0].name == "env-override"
        assert entries[0].url == "https://example.com/step-catalog.json"

    def test_project_level_config(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "custom",
                "url": "https://example.com/step-catalog.json",
                "priority": 1,
                "install_allowed": True,
            }]
        }))

        catalog = StepCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 1
        assert entries[0].name == "custom"

    def test_validate_url_http_rejected(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="HTTPS"):
            catalog._validate_catalog_url("http://evil.com/step-catalog.json")

    def test_validate_url_localhost_http_allowed(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        # Should not raise
        catalog._validate_catalog_url("http://localhost:8080/step-catalog.json")

    def test_add_catalog(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/new-steps.json", "my-steps")

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/new-steps.json"

    def test_add_catalog_empty_yaml_file(self, project_dir):
        """An empty YAML config file should be treated as empty, not corrupted."""
        from specify_cli.workflows.catalog import StepCatalog

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text("", encoding="utf-8")

        catalog = StepCatalog(project_dir)
        # Should not raise StepValidationError "corrupted"
        catalog.add_catalog("https://example.com/steps.json", "my-steps")

        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/steps.json"

    def test_add_catalog_duplicate_rejected(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/steps.json")

        with pytest.raises(StepValidationError, match="already configured"):
            catalog.add_catalog("https://example.com/steps.json")

    def test_remove_catalog(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/s1.json", "first")
        catalog.add_catalog("https://example.com/s2.json", "second")

        removed = catalog.remove_catalog(0)
        assert removed == "first"

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1

    def test_remove_catalog_invalid_index(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/s1.json")

        with pytest.raises(StepValidationError, match="out of range"):
            catalog.remove_catalog(5)

    def test_remove_catalog_no_config(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="No step catalog config file found"):
            catalog.remove_catalog(0)

    def test_add_catalog_wraps_write_oserror(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError
        import builtins

        catalog = StepCatalog(project_dir)
        config_path = project_dir / ".specify" / "step-catalogs.yml"
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == config_path and "w" in mode:
                raise OSError("simulated write failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(StepValidationError, match="Failed to write catalog config"):
            catalog.add_catalog("https://example.com/new-steps.json", "my-steps")

    def test_remove_catalog_wraps_write_oserror(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import StepCatalog, StepValidationError
        import builtins

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/s1.json", "first")
        config_path = project_dir / ".specify" / "step-catalogs.yml"
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == config_path and "w" in mode:
                raise OSError("simulated write failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(StepValidationError, match="Failed to write catalog config"):
            catalog.remove_catalog(0)

    def test_get_catalog_configs(self, project_dir):
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        configs = catalog.get_catalog_configs()
        assert len(configs) == 2
        assert configs[0]["name"] == "default"
        assert isinstance(configs[0]["install_allowed"], bool)

    def test_search_with_mock_catalog(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import StepCatalog

        mock_data = {
            "schema_version": "1.0",
            "steps": {
                "deploy": {
                    "id": "deploy",
                    "name": "Deploy Step",
                    "description": "Deploy to production",
                    "version": "1.0.0",
                },
                "notify": {
                    "id": "notify",
                    "name": "Notify Step",
                    "description": "Send notifications",
                    "version": "1.0.0",
                },
            },
        }

        catalog = StepCatalog(project_dir)
        monkeypatch.setattr(catalog, "_get_merged_steps", lambda **kw: {
            "deploy": dict(mock_data["steps"]["deploy"], _catalog_name="test", _install_allowed=True),
            "notify": dict(mock_data["steps"]["notify"], _catalog_name="test", _install_allowed=True),
        })

        results = catalog.search()
        assert len(results) == 2

        results = catalog.search(query="deploy")
        assert len(results) == 1
        assert results[0]["id"] == "deploy"

    def test_search_with_non_string_fields(self, project_dir, monkeypatch):
        """Non-string catalog fields (e.g. integer id) must not raise TypeError."""
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        monkeypatch.setattr(catalog, "_get_merged_steps", lambda **kw: {
            "42": {
                "id": 42,
                "name": None,
                "description": 99,
                "_catalog_name": "test",
                "_install_allowed": True,
            },
        })

        results = catalog.search()
        assert len(results) == 1

        results = catalog.search(query="42")
        assert len(results) == 1

        results = catalog.search(query="missing")
        assert len(results) == 0

    def test_get_merged_steps_normalizes_list_ids_to_strings(self, project_dir, monkeypatch):
        """List-based catalog entries with non-string ids must be normalized."""
        from specify_cli.workflows.catalog import StepCatalog, StepCatalogEntry

        catalog = StepCatalog(project_dir)
        entry = StepCatalogEntry(
            name="test",
            url="https://example.com/steps.json",
            priority=1,
            install_allowed=True,
        )
        monkeypatch.setattr(catalog, "get_active_catalogs", lambda: [entry])
        monkeypatch.setattr(
            catalog,
            "_fetch_single_catalog",
            lambda _entry, _force_refresh=False: {
                "steps": [{"id": 42, "name": "Integer ID"}]
            },
        )

        merged = catalog._get_merged_steps()
        assert "42" in merged
        assert 42 not in merged
        assert merged["42"]["id"] == "42"

    def test_get_step_info_returns_entry_or_none(self, project_dir, monkeypatch):
        """get_step_info returns matching entry or None for missing ids."""
        from specify_cli.workflows.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        monkeypatch.setattr(catalog, "_get_merged_steps", lambda **kw: {
            "deploy": {
                "id": "deploy",
                "name": "Deploy Step",
                "version": "1.0.0",
                "_catalog_name": "test",
                "_install_allowed": True,
            },
        })

        info = catalog.get_step_info("deploy")
        assert info is not None
        assert info["name"] == "Deploy Step"

        missing = catalog.get_step_info("nonexistent")
        assert missing is None


# ===== Load Custom Steps Tests =====

class TestLoadCustomSteps:
    """Test dynamic loading of custom step types from the filesystem."""

    def test_empty_steps_dir(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        loaded = load_custom_steps(project_dir)
        assert loaded == []

    def test_no_steps_dir(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        # .specify/workflows/steps does not exist
        loaded = load_custom_steps(project_dir)
        assert loaded == []

    def test_load_valid_custom_step(self, project_dir):
        from specify_cli.workflows import load_custom_steps, STEP_REGISTRY

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "test-custom"
        step_dir.mkdir(parents=True)

        step_yml = """
schema_version: "1.0"
step:
  type_key: "test-custom"
  name: "Test Custom Step"
  version: "1.0.0"
  author: "test"
  description: "A test custom step"
"""
        (step_dir / "step.yml").write_text(step_yml, encoding="utf-8")

        init_py = """
from specify_cli.workflows.base import StepBase, StepResult

class TestCustomStep(StepBase):
    type_key = "test-custom"

    def execute(self, config, context):
        return StepResult()
"""
        (step_dir / "__init__.py").write_text(init_py, encoding="utf-8")

        loaded = load_custom_steps(project_dir)
        assert "test-custom" in loaded
        assert "test-custom" in STEP_REGISTRY

    def test_skip_missing_step_yml(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "bad-step"
        step_dir.mkdir(parents=True)
        (step_dir / "__init__.py").write_text("# no step.yml", encoding="utf-8")

        loaded = load_custom_steps(project_dir)
        assert "bad-step" not in loaded

    def test_skip_missing_init_py(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "bad-step2"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: bad-step2\n", encoding="utf-8"
        )

        loaded = load_custom_steps(project_dir)
        assert "bad-step2" not in loaded

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_skip_symlinked_step_files(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "bad-symlinked-files"
        step_dir.mkdir(parents=True)

        outside = project_dir.parent / "outside-step-files"
        outside.mkdir(parents=True, exist_ok=True)
        step_yml_target = outside / "step.yml"
        step_yml_target.write_text("step:\n  type_key: bad-symlinked-files\n", encoding="utf-8")
        init_target = outside / "__init__.py"
        init_target.write_text("# external code", encoding="utf-8")

        (step_dir / "step.yml").symlink_to(step_yml_target)
        (step_dir / "__init__.py").symlink_to(init_target)

        loaded = load_custom_steps(project_dir)
        assert "bad-symlinked-files" not in loaded

    def test_skip_already_registered(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        # "command" is already registered as a built-in step
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "command"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: command\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        # Should not raise KeyError; just skip
        loaded = load_custom_steps(project_dir)
        assert "command" not in loaded

    def test_skip_broken_init_py(self, project_dir):
        from specify_cli.workflows import load_custom_steps

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "broken-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: broken-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text(
            "raise RuntimeError('broken')", encoding="utf-8"
        )

        # Should not propagate exception
        loaded = load_custom_steps(project_dir)
        assert "broken-step" not in loaded

    def test_module_name_sanitized_for_hyphenated_type_key(self, project_dir):
        """type_key values with hyphens produce valid Python module identifiers."""
        import hashlib
        import sys
        from specify_cli.workflows import load_custom_steps, STEP_REGISTRY

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "my-hyphen-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: my-hyphen-step\n  name: Hyphen Step\n",
            encoding="utf-8",
        )

        init_py = """
from specify_cli.workflows.base import StepBase, StepResult

class HyphenStep(StepBase):
    type_key = "my-hyphen-step"

    def execute(self, config, context):
        return StepResult()
"""
        (step_dir / "__init__.py").write_text(init_py, encoding="utf-8")

        loaded = load_custom_steps(project_dir)
        assert "my-hyphen-step" in loaded
        assert "my-hyphen-step" in STEP_REGISTRY
        # Synthetic module name must be a valid identifier (hyphens → underscores)
        # and include a collision-resistant hash suffix.
        key_hash = hashlib.sha256(b"my-hyphen-step").hexdigest()[:8]
        module_name = f"_speckit_custom_step_my_hyphen_step_{key_hash}"
        assert module_name in sys.modules

    def test_package_relative_import(self, project_dir):
        """Steps can use relative imports to access sibling modules."""
        import hashlib
        import sys
        from specify_cli.workflows import load_custom_steps, STEP_REGISTRY

        step_dir = project_dir / ".specify" / "workflows" / "steps" / "pkg-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: pkg-step\n  name: Package Step\n",
            encoding="utf-8",
        )
        # Helper module that the step will import relatively
        (step_dir / "helpers.py").write_text(
            "HELPER_VALUE = 'hello'\n", encoding="utf-8"
        )
        init_py = """
from specify_cli.workflows.base import StepBase, StepResult
from .helpers import HELPER_VALUE

class PkgStep(StepBase):
    type_key = "pkg-step"
    helper = HELPER_VALUE

    def execute(self, config, context):
        return StepResult()
"""
        (step_dir / "__init__.py").write_text(init_py, encoding="utf-8")

        loaded = load_custom_steps(project_dir)
        assert "pkg-step" in loaded
        assert "pkg-step" in STEP_REGISTRY
        # Verify the relative import actually resolved; module name includes hash suffix.
        key_hash = hashlib.sha256(b"pkg-step").hexdigest()[:8]
        module_name = f"_speckit_custom_step_pkg_step_{key_hash}"
        assert module_name in sys.modules
        assert sys.modules[module_name].PkgStep.helper == "hello"

    def test_module_name_collision_resistance(self, project_dir):
        """'a-b' and 'a_b' produce different module names despite the same sanitized form."""
        import hashlib

        # Simulate the module name generation for two type_keys that sanitize the same way
        def make_module_name(type_key: str) -> str:
            import re
            safe_key = re.sub(r"[^A-Za-z0-9_]", "_", type_key)
            key_hash = hashlib.sha256(type_key.encode()).hexdigest()[:8]
            return f"_speckit_custom_step_{safe_key}_{key_hash}"

        name_a = make_module_name("a-b")
        name_b = make_module_name("a_b")
        assert name_a != name_b, "Module names for 'a-b' and 'a_b' must differ"


# ===== CLI Step Remove Tests =====

class TestWorkflowStepRemoveCLI:
    """Test the 'specify workflow step remove' CLI command edge cases."""

    def test_remove_orphaned_directory(self, project_dir, monkeypatch):
        """step remove works when directory exists but registry entry is missing.

        This covers the case where the registry was reset due to corruption.
        """
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        # Create an orphaned step directory (no registry entry)
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "orphan-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: orphan-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "orphan-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        # Warning should be printed about missing registry entry
        assert "Warning" in result.output or "warning" in result.output.lower()

    def test_remove_not_installed(self, project_dir, monkeypatch):
        """step remove fails cleanly when neither directory nor registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "ghost-step"])

        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_remove_registered_step(self, project_dir, monkeypatch):
        """step remove works normally when both directory and registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import StepRegistry

        monkeypatch.chdir(project_dir)

        # Set up a registered step with a directory
        registry = StepRegistry(project_dir)
        registry.add("my-step", {"name": "My Step", "type_key": "my-step", "version": "1.0.0"})
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "my-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: my-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        registry2 = StepRegistry(project_dir)
        assert not registry2.is_installed("my-step")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_remove_rejects_symlinked_steps_base_dir(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code != 0
        assert "Refusing to use symlinked step directory" in result.output


class TestWorkflowRemoveGuard:
    def test_remove_rejects_traversal_registry_key(self, project_dir, monkeypatch):
        """A corrupted registry key must not let remove delete outside workflows/."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("../outside", {"name": "Bad"})
        outside = project_dir / ".specify" / "outside"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "../outside"])

        assert result.exit_code != 0
        assert "Invalid workflow ID" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"

    @pytest.mark.parametrize("workflow_id", ["runs", "steps"])
    def test_remove_rejects_reserved_storage_ids(
        self, project_dir, monkeypatch, workflow_id
    ):
        """Reserved workflow storage directories must never be removable workflows."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add(workflow_id, {"name": "Bad"})
        reserved_dir = project_dir / ".specify" / "workflows" / workflow_id
        reserved_dir.mkdir(exist_ok=True)
        sentinel = reserved_dir / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", workflow_id])

        assert result.exit_code != 0
        assert "Invalid workflow ID" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_remove_refuses_symlinked_workflow_dir(self, project_dir, monkeypatch):
        """A symlinked workflow directory must not let remove delete its target."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test"})
        outside = project_dir / "outside-workflow-remove-target"
        outside.mkdir(exist_ok=True)
        sentinel = outside / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        (project_dir / ".specify" / "workflows" / "test-wf").symlink_to(
            outside, target_is_directory=True
        )

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows/test-wf" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"
        assert WorkflowRegistry(project_dir).is_installed("test-wf")

    def test_remove_refuses_non_directory_workflow_path(self, project_dir, monkeypatch):
        """A file at the workflow path must fail cleanly instead of crashing."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test"})
        workflow_path = project_dir / ".specify" / "workflows" / "test-wf"
        workflow_path.write_text("not a directory", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert "exists but is not a directory" in result.output
        assert workflow_path.read_text(encoding="utf-8") == "not a directory"
        assert WorkflowRegistry(project_dir).is_installed("test-wf")


class TestWorkflowAddSymlinkGuard:
    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_specify(self, temp_dir, monkeypatch):
        """workflow add must refuse a symlinked .specify (writes could escape root)."""
        from typer.testing import CliRunner
        from specify_cli import app

        outside = temp_dir.parent / "outside-specify-target"
        (outside / "workflows").mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify").symlink_to(outside, target_is_directory=True)

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", "anything.yml"])

        assert result.exit_code != 0
        assert "symlinked .specify" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_workflows_dir(self, temp_dir, monkeypatch):
        """workflow add must refuse a symlinked .specify/workflows directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify").mkdir()
        outside = temp_dir.parent / "outside-workflows-target"
        outside.mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify" / "workflows").symlink_to(outside, target_is_directory=True)

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", "anything.yml"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_id_dir(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A symlinked <id> install dir must not let a copy escape the project root."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        outside = temp_dir.parent / "outside-id-target"
        outside.mkdir(parents=True, exist_ok=True)
        # <id> from the YAML below is "test-workflow"; plant it as a symlink.
        (temp_dir / ".specify" / "workflows" / "test-workflow").symlink_to(
            outside, target_is_directory=True
        )
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        # No write-through: the symlink target stays empty.
        assert not (outside / "workflow.yml").exists()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_workflow_yml_leaf(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A symlinked <id>/workflow.yml must not let copy2 write through the link."""
        from typer.testing import CliRunner
        from specify_cli import app

        id_dir = temp_dir / ".specify" / "workflows" / "test-workflow"
        id_dir.mkdir(parents=True)
        outside_file = temp_dir.parent / "outside-leaf-target.yml"
        outside_file.write_text("original\n", encoding="utf-8")
        (id_dir / "workflow.yml").symlink_to(outside_file)
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        # Rich may wrap the message; assert on the unbroken path fragment.
        assert "test-workflow/workflow.yml" in result.output
        assert "symlinked" in result.output
        # The link target content is untouched.
        assert outside_file.read_text(encoding="utf-8") == "original\n"

    def test_add_refuses_non_directory_id(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """An <id> path that already exists as a file must fail cleanly, not crash."""
        from typer.testing import CliRunner
        from specify_cli import app

        wf_dir = temp_dir / ".specify" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "test-workflow").write_text("not a dir", encoding="utf-8")
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        assert "exists but is not a directory" in result.output
        assert result.exception is None or isinstance(result.exception, SystemExit)

    def test_add_refuses_workflow_yml_as_directory(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A pre-existing <id>/workflow.yml *directory* must fail cleanly, not crash."""
        from typer.testing import CliRunner
        from specify_cli import app

        id_dir = temp_dir / ".specify" / "workflows" / "test-workflow"
        id_dir.mkdir(parents=True)
        # Plant workflow.yml as a directory so a later write/copy2 would raise
        # IsADirectoryError without the explicit non-file guard.
        (id_dir / "workflow.yml").mkdir()
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        assert "test-workflow/workflow.yml" in result.output
        assert "is not a file" in result.output
        # Clean exit, not an unhandled IsADirectoryError traceback.
        assert result.exception is None or isinstance(result.exception, SystemExit)

    def test_safe_workflow_id_dir_escapes_markup_in_invalid_id(self, temp_dir, capsys):
        """A traversal <id> carrying Rich markup must be escaped, not interpreted."""
        import typer
        from specify_cli.workflows._commands import _safe_workflow_id_dir

        workflows_dir = temp_dir / ".specify" / "workflows"
        workflows_dir.mkdir(parents=True)
        # Traversal (so the "Invalid workflow ID" branch fires) plus markup.
        with pytest.raises(typer.Exit):
            _safe_workflow_id_dir(workflows_dir, "../[red]evil[/red]")

        out = capsys.readouterr().out
        # Literal bracketed text survives; Rich did not consume it as a tag.
        assert "[red]evil[/red]" in out

    @pytest.mark.parametrize(
        "workflow_id",
        [
            "runs",
            "steps",
            "nested/workflow",
            "nested\\workflow",
            "bad id",
            " bad-id",
            "bad-id ",
        ],
    )
    def test_safe_workflow_id_dir_rejects_reserved_or_non_segment_ids(
        self, temp_dir, workflow_id, capsys
    ):
        """Install IDs must not collide with workflow internals or create nested paths."""
        import typer
        from specify_cli.workflows._commands import _safe_workflow_id_dir

        workflows_dir = temp_dir / ".specify" / "workflows"
        workflows_dir.mkdir(parents=True)

        with pytest.raises(typer.Exit):
            _safe_workflow_id_dir(workflows_dir, workflow_id)

        assert "Invalid workflow ID" in capsys.readouterr().out
        assert not (workflows_dir / workflow_id).exists()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_list_refuses_symlinked_runs_dir(self, temp_dir, monkeypatch):
        """workflow commands using the project shim must refuse symlinked run storage."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        outside = temp_dir.parent / "outside-runs-target"
        outside.mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify" / "workflows" / "runs").symlink_to(
            outside, target_is_directory=True
        )

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "list"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows/runs" in result.output


class TestWorkflowStepAddCLI:
    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_rejects_symlinked_steps_base_dir(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            }

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "Refusing to use symlinked step directory" in result.output

    def test_add_rejects_non_string_extra_files_key(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {
                    123: "https://example.com/helper.py",
                },
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "non-string path key" in result.output

    @pytest.mark.parametrize(
        "rel_path,expected",
        [
            ("", "empty or non-string path key"),
            (".", "not a valid relative file path"),
            ("..", "not a valid relative file path"),
            ("sub/../x", "not a valid relative file path"),
        ],
    )
    def test_add_rejects_invalid_extra_files_path(
        self, project_dir, monkeypatch, rel_path, expected
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {rel_path: "https://example.com/helper.py"},
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert expected in result.output

    def test_add_rejects_non_string_extra_files_url(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {"helper.py": None},
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "empty or non-string URL" in result.output


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


class TestResumeWithInputs:
    """Test that `workflow resume` can accept updated workflow inputs."""

    _WF_CMD = """
schema_version: "1.0"
workflow:
  id: "resume-cmd-wf"
  name: "Resume Cmd WF"
  version: "1.0.0"
inputs:
  cmd:
    type: string
    default: "exit 1"
steps:
  - id: s
    type: shell
    run: "{{ inputs.cmd }}"
"""

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

    def test_resume_with_input_reruns_step_with_new_value(self, project_dir):
        from specify_cli.workflows.engine import WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string(self._WF_CMD)
        engine = self._engine(project_dir)

        state = engine.execute(definition)
        assert state.status == RunStatus.FAILED  # "exit 1" fails

        resumed = engine.resume(state.run_id, {"cmd": "exit 0"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.inputs["cmd"] == "exit 0"

    def test_resume_without_input_preserves_inputs(self, project_dir):
        from specify_cli.workflows.engine import WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string(self._WF_CMD)
        engine = self._engine(project_dir)

        state = engine.execute(definition)
        assert state.status == RunStatus.FAILED

        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.FAILED  # still "exit 1"
        assert resumed.inputs["cmd"] == "exit 1"

    def test_resume_merges_and_coerces_typed_input(self, project_dir):
        import json as _json
        from specify_cli.workflows.engine import WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string(self._WF_NUM)
        engine = self._engine(project_dir)

        state = engine.execute(definition)
        assert state.status == RunStatus.PAUSED

        resumed = engine.resume(state.run_id, {"count": "5"})
        assert resumed.inputs["count"] == 5  # coerced string -> number

        inputs_file = (
            project_dir / ".specify" / "workflows" / "runs" / state.run_id / "inputs.json"
        )
        assert _json.loads(inputs_file.read_text())["inputs"]["count"] == 5

    def test_resume_invalid_typed_input_raises(self, project_dir):
        from specify_cli.workflows.engine import WorkflowDefinition

        definition = WorkflowDefinition.from_string(self._WF_NUM)
        engine = self._engine(project_dir)

        state = engine.execute(definition)
        with pytest.raises(ValueError):
            engine.resume(state.run_id, {"count": "not-a-number"})

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


class TestWorkflowAddUrlResolution:
    """CLI-level tests for workflow add <url> GitHub release URL resolution."""

    VALID_WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "test-wf"
  name: "Test Workflow"
  version: "1.0.0"
  description: "A test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def test_workflow_add_from_github_release_url_resolves_and_downloads(self, project_dir):
        """'workflow add <github-release-url>' resolves to API asset URL."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/42"

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None):
            captured_urls.append((url, extra_headers, timeout))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://api.github.com/repos/org/repo/releases/assets/42"}]
                }).encode())
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://github.com/org/repo/releases/download/v1.0/workflow.yml",
            ])

        assert result.exit_code == 0, result.output
        assert "Test Workflow" in result.output
        # First call resolves the release tag with timeout=30
        tag_calls = [(url, h, t) for url, h, t in captured_urls if "releases/tags/" in url]
        assert len(tag_calls) == 1
        assert tag_calls[0][2] == 30  # timeout matches download timeout
        # Second call downloads from the resolved asset URL with octet-stream
        asset_calls = [(url, h, t) for url, h, t in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_from_direct_api_asset_url_passes_through(self, project_dir):
        """'workflow add <api-asset-url>' uses URL directly with octet-stream."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/42"

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None):
            captured_urls.append((url, extra_headers))
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://api.github.com/repos/org/repo/releases/assets/42",
            ])

        assert result.exit_code == 0, result.output
        # Should go directly to the asset URL with Accept header
        assert len(captured_urls) == 1
        assert captured_urls[0][0] == "https://api.github.com/repos/org/repo/releases/assets/42"
        assert captured_urls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_catalog_based_resolves_github_release_url(self, project_dir):
        """'workflow add <id>' with catalog GitHub release URL resolves via API."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/55"

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://api.github.com/repos/org/repo/releases/assets/55"}]
                }).encode())
            # Use workflow YAML with id matching catalog key
            wf_yaml = """
schema_version: "1.0"
workflow:
  id: "my-wf"
  name: "My Workflow"
  version: "1.0.0"
  description: "A catalog workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""
            return FakeResponse(wf_yaml.encode())

        fake_catalog_info = {
            "id": "my-wf",
            "name": "My Workflow",
            "version": "1.0.0",
            "url": "https://github.com/org/repo/releases/download/v2.0/workflow.yml",
            "_install_allowed": True,
        }

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch("specify_cli.workflows.catalog.WorkflowCatalog.get_workflow_info", return_value=fake_catalog_info):
            result = runner.invoke(app, ["workflow", "add", "my-wf"])

        assert result.exit_code == 0, result.output
        # Should resolve via releases/tags API
        tag_calls = [url for url, _ in captured_urls if "releases/tags/" in url]
        assert len(tag_calls) == 1
        assert "releases/tags/v2.0" in tag_calls[0]
        # Should download from resolved asset URL with octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_from_ghes_release_url_resolves_via_api_v3(self, project_dir, monkeypatch):
        """'workflow add <ghes-release-url>' resolves via GHES /api/v3 endpoint."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(_auth_http, "_config_override", [
            AuthConfigEntry(hosts=("ghes.example",), provider="github", auth="bearer", token="t"),
        ])

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._url = url or "https://ghes.example/api/v3/repos/org/repo/releases/assets/42"

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42"}]
                }).encode())
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://ghes.example/org/repo/releases/download/v1.0/workflow.yml",
            ])

        assert result.exit_code == 0, result.output
        # Tag lookup must use the GHES /api/v3 endpoint
        assert any("ghes.example/api/v3/repos/org/repo/releases/tags/v1.0" in url for url, _ in captured_urls)
        # Asset download must carry Accept: application/octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_catalog_based_ghes_release_url_resolves_via_api_v3(self, project_dir, monkeypatch):
        """'workflow add <id>' with a GHES catalog URL resolves via /api/v3."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(_auth_http, "_config_override", [
            AuthConfigEntry(hosts=("ghes.example",), provider="github", auth="bearer", token="t"),
        ])

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._url = url or "https://ghes.example/api/v3/repos/org/repo/releases/assets/55"

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        ghes_wf_yaml = """
schema_version: "1.0"
workflow:
  id: "my-wf"
  name: "My GHES Workflow"
  version: "1.0.0"
  description: "A GHES catalog workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

        def fake_open_url(url, timeout=None, extra_headers=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/55"}]
                }).encode())
            return FakeResponse(ghes_wf_yaml.encode())

        fake_catalog_info = {
            "id": "my-wf",
            "name": "My GHES Workflow",
            "version": "1.0.0",
            "url": "https://ghes.example/org/repo/releases/download/v2.0/workflow.yml",
            "_install_allowed": True,
        }

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch("specify_cli.workflows.catalog.WorkflowCatalog.get_workflow_info", return_value=fake_catalog_info):
            result = runner.invoke(app, ["workflow", "add", "my-wf"])

        assert result.exit_code == 0, result.output
        # Tag lookup must use GHES /api/v3
        tag_calls = [url for url, _ in captured_urls if "releases/tags/" in url]
        assert len(tag_calls) == 1
        assert "ghes.example/api/v3/repos/org/repo/releases/tags/v2.0" in tag_calls[0]
        # Asset download must carry Accept: application/octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


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
        from specify_cli.workflows.steps.gate import GateStep

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
