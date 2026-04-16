"""Fan-in step — join point for parallel steps."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class FanInStep(StepBase):
    """Join point that aggregates results from ``wait_for:`` steps.

    Reads completed step outputs from ``context.steps`` and collects
    them into ``output.results``.  Does not block; relies on the
    engine executing steps sequentially.
    """

    type_key = "fan-in"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        wait_for = config.get("wait_for", [])
        output_config = config.get("output") or {}
        if not isinstance(output_config, dict):
            output_config = {}

        # Collect results from referenced steps
        results = []
        for step_id in wait_for:
            step_data = context.steps.get(step_id, {})
            results.append(step_data.get("output", {}))

        # Resolve output expressions with fan_in in context
        prev_fan_in = getattr(context, "fan_in", None)
        context.fan_in = {"results": results}
        resolved_output: dict[str, Any] = {"results": results}

        try:
            for key, expr in output_config.items():
                if isinstance(expr, str) and "{{" in expr:
                    resolved_output[key] = evaluate_expression(expr, context)
                else:
                    resolved_output[key] = expr
        finally:
            # Restore previous fan_in state even if evaluation fails
            context.fan_in = prev_fan_in

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
