from __future__ import annotations

import os
import shlex
from functools import lru_cache
from pathlib import Path
from textwrap import dedent

from terminal_bench.agents.installed_agents.claude_code.claude_code_agent import (
    ClaudeCodeAgent,
)
from terminal_bench.agents.installed_agents.opencode.opencode_agent import (
    OpenCodeAgent,
)


def _repo_root() -> Path:
    """Return the root of the Spec Kit repository."""

    return Path(__file__).resolve().parents[4]


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as exc:  # pragma: no cover - fail fast during benchmarks
        raise RuntimeError(
            f"Required prompt asset missing: {path}"
        ) from exc


@lru_cache(maxsize=1)
def _prompt_assets() -> dict[str, str]:
    """Load the canonical Spec -> Plan -> Tasks prompts and templates."""

    root = _repo_root()
    return {
        "spec_command": _read_text(root / "templates" / "commands" / "specify.md"),
        "plan_command": _read_text(root / "templates" / "commands" / "plan.md"),
        "tasks_command": _read_text(root / "templates" / "commands" / "tasks.md"),
        "spec_template": _read_text(root / "templates" / "spec-template.md"),
        "plan_template": _read_text(root / "templates" / "plan-template.md"),
        "tasks_template": _read_text(root / "templates" / "tasks-template.md"),
    }


def _build_workflow_prompt(instruction: str) -> str:
    assets = _prompt_assets()

    return dedent(
        f"""
        You are the Specify Spec Kit benchmarking agent. Your job is to apply the
        Spec -> Plan -> Tasks workflow exactly as defined by the CLI prompts before
        attempting any implementation work in the Terminal Bench task container.

        Task instruction from Terminal Bench:
        ---
        {instruction.strip()}
        ---

        ## Workflow expectations
        1. Review repository context and any constitutions before acting.
        2. Produce SPECIFICATION, PLAN, and TASKS sections in that order using the
           canonical prompts below. Do not start execution until all three are
           drafted.
        3. After presenting the tasks list, print `BEGIN EXECUTION` and carry out the
           tasks sequentially, announcing each task ID as you start and finish.
        4. Keep artefacts up to date as understanding evolves and run relevant tests
           before concluding.

        ## Canonical command prompts
        These excerpts are copied directly from the Specify CLI. Use them verbatim when
        constructing the SPECIFICATION, PLAN, and TASKS artefacts.

        ### templates/commands/specify.md
        ```markdown
        {assets['spec_command'].strip()}
        ```

        ### templates/commands/plan.md
        ```markdown
        {assets['plan_command'].strip()}
        ```

        ### templates/commands/tasks.md
        ```markdown
        {assets['tasks_command'].strip()}
        ```

        ## Canonical templates
        Reference these structures while drafting the artefacts so they stay aligned
        with the Specify CLI outputs.

        ### templates/spec-template.md
        ```markdown
        {assets['spec_template'].strip()}
        ```

        ### templates/plan-template.md
        ```markdown
        {assets['plan_template'].strip()}
        ```

        ### templates/tasks-template.md
        ```markdown
        {assets['tasks_template'].strip()}
        ```

        Proceed only after you have completed the SPECIFICATION, PLAN, and TASKS
        sections above. Once `BEGIN EXECUTION` has been emitted, follow the plan to
        completion or explain any blockers.
        """
    ).strip()


class SpecifyWorkflowMixin:
    """Override instruction rendering to include Spec Kit workflow guidance."""

    def _render_instruction(self, instruction: str) -> str:  # type: ignore[override]
        return _build_workflow_prompt(instruction)


class SpecifyClaudeWorkflowAgent(SpecifyWorkflowMixin, ClaudeCodeAgent):
    """Claude Code agent preconfigured with the Spec -> Plan -> Tasks workflow."""

    @staticmethod
    def name() -> str:
        return "specify_claude_workflow"

    def __init__(self, model_name: str | None = None, *args, **kwargs):
        super().__init__(model_name=model_name, *args, **kwargs)


class SpecifyOpenCodeWorkflowAgent(SpecifyWorkflowMixin, OpenCodeAgent):
    """OpenCode agent that drives the Spec -> Plan -> Tasks workflow."""

    _DEFAULT_MODEL = "opencode/grok-code-fast-1"

    @staticmethod
    def name() -> str:
        return "specify_opencode_workflow"

    def __init__(self, model_name: str | None = None, *args, **kwargs):
        super().__init__(model_name=model_name or self._DEFAULT_MODEL, *args, **kwargs)

    def _render_instruction(self, instruction: str) -> str:  # type: ignore[override]
        # OpenCode uses stored prompts via `opencode run --command specify`, so pass
        # through the raw task instruction and let the CLI command wrap it.
        return instruction

    def _run_agent_commands(self, instruction: str) -> list[TerminalCommand]:
        escaped_instruction = shlex.quote(instruction)
        return [
            TerminalCommand(
                command=(
                    f"opencode --model {self._model_name} -p specify run --command specify {escaped_instruction}"
                ),
                min_timeout_sec=0.0,
                max_timeout_sec=float("inf"),
                block=True,
                append_enter=True,
            ),
        ]

    @property
    def _env(self) -> dict[str, str]:  # type: ignore[override]
        if getattr(self, "_provider", None) == "opencode":
            # OpenCode public models do not require credentials, but allow an
            # override if the user exports OPENCODE_API_KEY.
            env: dict[str, str] = {}
            if "OPENCODE_API_KEY" in os.environ:
                env["OPENCODE_API_KEY"] = os.environ["OPENCODE_API_KEY"]
            return env
        return super()._env
