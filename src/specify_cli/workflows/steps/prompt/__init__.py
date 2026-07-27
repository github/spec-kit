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

        # Resolve integration (step → workflow default).
        # Fall back to the workflow default ONLY for a genuinely-unset value
        # (missing / YAML-null / empty string). A ``config.get(...) or ...``
        # would also swallow a falsey *non-string* ([], {}, 0, False), coercing
        # it to the default before the guard below runs — so on an unvalidated
        # execute() such a step would silently dispatch with the configured
        # default instead of failing. Fall through instead, so every non-string
        # reaches the type guard.
        integration = config.get("integration")
        if integration is None or integration == "":
            integration = context.default_integration
        if integration and isinstance(integration, str) and "{{" in integration:
            integration = evaluate_expression(integration, context)

        # Resolve model (same fallback rationale as 'integration' above).
        model = config.get("model")
        if model is None or model == "":
            model = context.default_model
        if model and isinstance(model, str) and "{{" in model:
            model = evaluate_expression(model, context)

        # A non-string integration/model — a literal list/dict/number that
        # skipped validation, an unvalidated workflow-level default, or an
        # expression that resolved to one — crashes downstream: get_integration()
        # uses the value as a dict key (raw TypeError on an unhashable list/dict,
        # even on a *validated* run) and build_exec_args() feeds model into the
        # CLI argv. Fail the step with the contract error rather than taking down
        # the whole run. ``None`` stays valid — it means "unset" and falls back
        # to dispatch-not-possible.
        if integration is not None and not isinstance(integration, str):
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Prompt step {config.get('id', '?')!r}: 'integration' must "
                    f"be a string, got {type(integration).__name__}."
                ),
            )
        if model is not None and not isinstance(model, str):
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Prompt step {config.get('id', '?')!r}: 'model' must be a "
                    f"string, got {type(model).__name__}."
                ),
            )

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
            return StepResult(
                status=StepStatus.COMPLETED,
                output=output,
            )
        else:
            output["exit_code"] = 1
            output["dispatched"] = False
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    f"Cannot dispatch prompt: "
                    f"integration {integration!r} "
                    f"CLI not found or not installed."
                ),
            )

    @staticmethod
    def _try_dispatch(
        prompt: str,
        integration_key: str | None,
        model: str | None,
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Dispatch *prompt* directly through the integration CLI."""
        if not integration_key or not isinstance(integration_key, str) or not prompt:
            # A non-string integration would raise TypeError: unhashable type
            # from get_integration's dict lookup and abort the run; treat it as
            # not dispatchable so execute() falls through to its FAILED result.
            return None

        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            return None

        impl = get_integration(integration_key)
        if impl is None:
            return None

        exec_args = impl.build_exec_args(prompt, model=model, output_json=False)

        # Check if the CLI tool is actually installed.
        # Try the integration key first (covers most agents), then fall back
        # to exec_args[0] for agents whose executable differs.
        cli_path = shutil.which(impl.key)
        fallback_cli_path = shutil.which(exec_args[0]) if exec_args else None
        if cli_path is None and fallback_cli_path is None:
            return None

        # Prompt dispatch executes exec_args directly; require a non-empty argv.
        if not exec_args:
            return None

        import subprocess

        project_root = (
            Path(context.project_root) if context.project_root else Path.cwd()
        )

        try:
            result = subprocess.run(
                exec_args,
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
        elif not isinstance(config["prompt"], str):
            # execute() str()-coerces prompt and dispatches it to the
            # integration CLI, so a null or list 'prompt' would send the Python
            # repr ('None', "['review', 'this']") to the model as instructions —
            # silently wrong, with no error. Reject non-strings at validation,
            # mirroring the shell-step 'run' and command-step input/options type
            # checks. An expression like "{{ ... }}" is still a str, so it stays
            # valid.
            errors.append(
                f"Prompt step {config.get('id', '?')!r}: 'prompt' must be a "
                f"string, got {type(config['prompt']).__name__}."
            )
        # execute() passes 'integration' to get_integration(), which uses it as a
        # dict key — a non-string (list/dict) raises a raw TypeError (unhashable),
        # even on a validated run — and feeds 'model' into the CLI argv. Reject a
        # literal non-string here, mirroring the 'prompt' check above. ``None``
        # (an explicit ``integration:``/``model:`` YAML null) means "inherit the
        # workflow default" and stays valid; an expression like "{{ ... }}" is
        # still a str, so it stays valid too.
        integration = config.get("integration")
        if integration is not None and not isinstance(integration, str):
            errors.append(
                f"Prompt step {config.get('id', '?')!r}: 'integration' must be a "
                f"string, got {type(integration).__name__}."
            )
        model = config.get("model")
        if model is not None and not isinstance(model, str):
            errors.append(
                f"Prompt step {config.get('id', '?')!r}: 'model' must be a "
                f"string, got {type(model).__name__}."
            )
        return errors
