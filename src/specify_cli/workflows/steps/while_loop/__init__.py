"""While loop step — repeat while condition is truthy."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_condition


class WhileStep(StepBase):
    """Repeat nested steps while condition is truthy.

    Evaluates condition *before* each iteration.  If falsy on first
    check, the body never runs.  ``max_iterations`` is required as
    a safety cap.
    """

    type_key = "while"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        condition = config.get("condition", "false")
        max_iterations = config.get("max_iterations", 10)
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
        if "max_iterations" not in config:
            errors.append(
                f"While step {config.get('id', '?')!r} is missing "
                f"'max_iterations' field."
            )
        nested = config.get("steps", [])
        if not isinstance(nested, list):
            errors.append(
                f"While step {config.get('id', '?')!r}: 'steps' must be a list."
            )
        return errors
