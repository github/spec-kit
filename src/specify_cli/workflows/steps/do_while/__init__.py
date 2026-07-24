"""Do-While loop step — execute at least once, then repeat while condition is truthy."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus


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
        elif not isinstance(config["condition"], str):
            # The engine re-evaluates 'condition' via evaluate_condition() after
            # each iteration; it returns a non-string as-is and takes bool() of
            # it -- so a list/dict/number condition silently resolves to a
            # truthiness (e.g. condition: [1, 2] is always truthy, looping to
            # max_iterations) with no error. Reject non-strings at validation,
            # mirroring the prompt/shell/command 'must be a string' checks.
            # "true"/"false" and an expression like "{{ ... }}" stay valid.
            errors.append(
                f"Do-while step {config.get('id', '?')!r}: 'condition' must be a "
                f"string, got {type(config['condition']).__name__}."
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
