"""Agent invocation-style constants and helpers.

Agents that scaffold skills (``speckit-<name>/SKILL.md``) use different
slash-command invocation formats depending on the agent.  This module
centralises the mapping so that ``HookExecutor._render_hook_invocation``
and ``specify init``'s next-steps output stay consistent.
"""

from __future__ import annotations

# Agents that render $speckit-<name> (chat invocation) when in skills mode.
DOLLAR_SKILLS_AGENTS: frozenset[str] = frozenset({"codex", "zcode"})

# Agents that always render /speckit-<name>, regardless of ai_skills.
ALWAYS_SLASH_AGENTS: frozenset[str] = frozenset({"devin", "grok", "trae", "zed"})

# Agents that render /speckit-<name> only when ai_skills is enabled.
CONDITIONAL_SLASH_AGENTS: frozenset[str] = frozenset(
    {
        "agy",
        "bob",
        "claude",
        "copilot",
        "cursor-agent",
        "hermes",
        "lingma",
        "rovodev",
        "vibe",
    }
)


def is_dollar_skills_agent(selected_ai: str | None, ai_skills_enabled: bool) -> bool:
    """Return ``True`` if *selected_ai* uses ``$speckit-<name>`` invocations.

    Agents in `DOLLAR_SKILLS_AGENTS` (e.g. ``codex``, ``zcode``) render
    ``$speckit-<name>`` chat invocations when installed in skills mode.
    """
    if not isinstance(selected_ai, str):
        return False
    return selected_ai in DOLLAR_SKILLS_AGENTS and ai_skills_enabled


def is_slash_skills_agent(selected_ai: str | None, ai_skills_enabled: bool) -> bool:
    """Return ``True`` if *selected_ai* uses ``/speckit-<name>`` invocations.

    The decision is based on the agent sets defined in this module:

    *   Agents in `ALWAYS_SLASH_AGENTS` always use slash invocations.
    *   Agents in `CONDITIONAL_SLASH_AGENTS` only use them when
        *ai_skills_enabled* is ``True``.
    *   All other agents return ``False``.
    """
    if selected_ai is None:
        return False
    if not isinstance(selected_ai, str):
        return False
    return selected_ai in ALWAYS_SLASH_AGENTS or (
        selected_ai in CONDITIONAL_SLASH_AGENTS and ai_skills_enabled
    )
