"""Tests for the per-integration `SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS` and
`SPECKIT_INTEGRATION_<KEY>_EXECUTABLE` env-var hooks.

The hooks are implemented in `IntegrationBase._apply_extra_args_env_var` and
`IntegrationBase._resolve_executable` and wired into every concrete
`build_exec_args` — `MarkdownIntegration`, `TomlIntegration`,
`SkillsIntegration`, plus override integrations.
These tests cover both the shared mechanisms (via `SkillsIntegration` stubs
near the top of the file) and override integrations end-to-end (further down).
See issues #2595 and #2596."""

import os

import pytest

from specify_cli.integrations.base import (
    MarkdownIntegration,
    SkillsIntegration,
    TomlIntegration,
)


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


class _MarkdownAgentStub(MarkdownIntegration):
    """Bare MarkdownIntegration subclass — does NOT override
    `build_exec_args`. Locks the base implementation in
    `MarkdownIntegration.build_exec_args` for the common case
    (most concrete integrations: Amp, Auggie, Generic, …)."""

    key = "md-agent"
    config = {
        "name": "Markdown agent (test stub)",
        "folder": ".md-agent/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".md-agent/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "MDAGENT.md"


class _TomlAgentStub(TomlIntegration):
    """Bare TomlIntegration subclass — does NOT override
    `build_exec_args`. Locks the base implementation in
    `TomlIntegration.build_exec_args` (Gemini, Tabnine)."""

    key = "toml-agent"
    config = {
        "name": "TOML agent (test stub)",
        "folder": ".toml-agent/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".toml-agent/commands",
        "format": "toml",
        "args": "$ARGUMENTS",
        "extension": ".toml",
    }
    context_file = "TOMLAGENT.md"


@pytest.fixture(autouse=True)
def _clean_extra_args_env(monkeypatch):
    """Strip any leaked SPECKIT_INTEGRATION_*_EXTRA_ARGS and
    SPECKIT_INTEGRATION_*_EXECUTABLE vars from the test env so a
    developer's shell setting doesn't pollute results."""
    for key in list(os.environ):
        if key.startswith("SPECKIT_INTEGRATION_") and (
            key.endswith("_EXTRA_ARGS") or key.endswith("_EXECUTABLE")
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
        "SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS", "--dangerously-skip-permissions"
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
        "SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS",
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
        "SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS",
        '--flag "unterminated',
    )
    with pytest.raises(ValueError) as excinfo:
        _ClaudeStub().build_exec_args("p")
    msg = str(excinfo.value)
    assert "SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS" in msg
    assert "--flag \"unterminated" in msg


def test_env_var_empty_or_whitespace_is_noop(monkeypatch):
    """An env var set to '' or '   ' is treated as unset."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS", "   ")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_other_integration_env_var_ignored(monkeypatch):
    """`SPECKIT_INTEGRATION_GEMINI_EXTRA_ARGS` set must NOT leak into
    Claude's argv (per-integration scoping)."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_GEMINI_EXTRA_ARGS", "--gemini-only-flag")
    args = _ClaudeStub().build_exec_args("p")
    assert args == ["claude", "-p", "p", "--output-format", "json"]


def test_key_normalization_hyphen_to_underscore_uppercase(monkeypatch):
    """`kiro-cli` key looks up `SPECKIT_INTEGRATION_KIRO_CLI_EXTRA_ARGS`
    (hyphens replaced with underscores, then uppercased)."""
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_KIRO_CLI_EXTRA_ARGS", "--some-kiro-flag"
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
    monkeypatch.setenv("SPECKIT_INTEGRATION_NO_CLI_EXTRA_ARGS", "--should-not-appear")
    assert _NoCliStub().build_exec_args("p") is None


# ---------------------------------------------------------------------------
# Base-class coverage
#
# Most integrations inherit `build_exec_args` from `MarkdownIntegration`
# or `TomlIntegration` without overriding it. The tests above use
# `SkillsIntegration` stubs (which share the same hook mechanism) — these
# tests exercise the two other base implementations directly so all three
# concrete bases are covered.
# ---------------------------------------------------------------------------


def test_markdown_integration_base_honours_extra_args(monkeypatch):
    """A bare `MarkdownIntegration` subclass — which does not override
    `build_exec_args` — must honour the env var via the base
    implementation. Covers the most common integration pattern."""
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_MD_AGENT_EXTRA_ARGS", "--debug --max-tokens 100"
    )
    args = _MarkdownAgentStub().build_exec_args("p")
    assert args == [
        "md-agent",
        "-p",
        "p",
        "--debug",
        "--max-tokens",
        "100",
        "--output-format",
        "json",
    ]


def test_toml_integration_base_honours_extra_args(monkeypatch):
    """A bare `TomlIntegration` subclass — which does not override
    `build_exec_args` — must honour the env var via the base
    implementation. Covers Gemini/Tabnine-style integrations."""
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_TOML_AGENT_EXTRA_ARGS", "--yolo"
    )
    args = _TomlAgentStub().build_exec_args("p", model="gemini-pro")
    # TomlIntegration uses `-m` for model (vs Markdown's `--model`).
    assert args == [
        "toml-agent",
        "-p",
        "p",
        "--yolo",
        "-m",
        "gemini-pro",
        "--output-format",
        "json",
    ]


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

    monkeypatch.setenv("SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS", "--sandbox read-only")
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

    monkeypatch.setenv("SPECKIT_INTEGRATION_DEVIN_EXTRA_ARGS", "--no-confirm")
    args = DevinIntegration().build_exec_args("p")
    assert args == ["devin", "-p", "p", "--no-confirm"]


def test_opencode_integration_honours_extra_args(monkeypatch):
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv("SPECKIT_INTEGRATION_OPENCODE_EXTRA_ARGS", "--quiet")
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
    ``SPECKIT_INTEGRATION_OPENCODE_EXTRA_ARGS="--command malicious"`` could redirect
    a slash-prefixed prompt to a different command.
    """
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_OPENCODE_EXTRA_ARGS", "--command operator-override"
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
    from specify_cli.integrations.copilot import (
        CopilotIntegration,
        _copilot_executable,
    )

    # Disable --yolo so the argv shape stays deterministic.
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_COPILOT_EXTRA_ARGS", "--allow-tool 'shell(echo)'"
    )
    args = CopilotIntegration().build_exec_args("p")
    # `_copilot_executable()` returns "copilot.cmd" on Windows and
    # "copilot" elsewhere; the test must mirror that to stay portable.
    assert args == [
        _copilot_executable(),
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
    must honour `SPECKIT_INTEGRATION_COPILOT_EXTRA_ARGS`, not just `build_exec_args`.
    """
    import subprocess

    from specify_cli.integrations.copilot import CopilotIntegration

    capture = _RunCapture()
    monkeypatch.setattr(subprocess, "run", capture)
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_COPILOT_EXTRA_ARGS", "--allow-tool 'shell(echo)'"
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
    monkeypatch.setenv("SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS", "--sandbox read-only")

    CodexIntegration().dispatch_command(
        "speckit.plan", args="body", stream=False
    )

    assert capture.captured_args is not None
    assert "--sandbox" in capture.captured_args
    assert "read-only" in capture.captured_args


# ---------------------------------------------------------------------------
# SPECKIT_INTEGRATION_<KEY>_EXECUTABLE tests
#
# The `_resolve_executable()` method on `IntegrationBase` checks
# `SPECKIT_INTEGRATION_<KEY>_EXECUTABLE` and, when set, substitutes that
# value for `self.key` as the first token in argv.  The tests below lock
# the behaviour across shared and override integration paths:
#   - the shared SkillsIntegration/MarkdownIntegration/TomlIntegration bases,
#   - representative override integrations,
#   - the hyphen→underscore key normalisation, and
#   - whitespace/unset no-op guarantee.
# ---------------------------------------------------------------------------


def test_executable_env_var_unset_uses_key():
    """Default: no override → executable is the integration key."""
    args = _ClaudeStub().build_exec_args("p")
    assert args[0] == "claude"


def test_executable_env_var_replaces_first_argv_token(monkeypatch):
    """Setting the env var substitutes the executable name in argv."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXECUTABLE", "/opt/claude/bin/claude")
    args = _ClaudeStub().build_exec_args("hello")
    assert args[0] == "/opt/claude/bin/claude"
    assert args[1:] == ["-p", "hello", "--output-format", "json"]


def test_executable_env_var_whitespace_only_falls_back_to_key(monkeypatch):
    """Whitespace-only value is treated as unset → falls back to self.key."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXECUTABLE", "   ")
    args = _ClaudeStub().build_exec_args("p")
    assert args[0] == "claude"


def test_executable_env_var_key_normalization_hyphen_to_underscore(monkeypatch):
    """`kiro-cli` key maps to `SPECKIT_INTEGRATION_KIRO_CLI_EXECUTABLE`."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_KIRO_CLI_EXECUTABLE", "/usr/local/bin/kiro-cli")
    args = _KiroCliStub().build_exec_args("p")
    assert args[0] == "/usr/local/bin/kiro-cli"


def test_executable_env_var_other_integration_ignored(monkeypatch):
    """`SPECKIT_INTEGRATION_GEMINI_EXECUTABLE` must NOT affect Claude."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_GEMINI_EXECUTABLE", "/custom/gemini")
    args = _ClaudeStub().build_exec_args("p")
    assert args[0] == "claude"


def test_executable_env_var_markdown_integration(monkeypatch):
    """MarkdownIntegration base honours the executable env var."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_MD_AGENT_EXECUTABLE", "/custom/md-agent")
    args = _MarkdownAgentStub().build_exec_args("p")
    assert args[0] == "/custom/md-agent"


def test_executable_env_var_toml_integration(monkeypatch):
    """TomlIntegration base honours the executable env var."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_TOML_AGENT_EXECUTABLE", "/custom/toml-agent")
    args = _TomlAgentStub().build_exec_args("p")
    assert args[0] == "/custom/toml-agent"


def test_executable_env_var_requires_cli_false_returns_none(monkeypatch):
    """`requires_cli: False` still returns None even when executable is set."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_NO_CLI_EXECUTABLE", "/custom/no-cli")
    assert _NoCliStub().build_exec_args("p") is None


def test_executable_env_var_codex_integration(monkeypatch):
    """CodexIntegration honours the executable env var."""
    from specify_cli.integrations.codex import CodexIntegration

    monkeypatch.setenv("SPECKIT_INTEGRATION_CODEX_EXECUTABLE", "/opt/codex")
    args = CodexIntegration().build_exec_args("p")
    assert args[0] == "/opt/codex"
    assert args[1] == "exec"


def test_executable_env_var_devin_integration(monkeypatch):
    """DevinIntegration honours the executable env var."""
    from specify_cli.integrations.devin import DevinIntegration

    monkeypatch.setenv("SPECKIT_INTEGRATION_DEVIN_EXECUTABLE", "/opt/devin")
    args = DevinIntegration().build_exec_args("p")
    assert args[0] == "/opt/devin"


def test_executable_env_var_opencode_integration(monkeypatch):
    """OpencodeIntegration honours the executable env var."""
    from specify_cli.integrations.opencode import OpencodeIntegration

    monkeypatch.setenv("SPECKIT_INTEGRATION_OPENCODE_EXECUTABLE", "/opt/opencode")
    args = OpencodeIntegration().build_exec_args("p")
    assert args[0] == "/opt/opencode"
    assert args[1] == "run"


def test_executable_env_var_copilot_integration(monkeypatch):
    """CopilotIntegration honours the executable env var, overriding the
    platform-specific default from `_copilot_executable()`."""
    from specify_cli.integrations.copilot import CopilotIntegration

    monkeypatch.setenv("SPECKIT_INTEGRATION_COPILOT_EXECUTABLE", "/opt/copilot")
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    args = CopilotIntegration().build_exec_args("p")
    assert args[0] == "/opt/copilot"


def test_executable_env_var_copilot_unset_uses_platform_default(monkeypatch):
    """When `SPECKIT_INTEGRATION_COPILOT_EXECUTABLE` is unset, Copilot
    falls back to the platform-specific default from `_copilot_executable()`."""
    from specify_cli.integrations.copilot import CopilotIntegration, _copilot_executable

    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")
    args = CopilotIntegration().build_exec_args("p")
    assert args[0] == _copilot_executable()


def test_executable_env_var_copilot_dispatch_command(monkeypatch):
    """CopilotIntegration.dispatch_command honours the executable env var."""
    import subprocess

    from specify_cli.integrations.copilot import CopilotIntegration

    capture = _RunCapture()
    monkeypatch.setattr(subprocess, "run", capture)
    monkeypatch.setenv("SPECKIT_INTEGRATION_COPILOT_EXECUTABLE", "/opt/copilot")
    monkeypatch.setenv("SPECKIT_COPILOT_ALLOW_ALL_TOOLS", "0")

    CopilotIntegration().dispatch_command("speckit.plan", args="body", stream=False)

    assert capture.captured_args is not None
    assert capture.captured_args[0] == "/opt/copilot"


def test_executable_and_extra_args_both_honoured(monkeypatch):
    """Both the executable override and extra args env vars can be set
    simultaneously — they are independent hooks."""
    monkeypatch.setenv("SPECKIT_INTEGRATION_CLAUDE_EXECUTABLE", "/opt/claude")
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS", "--dangerously-skip-permissions"
    )
    args = _ClaudeStub().build_exec_args("hello", model="sonnet")
    assert args == [
        "/opt/claude",
        "-p",
        "hello",
        "--dangerously-skip-permissions",
        "--model",
        "sonnet",
        "--output-format",
        "json",
    ]
