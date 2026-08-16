"""
Tests for non-interactive (no-TTY) behavior of select_with_arrows.

When stdin is not a TTY (agent harness, CI, piped input), the interactive
arrow-key selector must fail fast with a clear error instead of blocking
forever on readkey(). See issue #4152.
"""

import sys

import pytest

from specify_cli._console import select_with_arrows


class FakeStdin:
    """Stdin-like object that reports not a TTY."""

    def isatty(self) -> bool:
        return False


def test_select_with_arrows_fails_fast_without_tty_and_no_default(monkeypatch):
    monkeypatch.setattr("sys.stdin", FakeStdin())
    with pytest.raises(ValueError, match="not a terminal"):
        select_with_arrows({"a": "option a", "b": "option b"})


def test_select_with_arrows_uses_default_without_tty(monkeypatch):
    monkeypatch.setattr("sys.stdin", FakeStdin())
    # With a default, no-TTY should resolve to the default (no hang).
    result = select_with_arrows(
        {"a": "option a", "b": "option b"},
        default_key="b",
    )
    assert result == "b"


def test_select_with_arrows_still_interactive_with_tty(monkeypatch):
    """With a real TTY, the interactive loop is untouched."""
    real_stdin = sys.stdin

    class RealStdin:
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr("sys.stdin", RealStdin())
    # Simulate a single 'enter' keypress on the first get_key() call.
    import specify_cli._console as console

    monkeypatch.setattr(console, "get_key", lambda: "enter")
    result = select_with_arrows({"a": "option a"})
    assert result == "a"
    monkeypatch.setattr("sys.stdin", real_stdin)
