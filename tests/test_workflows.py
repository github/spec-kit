"""Tests for the workflow engine subsystem.

Covers:
- Step registry & auto-discovery
- Base classes (StepBase, StepContext, StepResult)
- Expression engine
- All 12 built-in step types
- Workflow definition loading & validation
- Workflow engine execution & state persistence
- Workflow catalog & registry
"""

from __future__ import annotations

import json

import os
import shutil
import stat
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
            "while", "do-while", "fan-out", "fan-in", "init", "slot",
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
        from specify_cli.workflows.step.command import CommandStep

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

    def test_multi_expression_with_literal_close_brace_in_argument(self):
        """A multi-expression template with a literal ``}}`` inside a string
        argument must interpolate, not raise. #3208/#3228 hardened the single-
        expression fast path for literal braces but left the interpolation path
        on ``_EXPR_PATTERN``, whose non-greedy body stops at the first ``}}`` --
        so the block was captured truncated and the filter parser raised
        ValueError."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"name": "Bob", "missing": None})
        # ``}}`` in the default fallback of the second block.
        result = evaluate_expression(
            "{{ inputs.name }}: {{ inputs.missing | default('}}') }}", ctx
        )
        assert result == "Bob: }}"
        # ``}}`` in the first block, expression following it.
        result = evaluate_expression(
            "{{ inputs.missing | default('}}') }} / {{ inputs.name }}", ctx
        )
        assert result == "}} / Bob"

    def test_multi_expression_with_literal_open_brace_in_argument(self):
        """A literal ``{{`` inside a string argument in a multi-expression
        template must not confuse block detection either."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"name": "Bob", "missing": None})
        result = evaluate_expression(
            "{{ inputs.name }} {{ inputs.missing | default('{{') }}", ctx
        )
        assert result == "Bob {{"

    def test_multi_expression_unbalanced_quote_still_raises(self):
        """A malformed block (an unbalanced quote in a filter arg) must still
        surface a ValueError, not be silently emitted verbatim.

        The quote-aware scan never finds a block-closing ``}}`` when a quote is
        left open, but a raw ``}}`` is still present in the tail. It must fall
        back to that raw delimiter and evaluate — same as the old regex path —
        so a typo fails loudly instead of being hidden (Copilot review on
        #3307)."""
        import pytest

        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"name": "Bob", "missing": None})
        with pytest.raises(ValueError):
            evaluate_expression(
                "{{ inputs.name }} {{ inputs.missing | default('oops }}", ctx
            )

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

    def test_ordering_comparison_of_non_numeric_strings(self):
        """`<`/`>`/`<=`/`>=` between non-numeric strings must compare
        lexicographically, not silently return False.

        `_safe_compare` used to coerce both operands to int/float unconditionally;
        a non-numeric string (date, version tag, name) failed that coercion and
        the whole comparison returned False. Ordinary strings should order the
        way Python does; numeric strings must still compare as numbers."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        # ISO dates compare lexicographically (correct chronological order).
        ctx = StepContext(inputs={"d": "2026-01-01"})
        assert evaluate_expression("{{ inputs.d < '2026-02-01' }}", ctx) is True
        assert evaluate_expression("{{ inputs.d > '2026-02-01' }}", ctx) is False

        # Plain string ordering.
        ctx = StepContext(inputs={"name": "beta"})
        assert evaluate_expression("{{ inputs.name > 'alpha' }}", ctx) is True

        # Two numeric strings still compare numerically, not lexically
        # ("10" > "9" is True as numbers; as strings it would be False).
        ctx = StepContext(inputs={"v": "10"})
        assert evaluate_expression("{{ inputs.v > '9' }}", ctx) is True

        # A number vs a non-numeric string is genuinely incomparable -> False.
        ctx = StepContext(inputs={"n": 5})
        assert evaluate_expression("{{ inputs.n > 'abc' }}", ctx) is False

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

    def test_list_literal_ignores_trailing_and_empty_commas(self):
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        # A trailing comma must not append a spurious None element.
        assert evaluate_expression("{{ [1, 2,] }}", ctx) == [1, 2]
        assert evaluate_expression("{{ [1,, 2] }}", ctx) == [1, 2]
        # …but an intentional empty-string element is still preserved.
        assert evaluate_expression("{{ ['', 'a'] }}", ctx) == ["", "a"]

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

    def test_membership_against_non_iterable_is_false_not_error(self):
        from specify_cli.workflows.expressions import (
            evaluate_condition,
            evaluate_expression,
        )
        from specify_cli.workflows.base import StepContext

        # A non-iterable right operand (int, bool, None, float) makes a raw
        # `x in y` raise TypeError in Python. The evaluator must treat it as
        # "not contained" (False, and `not in` as True) instead of leaking the
        # TypeError and crashing the whole workflow run. This generalizes the
        # previous `right is not None` guard and mirrors _safe_compare, which
        # already swallows TypeError for the ordering operators.
        ctx = StepContext(inputs={"tag": "x", "count": 5, "ratio": 1.5, "flag": True})
        # `in` -> False and `not in` -> True for every non-iterable right
        # operand (int, float, bool, None), so neither operator can drift.
        for right in ("count", "ratio", "flag", "missing"):
            assert evaluate_expression(f"{{{{ inputs.tag in inputs.{right} }}}}", ctx) is False
            assert evaluate_expression(f"{{{{ inputs.tag not in inputs.{right} }}}}", ctx) is True
        # A condition that would otherwise crash the run now evaluates cleanly.
        assert evaluate_condition("{{ inputs.tag in inputs.count }}", ctx) is False

        # Regression: genuine membership over a real iterable still works.
        ok = StepContext(inputs={"items": ["x", "y"], "s": "xyz"})
        assert evaluate_expression("{{ 'x' in inputs.items }}", ok) is True
        assert evaluate_expression("{{ 'z' not in inputs.items }}", ok) is True
        assert evaluate_expression("{{ 'y' in inputs.s }}", ok) is True

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

    def test_filter_map_non_string_attr_raises(self):
        # A non-string attribute (authoring mistake like `map(5)`) must raise a
        # ValueError naming the problem, not leak the cryptic AttributeError
        # from attr.split() that would escape the evaluator and crash the run.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"rows": [{"id": "a"}, {"id": "b"}]})
        with pytest.raises(ValueError, match="map: expected a string attribute name"):
            evaluate_expression("{{ inputs.rows | map(5) }}", ctx)

    def test_filter_join_non_string_separator_raises(self):
        # A non-string separator (authoring mistake like `join(5)`) must raise a
        # ValueError, not leak the cryptic AttributeError from str.join.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"tags": ["a", "b"]})
        with pytest.raises(ValueError, match="join: expected a string separator"):
            evaluate_expression("{{ inputs.tags | join(5) }}", ctx)

    def test_filter_contains_non_string_arg_on_string_raises(self):
        # For a string value, `contains` requires a string argument: `x in y` on
        # a string needs a string left operand. A non-string argument must raise
        # a ValueError, not leak the cryptic TypeError that would crash the run.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"text": "hello"})
        with pytest.raises(ValueError, match="contains: expected a string argument"):
            evaluate_expression("{{ inputs.text | contains(5) }}", ctx)

    def test_filter_contains_non_string_arg_on_list_ok(self):
        # For a list value, membership of any element type is legitimate, so a
        # non-string argument stays valid and is not rejected.
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"nums": [1, 2, 5]})
        assert evaluate_expression("{{ inputs.nums | contains(5) }}", ctx) is True
        assert evaluate_expression("{{ inputs.nums | contains(9) }}", ctx) is False

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

    def test_filter_call_with_trailing_tokens_fails_loudly(self):
        # A trailing operator/token after a filter's closing paren must not be
        # silently discarded (the parser used an unanchored regex). It must
        # fall through to the "unsupported form" ValueError, like the from_json
        # branch's strict trailing-token handling.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        # A comparison after a filter (binds looser than the pipe) was dropped,
        # so `default('7') > '5'` silently returned '7'.
        with pytest.raises(ValueError, match="unsupported form"):
            evaluate_expression(
                "{{ inputs.missing | default('7') > '5' }}", StepContext(inputs={})
            )
        # Trailing garbage after a valid filter call.
        with pytest.raises(ValueError, match="unsupported form"):
            evaluate_expression(
                "{{ inputs.tags | join(',') extra }}",
                StepContext(inputs={"tags": ["a", "b"]}),
            )

    def test_filter_on_a_comparison_operand_is_refused(self):
        """A filter mixed with a comparison must be reported, not guessed at.

        The pipe is detected before the operators, so
        `count > limit | default(5)` evaluated `count > limit` first and then
        applied `default` to the resulting bool — a no-op — silently returning
        the comparison against the *unfiltered* operand (False, where the author
        meant `10 > 5` = True).

        This is the mirror of a filter followed by a comparison
        (`default('7') > '5'`), which this module already refuses rather than
        guessing at the intended precedence. Both are now refused the same way.
        """
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"count": 10, "name": "x"})
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression("{{ inputs.count > inputs.limit | default(5) }}", ctx)
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression(
                '{{ inputs.name == inputs.other | default("x") }}', ctx
            )
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression("{{ inputs.a and inputs.b | default(1) }}", ctx)

    def test_filter_after_a_unary_not_is_refused(self):
        """Unary `not` mis-binds the same way and must be caught too.

        `not` is a leading prefix rather than an infix token (the parser tests
        it with `expr.startswith("not ")`), so it has no surrounding space for
        the operator scan to match. Without an explicit check,
        `not inputs.missing | default(1)` evaluated `not inputs.missing` first
        and applied `default` to that boolean — a no-op — silently returning
        True where the author meant `not 1` = False.
        """
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"value": 0, "flag": True})
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression("{{ not inputs.missing | default(1) }}", ctx)
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression("{{ not inputs.value | default(1) }}", ctx)
        # A `not` that follows and/or is already caught by that token.
        with pytest.raises(ValueError, match="ambiguous filter precedence"):
            evaluate_expression(
                "{{ inputs.flag and not inputs.value | default(1) }}", ctx
            )
        # Plain unary `not`, with no filter, is untouched.
        assert evaluate_expression("{{ not inputs.value }}", ctx) is True
        assert evaluate_expression("{{ not inputs.flag }}", ctx) is False

    def test_plain_filters_and_chains_are_unaffected(self):
        """Only a filter mixed with an operator is refused."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"items": ["a", "b"], "count": 10, "name": "x"})
        assert evaluate_expression("{{ inputs.missing | default(5) }}", ctx) == 5
        assert evaluate_expression('{{ inputs.items | join(", ") }}', ctx) == "a, b"
        assert evaluate_expression("{{ inputs.items | contains('a') }}", ctx) is True
        # Operators without a filter, and filters without an operator, both fine.
        assert evaluate_expression("{{ inputs.count > 5 }}", ctx) is True
        assert evaluate_expression('{{ inputs.name == "x" }}', ctx) is True

    def test_chained_filters_apply_left_to_right(self):
        # Filters chain: each filter's result feeds the next. `map` yields a
        # list and `join` is the only filter that renders a list to a string,
        # so `map('name') | join(', ')` is the canonical pairing — it must not
        # raise. Previously the pipe parser split only at the first `|` and
        # handed the whole tail (`map('name') | join(', ')`) to one filter,
        # which the `name(arg)` regex mangled into a ValueError.
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(
            inputs={
                "rows": [{"name": "a"}, {"name": "b"}],
                "tags": ["x", "y"],
                "missing": None,
            }
        )
        assert (
            evaluate_expression(
                "{{ inputs.rows | map('name') | join(', ') }}", ctx
            )
            == "a, b"
        )
        # A three-link chain: map -> join -> contains.
        assert (
            evaluate_expression(
                "{{ inputs.rows | map('name') | join(', ') | contains('a') }}",
                ctx,
            )
            is True
        )
        # default's fallback then flows into the next filter.
        assert (
            evaluate_expression(
                "{{ inputs.missing | default('x') | contains('x') }}", ctx
            )
            is True
        )

    def test_chained_filter_error_in_later_link_raises(self):
        # A mis-wired filter anywhere in the chain must fail loudly, not just
        # the first link.
        import pytest
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"rows": [{"name": "a"}]})
        with pytest.raises(ValueError, match="unknown filter 'bogus'"):
            evaluate_expression(
                "{{ inputs.rows | map('name') | bogus }}", ctx
            )

    def test_pipe_in_quoted_arg_is_not_a_filter_separator(self):
        # A literal `|` inside a quoted operand or filter argument must not be
        # mistaken for a filter-chain separator — the top-level split has to
        # respect quotes.
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"mode": "a|b", "tags": ["a|b", "c"]})
        assert evaluate_expression("{{ inputs.mode == 'a|b' }}", ctx) is True
        # `|` inside a filter argument stays part of the argument.
        assert (
            evaluate_expression("{{ inputs.tags | join(' | ') }}", ctx)
            == "a|b | c"
        )

    def test_condition_evaluation(self):
        from specify_cli.workflows.expressions import evaluate_condition
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(inputs={"ready": True})
        assert evaluate_condition("{{ inputs.ready }}", ctx) is True
        assert evaluate_condition("{{ inputs.missing }}", ctx) is False

    def test_condition_strips_captured_command_output(self):
        """A condition resolving to captured stdout must honour "false".

        A ``shell`` step stores ``proc.stdout`` verbatim, so ``run: echo false``
        resolves to ``"false\\n"``. Without stripping, the trailing newline
        matched neither the "false" nor the "true" branch and fell through to
        ``bool("false\\n")`` -> True, so an ``if`` step took its ``then`` branch
        on a step that printed "false". There is no ``trim`` filter, so a
        workflow author cannot strip it themselves.
        """
        from specify_cli.workflows.expressions import evaluate_condition
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(steps={"check": {"output": {"stdout": "false\n"}}})
        assert evaluate_condition("{{ steps.check.output.stdout }}", ctx) is False

        for raw in ("false\n", "false\r\n", " false", "false ", "FALSE\n"):
            assert evaluate_condition(raw, StepContext()) is False, raw
        for raw in ("true\n", " true ", "TRUE\r\n"):
            assert evaluate_condition(raw, StepContext()) is True, raw

    def test_condition_whitespace_only_string_stays_truthy(self):
        """Stripping must not turn a whitespace-only string into False.

        Only the "false"/"true" special case is stripped; everything else still
        falls through to ``bool(result)`` on the raw string.
        """
        from specify_cli.workflows.expressions import evaluate_condition
        from specify_cli.workflows.base import StepContext

        assert evaluate_condition("   ", StepContext()) is True
        assert evaluate_condition("falsey", StepContext()) is True

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
        from specify_cli.workflows.step.command import CommandStep
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
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["command"] == "speckit.specify"
        assert result.output["integration"] == "claude"
        assert result.output["input"]["args"] == "login"

    def test_per_step_integration_config_is_resolved_and_isolated(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.command import CommandStep

        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            return type("Result", (), {"returncode": 0})()

        monkeypatch.delenv(
            "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda name: (
                "/usr/bin/docker-agent"
                if name in {"docker-agent", "/usr/bin/docker-agent"}
                else None
            ),
        )
        monkeypatch.setattr("subprocess.run", fake_run)

        step = CommandStep()
        context = StepContext(
            inputs={"config": "./review.yaml", "agent": "reviewer"},
            project_root=str(tmp_path),
        )
        first = step.execute(
            {
                "id": "review",
                "command": "speckit.plan",
                "integration": "docker-agent",
                "integration_args": ["{{ inputs.config }}"],
                "integration_options": {
                    "agent": "{{ inputs.agent }}",
                    "safety": "balanced",
                },
            },
            context,
        )
        second = step.execute(
            {
                "id": "implement",
                "command": "speckit.implement",
                "integration": "docker-agent",
                "integration_args": ["./implement.yaml"],
                "integration_options": {"agent": "implementer"},
            },
            context,
        )

        assert first.status is StepStatus.COMPLETED
        assert second.status is StepStatus.COMPLETED
        assert first.output["integration_args"] == ["./review.yaml"]
        assert first.output["integration_options"] == {
            "agent": "reviewer",
            "safety": "balanced",
        }
        assert calls[0][0] == [
            "/usr/bin/docker-agent",
            "run",
            "--exec",
            "./review.yaml",
            "--agent",
            "reviewer",
            "--safety",
            "balanced",
            "--",
            "/speckit-plan",
        ]
        assert calls[1][0] == [
            "/usr/bin/docker-agent",
            "run",
            "--exec",
            "./implement.yaml",
            "--agent",
            "implementer",
            "--",
            "/speckit-implement",
        ]
        assert calls[0][1]["cwd"] == str(tmp_path)
        assert calls[1][1]["cwd"] == str(tmp_path)

    @pytest.mark.parametrize(
        ("step_model", "default_model", "expected_model"),
        [
            ("step/model", "workflow/model", "step/model"),
            (None, "workflow/model", "workflow/model"),
        ],
    )
    def test_docker_agent_uses_one_effective_model(
        self,
        tmp_path,
        monkeypatch,
        step_model,
        default_model,
        expected_model,
    ):
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.command import CommandStep

        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            return type("Result", (), {"returncode": 0})()

        monkeypatch.delenv(
            "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda name: (
                "/usr/bin/docker-agent"
                if name in {"docker-agent", "/usr/bin/docker-agent"}
                else None
            ),
        )
        monkeypatch.setattr("subprocess.run", fake_run)

        config = {
            "id": "implement",
            "command": "speckit.implement",
            "integration": "docker-agent",
            "integration_args": ["./agent.yaml"],
        }
        if step_model is not None:
            config["model"] = step_model

        result = CommandStep().execute(
            config,
            StepContext(
                default_model=default_model,
                project_root=str(tmp_path),
            ),
        )

        assert result.status is StepStatus.COMPLETED
        assert calls[0].count("--model") == 1
        assert calls[0][calls[0].index("--model") + 1] == expected_model

    def test_unsupported_runtime_config_fails_with_actionable_error(self):
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.command import CommandStep

        result = CommandStep().execute(
            {
                "id": "review",
                "command": "speckit.plan",
                "integration": "claude",
                "integration_options": {"saftey": "balanced"},
            },
            StepContext(),
        )

        assert result.status is StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert "does not support per-step 'integration_options'" in (
            result.error or ""
        )
        assert "saftey" in (result.error or "")

    def test_validate_rejects_malformed_runtime_config(self):
        from specify_cli.workflows.step.command import CommandStep

        step = CommandStep()
        errors = step.validate(
            {
                "id": "review",
                "command": "speckit.plan",
                "integration_args": "./agent.yaml",
                "integration_options": ["agent", "root"],
            }
        )

        assert any("'integration_args' must be a list" in error for error in errors)
        assert any(
            "'integration_options' must be a mapping" in error for error in errors
        )

        errors = step.validate(
            {
                "id": "review",
                "command": "speckit.plan",
                "integration_args": [42],
                "integration_options": {1: "root"},
            }
        )
        assert any("'integration_args[0]' must be a string" in error for error in errors)
        assert any("keys must be strings" in error for error in errors)

    def test_try_dispatch_resolves_rovodev_via_acli(self, tmp_path):
        """When acli is installed, rovodev dispatch succeeds via acli."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.step.command import CommandStep
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

        with patch("specify_cli.workflows.step.command.shutil.which",
                    lambda name: "/usr/bin/acli" if name == "acli" else None), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

    def test_validate_missing_command(self):
        from specify_cli.workflows.step.command import CommandStep

        step = CommandStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'command'" in e for e in errors)

    def test_validate_rejects_non_mapping_input_and_options(self):
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        # execute() does input.items() / options.update(); a non-mapping must be
        # reported by validate(), not crash at run time (like switch 'cases').
        for bad in (None, "args", ["a", "b"], 5):
            errs = step.validate({"id": "c", "command": "/x", "input": bad})
            assert any("'input' must be a mapping" in e for e in errs), bad
        errs = step.validate({"id": "c", "command": "/x", "options": 42})
        assert any("'options' must be a mapping" in e for e in errs)
        # a valid mapping config is still accepted
        assert step.validate({"id": "c", "command": "/x", "input": {"args": "y"}, "options": {"k": 1}}) == []
        # execute() has no auto-validation guarantee (the engine may skip
        # validate), so a non-mapping input/options FAILS the step with the same
        # contract error — it does not silently coerce to empty and report
        # COMPLETED (which would defeat continue_on_error).
        res_in = step.execute({"id": "c", "command": "echo", "input": None}, StepContext())
        assert res_in.status is StepStatus.FAILED
        assert "'input' must be a mapping" in (res_in.error or "")
        res_opt = step.execute(
            {"id": "c", "command": "echo", "input": {}, "options": 42}, StepContext()
        )
        assert res_opt.status is StepStatus.FAILED
        assert "'options' must be a mapping" in (res_opt.error or "")

    @pytest.mark.parametrize("bad", [["claude"], {"a": 1}, 5, True])
    def test_validate_rejects_non_string_integration_and_model(self, bad):
        """A non-string 'integration'/'model' must be rejected at validation.

        execute() passes 'integration' to get_integration(), which uses it as a
        dict key — an unhashable list/dict raises a raw TypeError there, even on
        a validated run — and feeds 'model' into the CLI argv. Mirrors the
        'command'/'input'/'options' type checks.
        """
        from specify_cli.workflows.step.command import CommandStep

        step = CommandStep()
        errs = step.validate({"id": "c", "command": "/x", "integration": bad})
        assert any("'integration' must be a string" in e for e in errs), bad
        errs = step.validate({"id": "c", "command": "/x", "model": bad})
        assert any("'model' must be a string" in e for e in errs), bad

    def test_validate_accepts_none_and_expression_integration_model(self):
        """An explicit YAML-null (inherit default) or a '{{ ... }}' expression
        integration/model stays valid — only literal non-strings are rejected."""
        from specify_cli.workflows.step.command import CommandStep

        step = CommandStep()
        assert step.validate(
            {"id": "c", "command": "/x", "integration": None, "model": None}
        ) == []
        assert step.validate(
            {
                "id": "c",
                "command": "/x",
                "integration": "{{ inputs.agent }}",
                "model": "{{ inputs.model }}",
            }
        ) == []

    def test_validate_rejects_non_string_command(self):
        from specify_cli.workflows.step.command import CommandStep

        step = CommandStep()
        # execute() passes 'command' to build_command_invocation(), which does
        # command_name.startswith(...); a non-string crashes there with a raw
        # AttributeError. validate() must report it, like prompt-step 'prompt'.
        for bad in (None, ["a", "b"], 5, {"x": 1}):
            errs = step.validate({"id": "c", "command": bad})
            assert any("'command' must be a string" in e for e in errs), bad
        # a string command (incl. an expression) is still accepted
        assert step.validate({"id": "c", "command": "/x"}) == []
        assert step.validate({"id": "c", "command": "{{ inputs.cmd }}"}) == []

    def test_execute_non_string_command_fails_cleanly(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        # The engine may skip validate(); a non-string 'command' must FAIL the
        # step with the contract error rather than reaching _try_dispatch and
        # crashing build_command_invocation with a raw AttributeError. Force a
        # resolvable integration + installed CLI so, absent the guard, dispatch
        # would actually be attempted and the crash would fire.
        ctx = StepContext(default_integration="claude")
        with patch("specify_cli.workflows.step.command.shutil.which",
                   return_value="/usr/bin/claude"):
            for bad in (None, ["a", "b"], 5, {"x": 1}):
                result = step.execute(
                    {"id": "c", "command": bad, "input": {}}, ctx
                )
                assert result.status is StepStatus.FAILED, bad
                assert "'command' must be a string" in (result.error or ""), bad

    def test_execute_non_string_integration_fails_loudly(self):
        """On an unvalidated run, an unhashable 'integration' would crash
        get_integration() (dict.get on a list) with a raw TypeError. execute()
        must fail the step with the contract error instead."""
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        res = step.execute(
            {"id": "c", "command": "speckit.specify", "integration": ["claude"]},
            StepContext(),
        )
        assert res.status is StepStatus.FAILED
        assert "'integration' must be a string" in (res.error or "")
        # non-string model likewise fails before build_exec_args
        res = step.execute(
            {"id": "c", "command": "speckit.specify", "integration": "claude", "model": ["m"]},
            StepContext(),
        )
        assert res.status is StepStatus.FAILED
        assert "'model' must be a string" in (res.error or "")

    @pytest.mark.parametrize("falsey", [[], {}, 0, False])
    def test_execute_falsey_non_string_integration_fails_loudly(self, falsey):
        """A *falsey* non-string ([], {}, 0, False) must fail the step, not be
        swallowed by an ``or``-fallback to the workflow default.

        A ``config.get('integration') or context.default_integration`` coerces a
        falsey non-string to the default *before* the type guard runs, so with a
        configured default the step would silently dispatch using the wrong
        integration instead of surfacing the contract error. The default is set
        here so a regression dispatches rather than fails-not-possible."""
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        ctx = StepContext(default_integration="claude", default_model="sonnet")
        res = step.execute(
            {"id": "c", "command": "speckit.specify", "integration": falsey}, ctx
        )
        assert res.status is StepStatus.FAILED, falsey
        assert "'integration' must be a string" in (res.error or ""), falsey
        # a falsey non-string model likewise reaches the guard
        res = step.execute(
            {"id": "c", "command": "speckit.specify", "model": falsey}, ctx
        )
        assert res.status is StepStatus.FAILED, falsey
        assert "'model' must be a string" in (res.error or ""), falsey

    def test_step_override_integration(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_integration="claude")
        config = {
            "id": "test",
            "command": "speckit.plan",
            "integration": "gemini",
            "input": {},
        }
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_execute_non_string_integration_fails_cleanly(self):
        """A non-string integration (e.g. a list from an expression that resolved
        to one) must FAIL the step cleanly, not crash the run with
        'TypeError: unhashable type: list' from get_integration's dict lookup."""
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = CommandStep()
        config = {
            "id": "s", "command": "speckit.plan",
            "integration": ["claude"], "input": {},
        }
        result = step.execute(config, StepContext())
        assert result.status == StepStatus.FAILED

    def test_step_override_model(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_model="sonnet-4")
        config = {
            "id": "test",
            "command": "speckit.implement",
            "model": "opus-4",
            "input": {},
        }
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_options_merge(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import StepContext

        step = CommandStep()
        ctx = StepContext(default_options={"max-tokens": 8000})
        config = {
            "id": "test",
            "command": "speckit.plan",
            "options": {"thinking-budget": 32768},
            "input": {},
        }
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["options"]["max-tokens"] == 8000
        assert result.output["options"]["thinking-budget"] == 32768

    def test_dispatch_not_attempted_without_cli(self):
        """When the CLI tool is not installed, step should fail."""
        from unittest.mock import patch
        from specify_cli.workflows.step.command import CommandStep
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
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert result.error is not None

    def test_dispatch_with_mock_cli(self, tmp_path, monkeypatch):
        """When the CLI is installed, dispatch invokes the command by name."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.step.command import CommandStep
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

        with patch("specify_cli.workflows.step.command.shutil.which", return_value="/usr/local/bin/claude"), \
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
        from specify_cli.workflows.step.command import CommandStep
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

        with patch("specify_cli.workflows.step.command.shutil.which", side_effect=fake_which), \
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
        from specify_cli.workflows.step.command import CommandStep
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

        with patch("specify_cli.workflows.step.command.shutil.which", return_value="/usr/local/bin/claude"), \
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
        from specify_cli.workflows.step.prompt import PromptStep
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
        with patch("specify_cli.workflows.step.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["prompt"] == "Review auth.py for security issues"
        assert result.output["integration"] == "claude"
        assert result.output["dispatched"] is False

    def test_execute_non_string_integration_fails_cleanly(self):
        """A non-string integration must FAIL the step cleanly, not crash with
        'TypeError: unhashable type: list' from get_integration's dict lookup."""
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        config = {
            "id": "p", "type": "prompt", "prompt": "do it",
            "integration": ["claude"],
        }
        result = step.execute(config, StepContext())
        assert result.status == StepStatus.FAILED

    def test_execute_with_step_integration(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext

        step = PromptStep()
        ctx = StepContext(default_integration="claude")
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "Summarize the codebase",
            "integration": "gemini",
        }
        with patch("specify_cli.workflows.step.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["integration"] == "gemini"

    def test_execute_with_model(self):
        from unittest.mock import patch
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext

        step = PromptStep()
        ctx = StepContext(default_integration="claude", default_model="sonnet-4")
        config = {
            "id": "review",
            "type": "prompt",
            "prompt": "hello",
            "model": "opus-4",
        }
        with patch("specify_cli.workflows.step.prompt.shutil.which", return_value=None):
            result = step.execute(config, ctx)
        assert result.output["model"] == "opus-4"

    def test_try_dispatch_resolves_rovodev_via_acli(self, tmp_path):
        """When acli is installed, rovodev prompt dispatch succeeds via acli."""
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.step.prompt import PromptStep
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

        with patch("specify_cli.workflows.step.prompt.shutil.which",
                    lambda name: "/usr/bin/acli" if name == "acli" else None), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

    def test_try_dispatch_executes_the_resolved_executable(self, tmp_path):
        """argv[0] must be the shutil.which-resolved path, not the bare name.

        On Windows subprocess.run calls CreateProcess, which ignores PATHEXT, so
        a bare `claude` installed as `claude.cmd` (the usual npm shim) raises
        WinError 2. That OSError is swallowed and reported as "CLI not found or
        not installed" even though the preflight which() just found it, while
        the `command` step -- which goes through
        IntegrationBase.dispatch_command -- resolves argv[0] and works.
        """
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        ctx = StepContext(default_integration="claude", project_root=str(tmp_path))
        config = {"id": "test", "type": "prompt", "prompt": "hello"}

        resolved = r"C:\tools\claude.CMD"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch(
            "specify_cli.workflows.step.prompt.shutil.which",
            lambda name: resolved,
        ), patch("subprocess.run", return_value=mock_result) as run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        argv = run.call_args.args[0]
        assert argv[0] == resolved, argv

    def test_dispatch_with_mock_cli(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from specify_cli.workflows.step.prompt import PromptStep
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

        with patch("specify_cli.workflows.step.prompt.shutil.which", return_value="/usr/local/bin/claude"), \
             patch("subprocess.run", return_value=mock_result):
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert result.output["exit_code"] == 0

    def test_dispatch_uses_executable_override_for_fallback_preflight(self, tmp_path, monkeypatch):
        """Prompt preflight falls back to build_exec_args() argv[0]."""
        from unittest.mock import MagicMock, patch
        from specify_cli.workflows.step.prompt import PromptStep
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

        with patch("specify_cli.workflows.step.prompt.shutil.which", side_effect=fake_which), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = step.execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert result.output["dispatched"] is True
        assert seen_which[:2] == ["claude", "/opt/claude"]
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "/opt/claude"
        assert call_args[0][0][2] == "Explain this code"

    def test_validate_missing_prompt(self):
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'prompt'" in e for e in errors)

    @pytest.mark.parametrize("bad_prompt", [None, ["review", "this"], 42, {"a": 1}])
    def test_validate_rejects_non_string_prompt(self, bad_prompt):
        """A non-string 'prompt' must be rejected at validation.

        execute() str()-coerces prompt and dispatches it to the integration
        CLI, so a null or list prompt would otherwise send the Python repr to
        the model as instructions — silently wrong. Mirrors the shell-step
        'run' type check.
        """
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errors = step.validate({"id": "p", "prompt": bad_prompt})
        assert any("'prompt' must be a string" in e for e in errors)

    def test_validate_valid(self):
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errors = step.validate({"id": "test", "prompt": "do something"})
        assert errors == []

    def test_validate_accepts_expression_prompt(self):
        """A '{{ ... }}' expression prompt is a str, so it stays valid."""
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errors = step.validate(
            {"id": "p", "prompt": "Review {{ inputs.file }}"}
        )
        assert errors == []

    @pytest.mark.parametrize("bad", [["claude"], {"a": 1}, 5, True])
    def test_validate_rejects_non_string_integration_and_model(self, bad):
        """A non-string 'integration'/'model' must be rejected at validation.

        execute() passes 'integration' to get_integration(), which uses it as a
        dict key — an unhashable list/dict raises a raw TypeError there, even on
        a validated run — and feeds 'model' into the CLI argv."""
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errs = step.validate({"id": "p", "prompt": "hi", "integration": bad})
        assert any("'integration' must be a string" in e for e in errs), bad
        errs = step.validate({"id": "p", "prompt": "hi", "model": bad})
        assert any("'model' must be a string" in e for e in errs), bad

    def test_validate_accepts_none_and_expression_integration_model(self):
        """An explicit YAML-null (inherit default) or a '{{ ... }}' expression
        integration/model stays valid — only literal non-strings are rejected."""
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        assert step.validate(
            {"id": "p", "prompt": "hi", "integration": None, "model": None}
        ) == []
        assert step.validate(
            {
                "id": "p",
                "prompt": "hi",
                "integration": "{{ inputs.agent }}",
                "model": "{{ inputs.model }}",
            }
        ) == []

    def test_execute_non_string_integration_fails_loudly(self):
        """On an unvalidated run, an unhashable 'integration' would crash
        get_integration() (dict.get on a dict) with a raw TypeError. execute()
        must fail the step with the contract error instead."""
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        res = step.execute(
            {"id": "p", "prompt": "hi", "integration": {"a": 1}}, StepContext()
        )
        assert res.status is StepStatus.FAILED
        assert "'integration' must be a string" in (res.error or "")
        res = step.execute(
            {"id": "p", "prompt": "hi", "integration": "claude", "model": ["m"]},
            StepContext(),
        )
        assert res.status is StepStatus.FAILED
        assert "'model' must be a string" in (res.error or "")

    @pytest.mark.parametrize("falsey", [[], {}, 0, False])
    def test_execute_falsey_non_string_integration_fails_loudly(self, falsey):
        """A *falsey* non-string ([], {}, 0, False) must fail the step, not be
        swallowed by an ``or``-fallback to the workflow default.

        A ``config.get('integration') or context.default_integration`` coerces a
        falsey non-string to the default *before* the type guard runs, so with a
        configured default the step would silently dispatch using the wrong
        integration instead of surfacing the contract error. The default is set
        here so a regression dispatches rather than fails-not-possible."""
        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = PromptStep()
        ctx = StepContext(default_integration="claude", default_model="sonnet")
        res = step.execute({"id": "p", "prompt": "hi", "integration": falsey}, ctx)
        assert res.status is StepStatus.FAILED, falsey
        assert "'integration' must be a string" in (res.error or ""), falsey
        # a falsey non-string model likewise reaches the guard
        res = step.execute({"id": "p", "prompt": "hi", "model": falsey}, ctx)
        assert res.status is StepStatus.FAILED, falsey
        assert "'model' must be a string" in (res.error or ""), falsey

    @pytest.mark.parametrize(
        "bad", ["30", True, float("inf"), float("nan"), 0, -5, ["30"], None, 10**400]
    )
    def test_validate_rejects_invalid_timeout(self, bad):
        """'timeout' reaches subprocess.run(), so validate() must reject junk.

        The sibling shell step already rejects exactly these values; the
        prompt step gained a ``timeout`` without the matching guard, so a
        workflow that fails validation as a shell step passed as a prompt one.

        ``10**400`` is an int too large to convert to float: it passes
        ``isinstance``/``> 0`` but makes ``math.isfinite()`` — and later
        ``subprocess.run()`` — raise ``OverflowError``, so the guard has to
        catch that rather than let it escape as the crash it exists to stop.
        """
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        errors = step.validate(
            {"id": "p", "type": "prompt", "prompt": "hi", "timeout": bad}
        )
        assert any("'timeout' must be a positive number" in e for e in errors), (
            bad,
            errors,
        )

    @pytest.mark.parametrize("good", [300, 5, 0.5])
    def test_validate_accepts_valid_timeout(self, good):
        """A positive int/float timeout — and an absent one — stay valid."""
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        for config in (
            {"id": "p", "type": "prompt", "prompt": "hi", "timeout": good},
            {"id": "p", "type": "prompt", "prompt": "hi"},
        ):
            errors = step.validate(config)
            assert not any("'timeout'" in e for e in errors), (config, errors)

    def test_execute_fails_cleanly_on_invalid_timeout(self, monkeypatch):
        """execute() must fail the step, not raise, on an invalid timeout.

        The engine does not auto-validate step config and re-raises anything a
        step throws, so an unvalidated ``timeout`` reaching subprocess.run()
        raised a raw ``TypeError: unsupported operand type(s) for +: 'float'
        and 'str'`` (or ``ValueError`` for NaN) that aborted the entire run —
        naming neither the step nor the field — after earlier steps had
        already run their side effects.
        """
        import subprocess
        from unittest.mock import patch

        from specify_cli.workflows.step.prompt import PromptStep
        from specify_cli.workflows.base import StepContext, StepStatus

        def fail_if_called(*args, **kwargs):
            raise AssertionError("subprocess.run should not run on invalid timeout")

        monkeypatch.setattr(subprocess, "run", fail_if_called)
        step = PromptStep()
        ctx = StepContext(inputs={}, default_integration="claude")
        # A string/list raises TypeError and NaN raises ValueError inside
        # subprocess.run(); ``True`` would silently become a 1s timeout (bool
        # is an int subclass); a non-positive value reports an immediate
        # TimeoutExpired for a command that never got the time to run; an int
        # too large to convert to float raises OverflowError.
        for bad in ("30", True, float("nan"), 0, -5, ["30"], 10**400):
            with patch(
                "specify_cli.workflows.step.prompt.shutil.which",
                return_value="/opt/claude",
            ):
                result = step.execute(
                    {
                        "id": "p",
                        "type": "prompt",
                        "prompt": "hi",
                        "integration": "claude",
                        "timeout": bad,
                    },
                    ctx,
                )
            assert result.status is StepStatus.FAILED, bad
            assert "'timeout' must be a positive number" in (result.error or ""), bad

    def test_try_dispatch_threads_project_root(self):
        """PromptStep._try_dispatch must pass context.project_root to build_exec_args."""
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from specify_cli.workflows.base import StepContext
        from specify_cli.workflows.step.prompt import PromptStep

        step = PromptStep()
        ctx = StepContext(project_root="/fake/project/root", default_integration="dummy")

        mock_impl = MagicMock()
        mock_impl.key = "dummy"
        mock_impl.build_exec_args.return_value = ["dummy", "args"]
        mock_get_integration = MagicMock(return_value=mock_impl)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("specify_cli.integrations.get_integration", mock_get_integration), \
             patch("specify_cli.workflows.step.prompt.shutil.which", return_value="/opt/dummy"), \
             patch("subprocess.run", return_value=mock_result):
            step.execute(
                {"id": "p", "type": "prompt", "prompt": "hi", "integration": "dummy"},
                ctx,
            )

        mock_impl.build_exec_args.assert_called_once_with(
            "hi",
            model=None,
            output_json=False,
            project_root=Path("/fake/project/root"),
        )


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
        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext()
        config = {"id": "test", "run": "echo hello"}
        result = step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["exit_code"] == 0
        assert "hello" in result.output["stdout"]

    def test_execute_failure(self):
        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = ShellStep()
        ctx = StepContext()
        config = {"id": "test", "run": "exit 1"}
        result = step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["exit_code"] == 1
        assert result.error is not None

    def test_validate_missing_run(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'run'" in e for e in errors)

    @pytest.mark.parametrize("bad_run", [None, ["echo", "hi"], 42])
    def test_validate_rejects_non_string_run(self, bad_run):
        """A non-string 'run' must be rejected at validation.

        execute() str()-coerces run and invokes it under shell=True, so a
        null or list run would otherwise run the Python repr as a command.
        """
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        errors = step.validate({"id": "s", "run": bad_run})
        assert any("'run' must be a string" in e for e in errors)

    def test_validate_accepts_string_and_expression_run(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        assert step.validate({"id": "s", "run": "echo hi"}) == []
        assert step.validate({"id": "s", "run": "{{ steps.x.output }}"}) == []

    def test_output_format_json_exposes_data(self, tmp_path):
        from specify_cli.workflows.step.shell import ShellStep
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
        from specify_cli.workflows.step.shell import ShellStep
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
        from specify_cli.workflows.step.shell import ShellStep
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
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        errors = step.validate({"id": "emit", "run": "exit 0", "output_format": "yaml"})
        assert any("'output_format' must be 'json'" in e for e in errors)

    def test_configured_timeout_is_passed_to_subprocess(self, monkeypatch):
        """A ``timeout:`` value on the step overrides the 300s default and is
        threaded through to ``subprocess.run`` (issue #3327)."""
        import subprocess

        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        captured: dict[str, object] = {}

        def fake_run(*args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            return subprocess.CompletedProcess(
                args=args[0] if args else "", returncode=0, stdout="", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", fake_run)
        step = ShellStep()
        result = step.execute(
            {"id": "qa", "run": "echo hi", "timeout": 1800}, StepContext()
        )
        assert result.status == StepStatus.COMPLETED
        assert captured["timeout"] == 1800

    def test_default_timeout_preserved_when_omitted(self, monkeypatch):
        """Omitting ``timeout:`` preserves the historical 300s default."""
        import subprocess

        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext

        captured: dict[str, object] = {}

        def fake_run(*args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            return subprocess.CompletedProcess(
                args=args[0] if args else "", returncode=0, stdout="", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", fake_run)
        step = ShellStep()
        step.execute({"id": "qa", "run": "echo hi"}, StepContext())
        assert captured["timeout"] == 300

    def test_timeout_error_reports_configured_value(self, monkeypatch):
        """The timeout failure message reflects the configured duration, not a
        hardcoded 300."""
        import subprocess

        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="echo hi", timeout=5)

        monkeypatch.setattr(subprocess, "run", fake_run)
        step = ShellStep()
        result = step.execute(
            {"id": "qa", "run": "echo hi", "timeout": 5}, StepContext()
        )
        assert result.status == StepStatus.FAILED
        assert "5 seconds" in (result.error or "")

    def test_execute_fails_cleanly_on_invalid_timeout(self, monkeypatch):
        """execute() must fail the step (not raise) on an invalid timeout even
        when validate() was skipped — the engine does not auto-validate step
        config, so an unvalidated string/bool/non-finite timeout would
        otherwise crash subprocess.run() and take down the whole run."""
        import subprocess

        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        def fail_if_called(*args, **kwargs):
            raise AssertionError("subprocess.run should not run on invalid timeout")

        monkeypatch.setattr(subprocess, "run", fail_if_called)
        step = ShellStep()
        # A string would raise TypeError; ``True`` would silently become a 1s
        # timeout (bool is an int subclass); ``.inf`` would raise at runtime.
        for bad in ("30", True, float("inf"), 0):
            result = step.execute(
                {"id": "qa", "run": "echo hi", "timeout": bad}, StepContext()
            )
            assert result.status == StepStatus.FAILED
            assert "'timeout' must be a positive number" in (result.error or "")

    def test_validate_rejects_non_positive_timeout(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        for bad in (0, -30):
            errors = step.validate({"id": "qa", "run": "echo hi", "timeout": bad})
            assert any("'timeout' must be a positive number" in e for e in errors)

    def test_validate_rejects_non_numeric_timeout(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        # A string and a bool are both invalid (bool is an int subclass but a
        # config error, not a duration).
        for bad in ("30", True):
            errors = step.validate({"id": "qa", "run": "echo hi", "timeout": bad})
            assert any("'timeout' must be a positive number" in e for e in errors)

    def test_validate_rejects_non_finite_timeout(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        # inf/nan are floats and slip past a plain ``> 0`` check (``nan <= 0``
        # is False), but ``subprocess.run(timeout=...)`` would then fail at
        # runtime. YAML ``.inf``/``.nan`` scalars parse to these via safe_load.
        for bad in (float("inf"), float("-inf"), float("nan")):
            errors = step.validate({"id": "qa", "run": "echo hi", "timeout": bad})
            assert any("'timeout' must be a positive number" in e for e in errors)

    def test_validate_rejects_huge_int_timeout(self):
        """A too-large-to-convert int must be reported, not raise OverflowError.

        ``math.isfinite(10**400)`` raises ``OverflowError: int too large to
        convert to float``. Such a value is an ``int`` and is not a ``bool``,
        so it clears every clause before ``isfinite()`` and raises there —
        escaping ``validate()`` as the uncaught crash this guard exists to
        prevent. ``specify workflow run`` then aborts with a bare traceback
        instead of "Workflow validation failed". Both signs reach
        ``isfinite()`` because it is checked before ``timeout <= 0``.
        ``subprocess.run(timeout=...)`` raises the same OverflowError, so the
        value is genuinely invalid rather than merely unrepresentable here.
        The prompt step already catches this (PR #3847).
        """
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        for bad in (10**400, -(10**400)):
            errors = step.validate({"id": "qa", "run": "echo hi", "timeout": bad})
            assert any(
                "'timeout' must be a positive number" in e for e in errors
            ), (bad, errors)

    def test_validate_workflow_reports_huge_int_timeout(self):
        """The huge-int timeout surfaces as a validation error end to end.

        ``specify workflow run`` calls ``engine.validate()`` before executing
        any step; an OverflowError escaping the shell step's ``validate()``
        propagates out of ``validate_workflow`` and kills the command with a
        traceback, so pin the whole path, not just the helper.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition(
            {
                "schema_version": "1.0",
                "workflow": {"id": "demo", "name": "Demo", "version": "1.0.0"},
                "steps": [
                    {"id": "qa", "type": "shell", "run": "echo hi", "timeout": 10**400}
                ],
            }
        )
        errors = validate_workflow(definition)
        assert any("'timeout' must be a positive number" in e for e in errors), errors

    def test_execute_fails_cleanly_on_huge_int_timeout(self, monkeypatch):
        """execute() must fail just this step on a huge-int timeout.

        The engine does not auto-validate step config and re-raises anything a
        step throws, so on an unvalidated run the OverflowError would abort the
        whole workflow after earlier steps had already run their side effects.
        """
        import subprocess

        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext, StepStatus

        def fail_if_called(*args, **kwargs):
            raise AssertionError("subprocess.run should not run on invalid timeout")

        monkeypatch.setattr(subprocess, "run", fail_if_called)
        step = ShellStep()
        for bad in (10**400, -(10**400)):
            result = step.execute(
                {"id": "qa", "run": "echo hi", "timeout": bad}, StepContext()
            )
            assert result.status == StepStatus.FAILED, bad
            assert "'timeout' must be a positive number" in (result.error or ""), bad

    def test_validate_accepts_positive_numeric_timeout(self):
        from specify_cli.workflows.step.shell import ShellStep

        step = ShellStep()
        for good in (1, 300, 1800, 12.5):
            errors = step.validate({"id": "qa", "run": "echo hi", "timeout": good})
            assert not any("'timeout'" in e for e in errors)

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
    from specify_cli.workflows.step import gate as gate_module

    monkeypatch.setattr(gate_module, "sys", _FakeSys(tty=tty))


class TestInitStep:
    """Test the init step type."""

    def test_docstring_lists_every_valid_script_type(self):
        # The `script` field docstring must not contradict the step's own
        # VALID_SCRIPT_TYPES (which includes 'py'); validate() accepts all three.
        from specify_cli.workflows.step.init import InitStep, VALID_SCRIPT_TYPES

        for script_type in VALID_SCRIPT_TYPES:
            assert f"``{script_type}``" in InitStep.__doc__

    def test_builds_here_argv_and_bootstraps(self, tmp_path):
        from specify_cli.workflows.step.init import InitStep
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

    def test_explicit_null_ignore_agent_tools_keeps_documented_default(
        self, tmp_path
    ):
        """A bare ``ignore_agent_tools:`` must keep the documented default.

        The class docstring says "Because workflows run unattended, the step
        defaults to ``--ignore-agent-tools``" and the field docs say "defaults to
        ``true``". But ``config.get(key, True)`` applies the default only when the
        key is ABSENT — a bare ``ignore_agent_tools:`` in YAML parses to None,
        which ``_resolve_bool`` turned into False, dropping the flag and
        re-enabling the agent-CLI presence check for an unattended run.
        """
        from specify_cli.workflows.step.init import InitStep
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
                "ignore_agent_tools": None,
            },
            ctx,
        )

        assert result.status == StepStatus.COMPLETED
        assert "--ignore-agent-tools" in result.output["argv"]

    def test_explicit_false_ignore_agent_tools_is_honoured(self, tmp_path):
        """An explicit ``false`` must still opt in to the agent-CLI check."""
        from specify_cli.workflows.step.init import InitStep
        from specify_cli.workflows.base import StepContext

        step = InitStep()
        ctx = StepContext(
            project_root=str(tmp_path), default_integration="copilot"
        )
        result = step.execute(
            {
                "id": "bootstrap",
                "here": True,
                "script": "sh",
                "ignore_agent_tools": False,
            },
            ctx,
        )

        assert "--ignore-agent-tools" not in result.output["argv"]

    def test_default_integration_falls_back_to_workflow_default(self, tmp_path):
        from specify_cli.workflows.step.init import InitStep
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

    def test_default_integration_honors_env_var(self, tmp_path, monkeypatch):
        # With no step-level and no workflow-level default, the resolved
        # SPECKIT_INTEGRATION_DEFAULT value must drive both output.integration
        # and the argv passed to init (guards against reverting to the constant).
        from specify_cli.workflows.step.init import InitStep
        from specify_cli.workflows.base import StepContext, StepStatus

        monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "gemini")
        step = InitStep()
        ctx = StepContext(project_root=str(tmp_path))
        result = step.execute(
            {"id": "bootstrap", "here": True, "script": "sh"}, ctx
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["integration"] == "gemini"
        argv = result.output["argv"]
        assert "--integration" in argv and "gemini" in argv

    def test_project_name_creates_subdirectory(self, tmp_path):
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep
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
        from specify_cli.workflows.step.init import InitStep

        step = InitStep()
        errors = step.validate({"id": "bootstrap", "script": "bogus"})
        assert any("'script' must be 'sh' or 'ps'" in e for e in errors)

    def test_validate_accepts_valid(self):
        from specify_cli.workflows.step.init import InitStep

        step = InitStep()
        assert step.validate({"id": "bootstrap", "script": "sh"}) == []


class TestGateStep:
    """Test the gate step type."""

    def test_docstring_lists_every_on_reject_behaviour(self):
        # The docstring must not contradict validate()/execute(): on_reject
        # accepts 'abort', 'skip', AND 'retry' (execute() has a dedicated
        # retry -> PAUSED branch), but the summary omitted 'retry'.
        from specify_cli.workflows.step.gate import GateStep

        for behaviour in ("abort", "skip", "retry"):
            assert behaviour in GateStep.__doc__

    @pytest.fixture(autouse=True)
    def _non_tty_stdin_by_default(self, monkeypatch):
        # Default every gate test to a non-TTY stdin so none can drop into
        # the interactive prompt and block on input() when the suite runs
        # with a real TTY. Interactive tests opt back in with
        # _force_gate_stdin(monkeypatch, tty=True).
        _force_gate_stdin(monkeypatch, tty=False)

    def test_execute_returns_paused(self):
        from specify_cli.workflows.step.gate import GateStep
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

    @pytest.mark.parametrize(
        "inputs", [{}, {"spec_verdict": None}, {"spec_verdict": ""}]
    )
    def test_missing_or_empty_verdict_input_uses_existing_pause_behavior(self, inputs):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["approve", "reject"],
                "verdict_input": "spec_verdict",
            },
            StepContext(inputs=inputs),
        )
        assert result.status == StepStatus.PAUSED
        assert result.output["choice"] is None

    @pytest.mark.parametrize("inputs", [{}, {"spec_verdict": ""}])
    def test_missing_or_empty_verdict_input_prompts_on_tty(self, monkeypatch, inputs):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr(
            GateStep, "_prompt", staticmethod(lambda _message, _options: "approve")
        )
        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["approve", "reject"],
                "verdict_input": "spec_verdict",
            },
            StepContext(inputs=inputs),
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["choice"] == "approve"

    def test_verdict_input_uses_canonical_option_spelling(self):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["Approve", "Reject"],
                "verdict_input": "spec_verdict",
            },
            StepContext(inputs={"spec_verdict": "aPpRoVe"}),
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["choice"] == "Approve"

    @pytest.mark.parametrize(
        ("value", "error_fragment"),
        [(42, "must be a string"), ("maybe", "does not match")],
    )
    def test_invalid_verdict_input_value_fails(self, value, error_fragment):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["approve", "reject"],
                "verdict_input": "spec_verdict",
            },
            StepContext(inputs={"spec_verdict": value}),
        )
        assert result.status == StepStatus.FAILED
        assert error_fragment in (result.error or "")

    def test_verdict_input_fails_inside_fan_out_context(self):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the item.",
                "options": ["approve", "reject"],
                "verdict_input": "spec_verdict",
            },
            StepContext(
                inputs={"spec_verdict": "approve"},
                inside_fan_out=True,
            ),
        )

        assert result.status == StepStatus.FAILED
        assert "'verdict_input' is not supported inside fan-out" in (
            result.error or ""
        )

    @pytest.mark.parametrize(
        ("value", "error_fragment"),
        [(42, "must be a string"), ("maybe", "does not match")],
    )
    def test_failed_gate_persists_error_in_step_results(
        self, tmp_path, value, error_fragment
    ):
        """Engine persists result.error into step_results for failed gates."""
        from specify_cli.workflows.engine import WorkflowEngine

        wf_yaml = f"""
schema_version: "1.0"
workflow:
  id: "gate-error-persist"
  name: "Gate Error Persist"
  version: "1.0.0"
inputs:
  spec_verdict:
    type: {"number" if isinstance(value, int) else "string"}
    default: {value}
steps:
  - id: review
    type: gate
    message: "Review the spec."
    options: [approve, reject]
    on_reject: abort
    verdict_input: spec_verdict
"""
        wf_path = tmp_path / "wf.yml"
        wf_path.write_text(wf_yaml, encoding="utf-8")
        (tmp_path / ".specify").mkdir()
        engine = WorkflowEngine(tmp_path)
        definition = engine.load_workflow(str(wf_path))
        state = engine.execute(definition, {})
        assert state.status.value == "failed"
        step_data = state.step_results["review"]
        assert step_data["status"] == "failed"
        assert error_fragment in (step_data.get("error") or "")

    @pytest.mark.parametrize("invalid_value", ["", 42, None])
    def test_validate_invalid_verdict_input(self, invalid_value):
        from specify_cli.workflows.step.gate import GateStep

        errors = GateStep().validate({
            "id": "review",
            "message": "Review the spec.",
            "verdict_input": invalid_value,
        })
        assert any("verdict_input" in error for error in errors)

    @pytest.mark.parametrize(
        ("on_reject", "status", "aborted"),
        [
            ("abort", "failed", True),
            ("skip", "completed", False),
            ("retry", "paused", False),
        ],
    )
    def test_reject_verdict_input_preserves_reject_behavior(
        self, on_reject, status, aborted
    ):
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext

        context = StepContext(inputs={"spec_verdict": "reject"})
        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["approve", "reject"],
                "on_reject": on_reject,
                "verdict_input": "spec_verdict",
            },
            context,
        )
        assert result.status.value == status
        assert result.output.get("aborted", False) is aborted
        assert context.inputs["spec_verdict"] == (
            "" if on_reject == "retry" else "reject"
        )

    def test_validate_missing_message(self):
        from specify_cli.workflows.step.gate import GateStep

        step = GateStep()
        errors = step.validate({"id": "test", "options": ["approve"]})
        assert any("missing 'message'" in e for e in errors)

    def test_validate_invalid_on_reject(self):
        from specify_cli.workflows.step.gate import GateStep

        step = GateStep()
        errors = step.validate({
            "id": "test",
            "message": "Review",
            "on_reject": "invalid",
        })
        assert any("on_reject" in e for e in errors)

    @pytest.mark.parametrize(
        "bad_on_reject", ["Abort", "fail", "stop", "SKIP", None, 5, ["abort"]]
    )
    def test_execute_invalid_on_reject_fails_loudly(self, bad_on_reject):
        """An unrecognised ``on_reject`` must not silently complete a rejection.

        ``validate`` rejects anything outside abort/skip/retry, but the engine
        does not auto-validate before ``execute``. The reject branch handles only
        "abort" and "retry", then falls through to its ``"skip"`` case — so a
        REJECTED gate reported COMPLETED and the run continued past the review
        the gate exists to enforce. Reachable by a capitalisation slip, a guessed
        verb, a non-string, or a bare ``on_reject:`` (which yields None, since
        ``config.get(k, default)`` does not replace an explicit null).
        """
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        result = GateStep().execute(
            {
                "id": "review",
                "message": "Review the spec.",
                "options": ["approve", "reject"],
                "on_reject": bad_on_reject,
                "verdict_input": "spec_verdict",
            },
            StepContext(inputs={"spec_verdict": "reject"}),
        )
        assert result.status == StepStatus.FAILED
        assert "'on_reject' must be" in (result.error or "")

    def test_validate_non_string_options_does_not_raise(self):
        """Non-string options with on_reject=abort/retry must be REPORTED as an
        error, not crash: the reject-choice check calls o.lower() on each option,
        which previously raised AttributeError on a non-string option and broke
        validate_workflow's 'return errors, never raise' contract."""
        from specify_cli.workflows.step.gate import GateStep

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
        from specify_cli.workflows.step.gate import GateStep
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

    def test_interactive_prompt_rejects_non_decimal_digit(self, monkeypatch, capsys):
        """A Unicode digit int() can't parse — e.g. the superscript '²', which
        str.isdigit() accepts but int() rejects — must be treated as an invalid
        choice, not crash the prompt loop with an uncaught ValueError."""
        from specify_cli.workflows.step.gate import GateStep

        _force_gate_stdin(monkeypatch, tty=True)
        inputs = iter(["²", "1"])  # superscript-two, then a real "1"
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        choice = GateStep._prompt("Review the spec.", ["approve", "reject"])
        assert choice == "approve"

    def test_interactive_prompt_missing_show_file_does_not_crash(
        self, tmp_path, monkeypatch, capsys
    ):
        from specify_cli.workflows.step.gate import GateStep
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
        from specify_cli.workflows.step.gate import GateStep
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
        from specify_cli.workflows.step.gate import GateStep

        empty = tmp_path / "empty.md"
        empty.write_text("", encoding="utf-8")
        assert GateStep._read_show_file(str(empty)) == ["(file is empty)"]

    def test_read_show_file_truncates_large_file(self, tmp_path):
        from specify_cli.workflows.step.gate import GateStep

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
        from specify_cli.workflows.step.gate import GateStep

        # An embedded NUL byte makes the OS reject the path with ValueError
        # before any I/O; it must degrade to a notice, not crash the prompt.
        rendered = GateStep._read_show_file("bad\x00path.md")
        assert len(rendered) == 1
        assert rendered[0].startswith("(could not read file:")

    def test_read_show_file_strips_control_chars(self, tmp_path):
        from specify_cli.workflows.step.gate import GateStep

        # A file with ANSI/control bytes must not inject escapes into the
        # terminal; ESC and other C0 controls are stripped, tab is kept.
        f = tmp_path / "ansi.md"
        f.write_text("a\x1b[2Jb\tc\x07d\n", encoding="utf-8")
        rendered = GateStep._read_show_file(str(f))
        assert rendered == ["a[2Jb\tcd"]
        assert "\x1b" not in rendered[0] and "\x07" not in rendered[0]

    def test_compose_prompt_sanitizes_show_file_path(self):
        from specify_cli.workflows.step.gate import GateStep

        # The displayed path header (and the read-error notice it produces)
        # must not carry escapes even when the path string itself contains
        # control characters — ESC, LF, and C1 CSI (\x9b); the file is still
        # opened with the raw value.
        out = GateStep._compose_prompt("Review.", "ev\x1bil\x9b[2J\npath.md")
        assert "\x1b" not in out and "\x9b" not in out
        assert "evil[2Jpath.md:" in out

    def test_interactive_non_string_message_renders(self, monkeypatch, capsys):
        from specify_cli.workflows.step.gate import GateStep
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
        from specify_cli.workflows.step.gate import GateStep
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

    @pytest.mark.parametrize(
        "bad_options",
        [5, {"a": "approve"}, None, [], "approve"],
    )
    def test_execute_non_list_options_fails_cleanly(self, monkeypatch, bad_options):
        """A malformed ``options`` must FAIL the step, not crash the run.

        ``validate`` rejects a non-list/empty ``options``, but the engine does
        not auto-validate before ``execute``. On an interactive run a scalar/
        dict/None ``options`` would otherwise reach ``_prompt`` and raise a raw
        ``TypeError`` (``enumerate``/``len`` on a non-iterable) or ``KeyError``
        (indexing a dict), crashing the whole workflow. Mirrors the switch
        'cases' and command 'input' unvalidated-execute guards."""
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        # Force an interactive TTY so the crash-prone _prompt path is reached;
        # input() is stubbed so a (buggy) fall-through can't block the suite.
        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

        step = GateStep()
        config = {"id": "review", "message": "Review.", "options": bad_options}
        result = step.execute(config, StepContext())

        assert result.status == StepStatus.FAILED
        assert "options" in (result.error or "")
        assert result.output["choice"] is None

    def test_execute_non_string_options_element_fails_cleanly(self, monkeypatch):
        """A non-string option element must FAIL the step, not crash.

        A non-empty list with a non-string element passes the shape check but
        would reach the reject test ``choice.lower()`` and raise a raw
        ``AttributeError`` at run time. ``validate`` reports "must be strings";
        ``execute`` must fail cleanly on an unvalidated run too."""
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

        step = GateStep()
        config = {"id": "review", "message": "Review.", "options": [123, 456]}
        result = step.execute(config, StepContext())

        assert result.status == StepStatus.FAILED
        assert "options" in (result.error or "")

    def test_execute_non_list_options_fails_in_non_tty_too(self):
        """The guard runs before the non-TTY PAUSE short-circuit.

        A malformed ``options`` should surface as FAILED in CI (non-TTY) rather
        than PAUSING and only crashing later when an operator resumes on a real
        terminal."""
        from specify_cli.workflows.step.gate import GateStep
        from specify_cli.workflows.base import StepContext, StepStatus

        # Autouse fixture already forces non-TTY stdin.
        step = GateStep()
        config = {"id": "review", "message": "Review.", "options": 5}
        result = step.execute(config, StepContext())

        assert result.status == StepStatus.FAILED
        assert "options" in (result.error or "")


class TestIfThenStep:
    """Test the if/then/else step type."""

    def test_execute_then_branch(self):
        from specify_cli.workflows.step.if_then import IfThenStep
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
        from specify_cli.workflows.step.if_then import IfThenStep
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
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate({"id": "test", "then": []})
        assert any("missing 'condition'" in e for e in errors)

    @pytest.mark.parametrize("bad", [["a", "b"], {"k": "v"}, 5, 1.5])
    def test_validate_rejects_non_string_non_bool_condition(self, bad):
        # A list/dict/number condition is returned unchanged by
        # evaluate_expression, and evaluate_condition then bool()-coerces it, so
        # it silently resolves to its truthiness (e.g. [1, 2] is always True)
        # instead of erroring on the authoring mistake.
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate({"id": "test", "condition": bad, "then": []})
        assert any("'condition' must be a" in e for e in errors), bad

    @pytest.mark.parametrize(
        "good",
        [
            "true", "false", "{{ inputs.flag }}",
            True, False,  # unquoted YAML bool: resolved exactly, and it is the
                          # default this step itself uses -- must stay valid
        ],
    )
    def test_validate_accepts_string_or_bool_condition(self, good):
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate({"id": "test", "condition": good, "then": []})
        assert not any("'condition' must be a" in e for e in errors), good

    @pytest.mark.parametrize("bad_branch", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_then_fails_loudly(self, bad_branch):
        """A non-list ``then`` must fail the step, not crash the run.

        ``validate`` rejects a non-list ``then``, but the engine does not
        auto-validate (see ``WorkflowEngine.load_workflow``) and feeds
        ``next_steps`` straight into ``_execute_steps``, which iterates them as
        step mappings. Before the guard, a non-list ``then`` (a single mapping
        or scalar authoring mistake) was iterated element-wise and raised
        AttributeError on ``.get()``, taking down the whole run. Mirrors the
        switch/fan-out non-list handling.
        """
        from specify_cli.workflows.step.if_then import IfThenStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = IfThenStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "branch", "condition": "true", "then": bad_branch}, ctx
        )
        assert result.status == StepStatus.FAILED
        assert "'then' must be a list of steps" in (result.error or "")
        assert result.next_steps == []

    @pytest.mark.parametrize("bad_branch", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_else_fails_loudly(self, bad_branch):
        """A non-list ``else`` selected at runtime must fail the step, not crash.

        Same asymmetry as ``then``: the ``else`` branch is only reached when the
        condition is false, so a non-list ``else`` reaches ``next_steps`` and
        would crash the engine's step iteration on an unvalidated run.
        """
        from specify_cli.workflows.step.if_then import IfThenStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = IfThenStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "branch", "condition": "false", "then": [], "else": bad_branch},
            ctx,
        )
        assert result.status == StepStatus.FAILED
        assert "'else' must be a list of steps" in (result.error or "")
        assert result.next_steps == []

    def test_execute_none_else_stays_empty(self):
        """An explicit ``else: null`` selected at runtime stays an empty branch.

        ``validate`` deliberately accepts ``else: None``; the execute guard must
        normalize it to an empty branch (COMPLETED) rather than failing a
        validator-approved workflow when the condition is false.
        """
        from specify_cli.workflows.step.if_then import IfThenStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = IfThenStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "branch", "condition": "false", "then": [], "else": None}, ctx
        )
        assert result.status == StepStatus.COMPLETED
        assert result.next_steps == []

    @pytest.mark.parametrize("bad_else", [False, 0, "", {}, 42])
    def test_validate_rejects_non_list_else(self, bad_else):
        """A non-list 'else' must be rejected even when it is falsy.

        The original guard used ``if else_branch and ...`` which
        short-circuits for falsy non-list values (False/0/''/{}), letting a
        malformed else-branch pass validation only to be silently skipped at
        runtime. ``then`` is already strictly validated; ``else`` must match.
        """
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate(
            {"id": "i", "condition": "true", "then": [], "else": bad_else}
        )
        assert any("'else' must be a list of steps" in e for e in errors)

    @pytest.mark.parametrize("ok_else", [None, [], [{"id": "x", "command": "/y"}]])
    def test_validate_accepts_valid_else(self, ok_else):
        """An explicit 'else' of None or a list stays valid.

        ``else`` is set explicitly here (including ``else: None``) so the
        explicit-None case is exercised, not just the missing-key case.
        """
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate(
            {"id": "i", "condition": "true", "then": [], "else": ok_else}
        )
        assert not any("'else'" in e for e in errors)

    def test_validate_accepts_missing_else(self):
        """A missing 'else' key stays valid (no else branch)."""
        from specify_cli.workflows.step.if_then import IfThenStep

        step = IfThenStep()
        errors = step.validate({"id": "i", "condition": "true", "then": []})
        assert not any("'else'" in e for e in errors)


class TestSwitchStep:
    """Test the switch step type."""

    def test_execute_matches_case_ignoring_surrounding_whitespace(self):
        """A shell step's stdout keeps its trailing newline; the case must match.

        `ShellStep` stores `proc.stdout` verbatim, so `run: echo approve`
        resolves to "approve" plus a newline. Unstripped, that matched no
        `approve:` case and the switch silently fell through to `default:`
        while still reporting COMPLETED. There is no `trim` filter, so a
        workflow author cannot strip it themselves.
        """
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext, StepStatus

        config = {
            "id": "route",
            "expression": "{{ steps.check.output.stdout }}",
            "cases": {
                "approve": [{"id": "approved", "type": "command", "command": "echo"}],
                "reject": [{"id": "rejected", "type": "command", "command": "echo"}],
            },
            "default": [{"id": "fallback", "type": "command", "command": "echo"}],
        }
        for raw in ("approve\n", "approve\r\n", "  approve  ", "approve"):
            ctx = StepContext(steps={"check": {"output": {"stdout": raw}}})
            result = SwitchStep().execute(config, ctx)
            assert result.status == StepStatus.COMPLETED
            assert result.output["matched_case"] == "approve", repr(raw)
            assert [s["id"] for s in result.next_steps] == ["approved"], repr(raw)
            # The raw value is still reported unchanged.
            assert result.output["expression_value"] == raw

    def test_execute_still_falls_through_for_a_genuine_mismatch(self):
        """Stripping must not make unrelated values match."""
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext

        config = {
            "id": "route",
            "expression": "{{ steps.check.output.stdout }}",
            "cases": {
                "approve": [{"id": "approved", "type": "command", "command": "echo"}]
            },
            "default": [{"id": "fallback", "type": "command", "command": "echo"}],
        }
        ctx = StepContext(steps={"check": {"output": {"stdout": "approve-later\n"}}})
        result = SwitchStep().execute(config, ctx)

        assert result.output["matched_case"] == "__default__"
        assert [s["id"] for s in result.next_steps] == ["fallback"]

    def test_execute_matches_case(self):
        from specify_cli.workflows.step.switch import SwitchStep
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
        from specify_cli.workflows.step.switch import SwitchStep
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
        from specify_cli.workflows.step.switch import SwitchStep
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

    def test_execute_non_dict_cases_fails_loudly(self):
        """A non-mapping ``cases`` must fail the step, not crash the run.

        ``validate`` rejects a non-dict ``cases``, but the engine's
        ``execute()`` does not auto-validate (see ``WorkflowEngine.load_workflow``
        docstring). Before the guard, ``execute`` called ``cases.items()`` on the
        raw value, so an unvalidated run with a list/scalar ``cases`` raised
        AttributeError and took down the whole run instead of failing this step.
        Mirrors the fan-out step's non-list ``items`` handling.
        """
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = SwitchStep()
        ctx = StepContext(steps={"review": {"output": {"choice": "approve"}}})
        for bad_cases in (["approve"], "approve", 5):
            result = step.execute(
                {
                    "id": "route",
                    "expression": "{{ steps.review.output.choice }}",
                    "cases": bad_cases,
                },
                ctx,
            )
            assert result.status == StepStatus.FAILED
            assert "'cases' must be a mapping" in (result.error or "")
            # expression is still evaluated, so its value is surfaced for context.
            assert result.output["expression_value"] == "approve"

    @pytest.mark.parametrize("bad_branch", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_matched_case_fails_loudly(self, bad_branch):
        """A matched case with a non-list body must fail the step, not crash.

        ``validate`` rejects a non-list case body, but the engine does not
        auto-validate (see ``WorkflowEngine.load_workflow``) and feeds the
        selected branch straight into ``_execute_steps``, which iterates it as
        step mappings. A non-list body (a single mapping or scalar authoring
        mistake) would be iterated element-wise and raise AttributeError on
        ``.get()``, taking down the whole run. Mirrors the non-mapping
        ``cases`` guard.
        """
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = SwitchStep()
        ctx = StepContext(steps={"review": {"output": {"choice": "approve"}}})
        result = step.execute(
            {
                "id": "route",
                "expression": "{{ steps.review.output.choice }}",
                "cases": {"approve": bad_branch},
            },
            ctx,
        )
        assert result.status == StepStatus.FAILED
        assert "case 'approve' must be a list of steps" in (result.error or "")
        assert result.next_steps == []
        # expression is still evaluated, so its value is surfaced for context.
        assert result.output["expression_value"] == "approve"

    @pytest.mark.parametrize("bad_branch", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_default_fails_loudly(self, bad_branch):
        """A non-list ``default`` reached at runtime must fail, not crash.

        Same asymmetry as the case body: ``default`` is only selected when no
        case matches, so a non-list ``default`` reaches ``next_steps`` and would
        crash the engine's step iteration on an unvalidated run.
        """
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = SwitchStep()
        ctx = StepContext(steps={"review": {"output": {"choice": "other"}}})
        result = step.execute(
            {
                "id": "route",
                "expression": "{{ steps.review.output.choice }}",
                "cases": {"approve": [{"id": "plan", "command": "speckit.plan"}]},
                "default": bad_branch,
            },
            ctx,
        )
        assert result.status == StepStatus.FAILED
        assert "'default' must be a list of steps" in (result.error or "")
        assert result.next_steps == []
        # expression is still evaluated, so its value is surfaced for context.
        assert result.output["expression_value"] == "other"

    @pytest.mark.parametrize("ok_default", [None, [], [{"id": "x", "command": "/y"}]])
    def test_execute_none_default_stays_empty(self, ok_default):
        """An explicit ``default: null`` or a list default stays valid.

        ``validate`` deliberately accepts ``default: None``; the execute guard
        must normalize it to an empty branch (COMPLETED) rather than failing a
        validator-approved workflow.
        """
        from specify_cli.workflows.step.switch import SwitchStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = SwitchStep()
        ctx = StepContext(steps={"review": {"output": {"choice": "other"}}})
        result = step.execute(
            {
                "id": "route",
                "expression": "{{ steps.review.output.choice }}",
                "cases": {"approve": [{"id": "plan", "command": "speckit.plan"}]},
                "default": ok_default,
            },
            ctx,
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["matched_case"] == "__default__"
        assert result.next_steps == (ok_default or [])

    def test_validate_missing_expression(self):
        from specify_cli.workflows.step.switch import SwitchStep

        step = SwitchStep()
        errors = step.validate({"id": "test", "cases": {}})
        assert any("missing 'expression'" in e for e in errors)

    def test_validate_missing_cases(self):
        """`cases` is the switch's branch payload and must be required.

        Every other control-flow step requires its own: `if` requires `then`,
        `fan-out` requires `items` and `step`, `fan-in` a non-empty `wait_for`,
        `gate` a `message`. Without it, a `case:` typo validated clean and then
        reported COMPLETED with `matched_case: "__default__"` having dispatched
        nothing.
        """
        from specify_cli.workflows.step.switch import SwitchStep

        step = SwitchStep()

        # Absent entirely.
        errors = step.validate({"id": "route", "expression": "{{ inputs.x }}"})
        assert any("missing 'cases'" in e for e in errors), errors

        # The realistic slip: `case:` instead of `cases:`.
        errors = step.validate(
            {"id": "route", "expression": "{{ inputs.x }}", "case": {"a": []}}
        )
        assert any("missing 'cases'" in e for e in errors), errors

    def test_validate_accepts_an_empty_cases_mapping(self):
        """An explicitly declared but empty `cases:` is still a declaration."""
        from specify_cli.workflows.step.switch import SwitchStep

        errors = SwitchStep().validate(
            {"id": "route", "expression": "{{ inputs.x }}", "cases": {}}
        )
        assert not any("missing 'cases'" in e for e in errors), errors

    def test_validate_invalid_cases_and_default(self):
        from specify_cli.workflows.step.switch import SwitchStep

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
        from specify_cli.workflows.step.while_loop import WhileStep
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
        from specify_cli.workflows.step.while_loop import WhileStep
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

    @pytest.mark.parametrize("bad_steps", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_steps_fails_loudly(self, bad_steps):
        """A non-list ``steps`` reached at runtime must fail the step, not crash.

        ``validate`` rejects a non-list ``steps``, but the engine does not
        auto-validate (see ``WorkflowEngine.load_workflow``) and feeds
        ``next_steps`` straight into ``_execute_steps``, which iterates them as
        step mappings. The while body only dispatches when the condition is
        truthy, so a non-list ``steps`` reaches ``next_steps`` and would crash
        the engine's step iteration on an unvalidated run. Mirrors the
        if/switch/fan-out non-list handling.
        """
        from specify_cli.workflows.step.while_loop import WhileStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = WhileStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "retry", "condition": "true", "steps": bad_steps}, ctx
        )
        assert result.status == StepStatus.FAILED
        assert "'steps' must be a list of steps" in (result.error or "")
        assert result.next_steps == []

    @pytest.mark.parametrize("bad_steps", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_steps_ok_when_condition_false(self, bad_steps):
        """A false condition never dispatches the body, so a non-list ``steps``
        stays benign — the step completes without touching ``next_steps``.
        """
        from specify_cli.workflows.step.while_loop import WhileStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = WhileStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "retry", "condition": "false", "steps": bad_steps}, ctx
        )
        assert result.status == StepStatus.COMPLETED
        assert result.output["condition_result"] is False
        assert result.next_steps == []

    def test_validate_missing_fields(self):
        from specify_cli.workflows.step.while_loop import WhileStep

        step = WhileStep()
        errors = step.validate({"id": "test", "steps": []})
        assert any("missing 'condition'" in e for e in errors)
        # max_iterations is optional (defaults to 10)

    def test_validate_requires_steps_body(self):
        """A while loop with no body must be rejected, not silently a no-op.

        Without this, ``step:`` written instead of ``steps:`` -- an easy slip,
        since fan-out's payload key really is the singular ``step:`` -- passed
        ``specify workflow validate`` with zero errors, and then reported
        COMPLETED at run time while returning no ``next_steps``, so the loop
        never ran even once.
        """
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.while_loop import WhileStep

        step = WhileStep()
        config = {
            "id": "retry",
            "condition": "true",
            # The mistype: singular 'step' instead of 'steps'.
            "step": {"id": "x", "type": "command", "command": "echo"},
        }
        errors = step.validate(config)
        assert errors == ["While step 'retry' is missing 'steps' field."], errors

        # Demonstrates why it matters: execution is a silent no-op.
        result = step.execute(config, StepContext())
        assert result.status == StepStatus.COMPLETED
        assert result.next_steps == []

    @pytest.mark.parametrize("bad", [["a", "b"], {"k": "v"}, 5, 1.5])
    def test_validate_rejects_non_string_non_bool_condition(self, bad):
        from specify_cli.workflows.step.while_loop import WhileStep

        step = WhileStep()
        errors = step.validate({"id": "test", "condition": bad, "steps": []})
        assert any("'condition' must be a" in e for e in errors), bad

    @pytest.mark.parametrize("good", [True, False, "true", "{{ inputs.go }}"])
    def test_validate_accepts_string_or_bool_condition(self, good):
        # ``condition: false`` unquoted is idiomatic YAML and is this step's own
        # default, so a literal bool must not be rejected.
        from specify_cli.workflows.step.while_loop import WhileStep

        step = WhileStep()
        errors = step.validate({"id": "test", "condition": good, "steps": []})
        assert not any("'condition' must be a" in e for e in errors), good

    def test_validate_invalid_max_iterations(self):
        from specify_cli.workflows.step.while_loop import WhileStep

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
        from specify_cli.workflows.step.do_while import DoWhileStep
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
        from specify_cli.workflows.step.do_while import DoWhileStep
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
        from specify_cli.workflows.step.do_while import DoWhileStep

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
        from specify_cli.workflows.step.do_while import DoWhileStep
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

    @pytest.mark.parametrize("bad_steps", [{"id": "x"}, "oops", 5])
    def test_execute_non_list_steps_fails_loudly(self, bad_steps):
        """A non-list ``steps`` must fail the step, not crash the run.

        ``validate`` rejects a non-list ``steps``, but the engine does not
        auto-validate (see ``WorkflowEngine.load_workflow``) and feeds
        ``next_steps`` straight into ``_execute_steps``, which iterates them as
        step mappings. The do-while body always dispatches on the first call
        regardless of condition, so a non-list ``steps`` always reaches
        ``next_steps`` and would crash the engine's step iteration on an
        unvalidated run. Mirrors the if/switch/fan-out non-list handling.
        """
        from specify_cli.workflows.step.do_while import DoWhileStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = DoWhileStep()
        ctx = StepContext(inputs={})
        result = step.execute(
            {"id": "cycle", "condition": "false", "steps": bad_steps}, ctx
        )
        assert result.status == StepStatus.FAILED
        assert "'steps' must be a list of steps" in (result.error or "")
        assert result.next_steps == []

    def test_validate_missing_fields(self):
        from specify_cli.workflows.step.do_while import DoWhileStep

        step = DoWhileStep()
        errors = step.validate({"id": "test", "steps": []})
        assert any("missing 'condition'" in e for e in errors)
        # max_iterations is optional (defaults to 10)

    def test_validate_requires_steps_body(self):
        """A do-while with no body must be rejected, not silently a no-op.

        The step's own docstring promises "The first invocation always returns
        the nested steps for execution" -- with no body it validated clean and
        then returned none, so the loop never ran even once.
        """
        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.do_while import DoWhileStep

        step = DoWhileStep()
        config = {"id": "refine", "condition": "true", "max_iterations": 3}
        errors = step.validate(config)
        assert errors == ["Do-while step 'refine' is missing 'steps' field."], errors

        result = step.execute(config, StepContext())
        assert result.status == StepStatus.COMPLETED
        assert result.next_steps == []

    @pytest.mark.parametrize("bad", [["a", "b"], {"k": "v"}, 5, 1.5])
    def test_validate_rejects_non_string_non_bool_condition(self, bad):
        from specify_cli.workflows.step.do_while import DoWhileStep

        step = DoWhileStep()
        errors = step.validate({"id": "test", "condition": bad, "steps": []})
        assert any("'condition' must be a" in e for e in errors), bad

    @pytest.mark.parametrize("good", [True, False, "true", "{{ inputs.go }}"])
    def test_validate_accepts_string_or_bool_condition(self, good):
        # ``condition: false`` unquoted is idiomatic YAML; evaluate_condition
        # resolves a literal bool exactly, so it must not be rejected.
        from specify_cli.workflows.step.do_while import DoWhileStep

        step = DoWhileStep()
        errors = step.validate({"id": "test", "condition": good, "steps": []})
        assert not any("'condition' must be a" in e for e in errors), good

    def test_validate_steps_not_list(self):
        from specify_cli.workflows.step.do_while import DoWhileStep

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
        from specify_cli.workflows.step.fan_out import FanOutStep
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
        from specify_cli.workflows.step.fan_out import FanOutStep
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
        from specify_cli.workflows.step.fan_out import FanOutStep
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

    def test_execute_non_dict_step_fails_loudly(self):
        """A truthy non-mapping ``step`` must fail the step, not crash the run.

        ``validate`` rejects a non-dict ``step``, but the engine's ``execute()``
        does not auto-validate (see ``WorkflowEngine.load_workflow``). On a
        COMPLETED fan-out the engine reads ``step_template`` back out and, when
        it is truthy, calls ``template.get("id", ...)`` in ``_run_fan_out``. A
        truthy non-mapping ``step`` (a scalar or list authoring mistake) raised
        AttributeError there and took down the whole run. Mirrors the fan-out
        non-list ``items`` guard and the switch non-dict ``cases`` guard.
        """
        from specify_cli.workflows.step.fan_out import FanOutStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanOutStep()
        ctx = StepContext(steps={"tasks": {"output": {"task_list": [1, 2]}}})
        # ``None`` is an explicit ``step: null``: ``config.get("step", {})`` only
        # substitutes the default for an *absent* key, so it reaches the guard
        # and must fail here too — matching ``validate``.
        for bad_step in (["impl"], "impl", 5, None):
            result = step.execute(
                {
                    "id": "parallel",
                    "items": "{{ steps.tasks.output.task_list }}",
                    "step": bad_step,
                },
                ctx,
            )
            assert result.status == StepStatus.FAILED
            assert "'step' must be a" in (result.error or "")
            assert result.output["item_count"] == 0
            assert result.output["step_template"] == {}

    def test_validate_missing_fields(self):
        from specify_cli.workflows.step.fan_out import FanOutStep

        step = FanOutStep()
        errors = step.validate({"id": "test"})
        assert any("missing 'items'" in e for e in errors)
        assert any("missing 'step'" in e for e in errors)

    def test_validate_step_not_mapping(self):
        from specify_cli.workflows.step.fan_out import FanOutStep

        step = FanOutStep()
        for bad_step in ("not-a-dict", ["impl"], 5, None):
            errors = step.validate({
                "id": "test",
                "items": "{{ x }}",
                "step": bad_step,
            })
            assert any("'step' must be a mapping" in e for e in errors), bad_step


class TestFanInStep:
    """Test the fan-in step type."""

    def test_execute_collects_results(self):
        from specify_cli.workflows.step.fan_in import FanInStep
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
        from specify_cli.workflows.step.fan_in import FanInStep
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
        from specify_cli.workflows.step.fan_in import FanInStep
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

    @pytest.mark.parametrize("bad_wait_for", ["stepA", 5, None, {"a": 1}])
    def test_execute_non_list_wait_for_fails_loudly(self, bad_wait_for):
        """A non-list ``wait_for`` must fail the step, not crash the run or
        silently produce a bogus join.

        ``validate`` rejects a non-list ``wait_for``, but the engine's
        ``execute()`` does not auto-validate. Before the guard, ``execute``
        iterated the raw value: a scalar (int/None) raised TypeError and took
        down the whole run, while a string silently iterated its characters and
        returned a join of empty results with a COMPLETED status — the exact
        "silent empty result + COMPLETED" wiring bug the engine's fan-in
        validation warns against. Mirrors the fan-out non-list ``items`` guard.
        """
        from specify_cli.workflows.step.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanInStep()
        ctx = StepContext(steps={"a": {"output": {"x": 1}}})
        result = step.execute({"id": "collect", "wait_for": bad_wait_for}, ctx)
        assert result.status == StepStatus.FAILED
        assert "'wait_for' must be a list" in (result.error or "")
        assert result.output["results"] == []

    @pytest.mark.parametrize(
        "bad_output", [[], False, 0, "", ["a"], "oops", 5]
    )
    def test_execute_non_mapping_output_fails_loudly(self, bad_output):
        """A non-mapping ``output`` must fail the step, not drop every key.

        ``validate`` rejects it and says why: "execute() silently coerces a
        non-mapping output to {}, so the author's declared aggregation keys would
        vanish with no error." The engine does not auto-validate before
        ``execute``, so that is exactly what happened — and ``x or {}`` masked
        the falsy shapes (``[]``, ``false``, ``0``, ``''``) before the isinstance
        check even ran. The step still returned COMPLETED, so downstream
        ``steps.<id>.output.<key>`` resolved to None and interpolated as "".
        """
        from specify_cli.workflows.step.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanInStep()
        ctx = StepContext(steps={"a": {"output": {"x": 1}}})
        result = step.execute(
            {"id": "collect", "wait_for": ["a"], "output": bad_output}, ctx
        )
        assert result.status == StepStatus.FAILED
        assert "'output' must be a mapping" in (result.error or "")
        assert result.output["results"] == []

    def test_execute_explicit_null_output_stays_valid(self):
        """An explicit ``output:`` (YAML null) is valid, matching ``validate``."""
        from specify_cli.workflows.step.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanInStep()
        ctx = StepContext(steps={"a": {"output": {"x": 1}}})
        result = step.execute(
            {"id": "collect", "wait_for": ["a"], "output": None}, ctx
        )
        assert result.status == StepStatus.COMPLETED

    @pytest.mark.parametrize("bad_entry", [["a", "b"], {"a": 1}, 123, None])
    def test_execute_non_string_wait_for_entry_fails_loudly(self, bad_entry):
        """A ``wait_for`` list with a non-string entry must fail the step, not
        crash the run or silently produce a bogus join.

        The whole-list guard (``test_execute_non_list_wait_for_fails_loudly``)
        and the engine's fan-in validation both already reject the list *shape*,
        but neither the step's ``execute`` nor the engine's runtime path guarded
        the list's *elements*. On an unvalidated run an unhashable entry
        (a list/dict from a YAML indentation slip like ``wait_for: [[a, b]]``)
        crashed ``context.steps.get(entry, ...)`` with a raw TypeError, while a
        hashable-but-non-string entry (``wait_for: [123]``) silently joined an
        empty ``{}`` and still reported COMPLETED — the same wiring bug the
        list-shape guard exists to prevent. Mirrors the engine's
        ``test_non_string_wait_for_entry_is_rejected`` load-time check.
        """
        from specify_cli.workflows.step.fan_in import FanInStep
        from specify_cli.workflows.base import StepContext, StepStatus

        step = FanInStep()
        ctx = StepContext(steps={"a": {"output": {"x": 1}}})
        # A valid entry alongside the bad one proves it is the entry, not the
        # list, that is rejected.
        result = step.execute({"id": "collect", "wait_for": ["a", bad_entry]}, ctx)
        assert result.status == StepStatus.FAILED
        assert "'wait_for' entries must be step-id strings" in (result.error or "")
        assert result.output["results"] == []

    def test_validate_empty_wait_for(self):
        from specify_cli.workflows.step.fan_in import FanInStep

        step = FanInStep()
        errors = step.validate({"id": "test", "wait_for": []})
        assert any("non-empty list" in e for e in errors)

    def test_validate_wait_for_not_list(self):
        from specify_cli.workflows.step.fan_in import FanInStep

        step = FanInStep()
        errors = step.validate({"id": "test", "wait_for": "not-a-list"})
        assert any("non-empty list" in e for e in errors)

    @pytest.mark.parametrize("bad_output", [["{{ fan_in.results }}"], "{{ x }}", 42])
    def test_validate_rejects_non_mapping_output(self, bad_output):
        """A non-mapping 'output' must be rejected: execute() would otherwise
        silently coerce it to {} and drop the declared aggregation keys."""
        from specify_cli.workflows.step.fan_in import FanInStep

        step = FanInStep()
        errors = step.validate(
            {"id": "j", "wait_for": ["a"], "output": bad_output}
        )
        assert any("'output' must be a mapping" in e for e in errors)

    def test_validate_accepts_mapping_or_absent_output(self):
        from specify_cli.workflows.step.fan_in import FanInStep

        step = FanInStep()
        assert step.validate(
            {"id": "j", "wait_for": ["a"], "output": {"joined": "{{ x }}"}}
        ) == []
        assert step.validate({"id": "j", "wait_for": ["a"]}) == []


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

    @pytest.mark.parametrize(
        "bad", [0, -1, None, "abc", 1.0, float("inf"), float("nan")]
    )
    def test_invalid_max_concurrency_coerces_to_sequential(self, tmp_path, bad):
        # float("inf") -> int() raises OverflowError (not TypeError/ValueError);
        # it must fall back to sequential like any other uncoercible value, not
        # crash the run.
        results, _ = self._run(tmp_path, list(range(4)), bad)
        assert results == [{"seen": i} for i in range(4)]

    def test_string_max_concurrency_is_honored(self, tmp_path):
        results, _ = self._run(tmp_path, list(range(4)), "2")
        assert results == [{"seen": i} for i in range(4)]

    def test_context_item_isolation_across_threads(self, tmp_path):
        items = [{"id": f"x{i}"} for i in range(6)]
        results, _ = self._run(tmp_path, items, 6)
        assert [r["seen"]["id"] for r in results] == [f"x{i}" for i in range(6)]

    @pytest.mark.parametrize("max_concurrency", [1, 2])
    def test_marks_item_context_as_inside_fan_out(self, tmp_path, max_concurrency):
        from specify_cli.workflows.base import StepBase, StepResult, StepStatus

        class _ContextProbeStep(StepBase):
            type_key = "context-probe"

            def execute(self, config, context):
                return StepResult(
                    status=StepStatus.COMPLETED,
                    output={"inside_fan_out": context.inside_fan_out},
                )

        engine, context, state, _registry, _template = self._build(tmp_path)
        results = engine._run_fan_out(
            ["a", "b"],
            {"id": "probe", "type": "context-probe"},
            "fan",
            context,
            state,
            {"context-probe": _ContextProbeStep()},
            max_concurrency,
        )

        assert results == [
            {"inside_fan_out": True},
            {"inside_fan_out": True},
        ]
        assert context.inside_fan_out is False

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

    def test_concurrent_restores_halting_item_error(self, tmp_path):
        # After a concurrent fan-out halts, the run-level error must be the first
        # halting item's own error (parity with the sequential path), even when a
        # later concurrent item failed with a different error AND the halting
        # item's error is falsy. Covers the pool-join restore branch, which must
        # assign unconditionally rather than skip a falsy value.
        from specify_cli.workflows.base import (
            RunStatus,
            StepBase,
            StepResult,
            StepStatus,
        )

        class _ErrorProbe(StepBase):
            type_key = "err-probe"

            def execute(self, config, context):
                item = context.item
                if item == "halt":
                    # First failing item in item order; empty (falsy) error.
                    return StepResult(
                        status=StepStatus.FAILED, error="", output={}
                    )
                if item == "leak":
                    return StepResult(
                        status=StepStatus.FAILED,
                        error="leaked-error",
                        output={},
                    )
                return StepResult(
                    status=StepStatus.COMPLETED, output={"seen": item}
                )

        engine, context, state, _registry, _template = self._build(tmp_path)
        engine._run_fan_out(
            ["ok0", "halt", "ok2", "leak"],
            {"id": "impl", "type": "err-probe"},
            "fan",
            context,
            state,
            {"err-probe": _ErrorProbe()},
            4,
        )

        assert state.status == RunStatus.FAILED
        # Halt is attributed to "halt" (index 1). Its empty error must win over
        # the later "leak" item's error — the restore assigns the halting item's
        # error verbatim, even when falsy.
        assert state.error == ""

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

    @pytest.mark.parametrize(
        "block",
        [
            "workflow:\n  id: w\n  name: W\nsteps: []\ninputs: []\n",   # list
            "workflow:\n  id: w\n  name: W\nsteps: []\ninputs:\n",       # null
        ],
    )
    def test_resolve_inputs_tolerates_non_mapping_inputs(self, block):
        # execute()/resume() run UNVALIDATED definitions; a non-mapping `inputs:`
        # block (list/null) is stored raw and would crash _resolve_inputs at
        # `.items()`. It must be treated as "no inputs" instead.
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition.from_string(block)
        resolved = WorkflowEngine()._resolve_inputs(definition, {})  # must not raise
        assert resolved == {}

    @pytest.mark.parametrize(
        "block", ["workflow:\nsteps: []\n", "workflow: hi\nsteps: []\n", "workflow: [a]\nsteps: []\n"]
    )
    def test_non_mapping_workflow_block_parses_then_validates(self, block):
        # A present-but-non-mapping `workflow:` block must not crash construction
        # with AttributeError; it should parse to an empty header so
        # validate_workflow reports the missing id/name (it reads the parsed
        # attributes, not the raw block).
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string(block)  # must not raise
        assert definition.id == ""
        errors = validate_workflow(definition)
        assert any("workflow.id" in e for e in errors)
        # The RAW malformed value is preserved on .data (the guard only
        # normalizes the local var, not self.data) — .data is what gets written
        # back out when a definition is serialized. Assert it was NOT replaced
        # with {} by comparing against the original parse and confirming it is
        # still a non-mapping.
        import yaml

        raw_workflow = yaml.safe_load(block).get("workflow")
        assert definition.data["workflow"] == raw_workflow
        assert not isinstance(definition.data["workflow"], dict)

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

    def test_workflow_id_with_trailing_newline_is_invalid(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "valid\\n"
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("lowercase alphanumeric" in e for e in errors)

    def test_non_string_workflow_id_reports_error(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: 123
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("workflow.id" in e and "string" in e for e in errors)

    def test_non_string_name_reports_error(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: 123
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("workflow.name" in e and "string" in e for e in errors)

    def test_unquoted_float_version_reports_error(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: 1.0
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("workflow.version" in e and "quote" in e for e in errors)

    def test_version_with_trailing_newline_is_invalid(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0\\n"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("semantic version" in e for e in errors)

    def test_non_string_step_id_reports_error(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: 123
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("Step ID" in e and "string" in e for e in errors)

    def test_falsey_non_string_scalars_report_typed_errors(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
workflow:
  id: 0
  name: false
  version: 0.0
steps:
  - id: 0
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert any("'workflow.id' must be a string" in e for e in errors)
        assert any("'workflow.name' must be a string" in e for e in errors)
        assert any("'workflow.version' must be a string" in e for e in errors)
        assert any("Step ID must be a string" in e for e in errors)
        assert not any("missing" in e for e in errors)

    def test_unquoted_schema_version_accepted(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: 1.0
workflow:
  id: "test"
  name: "Test"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""")
        errors = validate_workflow(definition)
        assert errors == []

    @pytest.mark.parametrize(
        "field, bad_value",
        [
            ("integration", ["claude"]),
            ("integration", {"name": "claude"}),
            ("integration", False),
            ("model", ["gpt-5"]),
            ("model", {"name": "gpt-5"}),
            ("model", 0),
            ("options", ["max_tokens"]),
            ("options", "max_tokens"),
            ("options", False),
        ],
    )
    def test_rejects_invalid_workflow_dispatch_defaults(self, field, bad_value):
        """Top-level dispatch defaults must retain their invalid shape for
        validation instead of being passed to a step or normalized to ``{}``.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "test",
                    "name": "Test",
                    "version": "1.0.0",
                    field: bad_value,
                },
                "steps": [{"id": "step-one", "command": "speckit.specify"}],
            }
        )

        errors = validate_workflow(definition)

        assert any(f"workflow.{field}" in error for error in errors), errors
        assert any(type(bad_value).__name__ in error for error in errors), errors
        if field == "options":
            assert definition.default_options == bad_value

    def test_preserves_valid_workflow_dispatch_defaults(self):
        """String and mapping defaults stay available unchanged to steps."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        defaults = {
            "integration": "claude",
            "model": "gpt-5",
            "options": {"max_tokens": 8000},
        }
        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "test",
                    "name": "Test",
                    "version": "1.0.0",
                    **defaults,
                },
                "steps": [{"id": "step-one", "command": "speckit.specify"}],
            }
        )

        assert definition.default_integration == defaults["integration"]
        assert definition.default_model == defaults["model"]
        assert definition.default_options == defaults["options"]
        assert validate_workflow(definition) == []

    def test_accepts_null_workflow_dispatch_defaults(self):
        """Null integration/model inherit at runtime and null options stays {}."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "test",
                    "name": "Test",
                    "version": "1.0.0",
                    "integration": None,
                    "model": None,
                    "options": None,
                },
                "steps": [{"id": "step-one", "command": "speckit.specify"}],
            }
        )

        assert definition.default_integration is None
        assert definition.default_model is None
        assert definition.default_options == {}
        assert validate_workflow(definition) == []

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

    @pytest.mark.parametrize("step_type", [["shell"], {"name": "shell"}])
    def test_non_string_step_type_reports_error(self, step_type):
        """Unhashable YAML values must not crash registry membership checks."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "test",
                    "name": "Test",
                    "version": "1.0.0",
                },
                "steps": [{"id": "bad", "type": step_type}],
            }
        )

        errors = validate_workflow(definition)

        assert errors == [
            f"Step 'bad': 'type' must be a string, got "
            f"{type(step_type).__name__} ({step_type!r})."
        ]

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


class TestGateVerdictInputValidation:
    """Gate verdict_input must reference a declared workflow input.

    ``_resolve_inputs`` iterates only over ``definition.inputs`` — a provided
    value for an undeclared name is silently dropped at both initial run and
    resume. So an undeclared ``verdict_input`` can never receive a value; the
    gate would pause forever. Surface this wiring error at validation time.
    """

    @staticmethod
    def _errors(yaml_text):
        from specify_cli.workflows.engine import (
            WorkflowDefinition,
            validate_workflow,
        )

        return validate_workflow(WorkflowDefinition.from_string(yaml_text))

    def test_undeclared_verdict_input_is_rejected(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    verdict_input: spec_verdit
""")
        assert any(
            "'verdict_input' references undeclared input 'spec_verdit'" in e
            for e in errors
        )

    def test_declared_verdict_input_passes(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    verdict_input: spec_verdict
""")
        assert not any("verdict_input" in e for e in errors)

    def test_gate_without_verdict_input_passes(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
""")
        assert not any("verdict_input" in e for e in errors)

    def test_malformed_verdict_input_no_duplicate_error(self):
        # Non-string verdict_input is already reported by GateStep.validate();
        # the cross-reference check must not pile on a confusing duplicate.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    verdict_input: 123
""")
        # Shape error from GateStep.validate()
        assert any("verdict_input" in e and "non-empty string" in e for e in errors)
        # No undeclared-input error (123 is not a string, so cross-check skips)
        assert not any("undeclared input" in e for e in errors)

    def test_retry_verdict_enum_must_allow_reset_sentinel(self):
        # on_reject: retry resets the bound input to "" before pausing, and
        # every resume re-resolves persisted inputs through _coerce_input. An
        # enum that omits "" makes that reset value instantly illegal, so the
        # next resume supplying any input dies with "value '' not in allowed
        # values" and no verdict can reach the gate again.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    enum: [approve, reject]
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    on_reject: retry
    verdict_input: spec_verdict
""")
        assert any(
            "on_reject='retry' resets verdict input 'spec_verdict'" in e
            for e in errors
        ), errors

    def test_retry_verdict_enum_including_sentinel_passes(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    enum: ["", approve, reject]
    default: ""
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    on_reject: retry
    verdict_input: spec_verdict
""")
        assert not any("on_reject='retry'" in e for e in errors), errors

    def test_verdict_enum_without_sentinel_passes_when_not_retry(self):
        # abort/skip never reset the input, so the enum need not admit "".
        for on_reject in ("abort", "skip"):
            errors = self._errors(f"""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    enum: [approve, reject]
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    on_reject: {on_reject}
    verdict_input: spec_verdict
""")
            assert not any("on_reject='retry'" in e for e in errors), (
                on_reject,
                errors,
            )

    def test_retry_verdict_without_enum_passes(self):
        # No enum means _coerce_input accepts "" — the documented shape.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    on_reject: retry
    verdict_input: spec_verdict
""")
        assert not any("on_reject='retry'" in e for e in errors), errors

    def test_retry_verdict_enum_wedge_is_reachable_end_to_end(self, tmp_path):
        """The validation error above guards a real, unrecoverable run state.

        Without the guard this workflow installs and runs fine, then wedges:
        the retry reset writes "" into the persisted inputs, and the next
        resume that supplies *any* input re-resolves them and dies on the
        enum. Only a resume with no inputs at all still works, so the bound
        verdict can never be delivered.
        """
        import pytest
        import yaml as _yaml

        from specify_cli.workflows.engine import WorkflowEngine

        definition_data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "inputs": {
                "spec_verdict": {"type": "string", "enum": ["approve", "reject"]},
                "note": {"type": "string", "default": "a"},
            },
            "steps": [
                {
                    "id": "review",
                    "type": "gate",
                    "message": "Review?",
                    "options": ["approve", "reject"],
                    "on_reject": "retry",
                    "verdict_input": "spec_verdict",
                }
            ],
        }
        wf_dir = tmp_path / ".specify" / "workflows" / "wf"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            _yaml.safe_dump(definition_data), encoding="utf-8"
        )

        engine = WorkflowEngine(tmp_path)
        definition = engine.load_workflow("wf")
        state = engine.execute(definition, inputs={"spec_verdict": "reject"})
        assert state.status.value == "paused"
        # The retry reset persisted a value the input's own enum forbids.
        assert state.inputs["spec_verdict"] == ""

        with pytest.raises(ValueError, match="not in allowed values"):
            engine.resume(state.run_id, inputs={"note": "b"})

    def test_verdict_input_in_switch_case(self):
        # Recursion coverage: bad reference inside a switch case must surface.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: branch
    type: switch
    expression: "{{ inputs.flag }}"
    cases:
      yes:
        - id: review
          type: gate
          message: "Review?"
          options: [approve, reject]
          verdict_input: ghost_input
""")
        assert any(
            "'verdict_input' references undeclared input 'ghost_input'" in e
            for e in errors
        )

    def test_verdict_input_in_if_branch(self):
        # Recursion coverage: bad reference inside an if-then branch.
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
      - id: review
        type: gate
        message: "Review?"
        options: [approve, reject]
        verdict_input: ghost_input
""")
        assert any(
            "'verdict_input' references undeclared input 'ghost_input'" in e
            for e in errors
        )

    def test_verdict_input_in_fan_out_template(self):
        # Fan-out items share workflow inputs, so a bound verdict would be
        # consumed by multiple item gates with undefined pause/resume semantics.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: fan
    type: fan-out
    items: [a, b]
    step:
      id: review
      type: gate
      message: "Review?"
      options: [approve, reject]
      verdict_input: spec_verdict
""")
        assert any(
            "'verdict_input' is not supported inside fan-out templates" in e
            for e in errors
        )

    def test_verdict_input_nested_inside_fan_out_template(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: fan
    type: fan-out
    items: [a, b]
    step:
      id: maybe-review
      type: if
      condition: "{{ item }}"
      then:
        - id: review
          type: gate
          message: "Review?"
          options: [approve, reject]
          verdict_input: spec_verdict
""")
        assert any(
            "'verdict_input' is not supported inside fan-out templates" in e
            for e in errors
        )

    def test_gate_without_verdict_input_in_fan_out_template_passes(self):
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
steps:
  - id: fan
    type: fan-out
    items: [a, b]
    step:
      id: review
      type: gate
      message: "Review?"
      options: [approve, reject]
""")
        assert not any(
            "not supported inside fan-out templates" in e for e in errors
        )

    def test_malformed_inputs_block_no_cascade(self):
        # When the inputs block itself is malformed (already reported), the
        # cross-check is disabled so one authoring mistake does not cascade
        # into N spurious "undeclared" errors.
        errors = self._errors("""
workflow:
  id: wf
  name: wf
  version: "1.0.0"
inputs:
  - not_a_mapping
steps:
  - id: review
    type: gate
    message: "Review?"
    options: [approve, reject]
    verdict_input: spec_verdict
""")
        # Inputs-shape error is reported
        assert any("'inputs' must be a mapping" in e for e in errors)
        # No cascade of undeclared-input errors
        assert not any("undeclared input" in e for e in errors)


# ===== Workflow Engine Tests =====

class TestWorkflowEngine:
    """Test WorkflowEngine execution."""

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("integration", ["claude"]),
            ("model", {"name": "gpt-5"}),
            ("options", ["max_tokens"]),
        ],
    )
    def test_execute_rejects_invalid_workflow_dispatch_defaults(
        self, project_dir, field, value
    ):
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "invalid-dispatch-defaults",
                    "name": "Invalid dispatch defaults",
                    "version": "1.0.0",
                    field: value,
                },
                "steps": [],
            }
        )

        with pytest.raises(ValueError, match=f"workflow.{field}"):
            WorkflowEngine(project_dir).execute(definition)

        assert not (project_dir / ".specify" / "workflows" / "runs").exists()

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
        with patch("specify_cli.workflows.step.command.shutil.which", return_value=None):
            state = engine.execute(definition, {"name": "login"})

        assert state.status == RunStatus.FAILED
        assert "step-one" in state.step_results
        assert state.step_results["step-one"]["output"]["command"] == "speckit.specify"
        assert state.step_results["step-one"]["output"]["input"]["args"] == "login"

    def test_execute_rejects_invalid_origin_before_creating_run_state(
        self, project_dir
    ):
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "simple"
  name: "Simple"
  version: "1.0.0"
steps: []
""")
        engine = WorkflowEngine(project_dir)

        with pytest.raises(ValueError, match="installed_registry_root"):
            engine.execute(
                definition,
                run_id="invalid-origin",
                installed_workflow_id="simple",
                installed_registry_root=Path("relative-owner"),
            )

        run_dir = (
            project_dir
            / ".specify"
            / "workflows"
            / "runs"
            / "invalid-origin"
        )
        assert not run_dir.exists()

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

    def test_coerce_input_rejects_non_list_enum_cleanly(self):
        """A non-list ``enum`` (scalar or string) must raise a clean ValueError,
        not the raw ``TypeError`` from the ``value not in enum`` membership test.

        A scalar (``enum: 5``) makes ``value not in 5`` raise
        ``TypeError: argument of type 'int' is not iterable``. A bare string
        (``enum: "abc"``) is silently wrong instead — ``value in "abc"`` is a
        substring test, not enum membership — so it must be rejected too.
        """
        from specify_cli.workflows.engine import WorkflowEngine

        for bad_enum in (5, True, "abc", {"a": 1}):
            with pytest.raises(ValueError, match="invalid 'enum': must be a list"):
                WorkflowEngine._coerce_input(
                    "scope", "x", {"type": "string", "enum": bad_enum}
                )
        # A valid list ``enum`` still works, and ``None`` means "no enum".
        assert (
            WorkflowEngine._coerce_input(
                "scope", "a", {"type": "string", "enum": ["a", "b"]}
            )
            == "a"
        )
        assert (
            WorkflowEngine._coerce_input("scope", "x", {"type": "string"}) == "x"
        )

    def test_validate_workflow_rejects_non_list_enum(self):
        """A non-list ``enum`` must be reported as an error, not crash
        ``validate_workflow``. The membership test would raise ``TypeError``,
        which escapes its ``except ValueError`` and breaks the "return a list of
        errors, never raise" contract. This must surface even with no ``default``
        present (the coercion path that would otherwise catch it is only reached
        when a default exists).
        """
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "bad-enum"
  name: "Bad Enum"
  version: "1.0.0"
inputs:
  scope:
    type: string
    enum: 5
steps:
  - id: noop
    type: gate
    message: "noop"
    options: [approve]
""")
        errors = validate_workflow(definition)
        assert any("invalid 'enum': must be a list" in e for e in errors), errors

    def test_resolve_inputs_rejects_non_list_enum_at_runtime(self, project_dir):
        """``execute()`` accepts unvalidated definitions, so a non-list ``enum``
        can reach ``_resolve_inputs`` at run time. It must fail with a clean
        ValueError rather than the raw ``TypeError`` from the membership test.
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "runtime-bad-enum"
  name: "Runtime Bad Enum"
  version: "1.0.0"
inputs:
  scope:
    type: string
    enum: 5
""")
        engine = WorkflowEngine(project_dir)
        with pytest.raises(ValueError, match="invalid 'enum': must be a list"):
            engine._resolve_inputs(definition, {"scope": "x"})

    def test_non_list_enum_on_integration_auto_still_rejected(self, project_dir):
        """The ``integration: auto`` sentinel strips a *list* ``enum`` before
        coercion (enum-membership is a runtime concern for ``auto``). A non-list
        ``enum`` must NOT be silently stripped by that path — it is still an
        authoring error and must fail with the clean shape ValueError.
        """
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "auto-bad-enum"
  name: "Auto Bad Enum"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: "auto"
    enum: 5
""")
        engine = WorkflowEngine(project_dir)
        with pytest.raises(ValueError, match="invalid 'enum': must be a list"):
            engine._resolve_inputs(definition, {})

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

    def test_loop_with_bool_max_iterations_uses_default_cap(self, project_dir):
        """A boolean max_iterations must fall back to the default cap of 10,
        not be treated as the int 1 (bool-is-int trap).

        ``max_iterations: true`` would otherwise slip past the int check
        (``isinstance(True, int)`` is True and ``True < 1`` is False) and
        cap the loop at ``range(True - 1) == range(0)`` — a single
        iteration. ``execute()`` does not auto-validate, so the engine's own
        guard is the only line of defence here.
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
  id: "while-bool-max-iterations"
  name: "While Bool Max Iterations"
  version: "1.0.0"
steps:
  - id: retry-loop
    type: while
    condition: "{{{{ 'done' not in steps.tick.output.stdout }}}}"
    max_iterations: true
    steps:
      - id: tick
        type: shell
        run: '"{py}" "{script_file}"'
"""
        definition = WorkflowDefinition.from_string(yaml_str)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        # Falls back to the default cap of 10, not range(True - 1) == 1 run.
        assert counter_file.read_text(encoding="utf-8").strip() == "10"

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
            "specify_cli.workflows.step.command.shutil.which",
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


# ===== context.workflow_dir Tests =====


class TestContextWorkflowDir:
    """Tests for `{{ context.workflow_dir }}` and `SPECKIT_WORKFLOW_DIR`."""

    def test_context_workflow_dir_resolves(self):
        """``{{ context.workflow_dir }}`` resolves to ``StepContext.workflow_dir``."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(workflow_dir="/home/user/my-workflow")
        assert evaluate_expression("{{ context.workflow_dir }}", ctx) == "/home/user/my-workflow"

    def test_context_workflow_dir_defaults_to_empty_when_unset(self):
        """``{{ context.workflow_dir }}`` resolves to ``""`` when no source
        path is available (string-loaded workflows, dry-run).
        """
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext()
        assert evaluate_expression("{{ context.workflow_dir }}", ctx) == ""

    def test_context_workflow_dir_string_interpolation(self):
        """Workflow dir interpolates inside a larger template string."""
        from specify_cli.workflows.expressions import evaluate_expression
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(workflow_dir="/opt/workflows/setup")
        result = evaluate_expression("cp {{ context.workflow_dir }}/config.yml .", ctx)
        assert result == "cp /opt/workflows/setup/config.yml ."

    def test_step_context_workflow_dir(self):
        """StepContext accepts and stores workflow_dir."""
        from specify_cli.workflows.base import StepContext

        ctx = StepContext(workflow_dir="/some/path")
        assert ctx.workflow_dir == "/some/path"

        ctx_none = StepContext()
        assert ctx_none.workflow_dir is None

    def test_from_yaml_sets_workflow_dir(self, project_dir):
        """Workflow loaded from a YAML file has workflow_dir set to the
        file's parent directory.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        wf_dir = project_dir / "my-workflows"
        wf_dir.mkdir()
        wf_file = wf_dir / "setup.yml"
        wf_file.write_text("""
schema_version: "1.0"
workflow:
  id: "from-yaml"
  name: "From YAML"
  version: "1.0.0"
steps:
  - id: check-dir
    type: shell
    run: "echo DIR={{ context.workflow_dir }}"
""")
        definition = WorkflowDefinition.from_yaml(wf_file)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        stdout = state.step_results["check-dir"]["output"]["stdout"]
        assert stdout.strip() == f"DIR={wf_dir.resolve()}"

    def test_from_string_has_empty_workflow_dir(self, project_dir):
        """String-loaded workflows have empty workflow_dir."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "from-string"
  name: "From String"
  version: "1.0.0"
steps:
  - id: check-dir
    type: shell
    run: "echo DIR={{ context.workflow_dir }}"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        stdout = state.step_results["check-dir"]["output"]["stdout"]
        assert stdout.strip() == "DIR="

    def test_shell_step_receives_speckit_workflow_dir_env_var(self, project_dir):
        """Shell steps receive SPECKIT_WORKFLOW_DIR in their environment."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        import sys

        wf_dir = project_dir / "wf"
        wf_dir.mkdir()
        wf_file = wf_dir / "workflow.yml"
        python = sys.executable.replace("\\", "/")
        wf_file.write_text(f"""
schema_version: "1.0"
workflow:
  id: "env-var-test"
  name: "Env Var Test"
  version: "1.0.0"
steps:
  - id: print-env
    type: shell
    run: '"{python}" -c "import os; print(os.environ.get(''SPECKIT_WORKFLOW_DIR'', ''UNSET''))"'
""")
        definition = WorkflowDefinition.from_yaml(wf_file)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        stdout = state.step_results["print-env"]["output"]["stdout"]
        assert stdout.strip() == str(wf_dir.resolve())

    def test_shell_step_no_env_var_when_workflow_dir_unset(self, project_dir, monkeypatch):
        """Shell steps do not set SPECKIT_WORKFLOW_DIR for string-loaded workflows."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        import sys

        monkeypatch.delenv("SPECKIT_WORKFLOW_DIR", raising=False)

        python = sys.executable.replace("\\", "/")
        definition = WorkflowDefinition.from_string(f"""
schema_version: "1.0"
workflow:
  id: "no-env-var"
  name: "No Env Var"
  version: "1.0.0"
steps:
  - id: check-env
    type: shell
    run: '"{python}" -c "import os; print(os.environ.get(''SPECKIT_WORKFLOW_DIR'', ''UNSET''))"'
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        stdout = state.step_results["check-env"]["output"]["stdout"]
        assert stdout.strip() == "UNSET"

    def test_resume_preserves_original_workflow_dir(self, project_dir):
        """Resumed workflow uses the original source directory, not the
        run-directory copy path.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        wf_dir = project_dir / "original-source"
        wf_dir.mkdir()
        wf_file = wf_dir / "resumable.yml"
        wf_file.write_text("""
schema_version: "1.0"
workflow:
  id: "resumable"
  name: "Resumable"
  version: "1.0.0"
steps:
  - id: gate-step
    type: gate
    message: "Approve?"
  - id: after-gate
    type: shell
    run: "echo DIR={{ context.workflow_dir }}"
""")
        definition = WorkflowDefinition.from_yaml(wf_file)
        engine = WorkflowEngine(project_dir)

        # Execute -- gate pauses the workflow
        state = engine.execute(definition)
        assert state.status == RunStatus.PAUSED
        assert state.workflow_dir == str(wf_dir.resolve())

        # Simulate gate approval by patching the gate step
        from unittest.mock import patch
        from specify_cli.workflows.base import StepResult

        with patch(
            "specify_cli.workflows.step.gate.GateStep.execute",
            return_value=StepResult(output={"approved": True}),
        ):
            state = engine.resume(state.run_id)

        assert state.status == RunStatus.COMPLETED
        stdout = state.step_results["after-gate"]["output"]["stdout"]
        assert stdout.strip() == f"DIR={wf_dir.resolve()}"

    def test_workflow_dir_persisted_in_state(self, project_dir):
        """workflow_dir is persisted in state.json and survives load/save."""
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine, RunState

        wf_dir = project_dir / "persist-test"
        wf_dir.mkdir()
        wf_file = wf_dir / "workflow.yml"
        wf_file.write_text("""
schema_version: "1.0"
workflow:
  id: "persist-wfdir"
  name: "Persist WfDir"
  version: "1.0.0"
steps:
  - id: noop
    type: shell
    run: "echo ok"
""")
        definition = WorkflowDefinition.from_yaml(wf_file)
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        # Reload state from disk and verify workflow_dir survived
        loaded = RunState.load(state.run_id, project_dir)
        assert loaded.workflow_dir == str(wf_dir.resolve())

    def test_installed_workflow_has_workflow_dir(self, project_dir):
        """Installed-by-ID workflows get workflow_dir pointing to the
        installation directory (.specify/workflows/<id>/).
        """
        from specify_cli.workflows.engine import WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        wf_id = "installed-wfdir"
        install_dir = project_dir / ".specify" / "workflows" / wf_id
        install_dir.mkdir(parents=True)
        (install_dir / "workflow.yml").write_text("""
schema_version: "1.0"
workflow:
  id: "installed-wfdir"
  name: "Installed WfDir"
  version: "1.0.0"
steps:
  - id: check-dir
    type: shell
    run: "echo DIR={{ context.workflow_dir }}"
""")
        engine = WorkflowEngine(project_dir)
        definition = engine.load_workflow(wf_id)
        state = engine.execute(definition)

        assert state.status == RunStatus.COMPLETED
        stdout = state.step_results["check-dir"]["output"]["stdout"]
        assert stdout.strip() == f"DIR={install_dir.resolve()}"

    def test_workflow_dir_is_resolved_to_absolute(self, project_dir):
        """workflow_dir is resolved to an absolute path even when the
        source path is relative.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        import os

        wf_dir = project_dir / "rel-test"
        wf_dir.mkdir()
        wf_file = wf_dir / "workflow.yml"
        wf_file.write_text("""
schema_version: "1.0"
workflow:
  id: "rel-path"
  name: "Relative Path"
  version: "1.0.0"
steps:
  - id: check
    type: shell
    run: "echo ok"
""")
        # Load via a relative path
        saved_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            rel_path = Path("rel-test/workflow.yml")
            definition = WorkflowDefinition.from_yaml(rel_path)
            engine = WorkflowEngine(project_dir)
            state = engine.execute(definition)
        finally:
            os.chdir(saved_cwd)

        assert Path(state.workflow_dir).is_absolute()
        assert state.workflow_dir == str(wf_dir.resolve())


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


class TestWorkflowDispatchDefaultExecution:
    """Execution safeguards for defaults inherited by dispatch steps."""

    @pytest.mark.parametrize(
        "defaults",
        [
            {
                "integration": "claude",
                "model": "gpt-5",
                "options": {"max_tokens": 8000},
            },
            {"integration": None, "model": None, "options": None},
        ],
    )
    def test_execute_accepts_valid_and_null_dispatch_defaults(
        self, project_dir, defaults
    ):
        """Defaults with supported shapes remain executable without validation."""
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

        definition = WorkflowDefinition(
            {
                "workflow": {
                    "id": "valid-defaults",
                    "name": "Valid Defaults",
                    "version": "1.0.0",
                    **defaults,
                },
                "steps": [],
            }
        )

        state = WorkflowEngine(project_dir).execute(definition)

        assert state.status == RunStatus.COMPLETED
        assert state.step_results == {}


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
        from specify_cli.workflows.step.gate import GateStep

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

    def test_gate_reject_matches_case_insensitively(
        self, project_dir, monkeypatch
    ):
        """A capitalised reject option (`options: [Approve, Reject]`) still
        aborts the run. `validate` accepts a reject choice case-insensitively,
        so the runtime reject check must agree — a case-sensitive comparison
        would treat the echoed `Reject` as approval and silently run
        downstream steps.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.step.gate import GateStep

        # `_prompt` echoes the option's original casing, so the operator
        # picking "Reject" hands `execute` the capitalised string.
        _force_gate_stdin(monkeypatch, tty=True)
        monkeypatch.setattr(
            GateStep, "_prompt", staticmethod(lambda _msg, _opts: "Reject")
        )

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "gate-reject-case"
  name: "Gate Reject Case"
  version: "1.0.0"
steps:
  - id: gate-step
    type: gate
    message: "Approve?"
    options: [Approve, Reject]
    on_reject: abort
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

    def test_continue_on_error_failure_not_surfaced_as_terminal_error(
        self, project_dir
    ):
        """A continue_on_error step's error must not be reported as the
        terminal run error when a later step fails for a different reason.

        Regression test: the engine sets state.error only at terminal
        branches, not in the continue_on_error branch. A handled failure
        must not leak into the run-level error.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "coe-leak"
  name: "COE Leak"
  version: "1.0.0"
steps:
  - id: handled-failure
    type: shell
    run: "exit 42"
    continue_on_error: true
  - id: terminal-failure
    type: shell
    run: "exit 7"
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.FAILED
        # The terminal error must be from the terminal-failure step, not
        # the handled-failure step.
        assert state.error is not None
        assert "42" not in (state.error or "")
        # The handled step's per-step error is still preserved.
        assert state.step_results["handled-failure"]["status"] == "failed"
        assert state.step_results["handled-failure"].get("error") is not None

    def test_unknown_step_type_sets_run_error(self, project_dir):
        """An unregistered step type fails the run with a descriptive
        run-level error persisted on state.error.

        The engine sets state.error at the unknown-step-type terminal
        branch, mirroring the other terminal failure paths.
        """
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus

        # execute() bypasses validate_workflow(), which is what would
        # otherwise reject the unknown type up front.
        definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: "unknown-type"
  name: "Unknown Type"
  version: "1.0.0"
steps:
  - id: mystery
    type: definitely-not-a-real-step
""")
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)

        assert state.status == RunStatus.FAILED
        assert state.error == "Unknown step type: 'definitely-not-a-real-step'"


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

    def test_load_rejects_stored_run_id_mismatch(self, project_dir):
        """The state payload cannot redirect later writes to another run."""
        from specify_cli.workflows.engine import RunState

        run_dir = (
            project_dir
            / ".specify"
            / "workflows"
            / "runs"
            / "requested-run"
        )
        run_dir.mkdir(parents=True)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "other-run",
                    "workflow_id": "test-workflow",
                    "status": "created",
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(
            ValueError,
            match="stored run_id 'other-run' does not match requested run_id 'requested-run'",
        ):
            RunState.load("requested-run", project_dir)

    @pytest.mark.parametrize(
        "bad_current_step_index",
        ["not-a-number", 1.5, -1, [0], {"index": 0}, True],
    )
    def test_load_rejects_invalid_current_step_index(
        self, project_dir, bad_current_step_index
    ):
        """Reject non-integer and negative resume indices at load time.

        ``bool`` is covered explicitly because it subclasses ``int``.
        """
        from specify_cli.workflows.engine import RunState

        run_dir = (
            project_dir / ".specify" / "workflows" / "runs" / "bad-index-run"
        )
        run_dir.mkdir(parents=True)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "bad-index-run",
                    "workflow_id": "test-workflow",
                    "status": "paused",
                    "current_step_index": bad_current_step_index,
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(
            ValueError, match="'current_step_index' must be a non-negative integer"
        ):
            RunState.load("bad-index-run", project_dir)

    @pytest.mark.parametrize(
        ("installed_workflow_id", "installed_registry_root"),
        [
            ("", None),
            ("gated-wf\n", None),
            ("gated-wf", "relative-owner"),
        ],
    )
    def test_init_rejects_invalid_installed_origin(
        self, installed_workflow_id, installed_registry_root
    ):
        from specify_cli.workflows.engine import RunState

        with pytest.raises(ValueError, match="Invalid run state"):
            RunState(
                run_id="test-run",
                workflow_id="test-workflow",
                installed_workflow_id=installed_workflow_id,
                installed_registry_root=installed_registry_root,
            )

    def test_init_rejects_registry_root_without_workflow_id(
        self, project_dir
    ):
        from specify_cli.workflows.engine import RunState

        with pytest.raises(ValueError, match="requires"):
            RunState(
                run_id="test-run",
                workflow_id="test-workflow",
                installed_registry_root=str(project_dir),
            )

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
            "valid\n",      # regex end-anchor bypass
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

    def test_error_persists_across_save_and_load(self, project_dir):
        """Run-level error survives a save/load round trip."""
        from specify_cli.workflows.engine import RunState
        from specify_cli.workflows.base import RunStatus

        state = RunState(
            run_id="err-run",
            workflow_id="test-wf",
            project_root=project_dir,
        )
        state.status = RunStatus.FAILED
        state.error = "Something went wrong"
        state.save()

        loaded = RunState.load("err-run", project_dir)
        assert loaded.error == "Something went wrong"

    def test_error_defaults_none_for_legacy_state(self, project_dir):
        """Old state.json files without an error field load with error=None."""
        from specify_cli.workflows.engine import RunState

        state = RunState(
            run_id="legacy-run",
            workflow_id="test-wf",
            project_root=project_dir,
        )
        state.save()

        # Manually strip the error field to simulate a legacy state file.
        state_path = state.runs_dir / "state.json"
        data = json.loads(state_path.read_text())
        data.pop("error", None)
        state_path.write_text(json.dumps(data), encoding="utf-8")

        loaded = RunState.load("legacy-run", project_dir)
        assert loaded.error is None

    def test_resume_clears_stale_error(self, project_dir):
        """A resumed run starts with state.error = None."""
        from specify_cli.workflows.engine import RunState
        from specify_cli.workflows.base import RunStatus

        state = RunState(
            run_id="resume-err",
            workflow_id="test-wf",
            project_root=project_dir,
        )
        state.status = RunStatus.FAILED
        state.error = "Previous failure"
        state.save()

        loaded = RunState.load("resume-err", project_dir)
        assert loaded.error == "Previous failure"

        loaded.error = None
        loaded.status = RunStatus.RUNNING
        loaded.save()

        reloaded = RunState.load("resume-err", project_dir)
        assert reloaded.error is None


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

    def test_list_skips_malformed_json(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-run"
        bad_dir.mkdir(parents=True)
        (bad_dir / "state.json").write_text("{invalid json", encoding="utf-8")

        engine = WorkflowEngine(project_dir)
        assert engine.list_runs() == []

    def test_list_skips_unreadable_file(self, project_dir):
        import sys
        import subprocess
        from specify_cli.workflows.engine import WorkflowEngine

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-run"
        bad_dir.mkdir(parents=True)
        state_file = bad_dir / "state.json"
        state_file.write_text('{"run_id": "x"}', encoding="utf-8")

        if sys.platform == "win32":
            subprocess.run(["attrib", "+R", str(state_file)], check=True)
        else:
            state_file.chmod(0o000)

        try:
            engine = WorkflowEngine(project_dir)
            if sys.platform == "win32":
                assert engine.list_runs() == [{"run_id": "x"}]
            else:
                assert engine.list_runs() == []
        finally:
            if sys.platform == "win32":
                subprocess.run(["attrib", "-R", str(state_file)], check=True)
            else:
                state_file.chmod(0o644)

    def test_list_skips_non_dict_payload(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-run"
        bad_dir.mkdir(parents=True)
        (bad_dir / "state.json").write_text('["not", "a", "dict"]', encoding="utf-8")

        engine = WorkflowEngine(project_dir)
        assert engine.list_runs() == []

    def test_list_skips_empty_dict_payload(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-run"
        bad_dir.mkdir(parents=True)
        (bad_dir / "state.json").write_text('{}', encoding="utf-8")

        engine = WorkflowEngine(project_dir)
        assert engine.list_runs() == []

    def test_list_skips_bad_file_with_valid_sibling(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-run"
        bad_dir.mkdir(parents=True)
        (bad_dir / "state.json").write_text("{bad", encoding="utf-8")

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "good-run"
  name: "Good Run"
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
        assert runs[0]["workflow_id"] == "good-run"

    def test_list_skips_invalid_utf8_with_valid_sibling(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-utf8"
        bad_dir.mkdir(parents=True)
        (bad_dir / "state.json").write_bytes(b"\xff\xfe invalid utf8")

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "good-run-utf8"
  name: "Good Run UTF8"
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
        assert runs[0]["workflow_id"] == "good-run-utf8"

    def test_list_skips_oserror_with_valid_sibling(self, project_dir, monkeypatch):
        import builtins
        from specify_cli.workflows.engine import WorkflowEngine, WorkflowDefinition

        runs_dir = project_dir / ".specify" / "workflows" / "runs"
        bad_dir = runs_dir / "bad-oserror"
        bad_dir.mkdir(parents=True)
        state_file = bad_dir / "state.json"
        state_file.write_text('{"run_id": "bad"}', encoding="utf-8")

        original_open = builtins.open

        def _mock_open(path, *args, **kwargs):
            if str(path).endswith("state.json") and "bad-oserror" in str(path):
                raise OSError("permission denied")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _mock_open)

        yaml_str = """
schema_version: "1.0"
workflow:
  id: "good-run-oserror"
  name: "Good Run OSError"
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
        assert runs[0]["workflow_id"] == "good-run-oserror"


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

    @pytest.mark.parametrize("error_type", [OSError, TypeError, ValueError])
    def test_remove_rolls_back_in_memory_on_save_failure(
        self, project_dir, monkeypatch, error_type
    ):
        """A save() failure during remove() must not leave the in-memory registry
        out of sync with the (unchanged) file on disk, mirroring add()'s rollback."""
        from specify_cli.workflows.catalog import WorkflowRegistry
        import specify_cli.workflows.catalog as catalog_mod

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})

        def boom(*args, **kwargs):
            raise error_type("save failed")

        monkeypatch.setattr(catalog_mod.json, "dump", boom)
        with pytest.raises(error_type):
            registry.remove("test-wf")
        monkeypatch.undo()

        # In-memory state must still show the entry (rolled back), matching
        # the untouched file on disk.
        assert registry.is_installed("test-wf")
        fresh = WorkflowRegistry(project_dir)
        assert fresh.is_installed("test-wf")

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

    def test_load_read_oserror_refuses_to_save_over_existing_data(self, project_dir, monkeypatch):
        """A transient read failure (e.g. temporarily unreadable file) must not be
        treated the same as a corrupted/missing registry: constructing a registry
        on top of it -- and thus any query a caller makes before ever calling
        save() -- must fail closed instead of silently reporting an empty
        registry that a caller could then act on and overwrite."""
        from specify_cli.workflows.catalog import WorkflowRegistry
        import builtins

        registry1 = WorkflowRegistry(project_dir)
        registry1.add("test-wf", {"name": "Test", "version": "1.0.0"})
        registry_path = registry1.registry_path
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == registry_path and "r" in mode:
                raise OSError("simulated read failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(OSError):
            WorkflowRegistry(project_dir)
        # The original entry must survive on disk untouched.
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        assert "test-wf" in data["workflows"]

    def test_load_read_oserror_fails_closed_not_silently_empty(self, project_dir, monkeypatch):
        """Root cause: a registry that failed to read must never let a query
        method (is_installed/get/list) report as if nothing were installed --
        a caller (e.g. bundled workflow install) that only checks
        is_installed() before writing a file would otherwise overwrite real
        data on a transient read failure, long before any save() call could
        catch it. The failure must surface at construction, before any query
        or side effect is possible."""
        from specify_cli.workflows.catalog import WorkflowRegistry
        import builtins

        registry1 = WorkflowRegistry(project_dir)
        registry1.add("test-wf", {"name": "Test", "version": "1.0.0"})
        registry_path = registry1.registry_path
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file) == registry_path and "r" in mode:
                raise OSError("simulated read failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        with pytest.raises(OSError):
            WorkflowRegistry(project_dir)

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_load_symlinked_workflows_dir_fails_closed_not_silently_empty(
        self, project_dir
    ):
        """A symlinked .specify/workflows is the same fail-open hazard as a
        read OSError: silently reporting an empty registry lets a read-only
        caller (e.g. the bundler's remove path) conclude a workflow isn't
        installed, skip removing it, and then delete the bundle record --
        leaving the workflow untracked but still on disk. Raise here too,
        exactly like the unreadable-file case, so callers cannot act on
        fabricated empty state."""
        from specify_cli.workflows.catalog import WorkflowRegistry
        import json as _json

        outside = project_dir.parent / "outside-workflows"
        outside.mkdir(parents=True, exist_ok=True)
        (outside / "workflow-registry.json").write_text(
            _json.dumps({"schema_version": "1.0", "workflows": {"evil": {}}}),
            encoding="utf-8",
        )
        workflows_link = project_dir / ".specify" / "workflows"
        workflows_link.rmdir()
        workflows_link.symlink_to(outside, target_is_directory=True)

        with pytest.raises(OSError):
            WorkflowRegistry(project_dir)


# ===== Workflow Catalog Tests =====

class TestWorkflowCatalog:
    """Test WorkflowCatalog catalog resolution."""

    @pytest.mark.parametrize("catalog_type", ["workflow", "step"])
    def test_non_mapping_cache_metadata_is_invalid(
        self, project_dir, catalog_type
    ):
        from specify_cli.workflows.catalog import WorkflowCatalog
        from specify_cli.workflows.step.catalog import StepCatalog

        catalog_cls = WorkflowCatalog if catalog_type == "workflow" else StepCatalog
        catalog = catalog_cls(project_dir)
        _, metadata_path = catalog._get_cache_paths(
            f"https://example.com/{catalog_type}.json"
        )
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text("[]", encoding="utf-8")

        assert catalog._is_url_cache_valid(
            f"https://example.com/{catalog_type}.json"
        ) is False

    def test_non_mapping_cached_workflow_catalog_is_refetched(
        self, project_dir, monkeypatch
    ):
        import io

        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
        )

        url = "https://example.com/workflows.json"
        catalog = WorkflowCatalog(project_dir)
        cache_path, metadata_path = catalog._get_cache_paths(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("[]", encoding="utf-8")
        metadata_path.write_text(
            json.dumps({"fetched_at": 4_102_444_800}),
            encoding="utf-8",
        )

        payload = {"schema_version": "1.0", "workflows": {}}

        class _FakeResponse(io.BytesIO):
            def geturl(self):
                return url

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(
                json.dumps(payload).encode("utf-8")
            ),
        )
        entry = WorkflowCatalogEntry(
            url=url,
            name="test",
            priority=1,
            install_allowed=True,
        )

        assert catalog._fetch_single_catalog(entry) == payload

    @pytest.mark.parametrize("catalog_type", ["workflow", "step"])
    def test_non_utf8_cached_catalog_is_refetched(
        self, project_dir, monkeypatch, catalog_type
    ):
        import io

        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowCatalogEntry
        from specify_cli.workflows.step.catalog import StepCatalog, StepCatalogEntry

        catalog_cls = WorkflowCatalog if catalog_type == "workflow" else StepCatalog
        entry_cls = (
            WorkflowCatalogEntry
            if catalog_type == "workflow"
            else StepCatalogEntry
        )
        payload_key = "workflows" if catalog_type == "workflow" else "steps"
        url = f"https://example.com/{catalog_type}.json"
        catalog = catalog_cls(project_dir)
        cache_path, metadata_path = catalog._get_cache_paths(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(b"\xff\xfe")
        metadata_path.write_text(
            json.dumps({"fetched_at": 4_102_444_800}),
            encoding="utf-8",
        )
        payload = {"schema_version": "1.0", payload_key: {}}

        class _FakeResponse(io.BytesIO):
            def geturl(self):
                return url

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(
                json.dumps(payload).encode("utf-8")
            ),
        )
        entry = entry_cls(
            url=url,
            name="test",
            priority=1,
            install_allowed=True,
        )

        assert catalog._fetch_single_catalog(entry) == payload
        assert json.loads(cache_path.read_text(encoding="utf-8")) == payload

    def test_non_mapping_stale_workflow_catalog_is_rejected(
        self, project_dir, monkeypatch
    ):
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            WorkflowCatalogError,
        )

        url = "https://example.com/workflows.json"
        catalog = WorkflowCatalog(project_dir)
        cache_path, _ = catalog._get_cache_paths(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("[]", encoding="utf-8")

        def _offline(url, timeout=30, redirect_validator=None):
            raise OSError("offline")

        monkeypatch.setattr(auth_http, "open_url", _offline)
        entry = WorkflowCatalogEntry(
            url=url,
            name="test",
            priority=1,
            install_allowed=True,
        )

        with pytest.raises(WorkflowCatalogError, match="Failed to fetch catalog"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

    def test_search_with_non_string_fields(self, project_dir, monkeypatch):
        """Non-string workflow fields (null/int name/description) must not
        raise TypeError in search — StepCatalog.search already coerces these."""
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        monkeypatch.setattr(catalog, "_get_merged_workflows", lambda **kw: {
            "42": {
                "id": 42,
                "name": None,
                "description": 99,
                "_catalog_name": "test",
                "_install_allowed": True,
            },
        })

        assert len(catalog.search()) == 1
        assert len(catalog.search(query="42")) == 1
        assert len(catalog.search(query="missing")) == 0

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

    @pytest.mark.parametrize("body", ["[]\n", "false\n", "0\n", "''\n"])
    def test_falsy_non_mapping_config_rejected(self, project_dir, body):
        """A FALSY non-mapping top-level config ([], false, 0, '') must raise,
        like a truthy non-mapping (5, a bare list) already does. The previous
        ``yaml.safe_load(...) or {}`` coerced these to {} and silently swallowed
        them, diverging from the truthy case."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="expected a mapping"):
            catalog._load_catalog_config(config_path)

    @pytest.mark.parametrize("body", ["catalogs: {}\n", "catalogs: ''\n", "catalogs: 0\n", "catalogs: false\n"])
    def test_falsy_non_list_catalogs_rejected(self, project_dir, body):
        """A FALSY non-list ``catalogs:`` value must raise, like a truthy one
        (``catalogs: 5``) already does. The shape check sat behind the emptiness
        check, so these were silently swallowed as "no catalogs"."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="'catalogs' must be a list"):
            catalog._load_catalog_config(config_path)

    @pytest.mark.parametrize("body", ["catalogs:\n", "catalogs: []\n"])
    def test_absent_or_empty_catalogs_is_noop(self, project_dir, body):
        """An explicit ``catalogs:`` null or an empty list stays a valid no-op —
        the layer contributes nothing and resolution falls through."""
        from specify_cli.workflows.catalog import WorkflowCatalog

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = WorkflowCatalog(project_dir)
        assert catalog._load_catalog_config(config_path) is None

    @pytest.mark.parametrize("body", ["", "# only a comment\n", "null\n", "~\n"])
    def test_empty_or_null_config_is_noop(self, project_dir, body):
        """An empty document, comment-only file, or explicit top-level null is a
        valid no-op: the loader returns None so that config layer is skipped and
        get_active_catalogs falls through to the next one. It must NOT be
        confused with a falsy non-mapping, which raises."""
        from specify_cli.workflows.catalog import WorkflowCatalog

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = WorkflowCatalog(project_dir)
        assert catalog._load_catalog_config(config_path) is None

    @pytest.mark.parametrize("bad_priority", [True, False, float("inf")])
    def test_config_priority_bool_or_inf_rejected(self, project_dir, bad_priority):
        """`priority: true` must not be silently coerced to 1, and `priority: .inf`
        must not crash with an uncaught OverflowError — both raise a clean
        validation error (parity with the base CatalogStackBase loader)."""
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "bad",
                "url": "https://example.com/wf-catalog.json",
                "priority": bad_priority,
                "install_allowed": True,
            }]
        }))
        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="Invalid priority|expected integer"):
            catalog.get_active_catalogs()

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

    @pytest.mark.parametrize(
        "url",
        [
            "https://[::1",              # unterminated IPv6 bracket
            "https://[not-an-ip]/x",     # bracketed non-IP host
            "https://example.com:notaport/catalog.json",
        ],
    )
    def test_validate_url_malformed_raises_validation_error(self, project_dir, url):
        """A malformed authority must raise WorkflowValidationError, not leak a
        raw ValueError.

        ``urlparse``/``.hostname`` raise ValueError on a malformed IPv6
        authority. The command handler only catches WorkflowValidationError,
        so a raw ValueError would surface as an uncaught traceback instead of a
        clean 'Error:' message + exit 1. Mirrors specify_cli.catalogs (#3435).
        """
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowValidationError,
        )

        catalog = WorkflowCatalog(project_dir)
        with pytest.raises(WorkflowValidationError, match="malformed"):
            catalog._validate_catalog_url(url)

    def test_fetch_malformed_redirect_target_raises_catalog_error(
        self, project_dir, monkeypatch
    ):
        """A malformed post-redirect URL must raise WorkflowCatalogError, not a
        raw ValueError.

        The fetch path re-validates ``resp.geturl()`` after following redirects,
        so a hostile/broken redirect to a malformed authority
        (``https://[::1``) hits ``urlparse``/``.hostname`` and raises
        ``ValueError``. Without the guard that ValueError is re-wrapped by the
        broad ``except`` as ``Failed to fetch catalog ...: Invalid IPv6 URL``;
        the guard turns it into a clean ``... malformed URL ...`` refusal. The
        initial ``entry.url`` is valid so validation only trips on the redirect
        target. Mirrors specify_cli.catalogs (#3435).
        """
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            WorkflowCatalogError,
        )
        from specify_cli.authentication import http as auth_http

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{}"

            def geturl(self):
                # A redirect landing on a malformed IPv6 authority.
                return "https://[::1"

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        catalog = WorkflowCatalog(project_dir)
        entry = WorkflowCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        # A fresh project_dir has no cache to fall back to, so the error
        # propagates instead of being masked by a stale-cache read.
        with pytest.raises(WorkflowCatalogError, match="malformed"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

    def test_fetch_validates_every_redirect_hop(self, project_dir, monkeypatch):
        """A redirect_validator is passed to open_url and rejects a non-HTTPS
        INTERMEDIATE hop — closing the https -> http -> attacker-https chain a
        terminal-URL-only check would miss. Mirrors presets/extensions
        (#3523 / #3524)."""
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            WorkflowCatalogError,
        )
        from specify_cli.authentication import http as auth_http

        captured = {}

        def fake_open(url, timeout=30, redirect_validator=None):
            captured["rv"] = redirect_validator
            # Simulate the hop urllib validates before following the redirect.
            redirect_validator(
                "https://good.example/catalog.json", "http://evil.test/hop"
            )
            raise AssertionError("redirect_validator should have raised")

        monkeypatch.setattr(auth_http, "open_url", fake_open)

        catalog = WorkflowCatalog(project_dir)
        entry = WorkflowCatalogEntry(
            url="https://good.example/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        with pytest.raises(WorkflowCatalogError, match="HTTPS"):
            catalog._fetch_single_catalog(entry, force_refresh=True)
        assert captured["rv"] is not None

    def test_fetch_rejects_oversized_catalog_response(
        self, project_dir, monkeypatch
    ):
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows import catalog as catalog_module
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            WorkflowCatalogError,
        )

        monkeypatch.setattr(catalog_module, "MAX_JSON_CATALOG_BYTES", 32)
        requested_sizes: list[int] = []

        class _FakeResponse:
            def __init__(self):
                self.body = b"x" * 64
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/catalog.json"

            def read(self, size=-1):
                requested_sizes.append(size)
                assert size >= 0
                chunk_size = min(size, 7)
                chunk = self.body[self.offset : self.offset + chunk_size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        catalog = WorkflowCatalog(project_dir)
        entry = WorkflowCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )

        with pytest.raises(WorkflowCatalogError, match="exceeds maximum size"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert requested_sizes
        assert not catalog.cache_dir.exists()

    def test_fetch_skips_json_parse_on_oversized_response(
        self, project_dir, monkeypatch
    ):
        """Regression: json.loads must never be reached when the response
        exceeds MAX_JSON_CATALOG_BYTES — the bounded reader must reject it
        first."""
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows import catalog as catalog_module
        from specify_cli.workflows.catalog import (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            WorkflowCatalogError,
        )

        monkeypatch.setattr(catalog_module, "MAX_JSON_CATALOG_BYTES", 32)

        class _FakeResponse:
            def __init__(self):
                self.body = b"x" * 64

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/catalog.json"

            def read(self, size=-1):
                return self.body[:size]

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        json_loads_called = False
        original_json_loads = json.loads

        def _tracking_json_loads(*args, **kwargs):
            nonlocal json_loads_called
            json_loads_called = True
            return original_json_loads(*args, **kwargs)

        monkeypatch.setattr(json, "loads", _tracking_json_loads)

        catalog = WorkflowCatalog(project_dir)
        entry = WorkflowCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )

        with pytest.raises(WorkflowCatalogError, match="exceeds maximum size"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert not json_loads_called, "json.loads was called despite oversized response"

    def test_add_catalog(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://example.com/new-catalog.json", "my-catalog")

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/new-catalog.json"

    def test_add_catalog_with_existing_inf_priority(self, project_dir):
        """add_catalog() derives the new priority from existing ones via
        _coerce_priority; an existing `priority: .inf` must not crash it
        (int(float('inf')) is an OverflowError) — it is treated as 0 and the add
        succeeds."""
        from specify_cli.workflows.catalog import WorkflowCatalog

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "existing",
                "url": "https://a.example.com/c.json",
                "priority": float("inf"),
                "install_allowed": True,
            }]
        }))

        catalog = WorkflowCatalog(project_dir)
        catalog.add_catalog("https://b.example.com/c.json", "new")

        data = yaml.safe_load(config_path.read_text())
        new = next(c for c in data["catalogs"] if c["url"] == "https://b.example.com/c.json")
        assert new["priority"] == 1  # max(inf coerced to 0) + 1

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

    @pytest.mark.parametrize("bad", [[], False, 0, ""])
    def test_remove_catalog_rejects_falsy_non_mapping_config(
        self, project_dir, bad
    ):
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowValidationError

        config_path = project_dir / ".specify" / "workflow-catalogs.yml"
        config_path.write_text(yaml.safe_dump(bad), encoding="utf-8")

        with pytest.raises(WorkflowValidationError, match="expected a mapping"):
            WorkflowCatalog(project_dir).remove_catalog(0)

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
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("deploy", {"name": "Deploy", "version": "1.0.0", "type_key": "deploy"})

        entry = registry.get("deploy")
        assert entry is not None
        assert entry["name"] == "Deploy"
        assert "installed_at" in entry

    def test_add_does_not_mutate_input_metadata(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

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
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("deploy", {"name": "Deploy", "type_key": "deploy"})
        assert registry.is_installed("deploy")

        registry.remove("deploy")
        assert not registry.is_installed("deploy")

    def test_remove_missing_returns_false(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        removed = registry.remove("nonexistent")
        assert removed is False

    def test_list(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.add("step-a", {"name": "A", "type_key": "step-a"})
        registry.add("step-b", {"name": "B", "type_key": "step-b"})

        installed = registry.list()
        assert "step-a" in installed
        assert "step-b" in installed

    def test_is_installed(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        assert not registry.is_installed("missing")

        registry.add("exists", {"name": "Exists", "type_key": "exists"})
        assert registry.is_installed("exists")

    def test_persistence(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

        registry1 = StepRegistry(project_dir)
        registry1.add("deploy", {"name": "Deploy", "type_key": "deploy"})

        registry2 = StepRegistry(project_dir)
        assert registry2.is_installed("deploy")

    def test_corrupted_registry_resets(self, project_dir):
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.steps_dir.mkdir(parents=True, exist_ok=True)
        registry.registry_path.write_text("not json", encoding="utf-8")

        # Loading again should reset
        registry2 = StepRegistry(project_dir)
        assert registry2.list() == {}

    def test_registry_missing_steps_key_resets(self, project_dir):
        """Valid JSON but missing 'steps' key should not crash add/get."""
        from specify_cli.workflows.step.catalog import StepRegistry
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
        from specify_cli.workflows.step.catalog import StepRegistry
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
        from specify_cli.workflows.step.catalog import StepRegistry
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
        from specify_cli.workflows.step.catalog import StepRegistry, StepValidationError

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

    # -- Config shape guards ----------------------------------------------
    # StepCatalog._load_catalog_config is a duplicated twin of
    # WorkflowCatalog._load_catalog_config, so it needs its own coverage: a
    # regression in one loader would not be caught by the other's tests.

    @pytest.mark.parametrize("body", ["[]\n", "false\n", "0\n", "''\n"])
    def test_falsy_non_mapping_config_rejected(self, project_dir, body):
        """A FALSY non-mapping top level had the same ``or {}`` coercion, which
        bypassed the isinstance guard. It must raise like a truthy non-mapping."""
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="expected a mapping"):
            catalog._load_catalog_config(config_path)

    @pytest.mark.parametrize(
        "body", ["catalogs: {}\n", "catalogs: ''\n", "catalogs: 0\n", "catalogs: false\n"]
    )
    def test_falsy_non_list_catalogs_rejected(self, project_dir, body):
        """...and the same nested guard: a FALSY non-list ``catalogs:`` value must
        raise rather than being swallowed as "no catalogs"."""
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="'catalogs' must be a list"):
            catalog._load_catalog_config(config_path)

    @pytest.mark.parametrize(
        "body",
        ["", "# only a comment\n", "null\n", "~\n", "catalogs:\n", "catalogs: []\n"],
    )
    def test_empty_or_null_config_is_noop(self, project_dir, body):
        """An empty document, explicit null, or absent/empty ``catalogs:`` stays a
        valid no-op — the layer contributes nothing and resolution falls
        through."""
        from specify_cli.workflows.step.catalog import StepCatalog

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")
        catalog = StepCatalog(project_dir)
        assert catalog._load_catalog_config(config_path) is None

    def test_default_catalogs(self, project_dir, monkeypatch):
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.setattr(Path, "home", lambda: project_dir)
        monkeypatch.delenv("SPECKIT_STEP_CATALOG_URL", raising=False)
        catalog = StepCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 2
        assert entries[0].name == "default"
        assert entries[1].name == "community"

    def test_env_var_override(self, project_dir, monkeypatch):
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.setenv("SPECKIT_STEP_CATALOG_URL", "https://example.com/step-catalog.json")
        catalog = StepCatalog(project_dir)
        entries = catalog.get_active_catalogs()
        assert len(entries) == 1
        assert entries[0].name == "env-override"
        assert entries[0].url == "https://example.com/step-catalog.json"

    def test_project_level_config(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog

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

    @pytest.mark.parametrize("bad_priority", [True, False, float("inf")])
    def test_config_priority_bool_or_inf_rejected(self, project_dir, bad_priority):
        """`priority: true`/`.inf` in a step-catalog config raise a clean
        validation error instead of coercing to 1 / crashing with OverflowError."""
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "bad",
                "url": "https://example.com/step-catalog.json",
                "priority": bad_priority,
                "install_allowed": True,
            }]
        }))
        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="Invalid priority|expected integer"):
            catalog.get_active_catalogs()

    def test_validate_url_http_rejected(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="HTTPS"):
            catalog._validate_catalog_url("http://evil.com/step-catalog.json")

    def test_validate_url_localhost_http_allowed(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        # Should not raise
        catalog._validate_catalog_url("http://localhost:8080/step-catalog.json")

    @pytest.mark.parametrize(
        "url",
        [
            "https://[::1",              # unterminated IPv6 bracket
            "https://[not-an-ip]/x",     # bracketed non-IP host
            "https://example.com:notaport/steps.json",
        ],
    )
    def test_validate_url_malformed_raises_validation_error(self, project_dir, url):
        """A malformed authority must raise StepValidationError, not leak a raw
        ValueError past the command handler (which only catches
        StepValidationError). Mirrors specify_cli.catalogs (#3435).
        """
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="malformed"):
            catalog._validate_catalog_url(url)

    def test_fetch_malformed_redirect_target_raises_catalog_error(
        self, project_dir, monkeypatch
    ):
        """A malformed post-redirect URL must raise StepCatalogError, not a raw
        ValueError.

        The fetch path re-validates ``resp.geturl()`` after redirects, so a
        broken redirect to a bracketed non-IP host (``https://[not-an-ip]/x``)
        makes ``urlparse``/``.hostname`` raise ``ValueError``. Without the guard
        that leaks out as ``... Invalid IPv6 URL`` re-wrapping; the guard turns
        it into a clean ``... malformed URL ...`` refusal. The initial
        ``entry.url`` is valid so validation only trips on the redirect target.
        Mirrors specify_cli.catalogs (#3435).
        """
        from specify_cli.workflows.step.catalog import (
            StepCatalog,
            StepCatalogEntry,
            StepCatalogError,
        )
        from specify_cli.authentication import http as auth_http

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{}"

            def geturl(self):
                # A redirect landing on a bracketed non-IP authority.
                return "https://[not-an-ip]/x"

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        catalog = StepCatalog(project_dir)
        entry = StepCatalogEntry(
            url="https://example.com/steps.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        # A fresh project_dir has no cache to fall back to, so the error
        # propagates instead of being masked by a stale-cache read.
        with pytest.raises(StepCatalogError, match="malformed"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

    def test_fetch_validates_every_redirect_hop(self, project_dir, monkeypatch):
        """A redirect_validator is passed to open_url and rejects a non-HTTPS
        INTERMEDIATE hop — closing the https -> http -> attacker-https chain a
        terminal-URL-only check would miss. Mirrors presets/extensions
        (#3523 / #3524)."""
        from specify_cli.workflows.step.catalog import (
            StepCatalog,
            StepCatalogEntry,
            StepCatalogError,
        )
        from specify_cli.authentication import http as auth_http

        captured = {}

        def fake_open(url, timeout=30, redirect_validator=None):
            captured["rv"] = redirect_validator
            # Simulate the hop urllib validates before following the redirect.
            redirect_validator(
                "https://good.example/steps.json", "http://evil.test/hop"
            )
            raise AssertionError("redirect_validator should have raised")

        monkeypatch.setattr(auth_http, "open_url", fake_open)

        catalog = StepCatalog(project_dir)
        entry = StepCatalogEntry(
            url="https://good.example/steps.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        with pytest.raises(StepCatalogError, match="HTTPS"):
            catalog._fetch_single_catalog(entry, force_refresh=True)
        assert captured["rv"] is not None

    def test_fetch_rejects_oversized_catalog_response(
        self, project_dir, monkeypatch
    ):
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import catalog as catalog_module
        from specify_cli.workflows.step.catalog import (
            StepCatalog,
            StepCatalogEntry,
            StepCatalogError,
        )

        monkeypatch.setattr(catalog_module, "MAX_JSON_CATALOG_BYTES", 32)
        requested_sizes: list[int] = []

        class _FakeResponse:
            def __init__(self):
                self.body = b"x" * 64
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/steps.json"

            def read(self, size=-1):
                requested_sizes.append(size)
                assert size >= 0
                chunk_size = min(size, 7)
                chunk = self.body[self.offset : self.offset + chunk_size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        catalog = StepCatalog(project_dir)
        entry = StepCatalogEntry(
            url="https://example.com/steps.json",
            name="test",
            priority=1,
            install_allowed=True,
        )

        with pytest.raises(StepCatalogError, match="exceeds maximum size"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert requested_sizes
        assert not catalog.cache_dir.exists()

    def test_fetch_skips_json_parse_on_oversized_response(
        self, project_dir, monkeypatch
    ):
        """Regression: json.loads must never be reached when the response
        exceeds MAX_JSON_CATALOG_BYTES — the bounded reader must reject it
        first."""
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows import catalog as catalog_module
        from specify_cli.workflows.catalog import (
            StepCatalog,
            StepCatalogEntry,
            StepCatalogError,
        )

        monkeypatch.setattr(catalog_module, "MAX_JSON_CATALOG_BYTES", 32)

        class _FakeResponse:
            def __init__(self):
                self.body = b"x" * 64

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/steps.json"

            def read(self, size=-1):
                return self.body[:size]

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(),
        )

        json_loads_called = False
        original_json_loads = json.loads

        def _tracking_json_loads(*args, **kwargs):
            nonlocal json_loads_called
            json_loads_called = True
            return original_json_loads(*args, **kwargs)

        monkeypatch.setattr(json, "loads", _tracking_json_loads)

        catalog = StepCatalog(project_dir)
        entry = StepCatalogEntry(
            url="https://example.com/steps.json",
            name="test",
            priority=1,
            install_allowed=True,
        )

        with pytest.raises(StepCatalogError, match="exceeds maximum size"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert not json_loads_called, "json.loads was called despite oversized response"

    def test_add_catalog(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/new-steps.json", "my-steps")

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/new-steps.json"

    def test_add_catalog_with_existing_inf_priority(self, project_dir):
        """Step-catalog add_catalog() must not crash when an existing entry has a
        `priority: .inf` (int(float('inf')) is an OverflowError) — _coerce_priority
        treats it as 0 and the add succeeds."""
        from specify_cli.workflows.step.catalog import StepCatalog

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.dump({
            "catalogs": [{
                "name": "existing",
                "url": "https://a.example.com/s.json",
                "priority": float("inf"),
                "install_allowed": True,
            }]
        }))

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://b.example.com/s.json", "new")

        data = yaml.safe_load(config_path.read_text())
        new = next(c for c in data["catalogs"] if c["url"] == "https://b.example.com/s.json")
        assert new["priority"] == 1  # max(inf coerced to 0) + 1

    def test_add_catalog_empty_yaml_file(self, project_dir):
        """An empty YAML config file should be treated as empty, not corrupted."""
        from specify_cli.workflows.step.catalog import StepCatalog

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text("", encoding="utf-8")

        catalog = StepCatalog(project_dir)
        # Should not raise StepValidationError "corrupted"
        catalog.add_catalog("https://example.com/steps.json", "my-steps")

        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1
        assert data["catalogs"][0]["url"] == "https://example.com/steps.json"

    @pytest.mark.parametrize("bad", [[], False, 0, ""])
    def test_add_catalog_rejects_falsy_non_mapping_config(
        self, project_dir, bad
    ):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        original = yaml.safe_dump(bad)
        config_path.write_text(original, encoding="utf-8")

        with pytest.raises(StepValidationError, match="expected a mapping"):
            StepCatalog(project_dir).add_catalog(
                "https://example.com/steps.json", "my-steps"
            )

        assert config_path.read_text(encoding="utf-8") == original

    def test_add_catalog_duplicate_rejected(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/steps.json")

        with pytest.raises(StepValidationError, match="already configured"):
            catalog.add_catalog("https://example.com/steps.json")

    def test_remove_catalog(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/s1.json", "first")
        catalog.add_catalog("https://example.com/s2.json", "second")

        removed = catalog.remove_catalog(0)
        assert removed == "first"

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        data = yaml.safe_load(config_path.read_text())
        assert len(data["catalogs"]) == 1

    def test_remove_catalog_invalid_index(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        catalog.add_catalog("https://example.com/s1.json")

        with pytest.raises(StepValidationError, match="out of range"):
            catalog.remove_catalog(5)

    @pytest.mark.parametrize("bad", [[], False, 0, ""])
    def test_remove_catalog_rejects_falsy_non_mapping_config(
        self, project_dir, bad
    ):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        config_path = project_dir / ".specify" / "step-catalogs.yml"
        config_path.write_text(yaml.safe_dump(bad), encoding="utf-8")

        with pytest.raises(StepValidationError, match="expected a mapping"):
            StepCatalog(project_dir).remove_catalog(0)

    def test_remove_catalog_no_config(self, project_dir):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError

        catalog = StepCatalog(project_dir)
        with pytest.raises(StepValidationError, match="No step catalog config file found"):
            catalog.remove_catalog(0)

    def test_add_catalog_wraps_write_oserror(self, project_dir, monkeypatch):
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError
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
        from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError
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
        from specify_cli.workflows.step.catalog import StepCatalog

        catalog = StepCatalog(project_dir)
        configs = catalog.get_catalog_configs()
        assert len(configs) == 2
        assert configs[0]["name"] == "default"
        assert isinstance(configs[0]["install_allowed"], bool)

    def test_search_with_mock_catalog(self, project_dir, monkeypatch):
        from specify_cli.workflows.step.catalog import StepCatalog

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
        from specify_cli.workflows.step.catalog import StepCatalog

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
        from specify_cli.workflows.step.catalog import StepCatalog, StepCatalogEntry

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
        from specify_cli.workflows.step.catalog import StepCatalog

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

    _WF_GATE_VERDICT = """
schema_version: "1.0"
workflow:
  id: "resume-gate-verdict-wf"
  name: "Resume Gate Verdict WF"
  version: "1.0.0"
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: gate
    type: gate
    message: "Review"
    options: [approve, reject]
    on_reject: retry
    verdict_input: spec_verdict
"""

    _WF_RUNTIME_CONFIG = """
schema_version: "1.0"
workflow:
  id: "resume-runtime-config-wf"
  name: "Resume Runtime Config WF"
  version: "1.0.0"
inputs:
  config:
    type: string
    default: "./initial-agent.yaml"
  agent_name:
    type: string
    default: "initial-root"
  model_name:
    type: string
    default: "initial/model"
steps:
  - id: implement
    type: command
    command: speckit.implement
    integration: docker-agent
    integration_args:
      - "{{ inputs.config }}"
    integration_options:
      agent: "{{ inputs.agent_name }}"
      safety: balanced
    model: "{{ inputs.model_name }}"
"""

    _WF_DYNAMIC_INTEGRATION = """
schema_version: "1.0"
workflow:
  id: "resume-dynamic-integration-wf"
  name: "Resume Dynamic Integration WF"
  version: "1.0.0"
inputs:
  integration:
    type: string
    default: docker-agent
  config:
    type: string
    default: "./initial-agent.yaml"
steps:
  - id: implement
    type: command
    command: speckit.implement
    integration: "{{ inputs.integration }}"
    integration_args:
      - "{{ inputs.config }}"
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

    def test_resume_re_resolves_complete_integration_config(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import WorkflowDefinition

        calls = []
        return_codes = iter((1, 0))

        def fake_run(args, **kwargs):
            calls.append(args)
            return type("Result", (), {"returncode": next(return_codes)})()

        monkeypatch.delenv(
            "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda name: (
                "/usr/bin/docker-agent"
                if name in {"docker-agent", "/usr/bin/docker-agent"}
                else None
            ),
        )
        monkeypatch.setattr("subprocess.run", fake_run)

        definition = WorkflowDefinition.from_string(self._WF_RUNTIME_CONFIG)
        engine = self._engine(project_dir)
        state = engine.execute(definition)

        assert state.status is RunStatus.FAILED
        assert state.step_results["implement"]["integration_args"] == [
            "./initial-agent.yaml"
        ]
        assert state.step_results["implement"]["integration_options"] == {
            "agent": "initial-root",
            "safety": "balanced",
        }

        resumed = engine.resume(
            state.run_id,
            {
                "config": "./changed-on-resume.yaml",
                "agent_name": "changed-root",
                "model_name": "changed/model",
            },
        )

        assert resumed.status is RunStatus.COMPLETED
        assert resumed.inputs["config"] == "./changed-on-resume.yaml"
        assert len(calls) == 2
        assert "./initial-agent.yaml" in calls[0]
        assert "./changed-on-resume.yaml" in calls[1]
        assert "./initial-agent.yaml" not in calls[1]
        assert calls[1][calls[1].index("--agent") + 1] == "changed-root"
        assert calls[1][calls[1].index("--model") + 1] == "changed/model"

    def test_resume_does_not_mix_new_integration_with_old_runtime_config(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import WorkflowDefinition

        monkeypatch.delenv(
            "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False
        )
        monkeypatch.setattr(
            "shutil.which",
            lambda name: (
                "/usr/bin/docker-agent"
                if name in {"docker-agent", "/usr/bin/docker-agent"}
                else None
            ),
        )
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: type("Result", (), {"returncode": 1})(),
        )

        definition = WorkflowDefinition.from_string(self._WF_DYNAMIC_INTEGRATION)
        engine = self._engine(project_dir)
        state = engine.execute(definition)
        assert state.status is RunStatus.FAILED

        resumed = engine.resume(
            state.run_id,
            {"integration": "claude", "config": "./changed-on-resume.yaml"},
        )

        assert resumed.status is RunStatus.FAILED
        step_result = resumed.step_results["implement"]
        assert step_result["integration"] == "claude"
        assert step_result["integration_args"] == ["./changed-on-resume.yaml"]
        assert "Integration 'claude'" in (step_result["error"] or "")
        assert "./initial-agent.yaml" not in str(step_result)

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

    def test_resume_rejects_legacy_invalid_options_before_state_mutation(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.base import RunStatus
        from specify_cli.workflows.engine import RunState, WorkflowDefinition

        definition = WorkflowDefinition.from_string(self._WF_NUM)
        engine = self._engine(project_dir)
        state = engine.execute(definition)
        assert state.status == RunStatus.PAUSED

        workflow_copy = (
            project_dir
            / ".specify"
            / "workflows"
            / "runs"
            / state.run_id
            / "workflow.yml"
        )
        workflow_copy.write_text(
            self._WF_NUM.replace(
                'version: "1.0.0"', 'version: "1.0.0"\n  options: [max_tokens]'
            ),
            encoding="utf-8",
        )

        def fail_step_context(*args, **kwargs):
            raise AssertionError("StepContext must not be created")

        monkeypatch.setattr("specify_cli.workflows.engine.StepContext", fail_step_context)

        with pytest.raises(ValueError, match="'workflow.options' must be a mapping or null"):
            engine.resume(state.run_id, {"count": "5"})

        reloaded = RunState.load(state.run_id, project_dir)
        assert reloaded.status == RunStatus.PAUSED
        assert reloaded.error is None
        assert reloaded.inputs["count"] == 1

    def test_retry_verdict_input_is_consumed_and_can_be_replaced(self, project_dir):
        import json as _json
        from specify_cli.workflows.engine import WorkflowDefinition
        from specify_cli.workflows.base import RunStatus

        definition = WorkflowDefinition.from_string(self._WF_GATE_VERDICT)
        engine = self._engine(project_dir)

        state = engine.execute(definition, {"spec_verdict": "reject"})
        assert state.status == RunStatus.PAUSED
        assert state.inputs["spec_verdict"] == ""

        inputs_file = (
            project_dir / ".specify" / "workflows" / "runs" / state.run_id / "inputs.json"
        )
        assert _json.loads(inputs_file.read_text())["inputs"]["spec_verdict"] == ""

        paused_again = engine.resume(state.run_id)
        assert paused_again.status == RunStatus.PAUSED
        assert paused_again.inputs["spec_verdict"] == ""

        completed = engine.resume(state.run_id, {"spec_verdict": "approve"})
        assert completed.status == RunStatus.COMPLETED
        assert completed.step_results["gate"]["output"]["choice"] == "approve"













class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    def test_registry_add_rolls_back_memory_on_save_failure(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {"version": "1.0.0", "source": "catalog"})

        def boom():
            raise OSError("disk full")

        monkeypatch.setattr(registry, "save", boom)
        with pytest.raises(OSError):
            registry.add("align-wf", {"version": "2.0.0", "source": "catalog"})
        assert registry.get("align-wf")["version"] == "1.0.0"

        with pytest.raises(OSError):
            registry.add("other-wf", {"version": "1.0.0", "source": "catalog"})
        assert registry.get("other-wf") is None

    @pytest.mark.parametrize("error_type", [TypeError, ValueError])
    def test_registry_add_rolls_back_memory_on_serialization_failure(
        self, project_dir, monkeypatch, error_type
    ):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {"version": "1.0.0", "source": "catalog"})

        def boom():
            raise error_type("not JSON serializable")

        monkeypatch.setattr(registry, "save", boom)
        with pytest.raises(error_type):
            registry.add("align-wf", {"version": "2.0.0", "source": "catalog"})
        assert registry.get("align-wf")["version"] == "1.0.0"

        with pytest.raises(error_type):
            registry.add("other-wf", {"version": "1.0.0", "source": "catalog"})
        assert registry.get("other-wf") is None

    def test_registry_add_survives_non_dict_existing_entry(self, project_dir):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.data["workflows"]["align-wf"] = "corrupted"
        registry.add("align-wf", {"version": "1.0.0", "source": "catalog"})
        assert registry.get("align-wf")["version"] == "1.0.0"

    def test_step_registry_add_survives_non_dict_existing_entry(self, project_dir):
        """StepRegistry.add must treat a corrupted non-dict existing entry as
        absent rather than crash on existing.get() (parity with
        WorkflowRegistry.add)."""
        from specify_cli.workflows.step.catalog import StepRegistry

        registry = StepRegistry(project_dir)
        registry.data["steps"]["my-step"] = "corrupted"
        registry.add("my-step", {"version": "1.0.0"})
        assert registry.get("my-step")["version"] == "1.0.0"

    @pytest.mark.parametrize(
        "contents",
        [
            "not json",
            "[]",
            '{"schema_version": "1.0"}',
            '{"schema_version": "1.0", "workflows": "broken"}',
        ],
    )
    def test_registry_load_rejects_corrupt_contents(
        self, project_dir, contents
    ):
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.workflows_dir.mkdir(parents=True, exist_ok=True)
        registry.registry_path.write_text(contents, encoding="utf-8")

        with pytest.raises(OSError, match="corrupt"):
            WorkflowRegistry(project_dir)

        assert registry.registry_path.read_text(encoding="utf-8") == contents

    def test_registry_save_refuses_symlinked_parent(self, project_dir, tmp_path):
        """Construction now fails closed on a symlinked .specify just like
        an unreadable registry file: a symlinked parent must never be
        silently tolerated up to save() -- it must raise immediately."""
        from specify_cli.workflows.catalog import WorkflowRegistry

        outside = tmp_path / "outside-specify"
        outside.mkdir()
        specify_dir = project_dir / ".specify"
        if specify_dir.exists():
            shutil.rmtree(specify_dir)
        specify_dir.symlink_to(outside)
        with pytest.raises(OSError, match="symlink"):
            WorkflowRegistry(project_dir)
        assert not (outside / "workflows").exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod mode bits not reliable on Windows")
    def test_registry_save_preserves_existing_file_mode(self, project_dir):
        """A registry shared as 0640/0644 must keep that mode after a save,
        not be silently replaced by mkstemp's 0600 default -- otherwise
        every add/remove locks other project users out of a previously
        shared registry file."""
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("first-wf", {"name": "First"})
        registry.registry_path.chmod(0o644)

        registry.add("second-wf", {"name": "Second"})

        mode = stat.S_IMODE(registry.registry_path.stat().st_mode)
        assert mode == 0o644, f"expected 0644, got {oct(mode)}"

    @pytest.mark.skipif(not hasattr(os, "fchown"), reason="os.fchown is unavailable")
    def test_registry_save_preserves_existing_owner_group(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.catalog import WorkflowRegistry
        import specify_cli.workflows.catalog as catalog_mod

        registry = WorkflowRegistry(project_dir)
        registry.add("first-wf", {"name": "First"})
        existing = registry.registry_path.stat()
        calls: list[tuple[os.stat_result, int, int]] = []

        monkeypatch.setattr(
            catalog_mod.os,
            "fchown",
            lambda fd, uid, gid: calls.append((os.fstat(fd), uid, gid)),
        )
        registry.add("second-wf", {"name": "Second"})

        assert len(calls) == 1
        temp_stat, uid, gid = calls[0]
        assert stat.S_ISREG(temp_stat.st_mode)
        assert uid == existing.st_uid
        assert gid == existing.st_gid

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod mode bits not reliable on Windows")
    def test_registry_save_on_new_registry_uses_secure_default_mode(self, project_dir):
        """A brand-new registry file (no prior mode to preserve) should keep
        mkstemp's secure 0600 default rather than something more permissive."""
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("first-wf", {"name": "First"})

        mode = stat.S_IMODE(registry.registry_path.stat().st_mode)
        assert mode == 0o600, f"expected 0600, got {oct(mode)}"

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_registry_save_rejects_swapped_temp_without_touching_target(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.catalog import WorkflowRegistry
        import specify_cli.workflows.catalog as catalog_mod

        registry = WorkflowRegistry(project_dir)
        registry.add("first-wf", {"name": "First"})
        registry.registry_path.chmod(0o640)

        victim = project_dir / "victim.txt"
        victim.write_text("untouched", encoding="utf-8")
        victim.chmod(0o600)

        tmp_path = None
        real_mkstemp = catalog_mod.tempfile.mkstemp
        real_dump = catalog_mod.json.dump

        def tracking_mkstemp(*args, **kwargs):
            nonlocal tmp_path
            fd, name = real_mkstemp(*args, **kwargs)
            tmp_path = Path(name)
            return fd, name

        def swap_after_dump(*args, **kwargs):
            result = real_dump(*args, **kwargs)
            assert tmp_path is not None
            tmp_path.unlink()
            tmp_path.symlink_to(victim)
            return result

        monkeypatch.setattr(catalog_mod.tempfile, "mkstemp", tracking_mkstemp)
        monkeypatch.setattr(catalog_mod.json, "dump", swap_after_dump)

        with pytest.raises(OSError):
            registry.add("second-wf", {"name": "Second"})

        assert victim.read_text(encoding="utf-8") == "untouched"
        if sys.platform != "win32":
            assert stat.S_IMODE(victim.stat().st_mode) == 0o600
        assert not registry.registry_path.is_symlink()
        assert WorkflowRegistry(project_dir).is_installed("first-wf")

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod mode bits not reliable on Windows")
    def test_registry_save_failure_preserves_file_on_disk(self, project_dir, monkeypatch):
        """A failed dump must not truncate the persisted registry, and must
        not alter its on-disk mode either -- the chmod-to-match-existing-mode
        step operates on the temp file, never the target, so a failed save
        (which never reaches os.replace) cannot touch the original's mode."""
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {"version": "1.0.0", "source": "catalog"})
        registry.registry_path.chmod(0o644)

        import specify_cli.workflows.catalog as catalog_mod

        def boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(catalog_mod.json, "dump", boom)
        with pytest.raises(OSError):
            registry.add("align-wf", {"version": "2.0.0", "source": "catalog"})
        monkeypatch.undo()

        fresh = WorkflowRegistry(project_dir)
        assert fresh.get("align-wf")["version"] == "1.0.0"
        assert stat.S_IMODE(registry.registry_path.stat().st_mode) == 0o644
        assert not list(registry.workflows_dir.glob("*.tmp"))
