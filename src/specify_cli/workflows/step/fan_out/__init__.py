"""Fan-out step — dispatch a step template over a collection."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class FanOutStep(StepBase):
    """Dispatch a step template for each item in a collection.

    The engine executes the nested ``step:`` template once per item,
    setting ``context.item`` for each iteration.  ``max_concurrency``
    controls parallelism: ``<= 1`` (the default) runs items
    sequentially, while ``> 1`` runs up to that many items concurrently
    on a bounded thread pool (see ``WorkflowEngine._run_fan_out``).
    """

    type_key = "fan-out"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        items_expr = config.get("items", "[]")
        items = evaluate_expression(items_expr, context)
        max_concurrency = config.get("max_concurrency", 1)
        step_template = config.get("step", {})

        # The engine does not auto-validate step config (see
        # ``WorkflowEngine.load_workflow``). On a COMPLETED fan-out it reads the
        # ``step_template`` back out and, when it is truthy, calls
        # ``template.get("id", ...)`` in ``_run_fan_out``. A truthy non-mapping
        # ``step`` (a scalar or list authoring mistake) would crash the whole
        # run with AttributeError there — the engine invokes ``execute`` and
        # ``_run_fan_out`` with no surrounding try/except. ``validate`` already
        # rejects a non-mapping ``step``; fail this step loudly on an
        # unvalidated run instead, mirroring the ``items`` guard below. An empty
        # or absent ``step`` defaults to ``{}`` (falsy) and the engine's
        # ``if template and items`` skips fan-out, so it stays valid here.
        if not isinstance(step_template, dict):
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Fan-out step {config.get('id', '?')!r}: 'step' must be a "
                    f"mapping (nested step template), got "
                    f"{type(step_template).__name__}."
                ),
                output={
                    "items": [],
                    "max_concurrency": max_concurrency,
                    "step_template": {},
                    "item_count": 0,
                },
            )

        if not isinstance(items, list):
            # A non-list here is a wiring error (the expression did not
            # resolve to a collection); silently fanning out over zero
            # items hides it. An explicit empty list remains valid input.
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Fan-out step {config.get('id', '?')!r}: 'items' must "
                    f"resolve to a list, got {type(items).__name__} from "
                    f"{items_expr!r}."
                ),
                output={
                    "items": [],
                    "max_concurrency": max_concurrency,
                    "step_template": step_template,
                    "item_count": 0,
                },
            )

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
        elif not isinstance(config["step"], dict):
            # A present-but-non-mapping ``step`` (including an explicit
            # ``step: null``) is an authoring mistake. ``config.get("step", {})``
            # in ``execute`` only substitutes the ``{}`` default for an *absent*
            # key, so an explicit ``None`` reaches the runtime guard and FAILS
            # the step. Reject it here too so a workflow cannot pass validation
            # and then fail during execution.
            errors.append(
                f"Fan-out step {config.get('id', '?')!r}: 'step' must be a mapping."
            )
        return errors
