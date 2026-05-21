"""Gate step — human review gate."""

from __future__ import annotations

import sys
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression
from specify_cli.workflows.gate_script import (
    extract_base_gate_id,
    lookup_scripted_verdict,
)


class GateStep(StepBase):
    """Interactive review gate.

    When running in an interactive terminal, prompts the user to choose
    an option (e.g. approve / reject).  Falls back to ``PAUSED`` when
    stdin is not a TTY (CI, piped input) so the run can be resumed
    later with ``specify workflow resume``.

    The user's choice is stored in ``output.choice``.  ``on_reject``
    controls abort / skip behaviour.

    When the engine receives a ``--gate-script`` (or a caller passes
    one through ``WorkflowEngine.execute(gate_script=...)``), the
    gate consults the script before doing anything else: a matching
    ``(gate_id, iteration)`` entry's verdict is used directly and
    ``output.scripted`` is set to ``True``. This is the
    non-interactive harness used by CI tests. When no script entry
    matches, the gate falls back to its normal behaviour.
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

        output: dict[str, Any] = {
            "message": message,
            "options": options,
            "on_reject": on_reject,
            "show_file": show_file,
            "choice": None,
            "scripted": False,
        }

        # Scripted verdict path: consult the gate-script first.
        # The firing counter increments for every gate execution
        # regardless of whether a script entry matches, so reordering
        # the YAML doesn't shift scripted verdicts onto unrelated
        # firings.
        base_gate_id = extract_base_gate_id(str(config.get("id", "")))
        iteration = context.gate_firing_counts.get(base_gate_id, 0)
        context.gate_firing_counts[base_gate_id] = iteration + 1

        scripted_verdict = lookup_scripted_verdict(
            context.gate_script, base_gate_id, iteration
        )
        if scripted_verdict is not None:
            output["choice"] = scripted_verdict
            output["scripted"] = True
            if scripted_verdict in ("reject", "abort"):
                if on_reject == "abort":
                    output["aborted"] = True
                    return StepResult(
                        status=StepStatus.FAILED,
                        output=output,
                        error=(
                            f"Gate scripted-rejected at step "
                            f"{config.get('id', '?')!r} (gate-script verdict)"
                        ),
                    )
                if on_reject == "retry":
                    return StepResult(status=StepStatus.PAUSED, output=output)
                # on_reject == "skip" → completed, downstream decides
            return StepResult(status=StepStatus.COMPLETED, output=output)

        # Non-interactive: pause for later resume
        if not sys.stdin.isatty():
            return StepResult(status=StepStatus.PAUSED, output=output)

        # Interactive: prompt the user
        choice = self._prompt(message, options)
        output["choice"] = choice

        if choice in ("reject", "abort"):
            if on_reject == "abort":
                output["aborted"] = True
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=f"Gate rejected by user at step {config.get('id', '?')!r}",
                )
            if on_reject == "retry":
                # Pause so the next resume re-executes this gate
                return StepResult(status=StepStatus.PAUSED, output=output)
            # on_reject == "skip" → completed, downstream steps decide
            return StepResult(status=StepStatus.COMPLETED, output=output)

        return StepResult(status=StepStatus.COMPLETED, output=output)

    @staticmethod
    def _prompt(message: str, options: list[str]) -> str:
        """Display gate message and prompt for a choice."""
        print("\n  ┌─ Gate ─────────────────────────────────────")
        print(f"  │ {message}")
        print("  │")
        for i, opt in enumerate(options, 1):
            print(f"  │  [{i}] {opt}")
        print("  └────────────────────────────────────────────")

        while True:
            try:
                raw = input(f"  Choose [1-{len(options)}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return options[-1]  # default to last (usually reject)
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            # Also accept the option name directly
            if raw.lower() in [o.lower() for o in options]:
                return next(o for o in options if o.lower() == raw.lower())
            print(f"  Invalid choice. Enter 1-{len(options)} or an option name.")

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "message" not in config:
            errors.append(
                f"Gate step {config.get('id', '?')!r} is missing 'message' field."
            )
        options = config.get("options", ["approve", "reject"])
        if not isinstance(options, list) or not options:
            errors.append(
                f"Gate step {config.get('id', '?')!r}: 'options' must be a non-empty list."
            )
        elif not all(isinstance(o, str) for o in options):
            errors.append(
                f"Gate step {config.get('id', '?')!r}: all options must be strings."
            )
        on_reject = config.get("on_reject", "abort")
        if on_reject not in ("abort", "skip", "retry"):
            errors.append(
                f"Gate step {config.get('id', '?')!r}: 'on_reject' must be "
                f"'abort', 'skip', or 'retry'."
            )
        if on_reject in ("abort", "retry") and isinstance(options, list):
            reject_choices = {"reject", "abort"}
            if not any(o.lower() in reject_choices for o in options):
                errors.append(
                    f"Gate step {config.get('id', '?')!r}: on_reject={on_reject!r} "
                    f"but options has no 'reject' or 'abort' choice."
                )
        return errors
