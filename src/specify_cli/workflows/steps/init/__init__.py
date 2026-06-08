"""Init step — bootstrap a Spec Kit project from within a workflow.

Runs the same scaffolding as ``specify init`` so a workflow can create
(or merge into) a project before driving the rest of the spec-driven
process.  The step invokes the ``init`` command in-process and captures
its exit code and output.
"""

from __future__ import annotations

import os
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

#: Valid ``script`` values, mirroring ``specify init --script``.
VALID_SCRIPT_TYPES = ("sh", "ps")


class InitStep(StepBase):
    """Bootstrap a project, equivalent to running ``specify init``.

    The step runs the bundled ``specify init`` command non-interactively,
    scaffolding templates, scripts, shared infrastructure, and the
    selected coding agent integration into the target directory.

    Because workflows run unattended, the step defaults to
    ``--ignore-agent-tools`` (skip checks for an installed agent CLI) and
    resolves the integration from the step config, falling back to the
    workflow-level default integration.

    Example YAML::

        - id: bootstrap
          type: init
          here: true
          integration: copilot
          script: sh

    Supported config fields (all optional):

    ``project``
        Project name or path to create.  Use ``"."`` for the current
        directory.  Ignored when ``here`` is truthy.
    ``here``
        Initialize in the target directory instead of creating a new one.
    ``integration``
        Integration key (e.g. ``copilot``).  Defaults to the workflow's
        default integration.
    ``script``
        Script type, ``sh`` or ``ps``.
    ``force``
        Merge/overwrite without confirmation when the directory is not
        empty.
    ``no_git``
        Skip git repository initialization.
    ``ignore_agent_tools``
        Skip checks for the coding agent CLI (defaults to ``true``).
    ``preset``
        Preset ID to install during initialization.
    ``branch_numbering``
        Branch numbering strategy (``sequential`` or ``timestamp``).
    """

    type_key = "init"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        project = self._resolve(config.get("project"), context)
        here = self._resolve_bool(config.get("here"), context)

        integration = config.get("integration") or context.default_integration
        integration = self._resolve(integration, context)

        script = self._resolve(config.get("script"), context)
        preset = self._resolve(config.get("preset"), context)
        branch_numbering = self._resolve(config.get("branch_numbering"), context)

        force = self._resolve_bool(config.get("force"), context)
        no_git = self._resolve_bool(config.get("no_git"), context)
        # Workflows run unattended; skip the agent CLI presence check by default.
        ignore_agent_tools = self._resolve_bool(
            config.get("ignore_agent_tools", True), context
        )

        argv: list[str] = ["init"]
        if here:
            argv.append("--here")
        elif project:
            argv.append(str(project))
        else:
            # No explicit target → initialize the current directory.
            argv.append(".")

        # When the target is the current directory and ``force`` is not set,
        # ``specify init`` prompts for confirmation if the directory is not
        # empty.  Workflows run unattended (no stdin), so the prompt would
        # abort with a confusing error.  Fail fast with an actionable message.
        targets_current_dir = here or not project or str(project) == "."
        if targets_current_dir and not force:
            base = context.project_root or os.getcwd()
            try:
                with os.scandir(base) as it:
                    not_empty = any(it)
            except OSError:
                not_empty = False
            if not_empty:
                error_message = (
                    f"Target directory {base!r} is not empty. Set "
                    "'force: true' to merge into a non-empty directory."
                )
                return StepResult(
                    status=StepStatus.FAILED,
                    output={
                        "argv": argv,
                        "project": project,
                        "here": here,
                        "integration": integration,
                        "script": script,
                        "exit_code": 1,
                        "stdout": "",
                        "stderr": error_message,
                    },
                    error=error_message,
                )

        if integration:
            argv.extend(["--integration", str(integration)])
        if script:
            argv.extend(["--script", str(script)])
        if branch_numbering:
            argv.extend(["--branch-numbering", str(branch_numbering)])
        if preset:
            argv.extend(["--preset", str(preset)])
        if force:
            argv.append("--force")
        if no_git:
            argv.append("--no-git")
        if ignore_agent_tools:
            argv.append("--ignore-agent-tools")

        exit_code, stdout, stderr = self._run_init(argv, context)

        output: dict[str, Any] = {
            "argv": argv,
            "project": project,
            "here": here,
            "integration": integration,
            "script": script,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }

        if exit_code != 0:
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    stderr.strip()
                    or stdout.strip()
                    or f"specify init exited with code {exit_code}."
                ),
            )
        return StepResult(status=StepStatus.COMPLETED, output=output)

    @staticmethod
    def _resolve(value: Any, context: StepContext) -> Any:
        """Resolve ``{{ ... }}`` expressions in string config values."""
        if isinstance(value, str) and "{{" in value:
            return evaluate_expression(value, context)
        return value

    @classmethod
    def _resolve_bool(cls, value: Any, context: StepContext) -> bool:
        """Coerce a config value (possibly an expression) to a boolean."""
        resolved = cls._resolve(value, context)
        if isinstance(resolved, str):
            return resolved.strip().lower() in ("true", "1", "yes")
        return bool(resolved)

    @staticmethod
    def _run_init(
        argv: list[str], context: StepContext
    ) -> tuple[int, str, str]:
        """Invoke ``specify init`` in-process and capture exit code/output.

        Runs with the working directory set to ``context.project_root`` so
        that ``--here`` and relative project paths target the right place.
        """
        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        prev_cwd = os.getcwd()
        if context.project_root:
            try:
                os.chdir(context.project_root)
            except OSError as exc:
                return (1, "", f"Cannot enter project root: {exc}")
        try:
            result = runner.invoke(app, argv, catch_exceptions=True)
        finally:
            try:
                os.chdir(prev_cwd)
            except OSError:
                pass

        stdout = result.output or ""
        # click >= 8.2 captures stderr separately; older versions mix it into
        # stdout and raise when ``result.stderr`` is accessed.
        try:
            stderr = result.stderr or ""
        except (ValueError, AttributeError):
            stderr = ""

        if result.exit_code != 0 and result.exception is not None:
            detail = f"{type(result.exception).__name__}: {result.exception}"
            stderr = f"{stderr}\n{detail}".strip() if stderr else detail

        return (result.exit_code, stdout, stderr)

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        script = config.get("script")
        if script is not None and not isinstance(script, str):
            errors.append(
                f"Init step {config.get('id', '?')!r}: 'script' must be a string "
                f"({' or '.join(repr(s) for s in VALID_SCRIPT_TYPES)})."
            )
        elif (
            isinstance(script, str)
            and "{{" not in script
            and script not in VALID_SCRIPT_TYPES
        ):
            errors.append(
                f"Init step {config.get('id', '?')!r}: 'script' must be "
                f"{' or '.join(repr(s) for s in VALID_SCRIPT_TYPES)}."
            )
        return errors
