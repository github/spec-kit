"""DeepSeek Harness (DSH) integration — skills-based agent.

DSH discovers project skills from ``.dsh/skills`` (its native root, highest
provider rank) and from the shared ``.agents/skills`` root, one level deep,
using ``<name>/SKILL.md`` directory bundles with ``name``/``description``
frontmatter — the same agentskills.io layout Spec Kit scaffolds for other
skills-based agents. Skills are user-invocable through the ``/``-trigger
input in the DSH Web GUI (and any TUI/ACP front end): typing
``/speckit-specify <feature description>`` ships the literal token plus the
user text, and the harness injects the skill's ``<skill_content>`` into the
turn. Project guidance in ``AGENTS.md`` at the repo root is loaded
automatically by DSH, so no context-file handling is needed here.

See: https://github.com/deepseek-ai/deepseek-harness
"""

from __future__ import annotations

from ..base import SkillsIntegration


class DshIntegration(SkillsIntegration):
    """Integration for the DeepSeek Harness (DSH) agent."""

    key = "dsh"
    config = {
        "name": "DeepSeek Harness",
        "folder": ".dsh/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/deepseek-ai/deepseek-harness",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".dsh/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    # ``.dsh/`` is a static, unique agent root that no other integration
    # writes into, so co-installing DSH alongside other agents is safe.
    multi_install_safe = True

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build non-interactive CLI args for DSH.

        DSH's one-shot mode is ``dsh --profile headless "<task>"``: the
        runner submits the task as an ordinary user message, waits for
        quiescence, and prints the last assistant message to stdout. The
        headless profile recognizes whitespace-bounded ``/name`` tokens
        naming user-invocable skills, so a slash-command prompt such as
        ``/speckit-specify build photo albums`` loads the skill exactly as
        an interactive session would. The CLI has no structured-JSON output
        flag, so ``output_json`` and ``model`` are ignored.
        """
        args = [self._resolve_executable(), "--profile", "headless"]
        self._apply_extra_args_env_var(args)
        args.append(prompt)
        return args
