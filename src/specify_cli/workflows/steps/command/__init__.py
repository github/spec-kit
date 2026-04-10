"""Command step — dispatches to an integration CLI."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class CommandStep(StepBase):
    """Default step type — dispatches a spec-kit command to a CLI integration."""

    type_key = "command"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        """Execute a command step by resolving integration and building output.

        In the current implementation this records the resolved command
        configuration into the step output.  Actual CLI dispatch is
        handled by the engine layer.
        """
        command = config.get("command", "")
        input_data = config.get("input", {})

        # Resolve expressions in input
        resolved_input: dict[str, Any] = {}
        for key, value in input_data.items():
            resolved_input[key] = evaluate_expression(value, context)

        # Resolve integration (step → workflow default → project default)
        integration = config.get("integration") or context.default_integration
        if integration and isinstance(integration, str) and "{{" in integration:
            integration = evaluate_expression(integration, context)

        # Resolve model
        model = config.get("model") or context.default_model
        if model and isinstance(model, str) and "{{" in model:
            model = evaluate_expression(model, context)

        # Merge options (workflow defaults ← step overrides)
        options = dict(context.default_options)
        step_options = config.get("options", {})
        if step_options:
            options.update(step_options)

        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "command": command,
                "integration": integration,
                "model": model,
                "options": options,
                "input": resolved_input,
                "exit_code": 0,
            },
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "command" not in config:
            errors.append(
                f"Command step {config.get('id', '?')!r} is missing 'command' field."
            )
        return errors
