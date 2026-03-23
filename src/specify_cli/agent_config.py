"""Shared AI-agent configuration for runtime and command registration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

AGENT_CONFIG: dict[str, dict[str, Any]] = {'copilot': {'name': 'GitHub Copilot',
             'folder': '.github/',
             'commands_subdir': 'agents',
             'install_url': None,
             'requires_cli': False},
 'claude': {'name': 'Claude Code',
            'folder': '.claude/',
            'commands_subdir': 'commands',
            'install_url': 'https://docs.anthropic.com/en/docs/claude-code/setup',
            'requires_cli': True},
 'gemini': {'name': 'Gemini CLI',
            'folder': '.gemini/',
            'commands_subdir': 'commands',
            'install_url': 'https://github.com/google-gemini/gemini-cli',
            'requires_cli': True},
 'cursor-agent': {'name': 'Cursor',
                  'folder': '.cursor/',
                  'commands_subdir': 'commands',
                  'install_url': None,
                  'requires_cli': False},
 'qwen': {'name': 'Qwen Code',
          'folder': '.qwen/',
          'commands_subdir': 'commands',
          'install_url': 'https://github.com/QwenLM/qwen-code',
          'requires_cli': True},
 'opencode': {'name': 'opencode',
              'folder': '.opencode/',
              'commands_subdir': 'command',
              'install_url': 'https://opencode.ai',
              'requires_cli': True},
 'codex': {'name': 'Codex CLI',
           'folder': '.agents/',
           'commands_subdir': 'skills',
           'install_url': 'https://github.com/openai/codex',
           'requires_cli': True},
 'windsurf': {'name': 'Windsurf',
              'folder': '.windsurf/',
              'commands_subdir': 'workflows',
              'install_url': None,
              'requires_cli': False},
 'junie': {'name': 'Junie',
           'folder': '.junie/',
           'commands_subdir': 'commands',
           'install_url': 'https://junie.jetbrains.com/',
           'requires_cli': True},
 'kilocode': {'name': 'Kilo Code',
              'folder': '.kilocode/',
              'commands_subdir': 'workflows',
              'install_url': None,
              'requires_cli': False},
 'auggie': {'name': 'Auggie CLI',
            'folder': '.augment/',
            'commands_subdir': 'commands',
            'install_url': 'https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli',
            'requires_cli': True},
 'codebuddy': {'name': 'CodeBuddy',
               'folder': '.codebuddy/',
               'commands_subdir': 'commands',
               'install_url': 'https://www.codebuddy.ai/cli',
               'requires_cli': True},
 'qodercli': {'name': 'Qoder CLI',
              'folder': '.qoder/',
              'commands_subdir': 'commands',
              'install_url': 'https://qoder.com/cli',
              'requires_cli': True},
 'roo': {'name': 'Roo Code',
         'folder': '.roo/',
         'commands_subdir': 'commands',
         'install_url': None,
         'requires_cli': False},
 'kiro-cli': {'name': 'Kiro CLI',
              'folder': '.kiro/',
              'commands_subdir': 'prompts',
              'install_url': 'https://kiro.dev/docs/cli/',
              'requires_cli': True},
 'amp': {'name': 'Amp',
         'folder': '.agents/',
         'commands_subdir': 'commands',
         'install_url': 'https://ampcode.com/manual#install',
         'requires_cli': True},
 'shai': {'name': 'SHAI',
          'folder': '.shai/',
          'commands_subdir': 'commands',
          'install_url': 'https://github.com/ovh/shai',
          'requires_cli': True},
 'tabnine': {'name': 'Tabnine CLI',
             'folder': '.tabnine/agent/',
             'commands_subdir': 'commands',
             'install_url': 'https://docs.tabnine.com/main/getting-started/tabnine-cli',
             'requires_cli': True},
 'agy': {'name': 'Antigravity',
         'folder': '.agent/',
         'commands_subdir': 'commands',
         'install_url': None,
         'requires_cli': False},
 'bob': {'name': 'IBM Bob',
         'folder': '.bob/',
         'commands_subdir': 'commands',
         'install_url': None,
         'requires_cli': False},
 'vibe': {'name': 'Mistral Vibe',
          'folder': '.vibe/',
          'commands_subdir': 'prompts',
          'install_url': 'https://github.com/mistralai/mistral-vibe',
          'requires_cli': True},
 'kimi': {'name': 'Kimi Code',
          'folder': '.kimi/',
          'commands_subdir': 'skills',
          'install_url': 'https://code.kimi.com/',
          'requires_cli': True},
 'trae': {'name': 'Trae',
          'folder': '.trae/',
          'commands_subdir': 'rules',
          'install_url': None,
          'requires_cli': False},
 'pi': {'name': 'Pi Coding Agent',
        'folder': '.pi/',
        'commands_subdir': 'prompts',
        'install_url': 'https://www.npmjs.com/package/@mariozechner/pi-coding-agent',
        'requires_cli': True},
 'iflow': {'name': 'iFlow CLI',
           'folder': '.iflow/',
           'commands_subdir': 'commands',
           'install_url': 'https://docs.iflow.cn/en/cli/quickstart',
           'requires_cli': True},
 'generic': {'name': 'Generic (bring your own agent)',
             'folder': None,
             'commands_subdir': 'commands',
             'install_url': None,
             'requires_cli': False}}

AI_ASSISTANT_ALIASES: dict[str, str] = {'kiro': 'kiro-cli', 'cursor': 'cursor-agent'}

# Runtime agent keys that map to a different registrar key.
RUNTIME_TO_REGISTRAR_AGENT_KEY: dict[str, str] = {
    "cursor-agent": "cursor",
}


def build_command_registrar_configs() -> dict[str, dict[str, str]]:
    """Derive command-registrar config from runtime AGENT_CONFIG.

    Keeps command registration targets synchronized with runtime agent support
    while preserving backward-compatible key aliases (for example: runtime
    ``cursor-agent`` maps to registrar key ``cursor``).
    """
    configs: dict[str, dict[str, str]] = {}

    for runtime_key, cfg in AGENT_CONFIG.items():
        if runtime_key == "generic":
            continue

        folder = cfg.get("folder")
        subdir = cfg.get("commands_subdir")
        if not folder or not subdir:
            continue

        registrar_key = RUNTIME_TO_REGISTRAR_AGENT_KEY.get(runtime_key, runtime_key)

        command_format = "toml" if registrar_key in {"gemini", "tabnine"} else "markdown"
        extension = ".toml" if command_format == "toml" else ".md"

        if registrar_key == "copilot":
            extension = ".agent.md"
        if registrar_key in {"codex", "kimi"}:
            extension = "/SKILL.md"

        configs[registrar_key] = {
            "dir": f"{folder.rstrip('/')}/{subdir}",
            "format": command_format,
            "args": "{{args}}" if command_format == "toml" else "$ARGUMENTS",
            "extension": extension,
        }

    return configs


COMMAND_REGISTRAR_CONFIGS: dict[str, dict[str, str]] = build_command_registrar_configs()


def get_command_registrar_configs() -> dict[str, dict[str, str]]:
    """Return a deep copy of command registrar config for safe mutation in tests."""
    return deepcopy(COMMAND_REGISTRAR_CONFIGS)
