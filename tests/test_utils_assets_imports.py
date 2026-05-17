"""Regression guard: utility and asset symbols importable from specify_cli."""
from pathlib import Path

from specify_cli import (
    CLAUDE_LOCAL_PATH,
    CLAUDE_NPM_LOCAL_PATH,
    check_tool,
    get_speckit_version,
    handle_vscode_settings,
    init_git_repo,
    is_git_repo,
    merge_json_files,
    run_command,
)


def test_utils_symbols_importable():
    assert callable(run_command)
    assert callable(check_tool)
    assert callable(is_git_repo)
    assert callable(init_git_repo)
    assert callable(handle_vscode_settings)
    assert callable(merge_json_files)


def test_get_speckit_version_returns_string():
    version = get_speckit_version()
    assert isinstance(version, str) and len(version) > 0


def test_claude_paths_are_paths():
    assert isinstance(CLAUDE_LOCAL_PATH, Path)
    assert isinstance(CLAUDE_NPM_LOCAL_PATH, Path)
