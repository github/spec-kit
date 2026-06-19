"""Gate step — human review gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

#: Control characters except tab: C0 (incl. LF, so an embedded newline cannot
#: break the boxed layout), DEL, and C1 (incl. ``\x9b`` CSI). Stripped from
#: anything derived from a ``show_file`` before it is printed — the file's
#: contents and the path itself — so neither can inject ANSI/terminal escapes.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0a-\x1f\x7f-\x9f]")

#: Choices that, if returned by the gate, abort or skip the run. The
#: dry-run branch must not pre-select one of these (see
#: ``_first_non_sentinel``) so a downstream ``if`` doesn't accidentally
#: follow a sentinel that was chosen on the user's behalf.
_REJECT_SENTINELS = frozenset({"reject", "abort"})


def _coerce_options(raw: object) -> list[str]:
    """Strictly normalize ``options`` to a ``list[str]`` of valid choices.

    Only a list/tuple of strings is treated as valid input — every other
    shape (``None``, string, dict, scalar, sequence of non-strings) is
    coerced to an empty list so the gate can fail loudly instead of
    silently inheriting an author's typo. ``list[bool]`` and
    ``list[int]`` are rejected on purpose: a workflow that bypassed
    validation must not pass through with ``['True', 'False']`` as
    option labels, since the rendered prompt would expose Python's
    ``repr`` strings instead of author intent.

    An empty list is the documented signal that the gate has no
    choices — the dry-run path leaves ``choice`` as ``None`` and the
    non-dry-run interactive path emits a clear ``FAILURE`` instead of
    indexing into ``[]`` and crashing with a confusing
    ``Choose [1-0]`` prompt.
    """
    if isinstance(raw, (list, tuple)):
        coerced: list[str] = []
        for item in raw:
            if isinstance(item, str) and item:
                coerced.append(item)
        return coerced
    # Anything else — ``None``, ``str``, ``dict``, ``int``, ``bool`` —
    # is invalid. The validation layer already rejects these shapes
    # for the real-run path; this defensive coercion ensures a workflow
    # that bypassed validation does not crash the prompt loop.
    return []


def _first_non_sentinel(options: list[str]) -> str | None:
    """Return the first ``options`` entry that is not a reject/abort sentinel.

    Used by the dry-run branch so a synthetic ``choice`` doesn't
    unintentionally steer downstream branching into a reject path. If
    every option is a sentinel — an authoring mistake, but one the gate
    must not crash on — return ``None`` (neutral default).
    """
    for option in options:
        if isinstance(option, str) and option.lower() not in _REJECT_SENTINELS:
            return option
    return None


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

        # ``options`` is normalized defensively even on the non-dry-run
        # path: a workflow that bypassed validation can pass strings,
        # dicts, scalars, or non-string Sequences. Coercing here keeps
        # the interactive branch honest (no IndexError on a string)
        # without changing the validated happy path. Mirrors the same
        # normalization used by the dry-run branch below.
        options = _coerce_options(config.get("options", ["approve", "reject"]))
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

        # Dry-run: never pause for interactive input. The original
        # ``message`` is preserved verbatim on ``output["message"]`` so
        # downstream ``{{ steps.<id>.output.message }}`` references
        # resolve to the gate prompt unchanged; the ``[DRY RUN]`` body
        # is duplicated on ``output["dry_run_message"]`` for the CLI's
        # preview loop. ``choice`` is the first non-reject/abort option
        # so a downstream ``if`` doesn't accidentally follow a reject
        # sentinel; if every option is a sentinel we leave ``choice``
        # ``None`` so a downstream gate defaults to neutral.
        # See ``test_dry_run_skips_interactive_gate``,
        # ``test_dry_run_accepts_tuple_options``, and
        # ``test_dry_run_skips_reject_sentinels_for_choice``.
        if context.dry_run:
            choice = _first_non_sentinel(options)
            preview = f"[DRY RUN] Gate: {message}"
            return StepResult(
                status=StepStatus.COMPLETED,
                output={
                    "message": message,
                    "options": options,
                    "on_reject": on_reject,
                    "show_file": show_file,
                    "choice": choice,
                    "dry_run": True,
                    "dry_run_message": preview,
                },
            )

        # Non-interactive: pause for later resume (the file is not read here)
        if not sys.stdin.isatty():
            return StepResult(status=StepStatus.PAUSED, output=output)

        # Interactive with no options: a workflow that bypassed validation
        # can hand us ``options=None`` (normalized to ``[]``). Indexing
        # into an empty list would emit ``Choose [1-0]:`` and crash the
        # gate on the first ``int(raw)``. Fail loudly instead so the
        # operator sees the authoring mistake on stdout, not a stack
        # trace. ``output`` carries the empty ``options`` so the engine
        # can still record what the gate saw.
        if not options:
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    f"Gate {config.get('id', '?')!r} has no options — "
                    "interactive review requires at least one choice."
                ),
            )

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
    def _compose_prompt(cls, message: object, show_file: str | None) -> str:
        """Build the gate's display text.

        ``message`` may be a non-string (e.g. a YAML numeric literal that
        ``execute`` does not coerce), so it is rendered through ``str``.
        When ``show_file`` names a file, its contents (read safely, see
        ``_read_show_file``) are appended below the message so the operator
        can review the referenced material before choosing. Always returns a
        ``str`` — possibly multi-line — for ``_prompt`` to render in the box.
        """
        text = str(message)
        if not show_file:
            return text
        # The path is opened with the original value but displayed stripped,
        # so a path that itself contains escapes cannot spoof the terminal.
        header = f"{_CONTROL_CHARS.sub('', show_file)}:"
        body = "\n".join(
            [header, *(f"  {line}" for line in cls._read_show_file(show_file))]
        )
        return f"{text}\n\n{body}"

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

        Control characters are stripped from each line so file content
        cannot inject ANSI escape sequences into the terminal.
        """
        lines: list[str] = []
        truncated = False
        try:
            with Path(show_file).open(encoding="utf-8") as handle:
                for line in handle:
                    if len(lines) >= GateStep.MAX_SHOW_FILE_LINES:
                        truncated = True
                        break
                    lines.append(_CONTROL_CHARS.sub("", line.rstrip("\n")))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            # ``exc`` echoes the (possibly hostile) path, so strip it too.
            return [_CONTROL_CHARS.sub("", f"(could not read file: {exc})")]
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
