"""A string condition with no ``{{ }}`` block is never evaluated (always true)."""

import pytest

from specify_cli.workflows.base import StepContext
from specify_cli.workflows.expressions import (
    condition_is_never_evaluated,
    evaluate_condition,
)
from specify_cli.workflows.steps.do_while import DoWhileStep
from specify_cli.workflows.steps.if_then import IfThenStep
from specify_cli.workflows.steps.while_loop import WhileStep

STEP_CLASSES = [IfThenStep, WhileStep, DoWhileStep]


@pytest.mark.parametrize(
    "condition",
    ["inputs.count > 100", "inputs.name == 'zzz'", "inputs.count < 3"],
)
def test_brace_less_condition_is_always_true_at_runtime(condition):
    """The behaviour the validator now warns about, pinned so it cannot drift."""
    ctx = StepContext(inputs={"count": 5, "name": "abc"})
    # Same expression with braces resolves to its real (false) value...
    assert evaluate_condition("{{ " + condition + " }}", ctx) is False
    # ...without them it is only non-empty text, so bool() makes it true.
    assert evaluate_condition(condition, ctx) is True


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
def test_validator_rejects_condition_without_expression_block(step_cls):
    config = {"id": "s1", "condition": "inputs.count > 100", "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "never evaluated" in e]
    assert len(errors) == 1
    assert "inputs.count > 100" in errors[0]
    # The message hands back the corrected form.
    assert '"{{ inputs.count > 100 }}"' in errors[0]


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize(
    "condition",
    ["{{ inputs.count > 100 }}", "true", "false", "TRUE", True, False, "", "   "],
)
def test_validator_accepts_evaluated_and_literal_conditions(step_cls, condition):
    """No false positives: braces, boolean literals and bools stay valid."""
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    assert not [e for e in step_cls().validate(config) if "never evaluated" in e]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("inputs.count > 100", True),
        ("{{ inputs.count > 100 }}", False),
        ("prefix {{ inputs.a }} suffix", False),
        ("true", False),
        ("False", False),
        ("", False),
        ("   ", False),
        (True, False),
        (["a"], False),
        (3, False),
    ],
)
def test_condition_is_never_evaluated(value, expected):
    assert condition_is_never_evaluated(value) is expected
