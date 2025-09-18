from __future__ import annotations

from pathlib import Path

from terminal_bench.agents.installed_agents.claude_code.claude_code_agent import (
    ClaudeCodeAgent,
)


class SpecifyClaudeWorkflowAgent(ClaudeCodeAgent):
    """Claude Code agent preconfigured with the Specify spec -> plan -> tasks prompt.

    The agent reuses the stock Claude installer but injects our prompt template so that
    benchmark runs automatically follow the specification-driven development workflow.
    """

    _DEFAULT_TEMPLATE = Path(__file__).parent / "prompt_templates" / "specify_workflow.j2"

    @staticmethod
    def name() -> str:
        return "specify_claude_workflow"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("prompt_template", str(self._DEFAULT_TEMPLATE))
        super().__init__(*args, **kwargs)
