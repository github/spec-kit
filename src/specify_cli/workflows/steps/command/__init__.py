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

    .. note::

        CLI output is streamed to the terminal for live progress.
        ``output.exit_code`` is always captured and can be referenced
        by later steps (e.g. ``{{ steps.specify.output.exit_code }}``).
        Full ``stdout``/``stderr`` capture is a planned enhancement.
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

        output: dict[str, Any] = {
            "command": command,
            "integration": integration,
            "model": model,
            "options": options,
            "input": resolved_input,
        }

        # Dry-run short-circuit — surface a synthetic preview of what a
        # real run would have dispatched, without invoking the CLI.
        if context.dry_run:
            preview_invocation: str | None = None
            if integration:
                try:
                    from specify_cli.integrations import get_integration

                    impl = get_integration(integration)
                except (ImportError, AttributeError, TypeError):
                    impl = None
                if impl is not None:
                    try:
                        preview_invocation = impl.build_command_invocation(
                            command, args_str
                        )
                    except (ImportError, AttributeError, TypeError):
                        # ImportError: integrations module not importable in
                        #   minimal environments or test sandboxes.
                        # AttributeError: integration class is missing
                        #   ``build_command_invocation`` (older integration
                        #   API).
                        # TypeError: integration returned a non-string value
                        #   from ``build_command_invocation``.
                        # Anything else (e.g. a real bug inside the
                        # integration) bubbles up so it's not silently
                        # masked by the dry-run preview path.
                        preview_invocation = None
            if preview_invocation:
                preview = f"DRY RUN: would invoke {preview_invocation!r}"
            else:
                preview = (
                    f"DRY RUN: would invoke command {command!r} "
                    f"(integration {integration!r}, args {args_str!r})"
                )
            output["exit_code"] = 0
            output["dispatched"] = False
            output["executed"] = False
            output["dry_run"] = True
            output["dry_run_message"] = preview
            # Preserve the original command/integration/input so
            # ``{{ steps.<id>.output.message }}`` keeps resolving to the
            # original command description for downstream templates.
            output["message"] = preview
            output["invoke_command"] = preview_invocation or command
            return StepResult(status=StepStatus.COMPLETED, output=output)

        dispatch_result = self._try_dispatch(
            command, integration, model, args_str, context
        )

        if dispatch_result is not None:
            output["exit_code"] = dispatch_result["exit_code"]
            output["stdout"] = dispatch_result["stdout"]
            output["stderr"] = dispatch_result["stderr"]
            output["dispatched"] = True
            output["executed"] = True
            output["dry_run"] = False
            if dispatch_result["exit_code"] != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=dispatch_result["stderr"] or f"Command exited with code {dispatch_result['exit_code']}",
                )
            return StepResult(
                status=StepStatus.COMPLETED,
                output=output,
            )
        else:
            output["exit_code"] = 1
            output["dispatched"] = False
            output["executed"] = False
            output["dry_run"] = False
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    f"Cannot dispatch command {command!r}: "
                    f"integration {integration!r} CLI not found or not installed. "
                    f"Install the CLI tool or check 'specify integration list'."
                ),
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

        # Build sample args for fallback executable detection when impl.key is not executable.
        exec_args = impl.build_exec_args("test")

        # Check if the CLI tool is actually installed.
        # Try the integration key first (covers most agents), then fall back
        # to exec_args[0] for agents whose executable differs.
        cli_path = shutil.which(impl.key)
        fallback_cli_path = shutil.which(exec_args[0]) if exec_args else None
        if cli_path is None and fallback_cli_path is None:
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
