"""Gemini CLI integration."""

from ..base import TomlIntegration


class GeminiIntegration(TomlIntegration):
    key = "gemini"
    config = {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".gemini/commands",
        "format": "toml",
        "args": "{{args}}",
        "extension": ".toml",
    }
    multi_install_safe = True

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "BeforeTool",
        "post_tool_use": "AfterTool",
        "session_end": "SessionEnd",
        # Gemini exposes BeforeAgent for the per-turn prompt-submit lifecycle
        # point (S6); its own Claude-hook migration maps UserPromptSubmit to
        # BeforeAgent. Mapping it so extension handlers fire.
        "user_prompt_submit": "BeforeAgent",
        "stop": "AfterAgent",
    }
    events_config_file = ".gemini/settings.json"
    events_format = "json-nested"
    # Gemini mandates JSON-only hook stdout ("silence is mandatory"): plain
    # text becomes a user-facing systemMessage, never context. Inject via
    # hookSpecificOutput.additionalContext on the two context events and
    # suppress stdout everywhere else (C13).
    events_context_envelope = {
        "*": "suppress",
        "session_start": "hookSpecificOutput",
        "user_prompt_submit": "hookSpecificOutput",
    }
    # Gemini measures hook timeouts in milliseconds, unlike Claude/Cursor/Codex
    # which use seconds. The shared formatter converts via _native_timeout (#7)
    # so the default 60s becomes 60000ms instead of terminating the dispatcher
    # after 60ms.
    events_timeout_unit = "ms"
