"""Command step — dispatches a Spec Kit command to an integration CLI."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class CommandStep(StepBase):
    """Default step type — invokes a Spec Kit command via the integration CLI.

    The command files (skills, markdown, TOML) are already installed in
    the integration's directory on disk.  This step tells the CLI to
    execute the command by name (e.g. ``/speckit.specify`` or
    ``/speckit-specify``) rather than reading the file contents.
    """

    type_key = "command"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
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

        # Attempt CLI dispatch
        args_str = str(resolved_input.get("args", ""))
        dispatch_result = self._try_dispatch(
            command, integration, model, args_str, context
        )

        output: dict[str, Any] = {
            "command": command,
            "integration": integration,
            "model": model,
            "options": options,
            "input": resolved_input,
        }

        if dispatch_result is not None:
            output["exit_code"] = dispatch_result["exit_code"]
            output["stdout"] = dispatch_result["stdout"]
            output["stderr"] = dispatch_result["stderr"]
            output["dispatched"] = True
            if dispatch_result["exit_code"] != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=dispatch_result["stderr"] or f"Command exited with code {dispatch_result['exit_code']}",
                )
        else:
            output["exit_code"] = 0
            output["dispatched"] = False

        return StepResult(
            status=StepStatus.COMPLETED,
            output=output,
        )

    @staticmethod
    def _try_dispatch(
        command: str,
        integration_key: str | None,
        model: str | None,
        args: str,
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Invoke *command* by name through the integration CLI.

        The integration's ``dispatch_command`` builds the native
        slash-command invocation (e.g. ``/speckit.specify`` for
        markdown agents, ``/speckit-specify`` for skills agents),
        then executes the CLI non-interactively.

        Returns the dispatch result dict, or ``None`` if dispatch is
        not possible (integration not found, CLI not installed, or
        dispatch not supported).
        """
        if not integration_key:
            return None

        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            return None

        impl = get_integration(integration_key)
        if impl is None:
            return None

        # Check if the integration supports CLI dispatch
        if impl.build_exec_args("test") is None:
            return None

        # Check if the CLI tool is actually installed
        if not shutil.which(impl.key):
            return None

        project_root = Path(context.project_root) if context.project_root else None

        try:
            return impl.dispatch_command(
                command,
                args=args,
                project_root=project_root,
                model=model,
            )
        except (NotImplementedError, OSError):
            return None

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "command" not in config:
            errors.append(
                f"Command step {config.get('id', '?')!r} is missing 'command' field."
            )
        return errors
