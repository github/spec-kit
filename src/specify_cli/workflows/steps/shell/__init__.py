"""Shell step — run a local shell command."""

from __future__ import annotations

import json
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
        # Defensive: the engine does not auto-validate step config, so an
        # invalid ``timeout`` (string, None, ...) would otherwise raise a
        # TypeError from subprocess.run() and crash the whole run.  Mirror
        # the engine's handling of unvalidated ``continue_on_error`` by
        # only honoring well-formed values and falling back to the default.
        timeout = config.get("timeout", 300)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            timeout = 300

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
        if "timeout" in config:
            timeout = config["timeout"]
            # bool is an int subclass, so reject it explicitly.
            if (
                isinstance(timeout, bool)
                or not isinstance(timeout, int)
                or timeout <= 0
            ):
                errors.append(
                    f"Shell step {config.get('id', '?')!r}: 'timeout' must be a "
                    f"positive integer (seconds) when present, got {timeout!r}."
                )
        return errors
