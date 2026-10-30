"""Shell step — run a local shell command."""

from __future__ import annotations

import io
import json
import locale
import math
import os
import re
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
        binding_errors = self._binding_errors(config)
        if binding_errors:
            return StepResult(
                status=StepStatus.FAILED,
                error="; ".join(binding_errors),
                output={"exit_code": -1, "stdout": "", "stderr": "invalid shell bindings"},
            )
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

        env = {**os.environ}
        for name, template in config.get("env", {}).items():
            try:
                value = evaluate_expression(template, context)
            except ValueError as exc:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Shell step {config.get('id', '?')!r}: env {name!r}: {exc}",
                    output={"exit_code": -1, "stdout": "", "stderr": "invalid environment expression"},
                )
            value_error = self._environment_value_error(name, value)
            if value_error is not None:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Shell step {config.get('id', '?')!r}: {value_error}",
                    output={"exit_code": -1, "stdout": "", "stderr": "invalid environment value"},
                )
            env[name.upper() if os.name == "nt" else name] = value
        if context.workflow_dir:
            env["SPECKIT_WORKFLOW_DIR"] = context.workflow_dir
        else:
            env.pop("SPECKIT_WORKFLOW_DIR", None)

        # NOTE: shell=True is required to support pipes, redirects, and
        # multi-command expressions in workflow YAML.  Workflow authors
        # control commands. strict=True rejects expression interpolation in
        # run; dynamic data can instead be bound through env without becoming
        # shell source. Neither mode sandboxes authored shell commands.
        try:
            proc = subprocess.run(  # noqa: S602 -- intentional shell=True (see NOTE above)
                run_cmd,
                shell=True,
                capture_output=True,
                cwd=cwd,
                env=env,
                timeout=timeout,
            )
            # Decode in this thread so malformed output becomes a step
            # failure on Windows too, where subprocess uses reader threads.
            # Preserve text=True's locale encoding and universal newlines.
            output = {"exit_code": proc.returncode, "stdout": "", "stderr": ""}
            encoding = locale.getpreferredencoding(False)
            decode_errors = []
            for name in ("stdout", "stderr"):
                try:
                    with io.TextIOWrapper(io.BytesIO(getattr(proc, name)), encoding=encoding) as stream:
                        output[name] = stream.read()
                except UnicodeDecodeError as exc:
                    decode_errors.append(f"Shell command {name} could not be decoded: {exc}")
            if decode_errors:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="; ".join(decode_errors),
                    output=output,
                )
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
                    output["data"] = json.loads(output["stdout"])
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
    def _environment_value_error(name: str, value: Any) -> str | None:
        if not isinstance(value, str):
            return f"env {name!r} must be a string, got {type(value).__name__}."
        if "\x00" in value:
            return f"env {name!r} must not contain NUL characters."
        if os.name == "posix":
            try:
                os.fsencode(value)
            except UnicodeEncodeError:
                return f"env {name!r} cannot be encoded for the process environment."
        return None

    @classmethod
    def _binding_errors(cls, config: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        prefix = f"Shell step {config.get('id', '?')!r}: "
        strict = config.get("strict", False)
        if not isinstance(strict, bool):
            errors.append(prefix + "'strict' must be a boolean.")
        elif strict:
            run = config.get("run")
            if not isinstance(run, str):
                errors.append(prefix + "'run' must be a string in strict mode.")
            elif "{{" in run:
                errors.append(
                    prefix + "strict mode forbids expressions in 'run'; "
                    "bind dynamic values through 'env' instead."
                )

        bindings = config.get("env", {})
        if not isinstance(bindings, dict):
            errors.append(prefix + "'env' must be a mapping.")
            return errors
        for name, template in bindings.items():
            if not isinstance(name, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None:
                errors.append(prefix + f"invalid environment variable name {name!r}.")
                continue
            if name.upper() == "SPECKIT_WORKFLOW_DIR":
                errors.append(prefix + f"environment variable {name!r} is reserved.")
            value_error = cls._environment_value_error(name, template)
            if value_error is not None:
                errors.append(prefix + value_error)
        return errors

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
        try:
            invalid_timeout = (
                isinstance(timeout, bool)
                or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout)
                or timeout <= 0
            )
        except OverflowError:
            # An int too large to convert to float (e.g. a 400-digit YAML
            # scalar) is not a bool and *is* an int, so it clears every clause
            # before ``isfinite()`` and raises there — and would raise the same
            # from subprocess.run(timeout=...). Mirrors the prompt step.
            invalid_timeout = True
        if invalid_timeout:
            return (
                f"Shell step {config.get('id', '?')!r}: 'timeout' must be a "
                f"positive number of seconds, got {timeout!r}."
            )
        return None

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        errors.extend(self._binding_errors(config))
        # Strict run errors are already reported by _binding_errors().
        if config.get("strict") is not True:
            if "run" not in config:
                errors.append(
                    f"Shell step {config.get('id', '?')!r} is missing 'run' field."
                )
            elif not isinstance(config["run"], str):
                # Legacy execution coerces run to shell source; validation
                # must still reject non-strings without changing that path.
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
