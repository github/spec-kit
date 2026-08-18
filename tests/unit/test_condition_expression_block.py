"""A string condition with no ``{{ }}`` block is never evaluated (always true)."""

import pytest
import yaml

from specify_cli.workflows.base import StepContext
from specify_cli.workflows.expressions import (
    condition_is_never_evaluated,
    evaluate_condition,
    format_condition_correction,
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


# --- An unterminated ``{{`` is the same defect, not a different one -----------
#
# ``_interpolate_expressions`` substitutes nothing when no ``}}`` follows the
# opening ``{{`` (its ``raw_close == -1`` branch appends the tail verbatim), so
# ``{{ inputs.count > 100`` is returned unchanged and coerced to true exactly
# like a brace-less string.

BACKSLASH = chr(92)

NEVER_EVALUATED = [
    "inputs.count > 100",        # no delimiter at all
    "{{ inputs.count > 100",     # opened, never closed
    "}} inputs.count > 100 {{",  # reversed: the only '{{' is last
]


@pytest.mark.parametrize("condition", NEVER_EVALUATED)
def test_incomplete_block_is_silently_true_and_is_flagged(condition):
    ctx = StepContext(inputs={"count": 5, "name": "abc"})
    assert evaluate_condition(condition, ctx) is True
    assert condition_is_never_evaluated(condition) is True


@pytest.mark.parametrize(
    "condition",
    [
        "{{ inputs.count > 100 }}",
        "{{ inputs.a }} and {{ inputs.b }}",
        "{{ inputs.text | default('}}') }}",  # literal '}}' inside an argument
    ],
)
def test_complete_block_is_not_flagged(condition):
    assert condition_is_never_evaluated(condition) is False


# --- The suggested correction has to survive a YAML round trip ---------------

TRICKY_CONDITIONS = [
    "inputs.count > 100",
    'inputs.name == "zzz"',                                   # double quote
    "inputs.name == 'zzz'",                                   # single quote
    'inputs.a == "x" and inputs.b == \'y\'',                  # both
    "inputs.path == 'C:" + BACKSLASH + "tmp'",                # backslash
    'inputs.path == "C:' + BACKSLASH + 'tmp"',                # backslash + quote
    '{{ inputs.name == "zzz"',                                # incomplete + quote
    "}} inputs.count > 100 {{",
]


@pytest.mark.parametrize("condition", TRICKY_CONDITIONS)
def test_correction_is_valid_yaml_and_round_trips(condition):
    """A correction the author cannot paste into their workflow is no correction."""
    loaded = yaml.safe_load("condition: " + format_condition_correction(condition))
    stripped = condition.strip().lstrip("{}").rstrip("{}").strip()
    assert loaded["condition"] == "{{ " + stripped + " }}"


@pytest.mark.parametrize("condition", TRICKY_CONDITIONS)
def test_correction_does_not_trip_the_validator_again(condition):
    loaded = yaml.safe_load("condition: " + format_condition_correction(condition))
    assert condition_is_never_evaluated(loaded["condition"]) is False


@pytest.mark.parametrize("condition", ["{{ inputs.count > 100", "}} a > 1 {{"])
def test_correction_replaces_a_stray_delimiter_instead_of_nesting_one(condition):
    corrected = format_condition_correction(condition)
    assert "{{ {{" not in corrected and "}} }}" not in corrected
    assert corrected.count("{{") == 1 and corrected.count("}}") == 1


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize("condition", ['inputs.name == "zzz"', "{{ inputs.count > 100"])
def test_validator_correction_is_yaml_safe(step_cls, condition):
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "never evaluated" in e]
    assert len(errors) == 1
    suggested = errors[0].split("Wrap the expression: ", 1)[1].rstrip(".")
    loaded = yaml.safe_load("condition: " + suggested)
    assert condition_is_never_evaluated(loaded["condition"]) is False
