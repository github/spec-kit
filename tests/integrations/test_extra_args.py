"""Tests for the per-integration `SPECIFY_<KEY>_EXTRA_ARGS` env-var hook
in `SkillsIntegration.build_exec_args`. See issue #2595."""

import os

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
    for key in list(os.environ):
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


# ---------------------------------------------------------------------------
# Override-integration coverage
#
# CodexIntegration, DevinIntegration, OpencodeIntegration and
# CopilotIntegration each override `build_exec_args` rather than using the
# base implementations. The env-var hook must be wired into every override
# so the documented behaviour ("works for every requires_cli integration")
# is honoured. These tests lock that contract per integration.
# ---------------------------------------------------------------------------


def test_codex_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.codex import CodexIntegration

    monkeypatch.setenv("SPECIFY_CODEX_EXTRA_ARGS", "--sandbox read-only")
    args = CodexIntegration().build_exec_args("p", model="gpt-5")
    assert args == [
        "codex",
        "exec",
        "p",
        "--sandbox",
        "read-only",
        "--model",
        "gpt-5",
        "--json",
    ]


def test_devin_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.devin import DevinIntegration

    monkeypatch.setenv("SPECIFY_DEVIN_EXTRA_ARGS", "--no-confirm")
    args = DevinIntegration().build_exec_args("p")
    assert args == ["devin", "-p", "p", "--no-confirm"]


def test_opencode_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv("SPECIFY_OPENCODE_EXTRA_ARGS", "--quiet")
    args = OpencodeIntegration().build_exec_args("p")
    assert args == [
        "opencode",
        "run",
        "--quiet",
        "--format",
        "json",
        "p",
    ]


def test_copilot_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.copilot import CopilotIntegration

    # Disable --yolo so the argv shape stays deterministic.
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    monkeypatch.setenv(
        "SPECIFY_COPILOT_EXTRA_ARGS", "--allow-tool 'shell(echo)'"
    )
    args = CopilotIntegration().build_exec_args("p")
    assert args == [
        "copilot",
        "-p",
        "p",
        "--allow-tool",
        "shell(echo)",
        "--output-format",
        "json",
    ]
