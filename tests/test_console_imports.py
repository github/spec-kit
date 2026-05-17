"""Regression guard: console symbols must remain importable from specify_cli."""
from specify_cli import (
    BANNER,
    BannerGroup,
    StepTracker,
    TAGLINE,
    console,
    get_key,
    select_with_arrows,
    show_banner,
)


def test_console_symbols_importable():
    from rich.console import Console

    assert isinstance(console, Console)
    assert StepTracker is not None
    assert callable(get_key)
    assert callable(select_with_arrows)
    assert BannerGroup is not None
    assert callable(show_banner)
    assert isinstance(BANNER, str)
    assert isinstance(TAGLINE, str)


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
