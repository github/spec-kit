"""A string condition with no ``{{ }}`` block is never evaluated (always true)."""

import pytest
import yaml

from specify_cli.workflows.base import StepContext
from specify_cli.workflows.expressions import (
    condition_has_malformed_expression_block,
    condition_is_never_evaluated,
    evaluate_condition,
    format_condition_correction,
    _has_unbalanced_quote,
    _has_unbalanced_bracket,
    _has_incomplete_operand,
    _unresolvable_term,
    _evaluator_rejects,
    _is_literal,
    _strip_stray_delimiters,
    _COMPARISON_OPERATORS,
    _WORD_OPERATORS,
    format_condition_remediation,
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
    ["{{ inputs.count > 100 }}", "true", "false", "TRUE", True, False, ""],
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
        # `bool("   ")` is true and evaluate_condition strips only around the
        # true/false keywords, so whitespace is a silent always-true, not a
        # definite False. Only "" coerces to False.
        ("   ", True),
        ("\t\n ", True),
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
    # A complete block does not vouch for the rest: interpolation leaves the
    # second fragment verbatim, and bool() makes the whole string true.
    "{{ true }} and {{ inputs.ready",
]

# A different fault, and the interpolator treats it differently: the quote-aware
# scan finds no close, but a raw '}}' exists further along, so
# _interpolate_expressions falls back to it and *evaluates* the truncated body.
# These are not "never evaluated" -- one leaves residual text that bool() makes
# true, the other reaches the filter parser and raises.
MALFORMED_BLOCKS = [
    "{{ inputs.x == '}}'",
    "{{ inputs.missing | default('oops }}",
    # Same, but the faulty block is the second one.
    "{{ inputs.name }} {{ inputs.missing | default('oops }}",
]


@pytest.mark.parametrize("condition", NEVER_EVALUATED)
def test_incomplete_block_is_silently_true_and_is_flagged(condition):
    ctx = StepContext(inputs={"count": 5, "name": "abc"})
    assert evaluate_condition(condition, ctx) is True
    assert condition_is_never_evaluated(condition) is True
    assert condition_has_malformed_expression_block(condition) is False


@pytest.mark.parametrize("condition", MALFORMED_BLOCKS)
def test_raw_close_fallback_is_malformed_not_never_evaluated(condition):
    """The block *is* evaluated, so it must not be reported as always true."""
    assert condition_has_malformed_expression_block(condition) is True
    assert condition_is_never_evaluated(condition) is False


def test_a_malformed_block_can_raise_rather_than_be_true():
    """The concrete case the "always true" wording got wrong.

    `default('oops` swallows the real close, the raw-close fallback hands the
    filter parser a truncated argument, and the run dies instead of taking a branch.
    """
    ctx = StepContext(inputs={"count": 5})
    with pytest.raises(ValueError):
        evaluate_condition("{{ inputs.missing | default('oops }}", ctx)


@pytest.mark.parametrize("condition", NEVER_EVALUATED + MALFORMED_BLOCKS)
def test_the_two_faults_are_mutually_exclusive(condition):
    assert condition_is_never_evaluated(condition) != condition_has_malformed_expression_block(condition)


@pytest.mark.parametrize(
    "condition",
    [
        "{{ inputs.count > 100 }}",
        "{{ inputs.a }} and {{ inputs.b }}",
        "{{ inputs.text | default('}}') }}",  # literal '}}' inside an argument
        "{{ inputs.x == '}}' }}",             # quoted '}}' then the real close
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
    # A YAML literal block hands the loader a real newline; a folded scalar
    # would lose it, so the correction has to escape rather than embed it.
    "inputs.x == 1\nand inputs.name == 'abc'",
    'he said "hi"\nthen left',                                # newline + quote
    "inputs.a == 'x\ty'",                                     # tab
    "inputs.a == 'x\ry'",                                     # carriage return
    "inputs.ten == 'mười'",                                   # non-ASCII operand
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


def test_correction_keeps_non_ascii_readable():
    """ensure_ascii=False: an operand should not turn into numeric escapes."""
    corrected = format_condition_correction("inputs.ten == 'mười'")
    assert "mười" in corrected
    assert chr(92) + "u" not in corrected


def test_whitespace_condition_is_flagged_but_the_empty_string_is_not():
    """Whitespace is the silent always-true this validator exists to catch.

    ``test_condition_whitespace_only_string_stays_truthy`` pins the runtime
    behaviour deliberately, so the mistake can only be caught at validation time.
    """
    assert evaluate_condition("   ", StepContext()) is True
    assert condition_is_never_evaluated("   ") is True

    assert evaluate_condition("", StepContext()) is False
    assert condition_is_never_evaluated("") is False


@pytest.mark.parametrize(
    "condition",
    [
        "prefix {{ inputs.ready",
        "inputs.ready }} suffix",
        "{{ inputs.a }} and {{ inputs.b",
    ],
)
def test_correction_removes_an_interior_delimiter_too(condition):
    """Trimming only the edges left the correction carrying an inner block.

    ``prefix {{ inputs.ready`` corrected to ``"{{ prefix {{ inputs.ready }}"``,
    whose complete outer block then walked back past this very validator.
    """
    corrected = format_condition_correction(condition)
    inner = yaml.safe_load("condition: " + corrected)["condition"]
    assert inner.count("{{") == 1 and inner.count("}}") == 1
    assert inner.startswith("{{ ") and inner.endswith(" }}")


def test_correction_keeps_a_delimiter_that_is_quoted_data():
    """``'}}'`` is an operand, not a block, so the stripper must not eat it."""
    corrected = format_condition_correction("{{ inputs.x == '}}'")
    inner = yaml.safe_load("condition: " + corrected)["condition"]
    assert inner == "{{ inputs.x == '}}' }}"
    assert condition_is_never_evaluated(inner) is False


def test_correction_preserves_spacing_inside_a_quoted_operand():
    """Whitespace is collapsed only where a delimiter was removed."""
    corrected = format_condition_correction('{{ inputs.name == "a  b"')
    inner = yaml.safe_load("condition: " + corrected)["condition"]
    assert inner == '{{ inputs.name == "a  b" }}'


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize("condition", MALFORMED_BLOCKS)
def test_validator_reports_malformed_rather_than_always_true(step_cls, condition):
    """The two faults need opposite advice, so they must not share a message.

    "never evaluated and is always true" is wrong here on both halves: the
    interpolator does evaluate the truncated body, and the result is not
    reliably true -- it can raise.
    """
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "'condition'" in e]

    assert len(errors) == 1
    assert "never evaluated" not in errors[0]
    assert "cannot close" in errors[0]
    assert "truncated expression" in errors[0]


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize("condition", MALFORMED_BLOCKS)
def test_malformed_message_offers_no_paste_ready_correction(step_cls, condition):
    """Deliberately no suggestion for this class.

    The fault is unbalanced delimiters or quotes, so the quote-aware stripper
    cannot tell operand from delimiter -- for `{{ inputs.missing | default('oops }}`
    it produces `"{{ inputs.missing | default('oops }} }}"`, which is not a fix.
    Naming the fault beats handing back something that looks authoritative and
    is not.
    """
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "'condition'" in e]
    assert "Wrap the expression" not in errors[0]
    assert errors[0].rstrip().endswith("Balance the delimiters and quotes.")


# A correction is only offered when wrapping would actually repair the condition.
# These two inputs reach the same "never evaluated" branch, but wrapping them
# produces something the author must not paste, so the advice names the fault
# instead. Both were previously advertised as paste-ready (Copilot review).
UNFIXABLE_BY_WRAPPING = [
    ("   ", "no expression here to wrap"),
    ("{{ inputs.name == 'abc", "quote opened in it is never closed"),
    ("'unterminated", "quote opened in it is never closed"),
    ("inputs.name ==", "missing an operand"),
    ("inputs.count >", "missing an operand"),
    ("inputs.ready and", "missing an operand"),
    ("inputs.x | ", "missing an operand"),
    ("inputs.f(", "brackets do not balance"),
]


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize("condition,expected", UNFIXABLE_BY_WRAPPING)
def test_no_paste_ready_correction_when_wrapping_would_not_repair(
    step_cls, condition, expected
):
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "'condition'" in e]

    assert len(errors) == 1
    assert "Wrap the expression" not in errors[0]
    assert expected in errors[0]


def test_wrapping_whitespace_would_invert_the_condition():
    """Why the blank case gets advice instead of a suggestion.

    `{{ }}` interpolates to the empty string, so pasting it turns an always-true
    condition into an always-false one -- a different defect, not a repair.
    """
    ctx = StepContext(inputs={})
    assert evaluate_condition("   ", ctx) is True
    assert evaluate_condition("{{ }}", ctx) is False


def test_wrapping_an_open_quote_inverts_the_condition():
    """Why the unbalanced-quote case gets advice instead of a suggestion.

    The raw-close fallback evaluates a truncated comparison and yields the string
    "False", which evaluate_condition then reads as the `false` keyword. Pasting
    the "correction" flips the condition rather than repairing it.
    """
    ctx = StepContext(inputs={"name": "Bob"})
    assert evaluate_condition("{{ inputs.name == 'abc", ctx) is True
    assert evaluate_condition("{{ inputs.name == 'abc }}", ctx) is False


@pytest.mark.parametrize(
    "text,unbalanced",
    [
        ("inputs.name == 'abc'", False),
        ('inputs.name == "abc"', False),
        ("inputs.name == 'abc", True),
        ('inputs.name == "abc', True),
        ("inputs.text == '\"'", False),
        ("inputs.count > 100", False),
    ],
)
def test_unbalanced_quote_scan(text, unbalanced):
    assert _has_unbalanced_quote(text) is unbalanced


# The property behind the case list above, stated once so a new malformed shape
# is caught by the invariant rather than by adding another fixture row.
# Genuine expressions only. TRICKY_CONDITIONS is a quoting/escaping fixture for
# the formatter and deliberately includes prose, so it must not be reused here.
OFFERED_CORRECTION_INPUTS = [
    "inputs.count > 100",
    'inputs.name == "zzz"',
    "inputs.name == 'zzz'",
    "{{ inputs.count > 100",
    "{{ true }} and {{ inputs.ready",
    "inputs.a and inputs.b",
    "inputs.name",
    "not inputs.ready",
    "inputs.tags | join(',')",
    # The tricky-quoting cases from TRICKY_CONDITIONS that really are expressions.
    # Listed rather than filtered out of that fixture, so adding prose there cannot
    # silently widen what this invariant claims.
    'inputs.a == "x" and inputs.b == \'y\'',
    "inputs.path == 'C:" + BACKSLASH + "tmp'",
    'inputs.path == "C:' + BACKSLASH + 'tmp"',
    "inputs.a == 'x\ty'",
    "inputs.a == 'x\ry'",
    "inputs.ten == 'mười'",
    '{{ inputs.name == "zzz"',
    "}} inputs.count > 100 {{",
]


@pytest.mark.parametrize("condition", OFFERED_CORRECTION_INPUTS)
def test_every_offered_correction_is_a_complete_expression(condition):
    """Whatever is advertised as paste-ready must pass our own validators.

    Both earlier rounds of this fix were partial because they enumerated broken
    shapes -- blank, then unbalanced quote. This asserts the property instead: if
    the remediation offers a correction at all, the wrapped form it hands back is
    a single complete block that neither validator objects to.
    """
    advice = format_condition_remediation(condition)
    assert advice.startswith("Wrap the expression: ")

    suggested = yaml.safe_load(
        "condition: " + advice.split("Wrap the expression: ", 1)[1].rstrip(".")
    )["condition"]
    assert condition_is_never_evaluated(suggested) is False
    assert condition_has_malformed_expression_block(suggested) is False


@pytest.mark.parametrize("condition,_reason", UNFIXABLE_BY_WRAPPING)
def test_withheld_corrections_would_indeed_have_been_broken(condition, _reason):
    """The other half: what is withheld really would not have survived wrapping.

    Guards against the gate growing over-eager and refusing to help with input it
    could have corrected.
    """
    core = _strip_stray_delimiters(condition).strip()
    wrapped = "{{ " + core + " }}"
    assert (
        not core
        or _has_unbalanced_quote(core)
        or _has_unbalanced_bracket(core)
        or _has_incomplete_operand(core)
        or condition_is_never_evaluated(wrapped)
        or condition_has_malformed_expression_block(wrapped)
    )


@pytest.mark.parametrize(
    "text,unbalanced",
    [
        ("inputs.f(1)", False),
        ("inputs.f(", True),
        ("inputs.f)", True),
        ("inputs.tags[0]", False),
        ("inputs.text == '('", False),
    ],
)
def test_unbalanced_bracket_scan(text, unbalanced):
    assert _has_unbalanced_bracket(text) is unbalanced


def test_incomplete_operand_reads_the_evaluator_operator_list():
    """The check must not restate the operator table it is predicting."""
    for op in _COMPARISON_OPERATORS:
        assert _has_incomplete_operand("inputs.a" + op) is True
        assert _has_incomplete_operand("inputs.a" + op + "inputs.b") is False


def test_incomplete_operand_covers_every_operator_the_evaluator_splits_on():
    """Hard-coded on purpose.

    Parametrising over `_COMPARISON_OPERATORS` shrinks with the constant, so
    dropping an operator from it would make that test pass vacuously -- the same
    can't-fail-when-it-matters shape this module exists to reject. Listing the
    operators here means removing one from the evaluator fails a test.
    """
    for op in ("!=", "==", ">=", "<=", ">", "<", " not in ", " in ", " and ", " or "):
        assert _has_incomplete_operand("inputs.a" + op) is True, op
        assert _has_incomplete_operand("inputs.a" + op + "inputs.b") is False, op


# Copilot round 3: the first two gates each inspected only one position. These pin
# every-position scanning, both ends, and bracket-type matching.
MULTI_POSITION_UNFIXABLE = [
    ("inputs.a == inputs.b ==", "missing an operand"),   # trailing, not the first op
    ("and inputs.ready", "missing an operand"),           # leading boolean operator
    ("inputs.a not in", "missing an operand"),            # trailing word operator
    ("in inputs.tags", "missing an operand"),             # leading word operator
    ("inputs.f(]", "brackets do not balance"),            # matched count, wrong types
    ("inputs.f(]", "brackets do not balance"),
    ("inputs.items | length", "the evaluator rejects it"),
    ("inputs.tags | join", "used in an unsupported form"),
    ('he said "hi" then left', "is not a name the evaluator can resolve"),
    ("inputs.count+1", "is not a valid path segment"),
    ("inputs.a === inputs.b", "is not a name the evaluator can resolve"),
    ("bogus == 'x'", "is not one of the namespace roots"),
    ("inputs.payload | from_json()", "the evaluator rejects it"),
    # `_find_top_level` matches " and " with literal spaces, so a newline before
    # the keyword is not an operator: the wrapped form evaluates False where the
    # same expression with a space evaluates True.
    ("inputs.x == 1\nand inputs.name == 'abc'", "is not a name the evaluator can resolve"),
]


@pytest.mark.parametrize("step_cls", STEP_CLASSES)
@pytest.mark.parametrize("condition,expected", MULTI_POSITION_UNFIXABLE)
def test_gates_inspect_every_position_not_just_the_first(step_cls, condition, expected):
    config = {"id": "s1", "condition": condition, "then": [], "steps": []}
    errors = [e for e in step_cls().validate(config) if "'condition'" in e]

    assert len(errors) == 1
    assert "Wrap the expression" not in errors[0]
    assert expected in errors[0]


@pytest.mark.parametrize(
    "text,unbalanced",
    [
        ("inputs.f(]", True),      # counts match, types do not
        ("inputs.f[)", True),
        ("inputs.f(}", True),
        ("inputs.f([])", False),
        ("inputs.f(])", True),
        ("inputs.text == '(]'", False),   # mismatched pair inside a quoted operand
    ],
)
def test_bracket_scan_matches_types_not_just_depth(text, unbalanced):
    assert _has_unbalanced_bracket(text) is unbalanced


def test_word_operators_are_derived_from_the_evaluator_table():
    """Guards the derivation, not the literal tuple.

    If a space-delimited operator is added to _COMPARISON_OPERATORS, the end-of-core
    checks must pick it up without another edit here.
    """
    assert _WORD_OPERATORS == (" or ", " and ", " not in ", " in ")
    for op in _WORD_OPERATORS:
        assert _has_incomplete_operand("inputs.a" + op.rstrip()) is True, op
        assert _has_incomplete_operand(op.lstrip() + "inputs.a") is True, op


def test_the_probe_reports_what_the_evaluator_reports():
    """The parse probe must not restate the filter table.

    Four review rounds each found a shape the structural gates did not know about.
    Asking the evaluator removes that class: any filter used under an unknown name
    or in an unsupported form is reported by the code that will run.
    """
    assert _evaluator_rejects("inputs.items | length") is not None
    assert _evaluator_rejects("inputs.tags | join") is not None
    assert _evaluator_rejects("inputs.tags | join(',')") is None
    assert _evaluator_rejects("inputs.count > 100") is None


@pytest.mark.parametrize(
    "text,not_a_path",
    [
        ("inputs.name", False),
        ("inputs.a.b.c", False),
        ("inputs.tags[0]", False),
        ("not inputs.ready", False),
        ("true", False),
        ("42", False),
        ("'a literal'", False),
        ("inputs.count > 100", False),      # has an operator, not a bare term
        ("inputs.count+1", True),           # the evaluator has no arithmetic
        ('he said "hi" then left', True),
        # _resolve_dot_path keys on [w-]+, so a key literally named "2bad" resolves.
        ("inputs.2bad", False),
        ("inputs.tags[foo]", True),
        ("inputs.matrix[0][1]", True),
        # Round 7: an operand one level down, which the single-term gate never saw.
        ("inputs.a === inputs.b", True),
        ("bogus", True),
        ("bogus == 'x'", True),
        ("item.name == 'x'", False),
        ("fan_in.results | join(',')", False),
        ("context.run_id != ''", False),
    ],
)
def test_operands_must_be_literals_or_known_paths(text, not_a_path):
    """Recursing to the leaves replaced the single-term check.

    The old gate only looked at a core with no operator, so `inputs.a === inputs.b`
    and `bogus == 'x'` walked past it. This asserts the reachable leaf instead.
    """
    assert (_unresolvable_term(text) is not None) is not_a_path


@pytest.mark.parametrize(
    "condition",
    [
        # Valid against a string output and exercised in tests/test_workflows.py.
        # The probe hands from_json a dict, so treating every probe error as a
        # rejection withheld a correction from a good condition.
        "steps.emit.output.stdout | from_json",
        # The filter argument is resolved from the namespace too.
        "inputs.tags | join(inputs.separator)",
    ],
)
def test_probe_value_errors_are_not_treated_as_rejections(condition):
    assert _evaluator_rejects(condition) is None
    assert format_condition_remediation(condition).startswith("Wrap the expression: ")


@pytest.mark.parametrize(
    "condition",
    ["inputs.items | length", "inputs.tags | join"],
)
def test_filter_wiring_errors_are_still_rejections(condition):
    """The other half: a filter named wrong or used wrong is the author's text."""
    assert _evaluator_rejects(condition) is not None
    assert "Wrap the expression" not in format_condition_remediation(condition)


@pytest.mark.parametrize(
    "condition,literal",
    [
        ("42", True),
        ("3.14", True),
        ("-7", True),
        # `1e3` has no "." so the evaluator calls int() on it, which fails; it then
        # falls through to a path lookup. float() alone accepted it here.
        ("1e3", False),
        ("'one'", True),
        ('"one"', True),
        # Two literals, not one: the evaluator requires the opening quote's match to
        # be the final character, which first/last-character equality does not.
        ("'a' 'b'", False),
        ("'a' == 'b'", False),
        ("true", True),
        ("inputs.name", False),
    ],
)
def test_literal_test_mirrors_the_evaluator(condition, literal):
    assert _is_literal(condition) is literal


@pytest.mark.parametrize(
    "condition",
    [
        # `_build_namespace` hands back mappings, so an indexed root always resolves
        # to None however the index is written.
        "inputs[0]",
        "steps[1]",
        "1e3",
        "'a' 'b'",
    ],
)
def test_shapes_the_evaluator_resolves_to_none_get_no_correction(condition):
    advice = format_condition_remediation(condition)
    assert "Wrap the expression" not in advice


# The two shapes below were each offered or withheld for the wrong reason. Both are
# checked against what the evaluator actually does with the wrapped form, not against
# a restatement of the check, so a check that drifts from the evaluator fails here.
CORRECTION_OFFERED = "Wrap the expression"


def _wrapped_evaluates(condition: str) -> bool:
    ctx = StepContext(
        inputs={
            "tag": "x",
            "tags": ["a", "b"],
            "count": 3,
            "fallback": ", ",
            "blob": '{"k": 1}',
        }
    )
    try:
        evaluate_condition("{{ " + condition + " }}", ctx)
    except Exception:
        return False
    return True


@pytest.mark.parametrize(
    "condition",
    [
        "inputs.tag in ['x', 'y']",
        "inputs.tag not in ['x']",
        "inputs.tag in [inputs.other, 'z']",
        # `_evaluate_simple_expression` drops empty segments, so a trailing comma is
        # `[1, 2]` rather than `[1, 2, None]`, and an empty list is a list.
        "inputs.count in [1, 2,]",
        "inputs.count in []",
    ],
)
def test_list_literal_operands_keep_the_correction(condition):
    """A list literal is a term, not a name.

    Resolving the brackets as a path reported `"['x', 'y']" is not a name the
    evaluator can resolve` and withheld the correction from a condition that
    wrapping repairs completely.
    """
    assert CORRECTION_OFFERED in format_condition_remediation(condition)
    assert _wrapped_evaluates(condition)


@pytest.mark.parametrize(
    "condition",
    ["inputs.tags | join(bogus)", "inputs.tags | map(bogus)"],
)
def test_filter_arguments_that_make_the_wrapped_form_raise_lose_the_correction(condition):
    """A filter argument is an operand like any other.

    `_apply_filter` evaluates it with `_evaluate_simple_expression`, so a name that
    is no namespace root arrives as None and the filter raises on it. Skipping the
    argument offered these as paste-ready.
    """
    assert CORRECTION_OFFERED not in format_condition_remediation(condition)
    assert not _wrapped_evaluates(condition)


def test_a_filter_argument_that_cannot_resolve_loses_it_even_without_raising():
    """`default` tolerates the None, so this one is policy rather than a crash.

    Withholding it is the same call already made for an unresolvable name anywhere
    else -- `bogus == 'x'` evaluates fine and is withheld too -- so the argument
    check does not need the wrapped form to raise before it declines.
    """
    condition = "inputs.count | default(bogus)"
    assert CORRECTION_OFFERED not in format_condition_remediation(condition)
    assert _wrapped_evaluates(condition)
    assert CORRECTION_OFFERED not in format_condition_remediation("bogus == 'x'")


@pytest.mark.parametrize(
    "condition",
    [
        "inputs.tags | join(', ')",
        "inputs.tags | join(inputs.fallback)",
        "inputs.tags | map('name')",
        "inputs.count | default(0)",
        "inputs.blob | from_json",
    ],
)
def test_resolvable_filter_arguments_keep_the_correction(condition):
    """The other direction: the argument check must not become a blanket refusal."""
    assert CORRECTION_OFFERED in format_condition_remediation(condition)
    assert _wrapped_evaluates(condition)


@pytest.mark.parametrize("condition", ["item[0] == 'x'", "item[1] == 'y'"])
def test_an_indexed_item_root_keeps_the_correction(condition):
    """`item` is the only root that is not always a mapping.

    `StepContext.item` is `Any` and a fan-out assigns the item value itself, so an
    item that is a list makes `item[0]` resolve. Rejecting every indexed root
    withheld the correction from a condition that evaluates.
    """
    ctx = StepContext(inputs={"a": 1}, item=["x", "y"])
    assert CORRECTION_OFFERED in format_condition_remediation(condition)
    assert evaluate_condition("{{ " + condition + " }}", ctx) is True


@pytest.mark.parametrize("condition", ["inputs[0]", "steps[1]", "fan_in[0]", "context[0]"])
def test_indexing_an_always_mapping_root_still_loses_the_correction(condition):
    """The other side of that split, so it does not widen into "any indexed root".

    `_build_namespace` hands these back as mappings, so `_resolve_dot_path` takes
    the index branch, finds no list, and returns None however the index is written.
    """
    ctx = StepContext(inputs={"a": 1}, item=["x", "y"])
    assert CORRECTION_OFFERED not in format_condition_remediation(condition)
    assert evaluate_condition("{{ " + condition + " }}", ctx) is False
