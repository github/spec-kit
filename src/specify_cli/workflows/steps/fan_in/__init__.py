"""Fan-in step — join point for parallel steps."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class FanInStep(StepBase):
    """Join point — blocks until all ``wait_for:`` steps complete.

    Aggregates their results into ``fan_in.results``.
    """

    type_key = "fan-in"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        wait_for = config.get("wait_for", [])
        output_config = config.get("output", {})

        # Collect results from referenced steps
        results = []
        for step_id in wait_for:
            step_data = context.steps.get(step_id, {})
            results.append(step_data.get("output", {}))

        # Resolve output expressions with fan_in in context
        context.fan_in = {"results": results}
        resolved_output: dict[str, Any] = {"results": results}

        for key, expr in output_config.items():
            if isinstance(expr, str) and "{{" in expr:
                resolved_output[key] = evaluate_expression(expr, context)
            else:
                resolved_output[key] = expr

        return StepResult(
            status=StepStatus.COMPLETED,
            output=resolved_output,
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        wait_for = config.get("wait_for", [])
        if not isinstance(wait_for, list) or not wait_for:
            errors.append(
                f"Fan-in step {config.get('id', '?')!r}: "
                f"'wait_for' must be a non-empty list of step IDs."
            )
        return errors
