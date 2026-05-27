"""Tests for the per-integration `SPECIFY_INTEGRATION_<KEY>_EXTRA_ARGS` env-var hook.

The hook is implemented in `IntegrationBase._apply_extra_args_env_var`
and wired into every concrete `build_exec_args` —
`MarkdownIntegration`, `TomlIntegration`, `SkillsIntegration`, plus the
overrides in Codex, Devin, Opencode and Copilot. These tests cover both
the shared mechanism (via `SkillsIntegration` stubs near the top of the
file) and each override integration end-to-end (further down). See
issue #2595."""

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
    """Strip any leaked SPECIFY_INTEGRATION_*_EXTRA_ARGS from the test
    env so a developer's shell setting doesn't pollute results."""
    for key in list(os.environ):
        if key.startswith("SPECIFY_INTEGRATION_") and key.endswith(
            "_EXTRA_ARGS"
        ):
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
        "SPECIFY_INTEGRATION_CLAUDE_EXTRA_ARGS", "--dangerously-skip-permissions"
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
        "SPECIFY_INTEGRATION_CLAUDE_EXTRA_ARGS",
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


def test_malformed_quoting_raises_actionable_value_error(monkeypatch):
    """An unmatched quote in the env-var value must surface a clear
    error naming the offending env var and showing the invalid value,
    rather than crashing workflow dispatch with a bare shlex traceback."""
    monkeypatch.setenv(
        "SPECIFY_INTEGRATION_CLAUDE_EXTRA_ARGS",
        '--flag "unterminated',
    )
    with pytest.raises(ValueError) as excinfo:
        _ClaudeStub().build_exec_args("p")
    msg = str(excinfo.value)
    assert "SPECIFY_INTEGRATION_CLAUDE_EXTRA_ARGS" in msg
    assert "--flag \"unterminated" in msg


def test_env_var_empty_or_whitespace_is_noop(monkeypatch):
    """An env var set to '' or '   ' is treated as unset."""
    monkeypatch.setenv("SPECIFY_INTEGRATION_CLAUDE_EXTRA_ARGS", "   ")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_other_integration_env_var_ignored(monkeypatch):
    """`SPECIFY_INTEGRATION_GEMINI_EXTRA_ARGS` set must NOT leak into
    Claude's argv (per-integration scoping)."""
    monkeypatch.setenv("SPECIFY_INTEGRATION_GEMINI_EXTRA_ARGS", "--gemini-only-flag")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_key_normalization_hyphen_to_underscore_uppercase(monkeypatch):
    """`kiro-cli` key looks up `SPECIFY_INTEGRATION_KIRO_CLI_EXTRA_ARGS`
    (hyphens replaced with underscores, then uppercased)."""
    monkeypatch.setenv(
        "SPECIFY_INTEGRATION_KIRO_CLI_EXTRA_ARGS", "--some-kiro-flag"
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
    monkeypatch.setenv("SPECIFY_INTEGRATION_NO_CLI_EXTRA_ARGS", "--should-not-appear")
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

    monkeypatch.setenv("SPECIFY_INTEGRATION_CODEX_EXTRA_ARGS", "--sandbox read-only")
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

    monkeypatch.setenv("SPECIFY_INTEGRATION_DEVIN_EXTRA_ARGS", "--no-confirm")
    args = DevinIntegration().build_exec_args("p")
    assert args == ["devin", "-p", "p", "--no-confirm"]


def test_opencode_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv("SPECIFY_INTEGRATION_OPENCODE_EXTRA_ARGS", "--quiet")
    args = OpencodeIntegration().build_exec_args("p")
    assert args == [
        "opencode",
        "run",
        "--quiet",
        "--format",
        "json",
        "p",
    ]


def test_opencode_extra_args_cannot_clobber_prompt_derived_command(
    monkeypatch,
):
    """Operator-injected extra args must appear BEFORE the prompt-derived
    ``--command <X>`` so that Spec Kit's command selection wins under
    repeated-flag CLI semantics (last value typically takes precedence).

    Locks against the regression where an operator setting
    ``SPECIFY_INTEGRATION_OPENCODE_EXTRA_ARGS="--command malicious"`` could redirect
    a slash-prefixed prompt to a different command.
    """
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv(
        "SPECIFY_INTEGRATION_OPENCODE_EXTRA_ARGS", "--command operator-override"
    )
    args = OpencodeIntegration().build_exec_args("/speckit body text")
    # Prompt-derived "--command speckit" appears AFTER the
    # operator-injected one, so a CLI that resolves repeated flags
    # last-wins will honour Spec Kit's choice.
    assert args == [
        "opencode",
        "run",
        "--command",
        "operator-override",
        "--command",
        "speckit",
        "--format",
        "json",
        "body text",
    ]


def test_copilot_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.copilot import CopilotIntegration

    # Disable --yolo so the argv shape stays deterministic.
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    monkeypatch.setenv(
        "SPECIFY_INTEGRATION_COPILOT_EXTRA_ARGS", "--allow-tool 'shell(echo)'"
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


# ---------------------------------------------------------------------------
# `dispatch_command` end-to-end coverage
#
# Workflow execution calls `impl.dispatch_command(...)`, not
# `build_exec_args` directly. `IntegrationBase.dispatch_command` delegates
# to `build_exec_args` (so the override fixes above flow through), but
# `CopilotIntegration` overrides `dispatch_command` and constructs
# `cli_args` inline — the hook must be invoked there too or the env var
# is silently ignored at workflow runtime. These tests monkeypatch
# `subprocess.run` and assert the env-var args reach the executed argv.
# ---------------------------------------------------------------------------


class _RunCapture:
    """Test double that captures argv passed to subprocess.run."""

    def __init__(self):
        self.captured_args: list[str] | None = None

    def __call__(self, args, **kwargs):
        self.captured_args = list(args)

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()


def test_copilot_dispatch_command_includes_extra_args(monkeypatch):
    """Locks the bypass fix: `CopilotIntegration.dispatch_command`
    must honour `SPECIFY_INTEGRATION_COPILOT_EXTRA_ARGS`, not just `build_exec_args`.
    """
    import subprocess

    from specify_cli.integrations.copilot import CopilotIntegration

    capture = _RunCapture()
    monkeypatch.setattr(subprocess, "run", capture)
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    monkeypatch.setenv(
        "SPECIFY_INTEGRATION_COPILOT_EXTRA_ARGS", "--allow-tool 'shell(echo)'"
    )

    CopilotIntegration().dispatch_command(
        "speckit.plan", args="body", stream=False
    )

    assert capture.captured_args is not None
    # Hook inserted between `-p prompt` and the canonical Copilot flags.
    p_idx = capture.captured_args.index("-p")
    agent_idx = capture.captured_args.index("--agent")
    extra_idx = capture.captured_args.index("--allow-tool")
    assert p_idx < extra_idx < agent_idx
    assert "shell(echo)" in capture.captured_args


def test_codex_dispatch_command_includes_extra_args(monkeypatch):
    """Lock the inherited `IntegrationBase.dispatch_command` path:
    Codex (and by transitivity Devin, Opencode) flow through
    `build_exec_args`, so the env var must reach argv at workflow
    runtime.
    """
    import subprocess

    from specify_cli.integrations.codex import CodexIntegration

    capture = _RunCapture()
    monkeypatch.setattr(subprocess, "run", capture)
    monkeypatch.setenv("SPECIFY_INTEGRATION_CODEX_EXTRA_ARGS", "--sandbox read-only")

    CodexIntegration().dispatch_command(
        "speckit.plan", args="body", stream=False
    )

    assert capture.captured_args is not None
    assert "--sandbox" in capture.captured_args
    assert "read-only" in capture.captured_args
