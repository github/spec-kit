"""Regression tests for integration-test environment isolation."""

from __future__ import annotations

import os
from pathlib import Path


def test_integration_tests_use_tmp_home(tmp_path: Path) -> None:
    home = tmp_path / "home"

    assert Path(os.environ["HOME"]) == home
    assert Path(os.environ["USERPROFILE"]) == home
    assert Path(os.environ["XDG_CACHE_HOME"]) == home / ".cache"
    assert Path(os.environ["XDG_CONFIG_HOME"]) == home / ".config"
    assert Path(os.environ["XDG_DATA_HOME"]) == home / ".local" / "share"

    assert home.is_dir()
    assert (home / ".cache").is_dir()
    assert (home / ".config").is_dir()
    assert (home / ".local" / "share").is_dir()
