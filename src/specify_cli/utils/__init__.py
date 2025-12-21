"""Utility modules for Specify CLI."""

from .commands import CLAUDE_LOCAL_PATH, check_tool, run_command
from .constants import AGENT_CONFIG, BANNER, SCRIPT_TYPE_CHOICES, TAGLINE
from .progress import StepTracker, get_key, select_with_arrows
from .templates import (
    download_and_extract_template,
    ensure_executable_scripts,
    handle_vscode_settings,
    merge_json_files,
)

__all__ = [
    # Constants
    "AGENT_CONFIG",
    "SCRIPT_TYPE_CHOICES",
    "CLAUDE_LOCAL_PATH",
    "BANNER",
    "TAGLINE",
    # Progress
    "StepTracker",
    "get_key",
    "select_with_arrows",
    # Commands
    "run_command",
    "check_tool",
    # Templates
    "handle_vscode_settings",
    "merge_json_files",
    "download_and_extract_template",
    "ensure_executable_scripts",
]
