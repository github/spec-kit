"""Do-While loop step — execute at least once, then repeat while condition is truthy."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import (
    condition_has_malformed_expression_block,
    condition_is_never_evaluated,
    format_condition_remediation,
)


class DoWhileStep(StepBase):
    """Execute body at least once, then check condition.

    Continues while condition is truthy.  ``max_iterations`` is an
    optional safety cap (defaults to 10 if omitted).

    The first invocation always returns the nested steps for execution.
    The engine re-evaluates ``step_config['condition']`` after each
    iteration to decide whether to loop again.
    """

    type_key = "do-while"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        max_iterations = config.get("max_iterations")
        if max_iterations is None:
            max_iterations = 10
        nested_steps = config.get("steps", [])
        condition = config.get("condition", "false")

        # The engine does not auto-validate step config (see
        # ``WorkflowEngine.load_workflow``) and feeds ``next_steps`` straight
        # into ``_execute_steps``, which iterates them as step mappings. A
        # non-list ``steps`` (a single mapping or scalar authoring mistake)
        # would otherwise be iterated element-wise — a dict yields its string
        # keys, a str its characters — and crash the whole run with
        # AttributeError on ``.get()``. ``validate`` already rejects a non-list
        # ``steps``; fail this step loudly on an unvalidated run instead,
        # mirroring the if/switch/fan-out steps. The body always runs on the
        # first call, so unlike the while step this guard is unconditional.
        if not isinstance(nested_steps, list):
            return StepResult(
                status=StepStatus.FAILED,
                output={
                    "condition": condition,
                    "max_iterations": max_iterations,
                    "loop_type": "do-while",
                },
                error=(
                    f"Do-while step {config.get('id', '?')!r}: 'steps' must be "
                    f"a list of steps, got {type(nested_steps).__name__}."
                ),
            )

        # Always execute body at least once; the engine layer evaluates
        # `condition` after each iteration to decide whether to loop.
        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "condition": condition,
                "max_iterations": max_iterations,
                "loop_type": "do-while",
            },
            next_steps=nested_steps,
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "condition" not in config:
            errors.append(
                f"Do-while step {config.get('id', '?')!r} is missing "
                f"'condition' field."
            )
        elif not isinstance(config["condition"], (str, bool)):
            # The engine re-evaluates 'condition' via evaluate_condition() after
            # each iteration. That call first delegates to
            # evaluate_expression() -- which returns a non-string unchanged --
            # and then coerces the result with bool(). So a list/dict/number
            # condition silently resolves to its truthiness (e.g.
            # condition: [1, 2] is always truthy, looping to max_iterations)
            # with no error. Reject those at validation, mirroring the
            # prompt/shell/command 'must be a string' checks.
            #
            # A literal ``bool`` stays valid: an unquoted ``condition: false``
            # is idiomatic YAML and evaluate_condition() already resolves it
            # exactly (bool passthrough, then a no-op bool()). "true"/"false"
            # and an expression like "{{ ... }}" stay valid too.
            errors.append(
                f"Do-while step {config.get('id', '?')!r}: 'condition' must be a "
                f"string or boolean, got {type(config['condition']).__name__}."
            )
        elif condition_is_never_evaluated(config["condition"]):
            # A string condition with no ``{{ }}`` block is never evaluated:
            # evaluate_expression() returns it unchanged and bool() then makes
            # any non-empty text true. `condition: inputs.count > 100` reads as
            # a real comparison but always takes every iteration. This is the same
            # silent-truthiness mistake the list/dict branch above rejects, and
            # GitHub Actions accepts a bare expression in `if:`, so it is easy
            # to write by habit.
            errors.append(
                f"Do-while step {config.get('id', '?')!r}: 'condition' "
                f"{config['condition']!r} is not a single complete '{{{{ }}}}' block, so "
                "it is never evaluated as an expression and is always true. "
                + format_condition_remediation(config["condition"])
            )
        elif condition_has_malformed_expression_block(config["condition"]):
            # Different fault, different advice. Here the block is *not* skipped:
            # _interpolate_expressions cannot close it with its quote-aware scan, so it
            # falls back to the first raw close and evaluates whatever that truncated.
            # `{{ inputs.missing | default('oops }}` reaches the filter parser and raises
            # ValueError at run time, so reporting it as "always true" would be wrong
            # twice over: it is evaluated, and it does not end up true.
            errors.append(
                f"Do-while step {config.get('id', '?')!r}: 'condition' "
                f"{config['condition']!r} opens a '{{{{' the interpolator cannot "
                "close, so it falls back to the first raw '}}' and evaluates a "
                "truncated expression instead of the one written. Balance the "
                "delimiters and quotes."
            )
        max_iter = config.get("max_iterations")
        if max_iter is not None:
            # bool is a subclass of int, so isinstance(True, int) is True and
            # True < 1 is False; reject bools explicitly so `max_iterations: true`
            # is a type error rather than a silent single iteration.
            if isinstance(max_iter, bool) or not isinstance(max_iter, int) or max_iter < 1:
                errors.append(
                    f"Do-while step {config.get('id', '?')!r}: "
                    f"'max_iterations' must be an integer >= 1."
                )
        nested = config.get("steps", [])
        if not isinstance(nested, list):
            errors.append(
                f"Do-while step {config.get('id', '?')!r}: 'steps' must be a list."
            )
        return errors
