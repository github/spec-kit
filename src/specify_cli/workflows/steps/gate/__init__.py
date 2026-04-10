"""Gate step — human review gate."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class GateStep(StepBase):
    """Pause for human review with interactive options.

    The user's choice is stored in ``output.choice``.  ``on_reject``
    controls abort / skip / retry behaviour.
    """

    type_key = "gate"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        message = config.get("message", "Review required.")
        if isinstance(message, str) and "{{" in message:
            message = evaluate_expression(message, context)

        options = config.get("options", ["approve", "reject"])
        on_reject = config.get("on_reject", "abort")

        show_file = config.get("show_file")
        if show_file and isinstance(show_file, str) and "{{" in show_file:
            show_file = evaluate_expression(show_file, context)

        # In non-interactive mode, auto-approve
        # The engine layer is responsible for presenting the gate to the user
        # and pausing execution.  This default implementation records the
        # gate config so the engine can act on it.
        return StepResult(
            status=StepStatus.PAUSED,
            output={
                "message": message,
                "options": options,
                "on_reject": on_reject,
                "show_file": show_file,
                "choice": None,  # Filled by engine after user interaction
            },
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "message" not in config:
            errors.append(
                f"Gate step {config.get('id', '?')!r} is missing 'message' field."
            )
        options = config.get("options", [])
        if options and not isinstance(options, list):
            errors.append(
                f"Gate step {config.get('id', '?')!r}: 'options' must be a list."
            )
        on_reject = config.get("on_reject", "abort")
        if on_reject not in ("abort", "skip", "retry"):
            errors.append(
                f"Gate step {config.get('id', '?')!r}: 'on_reject' must be "
                f"'abort', 'skip', or 'retry'."
            )
        return errors
