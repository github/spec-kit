"""Gate step — human review gate."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class GateStep(StepBase):
    """Interactive review gate.

    When running in an interactive terminal, prompts the user to choose
    an option (e.g. approve / reject).  Falls back to ``PAUSED`` when
    stdin is not a TTY (CI, piped input) so the run can be resumed
    later with ``specify workflow resume``.

    The user's choice is stored in ``output.choice``.  ``on_reject``
    controls abort / skip behaviour.
    """

    type_key = "gate"

    #: Maximum number of ``show_file`` lines rendered at the prompt, so a
    #: large file cannot flood the terminal before the choice.
    MAX_SHOW_FILE_LINES = 200

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        message = config.get("message", "Review required.")
        if isinstance(message, str) and "{{" in message:
            message = evaluate_expression(message, context)

        options = config.get("options", ["approve", "reject"])
        on_reject = config.get("on_reject", "abort")

        show_file = config.get("show_file")
        if isinstance(show_file, str) and "{{" in show_file:
            show_file = evaluate_expression(show_file, context)
        # ``evaluate_expression`` can return a non-string for a single
        # expression (e.g. a number from a prior step), and a literal
        # non-string is also possible; coerce so it is rendered rather
        # than silently skipped at the prompt.
        if show_file is not None:
            show_file = str(show_file)

        output = {
            "message": message,
            "options": options,
            "on_reject": on_reject,
            "show_file": show_file,
            "choice": None,
        }

        # Non-interactive: pause for later resume (the file is not read here)
        if not sys.stdin.isatty():
            return StepResult(status=StepStatus.PAUSED, output=output)

        # Interactive: prompt the user. ``show_file`` contents are folded
        # into the displayed message so the operator can review the
        # referenced material before choosing. Composing the prompt text
        # here keeps ``_prompt`` to its ``(message, options)`` contract, so
        # adding review material never widens the interactive seam.
        choice = self._prompt(self._compose_prompt(message, show_file), options)
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

    @classmethod
    def _compose_prompt(cls, message: str, show_file: str | None) -> str:
        """Build the gate's display text.

        When ``show_file`` names a file, its contents (read safely, see
        ``_read_show_file``) are appended below the message so the operator
        can review the referenced material before choosing. Returns a
        possibly multi-line string that ``_prompt`` renders inside the box.
        """
        if not show_file:
            return message
        body = "\n".join(
            [f"{show_file}:", *(f"  {line}" for line in cls._read_show_file(show_file))]
        )
        return f"{message}\n\n{body}"

    @staticmethod
    def _prompt(message: str, options: list[str]) -> str:
        """Display the gate message and prompt for a choice.

        ``message`` may span multiple lines (e.g. when review material has
        been folded in); each line is rendered inside the gate box.
        """
        print("\n  ┌─ Gate ─────────────────────────────────────")
        for line in message.split("\n"):
            print(f"  │ {line}" if line else "  │")
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

    @staticmethod
    def _read_show_file(show_file: str) -> list[str]:
        """Return the lines of ``show_file`` for display.

        Reads at most ``MAX_SHOW_FILE_LINES`` lines so a large file cannot
        flood the prompt, and returns a short notice instead of raising
        when the file is missing, undecodable, or names an invalid path,
        so a misconfigured ``show_file`` never breaks the interactive
        prompt. ``ValueError`` covers paths the OS rejects outright (e.g.
        an embedded NUL byte), which ``Path.open`` raises before any I/O.
        """
        lines: list[str] = []
        truncated = False
        try:
            with Path(show_file).open(encoding="utf-8") as handle:
                for line in handle:
                    if len(lines) >= GateStep.MAX_SHOW_FILE_LINES:
                        truncated = True
                        break
                    lines.append(line.rstrip("\n"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            return [f"(could not read file: {exc})"]
        if not lines and not truncated:
            return ["(file is empty)"]
        if truncated:
            lines.append(
                f"… (output truncated at {GateStep.MAX_SHOW_FILE_LINES} lines)"
            )
        return lines

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
