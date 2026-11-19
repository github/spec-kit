"""Filter table: arity, registration, evaluation and handler adaptation."""

from __future__ import annotations

import pytest

from specify_cli.workflows.base import StepContext
from specify_cli.workflows.expressions import (
    BUILTIN_FILTERS,
    FILTER_TABLE,
    _REGISTERED_FILTERS,
    _evaluator_rejects,
    evaluate_condition,
    evaluate_expression,
    format_filter_usage,
    register_custom_filter,
    unregister_custom_filter,
    unregister_custom_filters,
)

pytestmark = pytest.mark.usefixtures("reset_custom_functions")

BUILTIN_NAMES = (
    "default", "join", "map", "contains", "split",
    "from_json", "upper", "lower", "length", "to_json",
)
BUILTIN_LIST = (
    "default or default('x'), join('sep'), map('attr'), contains('s'), "
    "split('sep'), from_json, upper, lower, length, or to_json"
)


def ctx(**inputs):
    return StepContext(inputs=inputs)


def reg(name, function=lambda value: value, minimum=0, maximum=0):
    register_custom_filter(name, function, minimum, maximum)


# -- Arity refactor: built-in behaviour and messages are unchanged -----------


class TestBuiltinFiltersUnchanged:
    def test_builtin_snapshot_and_registered_names(self):
        assert tuple(BUILTIN_FILTERS) == BUILTIN_NAMES
        assert _REGISTERED_FILTERS == BUILTIN_NAMES
        assert {n: (s.min_args, s.max_args) for n, s in BUILTIN_FILTERS.items()} == {
            "default": (0, 1), "join": (1, 1), "map": (1, 1), "contains": (1, 1),
            "split": (1, 1), "from_json": (0, 0), "upper": (0, 0),
            "lower": (0, 0), "length": (0, 0), "to_json": (0, 0),
        }

    def test_builtin_snapshot_is_read_only(self):
        with pytest.raises(TypeError):
            BUILTIN_FILTERS["x"] = BUILTIN_FILTERS["upper"]  # type: ignore[index]

    @pytest.mark.parametrize(
        ("template", "message"),
        [
            (
                "{{ inputs.s | bogus }}",
                f"unknown filter 'bogus': expected one of {BUILTIN_LIST} (got '| bogus')",
            ),
            (
                "{{ inputs.s | join }}",
                "filter 'join' used in an unsupported form (got '| join'): "
                f"expected one of {BUILTIN_LIST}",
            ),
            (
                "{{ inputs.s | default() }}",
                "filter 'default' used in an unsupported form "
                f"(got '| default(...)'): expected one of {BUILTIN_LIST}",
            ),
            (
                "{{ inputs.s | upper() }}",
                "upper: expected '| upper' with no arguments or trailing tokens, "
                "got '| upper(...)'",
            ),
        ],
    )
    def test_builtin_messages_are_byte_identical(self, template, message):
        with pytest.raises(ValueError) as info:
            evaluate_expression(template, ctx(s="x"))
        assert str(info.value) == message

    def test_builtins_still_evaluate(self):
        context = ctx(s="ab", missing=None, items=["a", "b"])
        assert evaluate_expression("{{ inputs.s | upper }}", context) == "AB"
        assert evaluate_expression("{{ inputs.items | join('-') }}", context) == "a-b"
        assert evaluate_expression("{{ inputs.nope | default }}", context) in (None, "")
        assert evaluate_expression("{{ inputs.nope | default('z') }}", context) == "z"


# -- Usage formatter ----------------------------------------------------------


class TestUsageFormatter:
    @pytest.mark.parametrize(
        ("minimum", "maximum", "expected"),
        [
            (0, 0, "f"),
            (0, 1, "f or f('x')"),
            (1, 1, "f('arg1')"),
            (1, 2, "f(arg1, arg2)"),
            (2, 3, "f(arg1, arg2, arg3)"),
            (0, 2, "f or f(arg1, arg2)"),
        ],
    )
    def test_generic_placeholders(self, minimum, maximum, expected):
        assert format_filter_usage("f", minimum, maximum) == expected

    def test_custom_usage_is_listed_in_diagnostics(self):
        reg("pad", lambda v, a, b="": v, 2, 3)
        reg("trim")
        with pytest.raises(ValueError) as info:
            evaluate_expression("{{ inputs.s | nope }}", ctx(s="x"))
        message = str(info.value)
        assert "pad(arg1, arg2, arg3)" in message
        assert message.endswith("or trim (got '| nope')")

    def test_builtin_usage_overrides_stay_hand_written(self):
        assert BUILTIN_FILTERS["map"].usage == "map('attr')"
        assert BUILTIN_FILTERS["default"].usage == "default or default('x')"


# -- Registration API ---------------------------------------------------------


class TestRegistration:
    def test_register_adds_to_live_table_only(self):
        reg("trim")
        assert "trim" in FILTER_TABLE
        assert "trim" not in BUILTIN_FILTERS
        assert "trim" not in _REGISTERED_FILTERS

    @pytest.mark.parametrize("name", BUILTIN_NAMES)
    def test_builtin_name_is_rejected_and_unchanged(self, name):
        before = FILTER_TABLE[name]
        with pytest.raises(KeyError, match="built-in"):
            reg(name)
        assert FILTER_TABLE[name] is before

    def test_duplicate_is_rejected(self):
        reg("trim")
        with pytest.raises(KeyError, match="already registered"):
            reg("trim")

    @pytest.mark.parametrize("name", ["Trim", "a-b", "1x", "", "a b", "a.b", 5, None])
    def test_invalid_names_are_rejected(self, name):
        with pytest.raises(ValueError, match="Invalid custom filter name"):
            reg(name)
        assert name not in FILTER_TABLE

    def test_non_callable_handler_is_rejected(self):
        with pytest.raises(TypeError, match="callable"):
            register_custom_filter("x", "not callable")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [(2, 1), (-1, 1), (0, -1), (True, 1), (0, True), (0.0, 1), (0, "1")],
    )
    def test_invalid_bounds_are_rejected(self, minimum, maximum):
        with pytest.raises(ValueError, match="argument bounds"):
            reg("x", minimum=minimum, maximum=maximum)
        assert "x" not in FILTER_TABLE

    @pytest.mark.parametrize(("minimum", "maximum"), [(0, 17), (17, 17), (0, 10**9)])
    def test_bounds_above_the_cap_are_rejected_without_building_usage(
        self, minimum, maximum, monkeypatch
    ):
        from specify_cli.workflows.expressions import filters

        def forbidden(*args):
            raise AssertionError("usage text must not be built for rejected bounds")

        monkeypatch.setattr(filters, "format_filter_usage", forbidden)
        with pytest.raises(ValueError, match="argument bounds.*<= 16"):
            reg("x", minimum=minimum, maximum=maximum)
        assert "x" not in FILTER_TABLE

    def test_bounds_at_the_cap_are_accepted(self):
        reg("x", minimum=0, maximum=16)
        spec = FILTER_TABLE["x"]
        assert (spec.min_args, spec.max_args) == (0, 16)
        assert spec.usage.startswith("x or x(arg1, arg2")

    def test_unregister_removes_only_custom_filters(self):
        reg("a")
        reg("b")
        unregister_custom_filter("a")
        unregister_custom_filter("upper")
        assert "a" not in FILTER_TABLE and "b" in FILTER_TABLE
        assert "upper" in FILTER_TABLE
        unregister_custom_filters()
        assert tuple(FILTER_TABLE) == BUILTIN_NAMES


# -- Evaluation ---------------------------------------------------------------


class TestEvaluation:
    def test_interpolation_in_text(self):
        reg("trim", lambda v: v.strip())
        assert evaluate_expression("<{{ inputs.s | trim }}>", ctx(s="  x ")) == "<x>"

    def test_single_expression_keeps_the_returned_type(self):
        reg("pair", lambda v: [v, v])
        assert evaluate_expression("{{ inputs.s | pair }}", ctx(s="x")) == ["x", "x"]

    def test_chains_with_builtins_in_both_directions(self):
        reg("trim", lambda v: v.strip())
        assert evaluate_expression("{{ inputs.s | trim | upper }}", ctx(s=" ab ")) == "AB"
        assert evaluate_expression("{{ inputs.s | upper | trim }}", ctx(s=" ab ")) == "AB"

    def test_zero_args(self):
        reg("trim", lambda v: v.strip())
        assert evaluate_expression("{{ inputs.s | trim }}", ctx(s=" a ")) == "a"

    def test_optional_single_argument(self):
        reg("suffix", lambda v, s="!": v + s, 0, 1)
        context = ctx(s="a")
        assert evaluate_expression("{{ inputs.s | suffix }}", context) == "a!"
        assert evaluate_expression("{{ inputs.s | suffix('?') }}", context) == "a?"

    def test_required_single_argument(self):
        reg("wrap", lambda v, q: f"{q}{v}{q}", 1, 1)
        assert evaluate_expression("{{ inputs.s | wrap('\"') }}", ctx(s="a")) == '"a"'

    def test_ranged_arguments_are_passed_positionally_after_the_value(self):
        reg("pad", lambda v, left, right, extra="": f"{left}{v}{right}{extra}", 2, 3)
        context = ctx(s="x")
        with pytest.raises(ValueError):
            evaluate_expression("{{ inputs.s | pad('[') }}", context)
        assert evaluate_expression("{{ inputs.s | pad('[', ']') }}", context) == "[x]"
        assert evaluate_expression("{{ inputs.s | pad('[', ']', '!') }}", context) == "[x]!"

    def test_arguments_may_be_expressions(self):
        reg("wrap", lambda v, q: f"{q}{v}{q}", 1, 1)
        assert evaluate_expression("{{ inputs.s | wrap(inputs.q) }}", ctx(s="a", q="|")) == "|a|"

    def test_condition_uses_custom_filter(self):
        reg("blank", lambda v: not v.strip())
        assert evaluate_condition("{{ inputs.s | blank }}", ctx(s="  ")) is True
        assert evaluate_condition("{{ inputs.s | blank }}", ctx(s="x")) is False

    @pytest.mark.parametrize(
        ("minimum", "maximum", "template"),
        [
            (2, 3, "{{ inputs.s | f }}"),
            (2, 3, "{{ inputs.s | f('a') }}"),
            (2, 3, "{{ inputs.s | f('a', 'b', 'c', 'd') }}"),
            (1, 1, "{{ inputs.s | f }}"),
            (1, 1, "{{ inputs.s | f('a', 'b') }}"),
            (0, 1, "{{ inputs.s | f() }}"),
            (0, 1, "{{ inputs.s | f('a', 'b') }}"),
        ],
    )
    def test_wrong_call_form_names_the_filter(self, minimum, maximum, template):
        reg("f", lambda v, *a: v, minimum, maximum)
        with pytest.raises(ValueError, match="filter 'f' used in an unsupported form"):
            evaluate_expression(template, ctx(s="x"))

    def test_parentheses_on_zero_arg_filter_are_rejected(self):
        reg("f")
        with pytest.raises(ValueError, match=r"f: expected '\| f' with no arguments"):
            evaluate_expression("{{ inputs.s | f() }}", ctx(s="x"))

    def test_unregistered_name_is_unknown_after_unload(self):
        reg("f")
        unregister_custom_filters()
        with pytest.raises(ValueError, match="unknown filter 'f'"):
            evaluate_expression("{{ inputs.s | f }}", ctx(s="x"))


# -- Validation parity (same set of filters as evaluation) -------------------


class TestValidationParity:
    def test_evaluator_check_accepts_registered_and_rejects_unknown(self):
        assert _evaluator_rejects("inputs.s | f") == "unknown filter 'f'"
        reg("f", lambda v, a: v, 1, 1)
        assert _evaluator_rejects("inputs.s | f('a')") is None
        assert _evaluator_rejects("inputs.s | f") == "filter 'f' used in an unsupported form"
        assert _evaluator_rejects("inputs.s | f('a', 'b')") == (
            "filter 'f' used in an unsupported form"
        )

    def test_check_and_evaluation_agree_on_every_call_form(self):
        reg("f", lambda v, *a: v, 1, 2)
        for form in ("f", "f()", "f('a')", "f('a', 'b')", "f('a', 'b', 'c')"):
            rejected = _evaluator_rejects(f"inputs.s | {form}") is not None
            try:
                evaluate_expression(f"{{{{ inputs.s | {form} }}}}", ctx(s="x"))
                raised = False
            except ValueError:
                raised = True
            assert rejected == raised, form

    def test_bare_condition_error_names_unknown_filter_then_asks_for_wrapping(self):
        """A bare condition always errors: first naming the filter, once loaded asking for ``{{ }}``."""
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        definition = WorkflowDefinition.from_string(
            """
schema_version: "1.0"
workflow: {id: w, name: W, version: "1.0.0"}
steps:
  - id: a
    type: if
    condition: "inputs.s | blank"
    then:
      - id: b
        type: shell
        run: "echo hi"
"""
        )
        errors = validate_workflow(definition)
        assert len(errors) == 1 and "unknown filter 'blank'" in errors[0]

        reg("blank", lambda v: not v)
        errors = validate_workflow(definition)
        assert len(errors) == 1
        assert "unknown filter" not in errors[0]
        assert '"{{ inputs.s | blank }}"' in errors[0]

    def test_wrapped_condition_with_loaded_filter_validates_clean(self):
        from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

        reg("blank", lambda v: not v)
        definition = WorkflowDefinition.from_string(
            """
schema_version: "1.0"
workflow: {id: w, name: W, version: "1.0.0"}
inputs: {s: {type: string, default: x}}
steps:
  - id: a
    type: if
    condition: "{{ inputs.s | blank }}"
    then:
      - id: b
        type: shell
        run: "echo hi"
"""
        )
        assert validate_workflow(definition) == []


# -- Handler adapter (D7) ------------------------------------------------------


class TestHandlerAdapter:
    def test_arguments_and_return_value_pass_through_untouched(self):
        seen = []
        marker = object()

        def handler(value, *args):
            seen.append((value, args))
            return marker

        reg("f", handler, 0, 2)
        assert evaluate_expression("{{ inputs.s | f('a', 'b') }}", ctx(s="x")) is marker
        assert seen == [("x", ("a", "b"))]

    def test_ordinary_exception_becomes_value_error_with_cause(self):
        def handler(value):
            raise TypeError("needs a string")

        reg("boom", handler)
        with pytest.raises(ValueError) as info:
            evaluate_expression("{{ inputs.s | boom }}", ctx(s="x"))
        assert str(info.value) == "boom: needs a string"
        assert isinstance(info.value.__cause__, TypeError)

    def test_value_error_is_also_prefixed(self):
        def handler(value):
            raise ValueError("bad input")

        reg("boom", handler)
        with pytest.raises(ValueError, match="^boom: bad input$"):
            evaluate_expression("{{ inputs.s | boom }}", ctx(s="x"))

    @pytest.mark.parametrize("exception", [SystemExit, KeyboardInterrupt, GeneratorExit])
    def test_base_exceptions_pass_through(self, exception):
        def handler(value):
            raise exception()

        reg("boom", handler)
        with pytest.raises(exception):
            evaluate_expression("{{ inputs.s | boom }}", ctx(s="x"))

    def test_builtin_errors_are_not_rewrapped(self):
        reg("noop")
        with pytest.raises(ValueError) as info:
            evaluate_expression("{{ inputs.n | upper }}", ctx(n=3))
        assert not str(info.value).startswith("noop")
        assert str(info.value).startswith("upper")


# -- Return values (D8): no function-specific validation ----------------------


class TestReturnValues:
    @pytest.mark.parametrize(
        "value", [None, 0, False, "", ["a"], {"k": [1, 2]}, 1.5, b"bytes", {1, 2}]
    )
    def test_any_value_reaches_a_typed_template(self, value):
        reg("make", lambda v: value)
        result = evaluate_expression("{{ inputs.s | make }}", ctx(s="x"))
        assert result == value and type(result) is type(value)

    def test_returned_object_is_not_inspected_or_copied(self):
        class Opaque:
            pass

        instance = Opaque()
        reg("make", lambda v: instance)
        assert evaluate_expression("{{ inputs.s | make }}", ctx(s="x")) is instance

    def test_result_feeds_a_builtin_with_its_own_validation(self):
        reg("make_int", lambda v: 3)
        with pytest.raises(ValueError, match="upper"):
            evaluate_expression("{{ inputs.s | make_int | upper }}", ctx(s="x"))

    def test_result_round_trips_through_to_json(self):
        reg("make", lambda v: {"a": [1]})
        assert evaluate_expression("{{ inputs.s | make | to_json }}", ctx(s="x")) == (
            '{"a": [1]}'
        )
