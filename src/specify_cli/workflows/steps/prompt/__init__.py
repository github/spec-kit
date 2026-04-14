"""Prompt step — sends an arbitrary prompt to an integration CLI."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class PromptStep(StepBase):
    """Send a free-form prompt to an integration CLI.

    Unlike ``CommandStep`` which invokes an installed Spec Kit command
    by name (e.g. ``/speckit.specify`` or ``/speckit-specify``),
    ``PromptStep`` sends an arbitrary inline ``prompt:`` string
    directly to the CLI.  This is useful for ad-hoc instructions
    that don't map to a registered command.

    .. note::

        CLI output is streamed to the terminal for live progress.
        ``output.exit_code`` is always captured and can be referenced
        by later steps.  Full response text capture is a planned
        enhancement.

    Example YAML::

        - id: review-security
          type: prompt
          prompt: "Review {{ inputs.file }} for security vulnerabilities"
          integration: claude
    """

    type_key = "prompt"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        prompt_template = config.get("prompt", "")
        prompt = evaluate_expression(prompt_template, context)
        if not isinstance(prompt, str):
            prompt = str(prompt)

        # Resolve integration (step → workflow default)
        integration = config.get("integration") or context.default_integration
        if integration and isinstance(integration, str) and "{{" in integration:
            integration = evaluate_expression(integration, context)

        # Resolve model
        model = config.get("model") or context.default_model
        if model and isinstance(model, str) and "{{" in model:
            model = evaluate_expression(model, context)

        # Attempt CLI dispatch
        dispatch_result = self._try_dispatch(
            prompt, integration, model, context
        )

        output: dict[str, Any] = {
            "prompt": prompt,
            "integration": integration,
            "model": model,
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
                    error=(
                        dispatch_result["stderr"]
                        or f"Prompt exited with code {dispatch_result['exit_code']}"
                    ),
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
        prompt: str,
        integration_key: str | None,
        model: str | None,
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Dispatch *prompt* directly through the integration CLI."""
        if not integration_key or not prompt:
            return None

        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            return None

        impl = get_integration(integration_key)
        if impl is None:
            return None

        exec_args = impl.build_exec_args(prompt, model=model, output_json=False)
        if exec_args is None:
            return None

        if not shutil.which(impl.key):
            return None

        import subprocess
        import sys

        project_root = (
            Path(context.project_root) if context.project_root else Path.cwd()
        )

        try:
            result = subprocess.run(
                exec_args,
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                cwd=str(project_root),
            )
            return {
                "exit_code": result.returncode,
                "stdout": "",
                "stderr": "",
            }
        except KeyboardInterrupt:
            return {
                "exit_code": 130,
                "stdout": "",
                "stderr": "Interrupted by user",
            }
        except OSError:
            return None

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "prompt" not in config:
            errors.append(
                f"Prompt step {config.get('id', '?')!r} is missing 'prompt' field."
            )
        return errors
