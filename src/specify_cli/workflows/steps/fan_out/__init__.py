"""Fan-out step — dispatch a step template over a collection."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class FanOutStep(StepBase):
    """Dispatch a step template for each item in a collection.

    The engine executes the nested ``step:`` template once per item,
    setting ``context.item`` for each iteration.  Execution is
    currently sequential; ``max_concurrency`` is accepted but not
    enforced.
    """

    type_key = "fan-out"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        items_expr = config.get("items", "[]")
        items = evaluate_expression(items_expr, context)
        if not isinstance(items, list):
            items = []

        max_concurrency = config.get("max_concurrency", 1)
        step_template = config.get("step", {})

        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "items": items,
                "max_concurrency": max_concurrency,
                "step_template": step_template,
                "item_count": len(items),
            },
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "items" not in config:
            errors.append(
                f"Fan-out step {config.get('id', '?')!r} is missing "
                f"'items' field."
            )
        if "step" not in config:
            errors.append(
                f"Fan-out step {config.get('id', '?')!r} is missing "
                f"'step' field (nested step template)."
            )
        step = config.get("step")
        if step is not None and not isinstance(step, dict):
            errors.append(
                f"Fan-out step {config.get('id', '?')!r}: 'step' must be a mapping."
            )
        return errors
