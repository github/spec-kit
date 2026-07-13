"""Shell step — run a local shell command."""

from __future__ import annotations

import json
import math
import subprocess
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class ShellStep(StepBase):
    """Run a local shell command (non-agent).

    Captures exit code and stdout/stderr.
    """

    type_key = "shell"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        run_cmd = config.get("run", "")
        if isinstance(run_cmd, str) and "{{" in run_cmd:
            run_cmd = evaluate_expression(run_cmd, context)
        run_cmd = str(run_cmd)

        cwd = context.project_root or "."
        # Per-step execution timeout in seconds; defaults to 300 for backward
        # compatibility. The engine does not auto-validate step config, so
        # validate here as well — a caller that skips WorkflowEngine.validate()
        # must fail the step cleanly rather than crash subprocess.run() with a
        # TypeError (or silently coerce ``timeout: true`` to a 1s duration,
        # since bool is an int subclass).
        timeout = config.get("timeout", 300)
        timeout_error = self._timeout_error(config)
        if timeout_error is not None:
            return StepResult(
                status=StepStatus.FAILED,
                error=timeout_error,
                output={"exit_code": -1, "stdout": "", "stderr": "invalid timeout"},
            )
        # NOTE: shell=True is required to support pipes, redirects, and
        # multi-command expressions in workflow YAML.  Workflow authors
        # control commands; catalog-installed workflows should be reviewed
        # before use (see PUBLISHING.md for security guidance).
        try:
            proc = subprocess.run(  # noqa: S602 -- intentional shell=True (see NOTE above)
                run_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
            )
            output = {
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            if proc.returncode != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Shell command exited with code {proc.returncode}.",
                    output=output,
                )
            if config.get("output_format") == "json":
                # Opt-in structured output: expose the parsed stdout under
                # ``output.data`` so later steps can consume typed values
                # (e.g. a fan-out's ``items:``). A parse failure fails the
                # step — declaring ``output_format: json`` is a contract.
                try:
                    output["data"] = json.loads(proc.stdout)
                except json.JSONDecodeError as exc:
                    return StepResult(
                        status=StepStatus.FAILED,
                        error=(
                            f"Shell step {config.get('id', '?')!r} declared "
                            f"output_format: json but stdout is not valid "
                            f"JSON: {exc}"
                        ),
                        output=output,
                    )
            return StepResult(
                status=StepStatus.COMPLETED,
                output=output,
            )
        except subprocess.TimeoutExpired:
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Shell command timed out after {timeout} seconds.",
                output={"exit_code": -1, "stdout": "", "stderr": "timeout"},
            )
        except OSError as exc:
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Shell command failed: {exc}",
                output={"exit_code": -1, "stdout": "", "stderr": str(exc)},
            )

    @staticmethod
    def _timeout_error(config: dict[str, Any]) -> str | None:
        """Return an error message if ``config['timeout']`` is invalid, else None.

        Shared by execute() and validate() so both paths reject the same
        values with the same message. An absent ``timeout`` is valid (the
        default is used). bool is a subclass of int, but ``timeout: true`` is a
        config error rather than a duration, so it is rejected explicitly.
        Non-finite floats (YAML ``.inf``/``.nan``) pass a plain ``> 0`` check
        but would raise in subprocess.run(), so they are rejected too.
        """
        if "timeout" not in config:
            return None
        timeout = config["timeout"]
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            return (
                f"Shell step {config.get('id', '?')!r}: 'timeout' must be a "
                f"positive number of seconds, got {timeout!r}."
            )
        return None

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "run" not in config:
            errors.append(
                f"Shell step {config.get('id', '?')!r} is missing 'run' field."
            )
        elif not isinstance(config["run"], str):
            # execute() str()-coerces run and invokes it under shell=True, so a
            # null or list 'run' would run the Python repr ('None', "['echo']")
            # as a command. Reject non-strings at validation, mirroring the
            # command-step input/options and gate options type checks. An
            # expression like "{{ ... }}" is still a str, so it stays valid.
            errors.append(
                f"Shell step {config.get('id', '?')!r}: 'run' must be a string, "
                f"got {type(config['run']).__name__}."
            )
        output_format = config.get("output_format")
        if output_format is not None and output_format != "json":
            errors.append(
                f"Shell step {config.get('id', '?')!r}: 'output_format' must "
                f"be 'json' when present, got {output_format!r}."
            )
        timeout_error = self._timeout_error(config)
        if timeout_error is not None:
            errors.append(timeout_error)
        return errors
