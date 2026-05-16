"""Tests for the per-integration `SPECIFY_<KEY>_EXTRA_ARGS` env-var hook
in `SkillsIntegration.build_exec_args`. See issue #2595."""

import pytest

from specify_cli.integrations.base import SkillsIntegration


class _ClaudeStub(SkillsIntegration):
    """Minimal Claude-like SkillsIntegration for testing."""

    key = "claude"
    config = {
        "name": "Claude (test stub)",
        "folder": ".claude/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".claude/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "CLAUDE.md"


class _KiroCliStub(SkillsIntegration):
    """SkillsIntegration with a hyphenated key to exercise key
    normalization (`kiro-cli` → `KIRO_CLI`)."""

    key = "kiro-cli"
    config = {
        "name": "Kiro CLI (test stub)",
        "folder": ".kiro/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kiro/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "KIRO.md"


class _NoCliStub(SkillsIntegration):
    """SkillsIntegration with requires_cli=False — build_exec_args
    must return None and the env-var hook must not fire."""

    key = "no-cli"
    config = {
        "name": "No-CLI agent (test stub)",
        "folder": ".no-cli/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".no-cli/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "NOCLI.md"


@pytest.fixture(autouse=True)
def _clean_extra_args_env(monkeypatch):
    """Strip any leaked SPECIFY_*_EXTRA_ARGS from the test env so a
    developer's shell setting doesn't pollute results."""
    for key in list(__import__("os").environ):
        if key.startswith("SPECIFY_") and key.endswith("_EXTRA_ARGS"):
            monkeypatch.delenv(key, raising=False)


def test_env_var_unset_byte_identical_argv():
    """Default behaviour: env var unset → no extra args inserted.

    Locks the backward-compatibility guarantee that existing
    operators see no change.
    """
    args = _ClaudeStub().build_exec_args("hello prompt")
    assert args == ["claude", "-p", "hello prompt", "--output-format", "json"]


def test_env_var_set_flag_inserted_before_model_and_output_format(
    monkeypatch,
):
    monkeypatch.setenv(
        "SPECIFY_CLAUDE_EXTRA_ARGS", "--dangerously-skip-permissions"
    )
    args = _ClaudeStub().build_exec_args("hello prompt", model="sonnet")
    assert args == [
        "claude",
        "-p",
        "hello prompt",
        "--dangerously-skip-permissions",
        "--model",
        "sonnet",
        "--output-format",
        "json",
    ]


def test_env_var_multi_token_parsed_via_shlex(monkeypatch):
    monkeypatch.setenv(
        "SPECIFY_CLAUDE_EXTRA_ARGS",
        "--dangerously-skip-permissions --max-turns 3",
    )
    args = _ClaudeStub().build_exec_args("p")
    assert args == [
        "claude",
        "-p",
        "p",
        "--dangerously-skip-permissions",
        "--max-turns",
        "3",
        "--output-format",
        "json",
    ]


def test_env_var_empty_or_whitespace_is_noop(monkeypatch):
    """An env var set to '' or '   ' is treated as unset."""
    monkeypatch.setenv("SPECIFY_CLAUDE_EXTRA_ARGS", "   ")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_other_integration_env_var_ignored(monkeypatch):
    """`SPECIFY_GEMINI_EXTRA_ARGS` set must NOT leak into
    Claude's argv (per-integration scoping)."""
    monkeypatch.setenv("SPECIFY_GEMINI_EXTRA_ARGS", "--gemini-only-flag")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_key_normalization_hyphen_to_underscore_uppercase(monkeypatch):
    """`kiro-cli` key looks up `SPECIFY_KIRO_CLI_EXTRA_ARGS`
    (hyphens replaced with underscores, then uppercased)."""
    monkeypatch.setenv(
        "SPECIFY_KIRO_CLI_EXTRA_ARGS", "--some-kiro-flag"
    )
    args = _KiroCliStub().build_exec_args("p")
    assert args == [
        "kiro-cli",
        "-p",
        "p",
        "--some-kiro-flag",
        "--output-format",
        "json",
    ]


def test_requires_cli_false_returns_none(monkeypatch):
    """`requires_cli: False` short-circuits to None — the env-var
    hook is never reached and no argv is built."""
    monkeypatch.setenv("SPECIFY_NO_CLI_EXTRA_ARGS", "--should-not-appear")
    assert _NoCliStub().build_exec_args("p") is None
