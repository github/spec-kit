"""Regression guard: console symbols must remain importable from specify_cli."""
from specify_cli import (
    console,
    StepTracker,
    get_key,
    select_with_arrows,
    BannerGroup,
    show_banner,
    BANNER,
    TAGLINE,
)


def test_console_symbols_importable():
    from rich.console import Console
    assert isinstance(console, Console)


def test_step_tracker_instantiable():
    tracker = StepTracker("test")
    tracker.add("step1", "Step One")
    tracker.complete("step1", "done")
    assert tracker.steps[0]["status"] == "done"


def test_select_with_arrows_raises_on_empty_options():
    import pytest
    with pytest.raises(ValueError, match="at least one option"):
        select_with_arrows({})
