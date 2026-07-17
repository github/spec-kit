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

        # The engine does not auto-validate step config, so an unvalidated run
        # with a non-list ``wait_for`` reaches here raw. Iterating it then
        # either crashes the whole run (a scalar like an int or None raises
        # TypeError) or, worse, silently iterates a string's characters and
        # yields a bogus join of empty results with a COMPLETED status — the
        # exact "silent empty result + COMPLETED" wiring bug the engine's
        # fan-in validation guards against. Fail this step loudly instead,
        # mirroring the fan-out step's non-list ``items`` handling.
        if not isinstance(wait_for, list):
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Fan-in step {config.get('id', '?')!r}: 'wait_for' must be "
                    f"a list of step IDs, got {type(wait_for).__name__}."
                ),
                output={"results": []},
            )

        # A non-string entry can never match a real step id. An unhashable one
        # (a list/dict from a YAML indentation slip like ``wait_for: [[a, b]]``)
        # crashes the whole run at ``context.steps.get(step_id, ...)`` below with
        # a raw TypeError; a hashable-but-non-string one (``wait_for: [123]``)
        # silently joins an empty ``{}`` and still reports COMPLETED — the exact
        # "silent empty result + COMPLETED" wiring bug the whole-list guard above
        # and the engine's fan-in validation (engine.py) both reject. The engine
        # does not auto-validate step config, so fail this step loudly on an
        # unvalidated run too, using the engine's phrasing.
        bad_entries = [w for w in wait_for if not isinstance(w, str)]
        if bad_entries:
            first = bad_entries[0]
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Fan-in step {config.get('id', '?')!r}: 'wait_for' entries "
                    f"must be step-id strings, got {type(first).__name__} "
                    f"({first!r})."
                ),
                output={"results": []},
            )

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
        output = config.get("output")
        if output is not None and not isinstance(output, dict):
            # execute() silently coerces a non-mapping output to {}, so the
            # author's declared aggregation keys would vanish with no error.
            # Reject at validation, mirroring the command-step (#3262) fix.
            errors.append(
                f"Fan-in step {config.get('id', '?')!r}: 'output' must be a "
                f"mapping of key -> expression, got {type(output).__name__}."
            )
        return errors
