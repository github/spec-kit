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

from typer.testing import CliRunner

from specify_cli import app


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


def test_event_run_no_stdin_uses_empty_object():
    """A TTY (no piped input) must fall back to `"{}"`, not crash."""
    with patch(
        "specify_cli.events.resolve_and_run_event_command", return_value=0
    ) as mock_run:
        result = CliRunner().invoke(
            app,
            ["event", "run", "some-command", "session_start"],
        )

    assert result.exit_code == 0, result.output
    assert mock_run.called


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
