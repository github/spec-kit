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
