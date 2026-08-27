"""Qwen Code integration."""

from ..base import MarkdownIntegration


class QwenIntegration(MarkdownIntegration):
    key = "qwen"
    config = {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".qwen/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    multi_install_safe = True

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
    }
    events_config_file = ".qwen/settings.json"
    events_format = "json-nested"
    # Qwen hooks are a JSON stdin/stdout protocol (Gemini-derived) (C13).
    events_context_envelope = {
        "*": "suppress",
        "session_start": "hookSpecificOutput",
        "user_prompt_submit": "hookSpecificOutput",
    }
    # Qwen Code's command hooks measure timeout in milliseconds (default
    # 60000), per the Qwen Code hooks documentation. Declaring the unit makes
    # the shared formatter convert the 60s default to 60000ms instead of
    # emitting timeout: 60 (60 ms), which would terminate the dispatcher
    # before it starts (U1).
    events_timeout_unit = "ms"
