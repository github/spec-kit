"""Neutral behavior vocabulary for extension commands.

Extension command source files can declare a ``behavior:`` block in their
frontmatter to express agent-neutral intent (isolation, capability, tools,
etc.).  This module translates that vocabulary to concrete per-agent
frontmatter fields during rendering.

Extension authors can also declare an ``agents:`` escape-hatch block for
agent-specific fields that have no neutral equivalent::

    behavior:
      execution: isolated
      capability: strong
      effort: high
      tools: read-only
      invocation: explicit
      visibility: user

    agents:
      claude:
        paths: "src/**"
        argument-hint: "Codebase path to analyze"
      copilot:
        handoffs:
          - label: "Generate plan"
            agent: speckit.plan
            send: true
"""

from __future__ import annotations

from copy import deepcopy

# Keys that belong to the neutral behavior vocabulary
BEHAVIOR_KEYS: frozenset[str] = frozenset({
    "execution",    # command | isolated | agent
    "capability",   # fast | balanced | strong
    "effort",       # low | medium | high | max
    "tools",        # none | read-only | full
    "invocation",   # explicit | automatic
    "visibility",   # user | model | both
})

# Per-agent translation tables.
# Structure: agent_name -> behavior_key -> value -> (frontmatter_key, frontmatter_value)
# (None, None) means "no frontmatter injection for this combination"
_TRANSLATIONS: dict[str, dict[str, dict[str, tuple[str | None, object]]]] = {
    "claude": {
        "execution": {
            "isolated": ("context", "fork"),
            "command": (None, None),
            "agent": (None, None),   # routing concern, not frontmatter
        },
        "capability": {
            "fast": ("model", "claude-haiku-4-5-20251001"),
            "balanced": ("model", "claude-sonnet-4-6"),
            "strong": ("model", "claude-opus-4-6"),
        },
        "effort": {
            "low": ("effort", "low"),
            "medium": ("effort", "medium"),
            "high": ("effort", "high"),
            "max": ("effort", "max"),
        },
        "tools": {
            "none": ("allowed-tools", ""),
            "read-only": ("allowed-tools", "Read Grep Glob"),
            "write": ("allowed-tools", "Read Write Edit Grep Glob"),
            "full": (None, None),
        },
        "invocation": {
            "explicit": ("disable-model-invocation", True),
            "automatic": ("disable-model-invocation", False),
        },
        "visibility": {
            "user": ("user-invocable", True),
            "model": ("user-invocable", False),
            "both": (None, None),
        },
    },
    "copilot": {
        "execution": {
            "agent": ("mode", "agent"),
            "isolated": ("mode", "agent"),
            "command": (None, None),
        },
    },
    "codex": {
        "effort": {
            "low": ("effort", "low"),
            "medium": ("effort", "medium"),
            "high": ("effort", "high"),
            "max": ("effort", "max"),
        },
    },
}

# Tools list for Copilot when behavior.tools is set on an agent-type command.
_COPILOT_TOOLS: dict[str, list[str]] = {
    "read-only": ["read_file", "list_directory", "search_files"],
    "full": [],
    "none": [],
}


def translate_behavior(
    agent_name: str,
    behavior: dict,
    agents_overrides: dict | None = None,
) -> dict:
    """Translate neutral behavior dict to agent-specific frontmatter fields."""
    result: dict = {}
    agent_table = _TRANSLATIONS.get(agent_name, {})

    for key, value in behavior.items():
        if key not in BEHAVIOR_KEYS:
            continue
        key_table = agent_table.get(key, {})
        fm_key, fm_value = key_table.get(str(value), (None, None))
        if fm_key is not None:
            result[fm_key] = fm_value

    if agents_overrides and isinstance(agents_overrides, dict):
        overrides = agents_overrides.get(agent_name)
        if isinstance(overrides, dict):
            result.update(overrides)

    return result


def get_copilot_tools(behavior: dict) -> list[str]:
    """Return Copilot tool list for a given behavior.tools value."""
    tools_value = behavior.get("tools", "full")
    return _COPILOT_TOOLS.get(str(tools_value), [])


def strip_behavior_keys(frontmatter: dict) -> dict:
    """Return a copy of frontmatter with ``behavior:`` and ``agents:`` removed."""
    result = deepcopy(frontmatter)
    result.pop("behavior", None)
    result.pop("agents", None)
    return result


def get_deployment_type(frontmatter: dict) -> str:
    """Determine deployment type from behavior.execution.

    Returns 'agent' if behavior.execution == 'agent', otherwise 'command'.
    """
    behavior = frontmatter.get("behavior")
    if isinstance(behavior, dict) and behavior.get("execution") == "agent":
        return "agent"
    return "command"
