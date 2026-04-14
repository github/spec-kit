"""Do-While loop step — execute at least once, then repeat while condition is truthy."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus


class DoWhileStep(StepBase):
    """Execute body at least once, then check condition.

    Continues while condition is truthy.  ``max_iterations`` is an
    optional safety cap (defaults to 10 if omitted).

    The first invocation always returns the nested steps for execution.
    The ``condition`` field is stored in the output so the engine can
    evaluate it after the body runs and decide whether to re-invoke.
    """

    type_key = "do-while"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        max_iterations = config.get("max_iterations")
        if max_iterations is None:
            max_iterations = 10
        nested_steps = config.get("steps", [])
        condition = config.get("condition", "false")

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
        max_iter = config.get("max_iterations")
        if max_iter is not None:
            if not isinstance(max_iter, int) or max_iter < 1:
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
