"""
Agent configurations for infrakit-cli.
Shared between CLI initialization and the extension system.

Each entry's runtime-rendering keys mirror what `template_renderer` consumes:
- ``folder``: agent-specific root directory under the project (e.g. ``.claude/``).
- ``commands_subdir``: subdir under ``folder`` where rendered commands live.
- ``command_format``: ``markdown`` | ``toml`` | ``agent.md``.
- ``command_args``: the token that replaces ``{ARGS}`` in command bodies.
- ``command_extension``: the file extension applied to ``infrakit:<name>``.
- ``extras`` (optional list): post-render hooks. Recognised values:
    * ``"copilot_prompts"`` — for every ``infrakit:*.agent.md`` produced, also
      emit a companion ``infrakit:*.prompt.md`` with ``agent:`` frontmatter.
    * ``"vscode_settings"`` — copy ``templates/vscode-settings.json`` to
      ``.vscode/settings.json``.
"""

# Default values for agent metadata
DEFAULT_FORMAT = "markdown"
DEFAULT_ARGS = "$ARGUMENTS"
DEFAULT_EXTENSION = ".md"

AGENT_CONFIG = {
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
    },
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
    },
    "cursor-agent": {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
        "mcp_install_path": ".cursor/mcp.json",
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
        "command_format": "toml",
        "command_args": "{{args}}",
        "command_extension": ".toml",
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "command",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
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
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "commands_subdir": "commands",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "commands_subdir": "commands",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "qodercli": {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "commands_subdir": "commands",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "folder": ".amazonq/",
        "commands_subdir": "prompts",
        "install_url": "https://aws.amazon.com/developer/learning/q-developer-cli/",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/",
        "commands_subdir": "commands",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "shai": {
        "name": "SHAI",
        "folder": ".shai/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "agy": {
        "name": "Antigravity",
        "folder": ".agent/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
    },
    "bob": {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
        "command_format": DEFAULT_FORMAT,
        "command_args": DEFAULT_ARGS,
        "command_extension": DEFAULT_EXTENSION,
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
    },
}
