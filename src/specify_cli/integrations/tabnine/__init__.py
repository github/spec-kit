"""Tabnine CLI integration."""

from ..base import TomlIntegration


class TabnineIntegration(TomlIntegration):
    key = "tabnine"
    config = {
        "name": "Tabnine CLI",
        "folder": ".tabnine/agent/",
        "commands_subdir": "commands",
        "install_url": "https://docs.tabnine.com/main/getting-started/tabnine-cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".tabnine/agent/commands",
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
        # Tabnine's Gemini-compatible schema also provides BeforeAgent and
        # AfterAgent (S7); mapping them so user_prompt_submit and stop
        # extension handlers fire instead of being skipped.
        "user_prompt_submit": "BeforeAgent",
        "stop": "AfterAgent",
    }
    events_config_file = ".tabnine/agent/settings.json"
    events_format = "json-nested"
    # Tabnine is Gemini-hooks-compatible (JSON-only stdout) (C13).
    events_context_envelope = {
        "*": "suppress",
        "session_start": "hookSpecificOutput",
        "user_prompt_submit": "hookSpecificOutput",
    }
    # Tabnine mirrors Gemini's hook schema (BeforeTool/AfterTool) and, like
    # Gemini, measures hook timeouts in milliseconds. Declaring the unit makes
    # the shared formatter convert the 60s default to 60000ms instead of
    # emitting timeout: 60 (60 ms), which would terminate the dispatcher
    # before it starts (R5).
    events_timeout_unit = "ms"
