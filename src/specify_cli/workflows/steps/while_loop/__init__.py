"""While loop step — repeat while condition is truthy."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_condition


class WhileStep(StepBase):
    """Repeat nested steps while condition is truthy.

    Evaluates condition *before* each iteration.  If falsy on first
    check, the body never runs.  ``max_iterations`` is an optional
    safety cap (defaults to 10 if omitted).
    """

    type_key = "while"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        condition = config.get("condition", False)
        max_iterations = config.get("max_iterations")
        if max_iterations is None:
            max_iterations = 10
        nested_steps = config.get("steps", [])

        result = evaluate_condition(condition, context)
        if result:
            return StepResult(
                status=StepStatus.COMPLETED,
                output={
                    "condition_result": True,
                    "max_iterations": max_iterations,
                    "loop_type": "while",
                },
                next_steps=nested_steps,
            )

        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "condition_result": False,
                "max_iterations": max_iterations,
                "loop_type": "while",
            },
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "condition" not in config:
            errors.append(
                f"While step {config.get('id', '?')!r} is missing "
                f"'condition' field."
            )
        max_iter = config.get("max_iterations")
        if max_iter is not None:
            if not isinstance(max_iter, int) or max_iter < 1:
                errors.append(
                    f"While step {config.get('id', '?')!r}: "
                    f"'max_iterations' must be an integer >= 1."
                )
        nested = config.get("steps", [])
        if not isinstance(nested, list):
            errors.append(
                f"While step {config.get('id', '?')!r}: 'steps' must be a list."
            )
        return errors
