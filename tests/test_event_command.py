"""`specify event run` must read piped stdin without crashing.

`event_run` (src/specify_cli/commands/event.py) capped its stdin read at 1
MiB to prevent a DoS (#3857), but the truncation check read a `.eof`
attribute that does not exist on any Python file-like object (including
`sys.stdin`) — every piped-stdin invocation raised `AttributeError` instead
of running, regardless of payload size. Piped stdin is the command's
documented primary use case (it is how a native hook feeds it a JSON
payload), so this broke the feature entirely rather than only rejecting
oversized payloads. Even the intended oversized-payload branch was broken a
second way: `typer.Exit(code=1, message=...)` — `typer.Exit` accepts no
`message` keyword argument, so that path raised `TypeError` instead of a
clean CLI error.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.commands.event import event_run


def test_event_run_reads_piped_stdin_payload():
    """A normal, under-the-cap piped payload must reach the handler intact."""
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
            input='{"key": "value"}',
        )

    assert result.exit_code == 0, result.output
    assert mock_run.called
    payload_arg = mock_run.call_args[0][2]
    assert payload_arg == '{"key": "value"}'


def test_event_run_empty_pipe_reads_empty_payload():
    """An empty (but non-TTY) piped stream must not crash; it forwards `""`.

    CliRunner always provides a non-TTY stdin, even when no `input=` is
    given, so this exercises the piped-input branch with zero bytes — not
    the TTY fallback. See `test_event_run_tty_uses_empty_object` below for
    the actual TTY case.
    """
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
        )

    assert result.exit_code == 0, result.output
    assert mock_run.called
    payload_arg = mock_run.call_args[0][2]
    assert payload_arg == ""


def test_event_run_tty_uses_empty_object(monkeypatch):
    """A real TTY (no piped input at all) must fall back to `"{}"`."""

    class FakeTtyStdin:
        def isatty(self):
            return True

    monkeypatch.setattr("specify_cli.commands.event.sys.stdin", FakeTtyStdin())

    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        with pytest.raises(typer.Exit):
            event_run(command_name="some-command", event_name="session_start", timeout=120)

    assert mock_run.called
    payload_arg = mock_run.call_args[0][2]
    assert payload_arg == "{}"


def test_event_run_oversized_stdin_reports_clean_error():
    """A payload exceeding the 1 MiB cap must exit 1 with the limit message,
    not crash with AttributeError (missing `.eof`) or TypeError (`typer.Exit`
    does not accept `message=`)."""
    oversized = "x" * (1 * 1024 * 1024 + 10)
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
            input=oversized,
        )

    assert result.exit_code == 1, result.output
    assert "1 MiB limit" in result.output
    assert not mock_run.called


def test_event_run_invalid_utf8_reports_clean_error():
    """A piped payload that isn't valid UTF-8 must exit 1 with the encoding
    error message, not propagate a raw `UnicodeDecodeError`, and the handler
    must never be invoked with undecodable data."""
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
            input=b"\xff\xfe",
        )

    assert result.exit_code == 1, result.output
    assert "must be valid UTF-8" in result.output
    assert not mock_run.called


def test_event_run_multibyte_payload_enforces_byte_limit():
    """The 1 MiB cap must be enforced in encoded bytes, not decoded characters.

    300,000 emoji is ~1.14 MiB of UTF-8 (4 bytes each) but only 300,000
    *characters* — comfortably under the 1,048,576 character cap a text-mode
    `sys.stdin.read(MAX_STDIN_BYTES)` would have applied. Reading from the
    binary buffer instead must still reject it.
    """
    oversized = "\U0001F600" * 300_000  # 😀, 4 bytes each in UTF-8
    assert len(oversized) < 1 * 1024 * 1024  # under the old, wrong character cap
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
            input=oversized,
        )

    assert result.exit_code == 1, result.output
    assert "1 MiB limit" in result.output
    assert not mock_run.called
