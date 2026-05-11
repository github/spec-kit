"""Fan-out step — dispatch a step template over a collection."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class FanOutStep(StepBase):
    """Dispatch a step template for each item in a collection.

    The engine executes the nested ``step:`` template once per item,
    setting ``context.item`` for each iteration.  ``max_parallel`` caps
    the batch size (default 3); ``max_concurrency`` is a deprecated alias.
    """

    type_key = "fan-out"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        items_expr = config.get("items", "[]")
        items = evaluate_expression(items_expr, context)
        if not isinstance(items, list):
            items = []

        # max_parallel is canonical; max_concurrency is a deprecated alias
        max_parallel = config.get("max_parallel", config.get("max_concurrency", 3))
        step_template = config.get("step", {})

        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "items": items,
                "max_parallel": max_parallel,
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
        # Validate both canonical key and deprecated alias
        max_parallel = config.get("max_parallel", config.get("max_concurrency"))
        if max_parallel is not None:
            if not isinstance(max_parallel, int) or max_parallel < 1:
                errors.append(
                    f"Fan-out step {config.get('id', '?')!r}: 'max_parallel' "
                    f"(or deprecated 'max_concurrency') must be a positive integer."
                )
        return errors
