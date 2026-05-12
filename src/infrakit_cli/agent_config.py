"""
Agent configurations for infrakit-cli.

Five AI coding agents are supported. Each entry's runtime-rendering keys
mirror what :mod:`template_renderer` consumes:

- ``folder``: agent-specific root directory under the project (e.g. ``.claude/``).
- ``commands_subdir``: subdir under ``folder`` where rendered commands live.
- ``command_format``: ``markdown`` | ``toml`` | ``agent.md``.
- ``command_args``: the token that replaces ``{ARGS}`` in command bodies.
- ``command_extension``: the file extension applied to ``infrakit:<name>``.
- ``supports_subagents``: whether the agent has a built-in subagent
  invocation primitive (Claude Code's ``Task`` tool). The multi-persona
  commands check this to decide whether to delegate review phases.
- ``extras`` (optional list): post-render hooks. Recognised values:
    * ``"copilot_prompts"`` — for every ``infrakit:*.agent.md`` produced,
      also emit a companion ``infrakit:*.prompt.md`` with ``agent:``
      frontmatter.
    * ``"vscode_settings"`` — copy ``templates/vscode-settings.json`` to
      ``.vscode/settings.json``.

InfraKit historically supported 19 agents but the per-agent surface area
(layout differences, MCP install paths, command-format quirks) was
unmaintainable. The supported set is now the five agents we actively
test: Claude Code, Codex CLI, Gemini CLI, GitHub Copilot, plus a
``generic`` fallback for bring-your-own-agent setups.
"""

# Default values for agent metadata.
DEFAULT_FORMAT = "markdown"
DEFAULT_ARGS = "$ARGUMENTS"
DEFAULT_EXTENSION = ".md"

AGENT_CONFIG = {
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "commands_subdir": "commands",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
        "mcp_install_path": ".mcp.json",
        "supports_subagents": True,
        # Render persona files into .claude/agents/ so the Task tool can
        # invoke them by subagent_type matching the frontmatter `name:`.
        "extras": ["claude_subagents"],
    },
    "codex": {
        "name": "Codex CLI",
        "folder": ".codex/",
        "commands_subdir": "prompts",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
        "supports_subagents": False,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
        "command_format": "toml",
        "command_args": "{{args}}",
        "command_extension": ".toml",
        "supports_subagents": False,
    },
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "agents",
        "install_url": None,
        "requires_cli": False,
        "command_format": "agent.md",
        "command_args": DEFAULT_ARGS,
        "command_extension": ".agent.md",
        "extras": ["copilot_prompts", "vscode_settings"],
        "supports_subagents": False,
    },
    "generic": {
        "name": "Generic (bring your own agent)",
        "folder": ".infrakit/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
        "supports_subagents": False,
    },
}
