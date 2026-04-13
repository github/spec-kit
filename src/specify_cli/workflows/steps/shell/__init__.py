"""Shell step — run a local shell command."""

from __future__ import annotations

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

        # NOTE: shell=True is required to support pipes, redirects, and
        # multi-command expressions in workflow YAML.  Workflow authors
        # control commands; catalog-installed workflows should be reviewed
        # before use (see PUBLISHING.md for security guidance).
        try:
            proc = subprocess.run(
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

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "run" not in config:
            errors.append(
                f"Shell step {config.get('id', '?')!r} is missing 'run' field."
            )
        return errors
