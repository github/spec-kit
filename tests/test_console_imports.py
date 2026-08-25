"""Regression guard: console symbols must remain importable from specify_cli."""
import logging

from specify_cli import (
    console,
    StepTracker,
    select_with_arrows,
)
from specify_cli._console import logger as console_logger


def test_console_symbols_importable():
    from rich.console import Console
    assert isinstance(console, Console)


def test_console_symbols_available_from_star_import():
    namespace = {}
    exec("from specify_cli import *", namespace)

    for symbol in (
        "console",
        "StepTracker",
        "get_key",
        "select_with_arrows",
        "BannerGroup",
        "show_banner",
        "BANNER",
        "TAGLINE",
    ):
        assert symbol in namespace


def test_step_tracker_instantiable():
    tracker = StepTracker("test")
    tracker.add("step1", "Step One")
    tracker.complete("step1", "done")
    assert tracker.steps[0]["status"] == "done"


def test_select_with_arrows_raises_on_empty_options():
    import pytest
    with pytest.raises(ValueError, match="at least one option"):
        select_with_arrows({})


def test_select_with_arrows_fails_fast_when_stdin_is_not_a_tty(monkeypatch, capsys):
    """Regression for #4152: a missing TTY must error, not block on readchar."""
    import sys

    import pytest
    import typer

    def fail_readkey():
        raise AssertionError("readkey must not be called when stdin is not a TTY")

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr("specify_cli._console.readchar.readkey", fail_readkey)

    with pytest.raises(typer.Exit) as exc:
        select_with_arrows(
            {"copilot": "GitHub Copilot"},
            "Choose your coding agent integration:",
            "copilot",
            flag_hint="--integration <agent>",
        )

    assert exc.value.exit_code == 1
    captured = capsys.readouterr().out
    assert "stdin is not a TTY" in captured
    assert "--integration <agent>" in captured


def test_select_with_arrows_tty_check_does_not_call_readkey_without_hint(monkeypatch):
    import sys

    import pytest
    import typer

    def fail_readkey():
        raise AssertionError("readkey must not be called when stdin is not a TTY")

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr("specify_cli._console.readchar.readkey", fail_readkey)

    with pytest.raises(typer.Exit) as exc:
        select_with_arrows({"a": "Option A"}, "Pick one")

    assert exc.value.exit_code == 1


def test_step_tracker_refresh_error_is_logged(caplog):
    """Regression: _maybe_refresh must log exceptions instead of silently swallowing."""
    tracker = StepTracker("test")

    def failing_refresh():
        raise RuntimeError("simulated refresh failure")

    tracker.attach_refresh(failing_refresh)
    tracker.add("step1", "Step One")

    with caplog.at_level(logging.DEBUG, logger=console_logger.name):
        tracker.complete("step1", "done")

    assert "Progress tracker refresh failed" in caplog.text
    assert "RuntimeError: simulated refresh failure" in caplog.text
    assert tracker.steps[0]["status"] == "done"
