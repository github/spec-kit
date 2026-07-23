"""Init step — bootstrap a Spec Kit project from within a workflow.

Runs the same scaffolding as ``specify init`` so a workflow can create
(or merge into) a project before driving the rest of the spec-driven
process.  The step invokes the ``init`` command in-process and captures
its exit code and output.
"""

from __future__ import annotations

import os
from typing import Any

from specify_cli._agent_config import DEFAULT_INIT_INTEGRATION, SCRIPT_TYPE_CHOICES
from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

#: Valid ``script`` values, derived from the canonical source in _agent_config.
VALID_SCRIPT_TYPES = tuple(SCRIPT_TYPE_CHOICES.keys())

#: Directories the workflow engine may create before steps run.
#: These are excluded from the "non-empty directory" fast-fail check so
#: that ``here: true`` works without requiring ``force: true`` when the
#: only pre-existing content is engine run-state.
_ENGINE_OWNED_DIRS = {".specify"}


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
        default integration, then to ``DEFAULT_INIT_INTEGRATION``.
    ``integration_options``
        Extra options for the integration (e.g. ``"--skills"`` or
        ``"--commands-dir .myagent/cmds"``).
    ``script``
        Script type, ``sh``, ``ps``, or ``py``.
    ``force``
        Merge/overwrite without confirmation when the directory is not
        empty.
    ``ignore_agent_tools``
        Skip checks for the coding agent CLI (defaults to ``true``).
    ``preset``
        Preset ID to install during initialization.
    """

    type_key = "init"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        project = self._resolve(config.get("project"), context)
        here = self._resolve_bool(config.get("here"), context)

        integration = self._resolve(config.get("integration"), context)
        if not integration:
            integration = self._resolve(context.default_integration, context)
        # Apply the same default that specify init uses in non-interactive mode
        # so that output.integration reflects the actual integration used.
        if not integration:
            integration = DEFAULT_INIT_INTEGRATION

        integration_options = self._resolve(
            config.get("integration_options"), context
        )
        script = self._resolve(config.get("script"), context)
        preset = self._resolve(config.get("preset"), context)

        force = self._resolve_bool(config.get("force"), context)
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

        # Build the full argv (except --force, which may be set implicitly
        # below) so early-return outputs always reflect the complete command.
        if integration:
            argv.extend(["--integration", str(integration)])
        if integration_options:
            argv.extend(["--integration-options", str(integration_options)])
        if script:
            argv.extend(["--script", str(script)])
        if preset:
            argv.extend(["--preset", str(preset)])
        if ignore_agent_tools:
            argv.append("--ignore-agent-tools")

        # When the target is the current directory and ``force`` is not set,
        # ``specify init`` prompts for confirmation if the directory is not
        # empty.  Workflows run unattended (no stdin), so the prompt would
        # abort with a confusing error.  Fail fast with an actionable message.
        # Exception: if the only pre-existing content is engine-owned (e.g.
        # .specify/workflows/runs/), treat it as implicitly empty and auto-add
        # --force so init can proceed unattended.
        targets_current_dir = here or not project or str(project) == "."
        if targets_current_dir and not force:
            base = context.project_root or os.getcwd()
            has_engine_dirs = False
            try:
                with os.scandir(base) as it:
                    for entry in it:
                        if (
                            entry.name in _ENGINE_OWNED_DIRS
                            and entry.is_dir(follow_symlinks=False)
                        ):
                            has_engine_dirs = True
                        else:
                            # Non-engine content found — fail fast.
                            has_non_engine_content = True
                            break
                    else:
                        has_non_engine_content = False
            except OSError as exc:
                error_message = (
                    f"Cannot inspect target directory {base!r}: {exc}"
                )
                return StepResult(
                    status=StepStatus.FAILED,
                    output={
                        "argv": argv,
                        "project": project,
                        "here": here,
                        "integration": integration,
                        "integration_options": integration_options,
                        "script": script,
                        "preset": preset,
                        "force": force,
                        "ignore_agent_tools": ignore_agent_tools,
                        "exit_code": 1,
                        "stdout": "",
                        "stderr": error_message,
                    },
                    error=error_message,
                )
            if has_non_engine_content:
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
                        "integration_options": integration_options,
                        "script": script,
                        "preset": preset,
                        "force": force,
                        "ignore_agent_tools": ignore_agent_tools,
                        "exit_code": 1,
                        "stdout": "",
                        "stderr": error_message,
                    },
                    error=error_message,
                )
            else:
                # Only engine-owned dirs exist — implicitly force so specify
                # init doesn't prompt about the non-empty directory.
                # (Skip if the directory is completely empty — no force needed.)
                if has_engine_dirs:
                    force = True

        if force:
            argv.append("--force")

        exit_code, stdout, stderr = self._run_init(argv, context)

        output: dict[str, Any] = {
            "argv": argv,
            "project": project,
            "here": here,
            "integration": integration,
            "integration_options": integration_options,
            "script": script,
            "preset": preset,
            "force": force,
            "ignore_agent_tools": ignore_agent_tools,
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
                # Best-effort cleanup: avoid masking the init command result
                # if restoring the previous working directory fails.
                pass

        stdout = result.output or ""
        # click >= 8.2 captures stderr separately; older versions mix it into
        # stdout and raise when ``result.stderr`` is accessed.
        try:
            stderr = result.stderr or ""
        except (ValueError, AttributeError):
            # Older Click: stderr is mixed into stdout.  On failure, treat
            # stdout as stderr so workflows can consistently read
            # steps.<id>.output.stderr for error details.
            stderr = stdout if result.exit_code != 0 else ""

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
