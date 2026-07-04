"""Shell step — run a local shell command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class ShellStep(StepBase):
    """Run a local shell command (non-agent).

    Captures exit code and stdout/stderr.
    """

    type_key = "shell"
    TRUST_ENV_VAR = "SPECKIT_TRUSTED_WORKFLOW"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        run_cmd = config.get("run", "")
        if isinstance(run_cmd, str) and "{{" in run_cmd:
            run_cmd = evaluate_expression(run_cmd, context)
        run_cmd = str(run_cmd)

        cwd = context.project_root or "."

        trusted = self._is_trusted()
        if not trusted:
            output = {
                "trusted": False,
                "trust_env_var": self.TRUST_ENV_VAR,
                "run": run_cmd,
            }
            if not sys.stdin.isatty():
                return StepResult(
                    status=StepStatus.PAUSED,
                    output=output,
                    error=(
                        "Shell step requires explicit trust before executing "
                        f"local commands. Re-run or resume with {self.TRUST_ENV_VAR}=1 "
                        "after reviewing the workflow command."
                    ),
                )
            if not self._prompt_trust(run_cmd):
                output["aborted"] = True
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=f"Shell step {config.get('id', '?')!r} rejected by user.",
                )

        # NOTE: shell=True is required to support pipes, redirects, and
        # multi-command expressions in workflow YAML.  Workflow authors
        # control commands; catalog-installed workflows should be reviewed
        # before use (see PUBLISHING.md for security guidance).
        try:
            proc = subprocess.run(  # noqa: S602 -- guarded shell feature; see NOTE. # nosec B602
                run_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300,
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
                error="Shell command timed out after 300 seconds.",
                output={"exit_code": -1, "stdout": "", "stderr": "timeout"},
            )
        except OSError as exc:
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Shell command failed: {exc}",
                output={"exit_code": -1, "stdout": "", "stderr": str(exc)},
            )

    @classmethod
    def _is_trusted(cls) -> bool:
        return os.environ.get(cls.TRUST_ENV_VAR, "").strip() == "1"

    @staticmethod
    def _prompt_trust(run_cmd: str) -> bool:
        print("\n  Shell workflow step wants to run this local command:")
        print(f"    {run_cmd}")
        try:
            raw = input("  Trust and run this command? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        return raw in {"y", "yes"}

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "run" not in config:
            errors.append(
                f"Shell step {config.get('id', '?')!r} is missing 'run' field."
            )
        output_format = config.get("output_format")
        if output_format is not None and output_format != "json":
            errors.append(
                f"Shell step {config.get('id', '?')!r}: 'output_format' must "
                f"be 'json' when present, got {output_format!r}."
            )
        return errors
