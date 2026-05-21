"""Regression guard: utility and asset symbols importable from specify_cli."""
from specify_cli import (
    run_command, check_tool, is_git_repo, init_git_repo,
    handle_vscode_settings, merge_json_files,
    get_speckit_version,
    CLAUDE_LOCAL_PATH, CLAUDE_NPM_LOCAL_PATH,
)
from pathlib import Path

def test_utils_symbols_importable():
    assert callable(check_tool)
    assert callable(merge_json_files)
    assert callable(is_git_repo)

def test_get_speckit_version_returns_string():
    version = get_speckit_version()
    assert isinstance(version, str) and len(version) > 0

def test_claude_paths_are_paths():
    assert isinstance(CLAUDE_LOCAL_PATH, Path)
    assert isinstance(CLAUDE_NPM_LOCAL_PATH, Path)
